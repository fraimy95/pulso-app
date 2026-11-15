#!/usr/bin/env python3
"""Convierte el JSON de whisper.cpp (-ml 1 -sow -oj) en subtítulos para Remotion (@remotion/captions Caption[]).
uso: python subtitulos_remotion.py whisper.json salida.json [--desfase-ms 0]"""
import json, sys
src, out = sys.argv[1], sys.argv[2]
desfase = int(sys.argv[sys.argv.index("--desfase-ms") + 1]) if "--desfase-ms" in sys.argv else 0
caps = []
for seg in json.load(open(src, encoding="utf-8"))["transcription"]:
    txt = seg["text"].strip()
    if not txt:
        continue
    a, b = seg["offsets"]["from"] + desfase, seg["offsets"]["to"] + desfase
    caps.append({"text": " " + txt, "startMs": a, "endMs": b, "timestampMs": (a + b) // 2, "confidence": None})
json.dump(caps, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(caps)} palabras -> {out}")
