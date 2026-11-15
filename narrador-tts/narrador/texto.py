"""Preparación del texto en español: normalización para TTS y división en segmentos.

Qwen3-TTS lee mejor el texto "como se pronuncia": cifras, siglas y símbolos
escritos en palabras. Todo lo que no esté en el léxico se deja igual.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

try:
    from num2words import num2words
except ImportError:  # num2words es opcional; sin él las cifras se dejan como están
    num2words = None

LEXICO_POR_DEFECTO = Path(__file__).resolve().parent.parent / "lexico.json"


# ---------------------------------------------------------------- léxico
def cargar_lexico(ruta: str | Path | None = None) -> dict[str, str]:
    ruta = Path(ruta) if ruta else LEXICO_POR_DEFECTO
    if not ruta.exists():
        return {}
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return {k: v for k, v in datos.items() if not k.startswith("_")}


def aplicar_lexico(texto: str, lexico: dict[str, str]) -> str:
    # Las entradas más largas primero, para que "US$" no lo pise "US".
    for termino in sorted(lexico, key=len, reverse=True):
        patron = r"(?<![\wÁÉÍÓÚÑáéíóúñ])" + re.escape(termino) + r"(?![\wÁÉÍÓÚÑáéíóúñ])"
        texto = re.sub(patron, lexico[termino], texto)
    return texto


# ---------------------------------------------------------------- números
FEMENINOS = {
    "personas", "víctimas", "muertes", "escuelas", "tropas", "toneladas", "familias", "horas", "semanas",
    "mujeres", "niñas", "viviendas", "comunidades", "organizaciones", "elecciones", "vidas", "casas",
    "hectáreas", "ciudades", "deportaciones", "expulsiones", "camas", "plazas", "fuerzas", "bandas",
    "pandillas", "persona", "víctima", "escuela", "vez",
}


def _palabras(n: int | float, siguiente: str = "") -> str:
    if num2words is None:
        return str(n)
    t = num2words(n, lang="es")
    if siguiente.lower() in FEMENINOS:
        t = re.sub(r"ientos\b", "ientas", t)
        t = re.sub(r"\buno$", "una", t).replace("veintiuno", "veintiuna")
        t = re.sub(r"\buno\b(?= mil)", "un", t)
    elif siguiente and re.match(r"[a-záéíóúñ]", siguiente.lower()):
        t = re.sub(r"uno$", "ún" if t.endswith("veintiuno") else "un", t).replace("veintiún", "veintiún")
    return t


def _entero(cadena: str) -> int:
    return int(cadena.replace(".", "").replace("\u202f", "").replace(" ", ""))


_SIG = r"(?=(?:\s+(?:de\s+)?([a-záéíóúñ]+))?)"   # captura la palabra siguiente (para concordar género)


def normalizar_numeros(texto: str) -> str:
    if num2words is None:
        return texto
    # Rangos "80–90 %" -> "80 a 90 %"
    texto = re.sub(r"(\d+(?:,\d+)?)\s*[–-]\s*(\d+(?:,\d+)?)\s*%", r"\1 a \2 %", texto)
    # Porcentajes
    texto = re.sub(r"(\d+(?:,\d+)?)\s*%", r"\1 por ciento", texto)
    # Moneda: "US$ 880 millones" -> "880 millones de dólares"; "US$ 50" -> "50 dólares"
    texto = re.sub(r"US\$\s*(\d[\d.]*(?:,\d+)?)(\s+(?:mil\s+)?millones|\s+mil)?",
                   lambda m: f"{m.group(1)}{m.group(2) or ''} {'de ' if m.group(2) and 'millones' in m.group(2) else ''}dólares", texto)
    # Decimales con coma: "1,5" -> "uno coma cinco"
    def dec(m):
        ent, frac = m.group(1), m.group(2)
        frac_txt = _palabras(int(frac)) if not frac.startswith("0") else " ".join(_palabras(int(c)) for c in frac)
        return f"{_palabras(_entero(ent))} coma {frac_txt}"
    texto = re.sub(r"(?<![\d.])(\d{1,3}(?:\.\d{3})*|\d+),(\d+)(?![\d.]|,\d)", dec, texto)
    # Ordinales "1.º", "3.ª"
    texto = re.sub(r"(\d+)\.?\s*º(?=\s+[a-záéíóúñ])", lambda m: re.sub(r"(prim|terc)ero$", r"\1er", num2words(int(m.group(1)), lang="es", to="ordinal")), texto)
    texto = re.sub(r"(\d+)\.?\s*º", lambda m: num2words(int(m.group(1)), lang="es", to="ordinal"), texto)
    texto = re.sub(r"(\d+)\.?\s*ª", lambda m: num2words(int(m.group(1)), lang="es", to="ordinal")[:-1] + "a", texto)
    # Miles con punto o espacio fino: "4.217 muertes" -> "cuatro mil doscientas diecisiete muertes"
    texto = re.sub(r"(?<![\d,])(\d{1,3}(?:[.\u202f]\d{3})+)(?!\d|,\d)" + _SIG,
                   lambda m: _palabras(_entero(m.group(1)), m.group(2) or ""), texto)
    # Resto de enteros (años incluidos)
    texto = re.sub(r"(?<!\w)(?<!\d,)(\d+)(?!\w|,\d)" + _SIG,
                   lambda m: _palabras(int(m.group(1)), m.group(2) or ""), texto)
    return texto


def normalizar(texto: str, lexico: dict[str, str] | None = None) -> str:
    texto = texto.replace(" ", " ")
    texto = re.sub(r"\[\d+\]", "", texto)            # quita referencias tipo [12]
    texto = re.sub(r"\[[A-ZÁÉÍÓÚ ]+\]", "", texto)    # quita marcas tipo [VERIFICAR]
    # Rangos de años/cifras "1957–1986" -> "1957 a 1986" (los % se tratan después)
    texto = re.sub(r"(\d)\s*[–—-]\s*(\d[\d.,]*)(?!\s*%)", r"\1 a \2", texto)
    # Rayas de inciso -> pausa breve
    texto = re.sub(r"\s*[—–]\s*", ", ", texto)
    if lexico:
        texto = aplicar_lexico(texto, lexico)
    texto = normalizar_numeros(texto)
    texto = re.sub(r"\s+([.,;:!?…])", r"\1", texto)
    texto = re.sub(r",\s*,", ",", texto)
    texto = re.sub(r"[ \t]+", " ", texto)
    return texto.strip()


# ---------------------------------------------------------------- división
@dataclass
class Segmento:
    texto: str
    parrafo: int          # índice del párrafo (para pausas más largas entre párrafos)
    final_de_parrafo: bool


def dividir(texto: str, max_caracteres: int = 280) -> list[Segmento]:
    """Divide en párrafos (líneas en blanco) y, si un párrafo es largo,
    en grupos de frases completas de hasta `max_caracteres`.

    Segmentos cortos dan una voz más estable: el modelo pierde el hilo
    (repeticiones, cambios de ritmo) con entradas muy largas.
    """
    parrafos = [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]
    segmentos: list[Segmento] = []
    for i, p in enumerate(parrafos):
        p = re.sub(r"\s*\n\s*", " ", p)
        frases = re.split(r"(?<=[.!?…;:])\s+(?=[¿¡\"“A-ZÁÉÍÓÚÑ0-9])", p)
        grupo = ""
        trozos: list[str] = []
        for f in frases:
            if len(f) > max_caracteres:  # frase larguísima: corta por comas
                for sub in re.split(r"(?<=,)\s+", f):
                    if grupo and len(grupo) + len(sub) + 1 > max_caracteres:
                        trozos.append(grupo); grupo = sub
                    else:
                        grupo = f"{grupo} {sub}".strip()
                continue
            if grupo and len(grupo) + len(f) + 1 > max_caracteres:
                trozos.append(grupo); grupo = f
            else:
                grupo = f"{grupo} {f}".strip()
        if grupo:
            trozos.append(grupo)
        for j, t in enumerate(trozos):
            segmentos.append(Segmento(texto=t, parrafo=i, final_de_parrafo=(j == len(trozos) - 1)))
    return segmentos
