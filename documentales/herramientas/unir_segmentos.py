#!/usr/bin/env python3
"""Une WAV de narración por escenas (01-*.wav, 02-*.wav…) en voiceover.wav con pausas y -16 LUFS,
y escribe manifest.json con inicio/fin de cada escena (mismo formato que skill-tts).
uso: python unir_segmentos.py CARPETA [--pausa 0.45]"""
import json, sys, glob, os
import numpy as np, soundfile as sf
d = sys.argv[1]; pausa = float(sys.argv[sys.argv.index("--pausa") + 1]) if "--pausa" in sys.argv else 0.45
fs = sorted(f for f in glob.glob(os.path.join(d, "*.wav")) if not f.endswith("voiceover.wav"))
partes, segs, t, sr0 = [], [], 0.0, None
for f in fs:
    a, sr = sf.read(f, dtype="float32"); a = a if a.ndim == 1 else a.mean(1); sr0 = sr0 or sr
    act = np.where(np.abs(a) > 0.01)[0]; a = a[max(0, act[0] - int(.03 * sr)):act[-1] + int(.05 * sr)] if act.size else a
    segs.append({"id": os.path.basename(f)[:-4], "file": f, "duration": round(len(a) / sr, 3), "start": round(t, 3), "end": round(t + len(a) / sr, 3)})
    partes += [a, np.zeros(int(pausa * sr), np.float32)]; t += len(a) / sr + pausa
x = np.concatenate(partes[:-1])
try:
    import pyloudnorm as pl; x = pl.normalize.loudness(x, pl.Meter(sr0).integrated_loudness(x), -16.0)
except Exception: x = x / max(1e-6, np.abs(x).max()) * 0.7
x = x / max(1.0, np.abs(x).max() / 0.98)
sf.write(os.path.join(d, "voiceover.wav"), x, sr0, subtype="PCM_16")
json.dump({"segments": segs, "duration": round(len(x) / sr0, 3)}, open(os.path.join(d, "manifest.json"), "w"), ensure_ascii=False, indent=1)
print(f"{len(segs)} escenas -> voiceover.wav ({len(x)/sr0:.2f} s)")
