"""Genera Narrador_Qwen3TTS_Colab.ipynb a partir de narrador/texto.py y lexico.json.
Ejecuta:  python colab/construir_cuaderno.py
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TEXTO_PY = (RAIZ / "narrador" / "texto.py").read_text(encoding="utf-8")
LEXICO = json.loads((RAIZ / "lexico.json").read_text(encoding="utf-8"))
FRASES = json.loads((RAIZ / "pruebas" / "frases.json").read_text(encoding="utf-8"))

celdas = []


def md(texto):
    celdas.append({"cell_type": "markdown", "metadata": {}, "source": texto.strip("\n").splitlines(keepends=True)})


def code(texto, ocultar=False):
    meta = {"cellView": "form"} if ocultar else {}
    celdas.append({"cell_type": "code", "metadata": meta, "execution_count": None, "outputs": [],
                   "source": texto.strip("\n").splitlines(keepends=True)})


md("""
# 🎙️ Narrador documental en español · Qwen3-TTS en Google Colab

Gratis, con la GPU de Google. **Antes de empezar:** menú **Entorno de ejecución → Cambiar tipo de entorno de ejecución → GPU T4 → Guardar**.

Ejecuta las celdas **en orden** con el botón ▶️ de cada una:

1. **Instalar** (2–3 min, solo la primera vez en cada sesión)
2. **Guardar en Google Drive** (recomendado: así la voz elegida no se pierde)
3. **Elegir la voz**: escúchala y cambia la *semilla* hasta que te guste
4. **Pegar el guion y narrar**: descarga el WAV y los subtítulos SRT
5. *(Opcional)* **Pruebas de pronunciación**

Modelos: Qwen3-TTS 1.7B (Apache-2.0, uso comercial permitido). Pon «Narración generada con IA» en la descripción de tus videos.
""")

md("## 1 · Instalar")
code(r'''
#@title ▶️ Instalar (ejecuta y espera al ✅)
import subprocess, sys, torch
if not torch.cuda.is_available():
    raise SystemExit("❌ No hay GPU. Menú Entorno de ejecución → Cambiar tipo de entorno → GPU T4, y vuelve a ejecutar.")
print("GPU:", torch.cuda.get_device_name(0))
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "qwen-tts", "num2words", "pyloudnorm", "jiwer"], check=True)
print("✅ Instalado. Si más abajo aparece un error de 'transformers', usa Entorno de ejecución → Reiniciar sesión y ejecuta desde la celda 2.")
''', ocultar=True)

md("## 2 · Guardar en Google Drive (recomendado)")
code(r'''
#@title ▶️ Conectar Drive (las voces y narraciones se guardan en MyDrive/Narrador)
usar_drive = True #@param {type:"boolean"}
from pathlib import Path
if usar_drive:
    from google.colab import drive
    drive.mount("/content/drive")
    CARPETA = Path("/content/drive/MyDrive/Narrador")
else:
    CARPETA = Path("/content/Narrador")
(CARPETA / "voces").mkdir(parents=True, exist_ok=True)
(CARPETA / "narraciones").mkdir(parents=True, exist_ok=True)
print("📁 Carpeta de trabajo:", CARPETA)
''', ocultar=True)

md("### Motor (no hace falta tocar nada; solo ejecútala)")
code("%%writefile /content/texto.py\n" + TEXTO_PY.replace("Path(__file__).resolve().parent.parent / \"lexico.json\"", "Path(\"/content/lexico.json\")"))
code(r'''
#@title ▶️ Cargar motor y léxico de pronunciación
import json, math, re, time, gc
import numpy as np, soundfile as sf, torch
from IPython.display import Audio, display, HTML
import sys; sys.path.insert(0, "/content")
from texto import dividir, normalizar

# Léxico: a la izquierda cómo aparece en el guion, a la derecha cómo debe sonar. Edítalo aquí.
LEXICO = ''' + json.dumps({k: v for k, v in LEXICO.items() if not k.startswith("_")}, ensure_ascii=False, indent=2) + r'''
lex_dril = CARPETA / "lexico.json"
if lex_dril.exists():  # si ya guardaste un léxico en Drive, se usa ese
    LEXICO.update(json.loads(lex_dril.read_text(encoding="utf-8")))
lex_dril.write_text(json.dumps(LEXICO, ensure_ascii=False, indent=2), encoding="utf-8")

from qwen_tts import Qwen3TTSModel
DTYPE = torch.bfloat16 if torch.cuda.is_bf16_supported() and "T4" not in torch.cuda.get_device_name(0) else torch.float16
_MODELOS = {}
def modelo(tipo):
    nombre = {"diseno": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", "base": "Qwen/Qwen3-TTS-12Hz-1.7B-Base"}[tipo]
    if nombre not in _MODELOS:
        print("Cargando", nombre, "… (la primera vez descarga ~4 GB)")
        _MODELOS[nombre] = Qwen3TTSModel.from_pretrained(nombre, device_map="cuda:0", dtype=DTYPE, attn_implementation="sdpa")
    return _MODELOS[nombre]

def liberar(tipo):
    nombre = {"diseno": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", "base": "Qwen/Qwen3-TTS-12Hz-1.7B-Base"}[tipo]
    _MODELOS.pop(nombre, None); gc.collect(); torch.cuda.empty_cache()

def recortar(a, sr, umbral_db=-45, margen=0.04):
    v = int(0.01 * sr); n = len(a) // v
    if n == 0: return a
    rms = np.sqrt(np.mean(a[: n * v].reshape(n, v) ** 2, axis=1) + 1e-12)
    act = np.where(20 * np.log10(rms) > umbral_db)[0]
    if act.size == 0: return a
    return a[max(0, act[0] * v - int(margen * sr)): min(len(a), (act[-1] + 1) * v + int(margen * sr))]

def fundidos(a, sr, ms=12):
    k = min(len(a) // 2, int(ms / 1000 * sr))
    if k > 0:
        r = np.linspace(0, 1, k); a[:k] *= r; a[-k:] *= r[::-1]
    return a

def sonoridad(a, sr, lufs=-16.0):
    import pyloudnorm as pyln
    try:
        actual = pyln.Meter(sr).integrated_loudness(a)
        if math.isfinite(actual): a = pyln.normalize.loudness(a, actual, lufs)
    except Exception:
        a = a / (np.max(np.abs(a)) or 1) * 0.7
    p = np.max(np.abs(a))
    return a / p * 0.98 if p > 0.98 else a

def srt(manifiesto):
    def ts(x):
        h, r = divmod(x, 3600); m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    return "\n".join(f"{m['n']}\n{ts(m['inicio'])} --> {ts(m['fin'])}\n{m['texto']}\n" for m in manifiesto)
print("✅ Motor listo.")
''', ocultar=True)

md("## 3 · Elegir la voz")
code(r'''
#@title ▶️ Diseñar y escuchar la voz
voz = "Narradora documental (cálida, serena)" #@param ["Narrador documental (grave, pausado)", "Narrador cercano (claro, joven)", "Narradora documental (cálida, serena)", "Narradora periodística (clara, dinámica)", "Personalizada (escribe la descripción abajo)"]
descripcion_personalizada = "" #@param {type:"string"}
expresividad = "natural" #@param ["sobria", "natural", "expresiva"]
semilla = 7 #@param {type:"integer"}

VOCES = {
  "Narrador documental (grave, pausado)": "Adult male narrator in his mid-40s, deep warm baritone, native Latin American Spanish speaker with a neutral accent, crisp diction, calm and authoritative documentary delivery, measured pace.",
  "Narrador cercano (claro, joven)": "Male narrator around 30 years old, clear bright midrange voice, native neutral Latin American Spanish, friendly and engaging explainer tone, steady pace, very clear articulation.",
  "Narradora documental (cálida, serena)": "Adult female narrator in her early 40s, warm low-mezzo voice, native Latin American Spanish speaker with a neutral accent, serene and trustworthy documentary delivery, measured pace, crisp diction.",
  "Narradora periodística (clara, dinámica)": "Female news presenter around 35, clear confident voice, native neutral Latin American Spanish, dynamic yet serious journalistic delivery, precise articulation, moderate pace.",
}
ESTILO = {"sobria": (0.6, "Calm, measured, neutral documentary narration with minimal emotion."),
          "natural": (0.75, "Natural, warm documentary narration with gentle emphasis on key facts."),
          "expresiva": (0.9, "Engaging, expressive storytelling with clear emphasis on key figures and controlled emotion.")}
TEXTO_REF = ("Bienvenidos. En este documental recorreremos la historia de un país del Caribe, "
             "sus montañas, su gente y los desafíos que enfrenta hoy, con datos verificados y mucho respeto.")

desc = descripcion_personalizada.strip() if voz.startswith("Personalizada") else VOCES[voz]
if not desc:
    raise SystemExit("Escribe una descripción personalizada (en inglés funciona mejor).")
TEMP, estilo = ESTILO[expresividad]
import unicodedata
base_nombre = unicodedata.normalize("NFKD", voz if not voz.startswith("Personalizada") else desc[:30]).encode("ascii", "ignore").decode()
slug = re.sub(r"[^a-z0-9]+", "_", base_nombre.lower()).strip("_")
REF_WAV = CARPETA / "voces" / f"{slug}__{expresividad}__s{semilla}.wav"

if REF_WAV.exists():
    print("Ya tenías esta voz guardada; la reutilizo:", REF_WAV.name)
    ref_audio, SR = sf.read(REF_WAV, dtype="float32")
else:
    torch.manual_seed(semilla); np.random.seed(semilla)
    wavs, SR = modelo("diseno").generate_voice_design(text=TEXTO_REF, language="Spanish",
                                                       instruct=f"{desc} {estilo}", temperature=0.7)
    ref_audio = sonoridad(fundidos(recortar(np.asarray(wavs[0], dtype=np.float32), SR), SR), SR)
    sf.write(REF_WAV, ref_audio, SR, subtype="PCM_16")
    REF_WAV.with_suffix(".json").write_text(json.dumps({"voz": voz, "descripcion": desc, "expresividad": expresividad,
                                                        "semilla": semilla}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"🔊 {voz} · semilla {semilla} · {expresividad}")
display(Audio(ref_audio, rate=SR))
print("¿No te convence? Cambia la semilla (por ejemplo 8, 9, 10…) y vuelve a ejecutar. Apunta la que te guste.")
''', ocultar=True)

md("## 4 · Pegar el guion y narrar")
code(r'''
#@title ✍️ Pega tu guion entre las comillas triples (separa los párrafos con una línea en blanco)
GUION = """
¿Y quién gobierna Haití hoy? En 2024 se creó un Consejo Presidencial de Transición, el CPT, con la tarea de pacificar el país y organizar elecciones. Pero su mandato expiró el 7 de febrero de 2026 sin que se lograra celebrar los comicios.

Desde entonces, el primer ministro Alix Didier Fils-Aimé quedó al frente del Poder Ejecutivo sin presidente ni Parlamento en funciones.
"""
''')
code(r'''
#@title ▶️ Narrar y descargar
nombre_archivo = "narracion" #@param {type:"string"}
solo_vista_previa = False #@param {type:"boolean"}
pausa_entre_frases = 0.3 #@param {type:"number"}
pausa_entre_parrafos = 0.8 #@param {type:"number"}
ver_texto_leido = False #@param {type:"boolean"}

if "REF_WAV" not in globals():
    raise SystemExit("Primero ejecuta la celda 3 (elegir la voz).")
liberar("diseno")
base = modelo("base")
prompt = base.create_voice_clone_prompt(ref_audio=str(REF_WAV), ref_text=TEXTO_REF)

segmentos = dividir(GUION, 280)
if solo_vista_previa: segmentos = segmentos[:1]
if not segmentos: raise SystemExit("El guion está vacío.")

def generar(texto, s):
    torch.manual_seed(s); np.random.seed(s)
    w, sr = base.generate_voice_clone(text=texto, language="Spanish", voice_clone_prompt=prompt, temperature=TEMP)
    return recortar(np.asarray(w[0], dtype=np.float32), sr), sr

partes, manifiesto, t, inicio = [], [], 0.0, time.time()
for i, seg in enumerate(segmentos):
    leido = normalizar(seg.texto, LEXICO)
    if ver_texto_leido: print(f"   leído: {leido}")
    esperado = max(1.0, len(leido) / 14.5)
    mejor = None
    for intento in range(3):  # reintenta si la duración sale anómala (repeticiones o cortes)
        s = semilla + i + intento * 7919
        audio, SR = generar(leido, s)
        ratio = len(audio) / SR / esperado
        if mejor is None or abs(math.log(max(ratio, 1e-3))) < abs(math.log(max(mejor[1], 1e-3))):
            mejor = (audio, ratio, s)
        if 0.55 <= ratio <= 1.8: break
    audio, ratio, s = mejor
    audio = fundidos(audio, SR)
    dur = len(audio) / SR
    ok = 0.55 <= ratio <= 1.8
    print(f"[{i+1}/{len(segmentos)}] {'✅' if ok else '⚠️ revisar'} {dur:5.1f}s  {seg.texto[:70]}…")
    manifiesto.append({"n": i + 1, "texto": seg.texto, "leido": leido, "inicio": round(t, 3), "fin": round(t + dur, 3),
                       "semilla": s, "ratio": round(ratio, 2), "ok": ok})
    pausa = pausa_entre_parrafos if seg.final_de_parrafo else pausa_entre_frases
    partes += [audio, np.zeros(int(pausa * SR), np.float32)]
    t += dur + pausa

final = sonoridad(np.concatenate(partes[:-1]), SR)
destino = CARPETA / "narraciones" / f"{nombre_archivo}_{time.strftime('%Y%m%d_%H%M%S')}"
sf.write(destino.with_suffix(".wav"), final, SR, subtype="PCM_16")
destino.with_suffix(".srt").write_text(srt(manifiesto), encoding="utf-8")
destino.with_suffix(".json").write_text(json.dumps({"voz": REF_WAV.name, "segmentos": manifiesto}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n✅ {len(final)/SR:.1f} s de audio en {time.time()-inicio:.0f} s → {destino.with_suffix('.wav')}")
display(Audio(final, rate=SR))
from google.colab import files
files.download(str(destino.with_suffix(".wav"))); files.download(str(destino.with_suffix(".srt")))
''', ocultar=True)

md("## 5 · (Opcional) Pruebas de pronunciación\nGenera frases difíciles con tu voz, las transcribe con Whisper y marca las que fallan. Lo que suene mal, añádelo al léxico de la celda «Cargar motor».")
code(r'''
#@title ▶️ Probar pronunciación
FRASES = ''' + json.dumps(FRASES, ensure_ascii=False, indent=1) + r'''
import base64, io, html, unicodedata, jiwer
from transformers import pipeline
from texto import normalizar_numeros
if "prompt" not in globals():
    liberar("diseno"); base = modelo("base")
    prompt = base.create_voice_clone_prompt(ref_audio=str(REF_WAV), ref_text=TEXTO_REF)
asr = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3-turbo", torch_dtype=DTYPE, device="cuda:0")
def comparable(t):
    t = unicodedata.normalize("NFD", normalizar_numeros(t).lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-zñ0-9 ]+", " ", t)).strip()
filas, ok = [], 0
for i, f in enumerate(FRASES, 1):
    torch.manual_seed(semilla + i)
    w, sr = base.generate_voice_clone(text=normalizar(f["texto"], LEXICO), language="Spanish", voice_clone_prompt=prompt, temperature=TEMP)
    a = recortar(np.asarray(w[0], dtype=np.float32), sr)
    oido = asr({"raw": a, "sampling_rate": sr}, generate_kwargs={"language": "spanish"})["text"].strip()
    cer = jiwer.cer(comparable(f["texto"]), comparable(oido))
    estado = "revisar a oído" if f.get("revisar_oido") else ("OK" if cer <= 0.12 else "FALLA")
    ok += estado == "OK"
    buf = io.BytesIO(); sf.write(buf, a, sr, format="WAV"); b64 = base64.b64encode(buf.getvalue()).decode()
    color = {"OK": "#1f9d55", "FALLA": "#d64545", "revisar a oído": "#b7791f"}[estado]
    filas.append(f"<tr><td>{html.escape(f['texto'])}</td><td>{html.escape(oido)}</td><td>{cer:.2f}</td>"
                 f"<td style='color:{color};font-weight:700'>{estado}</td><td><audio controls src='data:audio/wav;base64,{b64}'></audio></td></tr>")
    print(f"{i:02d} {estado:14s} CER {cer:.2f}  {f['texto'][:60]}")
display(HTML(f"<p><b>{ok}/{len(FRASES)} OK</b></p><table style='border-collapse:collapse'><tr><th>Texto</th><th>Lo que entendió Whisper</th><th>CER</th><th>Estado</th><th>Audio</th></tr>{''.join(filas)}</table>"))
''', ocultar=True)

nb = {"cells": celdas, "metadata": {"accelerator": "GPU", "colab": {"provenance": [], "gpuType": "T4", "name": "Narrador_Qwen3TTS_Colab.ipynb"},
                                    "kernelspec": {"name": "python3", "display_name": "Python 3"}, "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 0}
destino = Path(__file__).resolve().parent / "Narrador_Qwen3TTS_Colab.ipynb"
destino.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("Cuaderno generado:", destino)
