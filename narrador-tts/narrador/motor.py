"""Motor de narración con Qwen3-TTS sobre MLX-Audio (Apple Silicon).

Flujo recomendado para una voz consistente en español:
  1. VoiceDesign crea UNA muestra de referencia de la voz (≈10 s) a partir de
     una descripción (género, edad, timbre, estilo).
  2. El modelo Base clona esa muestra para cada segmento del guion.
Así todos los párrafos comparten exactamente la misma referencia, en lugar
de "reinventar" la voz en cada llamada.

Alternativa: voces predefinidas (CustomVoice). Ninguna es nativa en español,
por lo que pueden tener acento; útiles para pruebas rápidas.
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import soundfile as sf

from .texto import Segmento, cargar_lexico, dividir, normalizar

RAIZ = Path(__file__).resolve().parent.parent
DIR_VOCES = RAIZ / "voces"

# ------------------------------------------------------------------ modelos
CALIDADES = ("8bit", "6bit", "4bit", "bf16")


def repo(tipo: str, calidad: str = "8bit", tam: str = "1.7B") -> str:
    tipos = {"diseno": "VoiceDesign", "base": "Base", "predefinida": "CustomVoice"}
    if tipo == "diseno":
        tam = "1.7B"  # VoiceDesign solo existe en 1.7B
    return f"mlx-community/Qwen3-TTS-12Hz-{tam}-{tipos[tipo]}-{calidad}"


# ------------------------------------------------------------------ voces
# Descripciones en inglés: el modelo se entrenó sobre todo con instrucciones en
# chino e inglés y las sigue con más fidelidad. El idioma de salida lo fija
# `language="spanish"` y el texto.
VOCES_DISENADAS = {
    "narrador_documental": {
        "genero": "masculina",
        "etiqueta": "Narrador documental (grave, pausado)",
        "descripcion": "Adult male narrator in his mid-40s, deep warm baritone, native Latin American Spanish speaker "
                       "with a neutral accent, crisp diction, calm and authoritative documentary delivery, measured pace.",
    },
    "narrador_cercano": {
        "genero": "masculina",
        "etiqueta": "Narrador cercano (claro, joven)",
        "descripcion": "Male narrator around 30 years old, clear bright midrange voice, native neutral Latin American "
                       "Spanish, friendly and engaging explainer tone, steady pace, very clear articulation.",
    },
    "narradora_documental": {
        "genero": "femenina",
        "etiqueta": "Narradora documental (cálida, serena)",
        "descripcion": "Adult female narrator in her early 40s, warm low-mezzo voice, native Latin American Spanish speaker "
                       "with a neutral accent, serene and trustworthy documentary delivery, measured pace, crisp diction.",
    },
    "narradora_periodistica": {
        "genero": "femenina",
        "etiqueta": "Narradora periodística (clara, dinámica)",
        "descripcion": "Female news presenter around 35, clear confident voice, native neutral Latin American Spanish, "
                       "dynamic yet serious journalistic delivery, precise articulation, moderate pace.",
    },
}

# Voces predefinidas de Qwen3-TTS (CustomVoice). Lengua nativa entre paréntesis.
VOCES_PREDEFINIDAS = {
    "masculina": ["Ryan", "Aiden", "Uncle_Fu", "Dylan", "Eric"],
    "femenina": ["Serena", "Vivian", "Sohee", "Ono_Anna"],
}

EXPRESIVIDAD = {
    # temperatura de muestreo + estilo de lectura
    "sobria": (0.60, "Calm, measured, neutral documentary narration with minimal emotion."),
    "natural": (0.75, "Natural, warm documentary narration with gentle emphasis on key facts."),
    "expresiva": (0.90, "Engaging, expressive storytelling with clear emphasis on key figures and controlled emotion."),
}

# Frase de referencia: cubre vocales, ñ, ll/y, rr, acentos y una cifra.
TEXTO_REFERENCIA = (
    "Bienvenidos. En este documental recorreremos la historia de un país del Caribe, "
    "sus montañas, su gente y los desafíos que enfrenta hoy, con datos verificados y mucho respeto."
)

SR = 24000  # frecuencia de salida de Qwen3-TTS


def temperatura_desde(nivel: str | float) -> tuple[float, str]:
    if isinstance(nivel, (int, float)):
        x = max(0.0, min(1.0, float(nivel)))
        temp = 0.55 + 0.40 * x
        estilo = EXPRESIVIDAD["sobria" if x < .34 else "natural" if x < .67 else "expresiva"][1]
        return temp, estilo
    return EXPRESIVIDAD[nivel]


# ------------------------------------------------------------------ audio
def _recortar_silencio(a: np.ndarray, umbral_db: float = -45.0, margen: float = 0.04) -> np.ndarray:
    if a.size == 0:
        return a
    ventana = int(0.01 * SR)
    n = len(a) // ventana
    if n == 0:
        return a
    rms = np.sqrt(np.mean(a[: n * ventana].reshape(n, ventana) ** 2, axis=1) + 1e-12)
    activo = np.where(20 * np.log10(rms) > umbral_db)[0]
    if activo.size == 0:
        return a
    ini = max(0, activo[0] * ventana - int(margen * SR))
    fin = min(len(a), (activo[-1] + 1) * ventana + int(margen * SR))
    return a[ini:fin]


def _fundidos(a: np.ndarray, ms: float = 12) -> np.ndarray:
    k = min(len(a) // 2, int(ms / 1000 * SR))
    if k > 0:
        rampa = np.linspace(0, 1, k)
        a[:k] *= rampa
        a[-k:] *= rampa[::-1]
    return a


def normalizar_sonoridad(a: np.ndarray, lufs: float = -16.0) -> np.ndarray:
    """-16 LUFS: estándar habitual para voz en web, YouTube y podcasts."""
    try:
        import pyloudnorm as pyln
        medidor = pyln.Meter(SR)
        actual = medidor.integrated_loudness(a)
        if math.isfinite(actual):
            a = pyln.normalize.loudness(a, actual, lufs)
    except Exception:
        pico = np.max(np.abs(a)) or 1.0
        a = a / pico * 0.7
    pico = np.max(np.abs(a))
    if pico > 0.98:  # limitador simple para no saturar
        a = a / pico * 0.98
    return a


# ------------------------------------------------------------------ motor
@dataclass
class Opciones:
    modo: str = "disenada"             # disenada | predefinida | clonar
    voz: str = "narrador_documental"   # clave de VOCES_DISENADAS o nombre predefinido
    expresividad: str | float = "natural"
    semilla: int = 1234
    calidad: str = "8bit"
    tam_base: str = "1.7B"             # 1.7B (mejor) o 0.6B (más rápido)
    ref_audio: Optional[str] = None    # solo modo "clonar": tu propia grabación
    ref_texto: Optional[str] = None
    max_caracteres: int = 280
    pausa_frase: float = 0.30
    pausa_parrafo: float = 0.80
    lufs: float = -16.0
    reintentos: int = 2
    usar_lexico: bool = True


class Narrador:
    def __init__(self, opciones: Opciones | None = None, log: Callable[[str], None] = print):
        self.op = opciones or Opciones()
        self.log = log
        self._modelos: dict[str, object] = {}

    # ---- carga perezosa de modelos (se descargan la primera vez a ~/.cache/huggingface)
    def _modelo(self, tipo: str):
        nombre = repo(tipo, self.op.calidad, self.op.tam_base)
        if nombre not in self._modelos:
            from mlx_audio.tts.utils import load_model
            self.log(f"Cargando {nombre} …")
            self._modelos[nombre] = load_model(nombre)
        return self._modelos[nombre]

    @staticmethod
    def _semilla(s: int):
        import mlx.core as mx
        mx.random.seed(int(s))
        np.random.seed(int(s) % (2**32))

    @staticmethod
    def _juntar(resultados) -> np.ndarray:
        return np.concatenate([np.array(r.audio, dtype=np.float32).reshape(-1) for r in resultados]) if resultados else np.zeros(0, np.float32)

    # ---- referencia de voz diseñada
    def ruta_referencia(self, voz: str | None = None, expresividad: str | None = None) -> Path:
        voz = voz or self.op.voz
        exp = expresividad or (self.op.expresividad if isinstance(self.op.expresividad, str) else "natural")
        return DIR_VOCES / f"{voz}__{exp}__s{self.op.semilla}.wav"

    def disenar_referencia(self, forzar: bool = False) -> Path:
        """Crea (o reutiliza) la muestra de referencia de la voz elegida."""
        ruta = self.ruta_referencia()
        if ruta.exists() and not forzar:
            return ruta
        if self.op.voz not in VOCES_DISENADAS:
            raise ValueError(f"Voz diseñada desconocida: {self.op.voz}. Opciones: {list(VOCES_DISENADAS)}")
        _, estilo = temperatura_desde(self.op.expresividad)
        descripcion = f"{VOCES_DISENADAS[self.op.voz]['descripcion']} {estilo}"
        modelo = self._modelo("diseno")
        self._semilla(self.op.semilla)
        self.log(f"Diseñando la voz «{VOCES_DISENADAS[self.op.voz]['etiqueta']}» (semilla {self.op.semilla}) …")
        audio = self._juntar(list(modelo.generate_voice_design(
            text=TEXTO_REFERENCIA, language="spanish", instruct=descripcion, temperature=0.7)))
        audio = normalizar_sonoridad(_fundidos(_recortar_silencio(audio)), self.op.lufs)
        DIR_VOCES.mkdir(exist_ok=True)
        sf.write(ruta, audio, SR, subtype="PCM_16")
        ruta.with_suffix(".txt").write_text(TEXTO_REFERENCIA, encoding="utf-8")
        ruta.with_suffix(".json").write_text(json.dumps({"voz": self.op.voz, "descripcion": descripcion,
                                                          "semilla": self.op.semilla}, ensure_ascii=False, indent=2), encoding="utf-8")
        self.log(f"Referencia guardada en {ruta}")
        return ruta

    # ---- un segmento
    def _sintetizar(self, texto: str, semilla: int) -> np.ndarray:
        temp, estilo = temperatura_desde(self.op.expresividad)
        self._semilla(semilla)
        if self.op.modo == "predefinida":
            if self.op.tam_base == "0.6B":
                self.log("Aviso: el modelo 0.6B CustomVoice no admite instrucciones de estilo; se ignoran.")
            modelo = self._modelo("predefinida")
            res = modelo.generate_custom_voice(text=texto, speaker=self.op.voz, language="spanish",
                                               instruct=None if self.op.tam_base == "0.6B" else estilo,
                                               temperature=temp)
        else:
            if self.op.modo == "clonar":
                if not (self.op.ref_audio and self.op.ref_texto):
                    raise ValueError("El modo «clonar» necesita ref_audio y ref_texto (transcripción exacta).")
                ref, ref_txt = self.op.ref_audio, self.op.ref_texto
            else:
                ref = str(self.disenar_referencia())
                ref_txt = TEXTO_REFERENCIA
            modelo = self._modelo("base")
            res = modelo.generate(text=texto, ref_audio=ref, ref_text=ref_txt, lang_code="spanish", temperature=temp)
        return self._juntar(list(res))

    def sintetizar_segmento(self, texto: str, semilla: int) -> tuple[np.ndarray, dict]:
        """Genera un segmento con control de calidad: si la duración es anómala
        (el modelo repitió o se cortó), reintenta con otra semilla."""
        esperado = max(1.0, len(texto) / 14.5)  # ≈14,5 caracteres por segundo en español narrado
        mejor, info = None, {}
        for intento in range(self.op.reintentos + 1):
            s = semilla + intento * 7919
            audio = _recortar_silencio(self._sintetizar(texto, s))
            ratio = (len(audio) / SR) / esperado
            ok = 0.55 <= ratio <= 1.8
            if mejor is None or abs(math.log(max(ratio, 1e-3))) < abs(math.log(max(info["ratio"], 1e-3))):
                mejor, info = audio, {"semilla": s, "ratio": round(ratio, 2), "intentos": intento + 1, "ok": ok}
            if ok:
                break
            self.log(f"  duración anómala (ratio {ratio:.2f}); reintento {intento + 1}…")
        return _fundidos(mejor), info

    # ---- texto completo
    def narrar(self, texto: str, salida: str | Path, progreso: Callable[[int, int, str], None] | None = None) -> dict:
        lexico = cargar_lexico() if self.op.usar_lexico else {}
        segmentos: list[Segmento] = dividir(texto, self.op.max_caracteres)
        if not segmentos:
            raise ValueError("El texto está vacío.")
        salida = Path(salida)
        dir_seg = salida.with_suffix("")
        dir_seg = dir_seg.parent / (dir_seg.name + "_segmentos")
        dir_seg.mkdir(parents=True, exist_ok=True)

        partes, manifiesto, t = [], [], 0.0
        inicio = time.time()
        for i, seg in enumerate(segmentos):
            leido = normalizar(seg.texto, lexico)
            if progreso:
                progreso(i, len(segmentos), seg.texto)
            self.log(f"[{i + 1}/{len(segmentos)}] {seg.texto[:70]}…")
            audio, info = self.sintetizar_segmento(leido, self.op.semilla + i)
            sf.write(dir_seg / f"{i + 1:03d}.wav", normalizar_sonoridad(audio.copy(), self.op.lufs), SR, subtype="PCM_16")
            dur = len(audio) / SR
            manifiesto.append({"n": i + 1, "texto": seg.texto, "leido": leido, "inicio": round(t, 3),
                               "fin": round(t + dur, 3), **info})
            pausa = self.op.pausa_parrafo if seg.final_de_parrafo else self.op.pausa_frase
            partes += [audio, np.zeros(int(pausa * SR), np.float32)]
            t += dur + pausa

        final = normalizar_sonoridad(np.concatenate(partes[:-1]), self.op.lufs)
        sf.write(salida, final, SR, subtype="PCM_16")
        meta = {"salida": str(salida), "duracion_s": round(len(final) / SR, 2),
                "tiempo_generacion_s": round(time.time() - inicio, 1),
                "opciones": {k: v for k, v in asdict(self.op).items()}, "segmentos": manifiesto}
        salida.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        salida.with_suffix(".srt").write_text(_srt(manifiesto), encoding="utf-8")
        self.log(f"Listo: {salida} ({meta['duracion_s']} s). Subtítulos: {salida.with_suffix('.srt')}")
        return meta


def _srt(manifiesto: list[dict]) -> str:
    def ts(x):
        h, r = divmod(x, 3600); m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    return "\n".join(f"{m['n']}\n{ts(m['inicio'])} --> {ts(m['fin'])}\n{m['texto']}\n" for m in manifiesto)
