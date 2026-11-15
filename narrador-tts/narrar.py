#!/usr/bin/env python3
"""Narra un texto largo con una voz consistente y exporta WAV + SRT + JSON.

Ejemplos:
  python narrar.py guion.txt -o salida/haiti.wav
  python narrar.py guion.txt --voz narradora_documental --expresividad sobria
  python narrar.py guion.txt --modo predefinida --voz Ryan
  python narrar.py guion.txt --modo clonar --ref mi_voz.wav --ref-texto "Texto exacto que leí."
  python narrar.py --disenar --voz narrador_documental --semilla 7    # solo crea/escucha la voz
  python narrar.py --listar
"""
import argparse
import sys
from pathlib import Path

from narrador.motor import (CALIDADES, EXPRESIVIDAD, VOCES_DISENADAS, VOCES_PREDEFINIDAS, Narrador, Opciones)


def main():
    p = argparse.ArgumentParser(description="Narrador en español con Qwen3-TTS + MLX-Audio")
    p.add_argument("texto", nargs="?", help="Archivo .txt o .md (párrafos separados por una línea en blanco)")
    p.add_argument("-o", "--salida", default="salida/narracion.wav")
    p.add_argument("--modo", choices=["disenada", "predefinida", "clonar"], default="disenada")
    p.add_argument("--voz", default="narrador_documental")
    p.add_argument("--expresividad", default="natural",
                   help="sobria | natural | expresiva, o un número entre 0 y 1")
    p.add_argument("--semilla", type=int, default=1234, help="Cambia la semilla para probar otra variante de voz")
    p.add_argument("--calidad", choices=CALIDADES, default="8bit")
    p.add_argument("--rapido", action="store_true", help="Usa el modelo 0.6B (más rápido, algo menos natural)")
    p.add_argument("--ref", help="Modo clonar: tu grabación WAV (5–15 s, sin música)")
    p.add_argument("--ref-texto", help="Modo clonar: transcripción exacta de la grabación")
    p.add_argument("--max-caracteres", type=int, default=280)
    p.add_argument("--sin-lexico", action="store_true")
    p.add_argument("--disenar", action="store_true", help="Solo genera la muestra de referencia de la voz")
    p.add_argument("--listar", action="store_true", help="Muestra las voces disponibles")
    a = p.parse_args()

    if a.listar:
        print("Voces diseñadas (recomendadas para español):")
        for k, v in VOCES_DISENADAS.items():
            print(f"  {k:24s} {v['genero']:10s} {v['etiqueta']}")
        print("\nVoces predefinidas (--modo predefinida; no son nativas en español):")
        for g, vs in VOCES_PREDEFINIDAS.items():
            print(f"  {g}: {', '.join(vs)}")
        print(f"\nExpresividad: {', '.join(EXPRESIVIDAD)} o un valor 0–1")
        return

    try:
        expr = float(a.expresividad)
    except ValueError:
        expr = a.expresividad
        if expr not in EXPRESIVIDAD:
            p.error(f"--expresividad debe ser {list(EXPRESIVIDAD)} o un número 0–1")

    op = Opciones(modo=a.modo, voz=a.voz, expresividad=expr, semilla=a.semilla, calidad=a.calidad,
                  tam_base="0.6B" if a.rapido else "1.7B", ref_audio=a.ref, ref_texto=a.ref_texto,
                  max_caracteres=a.max_caracteres, usar_lexico=not a.sin_lexico)
    n = Narrador(op)

    if a.disenar:
        ruta = n.disenar_referencia(forzar=True)
        print(f"Escucha la voz en: {ruta}\nSi no te gusta, repite con otra --semilla.")
        return
    if not a.texto:
        p.error("Indica un archivo de texto (o usa --disenar / --listar)")
    texto = Path(a.texto).read_text(encoding="utf-8")
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    n.narrar(texto, a.salida)


if __name__ == "__main__":
    sys.exit(main())
