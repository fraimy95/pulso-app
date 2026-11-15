#!/usr/bin/env python3
"""Pruebas de pronunciación: genera cada frase de pruebas/frases.json con la voz
elegida, la transcribe con Whisper (local, MLX) y compara con lo esperado.

Produce pruebas/informe.html (con reproductor por frase) y pruebas/informe.csv.

  python probar_pronunciacion.py --voz narrador_documental
  python probar_pronunciacion.py --modo predefinida --voz Serena
"""
import argparse
import csv
import html
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import soundfile as sf

from narrador.motor import SR, Narrador, Opciones
from narrador.texto import cargar_lexico, normalizar, normalizar_numeros

RAIZ = Path(__file__).resolve().parent
ASR = "mlx-community/whisper-large-v3-turbo"


def comparable(t: str) -> str:
    t = normalizar_numeros(t).lower()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")  # sin tildes: Whisper a veces las omite
    t = re.sub(r"[^a-zñ0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def tasas(ref: str, hip: str) -> tuple[float, float]:
    import jiwer
    return jiwer.wer(ref, hip), jiwer.cer(ref, hip)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--modo", default="disenada", choices=["disenada", "predefinida", "clonar"])
    p.add_argument("--voz", default="narrador_documental")
    p.add_argument("--expresividad", default="natural")
    p.add_argument("--semilla", type=int, default=1234)
    p.add_argument("--ref"); p.add_argument("--ref-texto")
    p.add_argument("--frases", default=str(RAIZ / "pruebas" / "frases.json"))
    p.add_argument("--umbral-cer", type=float, default=0.12)
    a = p.parse_args()

    frases = json.loads(Path(a.frases).read_text(encoding="utf-8"))
    n = Narrador(Opciones(modo=a.modo, voz=a.voz, expresividad=a.expresividad, semilla=a.semilla,
                          ref_audio=a.ref, ref_texto=a.ref_texto))
    lexico = cargar_lexico()
    from mlx_audio.stt.utils import load_model as load_stt
    print(f"Cargando reconocedor {ASR} …")
    asr = load_stt(ASR)

    out = RAIZ / "pruebas" / "resultados"
    out.mkdir(parents=True, exist_ok=True)
    filas = []
    for i, f in enumerate(frases, 1):
        leido = normalizar(f["texto"], lexico)
        audio, info = n.sintetizar_segmento(leido, a.semilla + i)
        ruta = out / f"{i:02d}.wav"
        sf.write(ruta, audio, SR, subtype="PCM_16")
        oido = asr.generate(str(ruta), language="es").text.strip()
        wer, cer = tasas(comparable(f["texto"]), comparable(oido))
        estado = "revisar a oído" if f.get("revisar_oido") else ("OK" if cer <= a.umbral_cer else "FALLA")
        filas.append({"n": i, "categoria": f["categoria"], "texto": f["texto"], "leido": leido, "oido": oido,
                      "wer": round(wer, 3), "cer": round(cer, 3), "estado": estado, "audio": ruta.name,
                      "duracion_ratio": info["ratio"]})
        print(f"{i:02d} [{estado:14s}] CER {cer:.2f} | {f['texto'][:60]}\n    oído: {oido[:80]}")

    with open(RAIZ / "pruebas" / "informe.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0].keys())); w.writeheader(); w.writerows(filas)
    color = {"OK": "#1f9d55", "FALLA": "#d64545", "revisar a oído": "#b7791f"}
    filas_html = "".join(
        f"<tr><td>{r['n']}</td><td>{r['categoria']}</td><td>{html.escape(r['texto'])}<br><small>Leído como: {html.escape(r['leido'])}</small></td>"
        f"<td>{html.escape(r['oido'])}</td><td>{r['cer']:.2f}</td><td style='color:{color[r['estado']]};font-weight:700'>{r['estado']}</td>"
        f"<td><audio controls src='resultados/{r['audio']}'></audio></td></tr>" for r in filas)
    ok = sum(r["estado"] == "OK" for r in filas)
    (RAIZ / "pruebas" / "informe.html").write_text(f"""<!doctype html><meta charset=utf-8><title>Pruebas de pronunciación</title>
<style>body{{font-family:system-ui;margin:24px;background:#fafafa}}table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #ddd;padding:8px;vertical-align:top;text-align:left}}small{{color:#777}}</style>
<h1>Pruebas de pronunciación</h1><p>Voz: <b>{html.escape(a.voz)}</b> · modo {a.modo} · {ok}/{len(filas)} frases OK (CER ≤ {a.umbral_cer}).
Los nombres propios se marcan para revisión a oído: Whisper no los transcribe de forma fiable. Si algo suena mal, añádelo a <code>lexico.json</code>.</p>
<table><tr><th>#</th><th>Tipo</th><th>Texto</th><th>Lo que entendió Whisper</th><th>CER</th><th>Estado</th><th>Audio</th></tr>{filas_html}</table>""", encoding="utf-8")
    print(f"\n{ok}/{len(filas)} OK. Abre pruebas/informe.html para escuchar cada frase.")


if __name__ == "__main__":
    main()
