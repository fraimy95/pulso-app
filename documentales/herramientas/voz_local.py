#!/usr/bin/env python3
"""voz-local: servidor TTS compatible con OpenAI (/v1/audio/speech) para skill-tts, sin Docker.

Motores:
  - kokoro (por defecto): Kokoro-82M con kokoro-onnx. Gratis, local, funciona en Mac Intel.
  - qwen   (opcional):    Qwen3-TTS clonando una voz de referencia (p. ej. la de Colab).
                          Solo es práctico con GPU (CUDA) o Apple Silicon (MLX). En CPU Intel
                          tarda ~100x el tiempo real: para eso usa el cuaderno de Colab.

Uso:
  python voz_local.py --kokoro-dir RUTA_CON_MODELOS [--puerto 8880]
  tts config set kokoro.base_url http://localhost:8880/v1   (o exporta KOKORO_BASE_URL)
  tts render guion.json -p kokoro -v em_alex

Voces: cualquier voz Kokoro (em_alex, ef_dora, …) o "qwen:<ruta_wav_ref>|<texto_ref>".
"""
import argparse, io, json, os, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

SR = 24000
_lock = threading.Lock()
_kokoro = None
_qwen = None


def kokoro(kdir):
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(os.path.join(kdir, "kokoro-v1.0.onnx"), os.path.join(kdir, "voices-v1.0.bin"))
    return _kokoro


def lang_de(voz):
    # prefijo de la voz Kokoro: e = español, a/b = inglés, f = francés, i = italiano, p = portugués
    return {"e": "es", "a": "en-us", "b": "en-gb", "f": "fr-fr", "i": "it", "p": "pt-br"}.get(voz[:1], "es")


def sintetizar(texto, voz, velocidad, kdir):
    if voz.startswith("qwen:"):
        return sintetizar_qwen(texto, voz[5:])
    with _lock:
        audio, sr = kokoro(kdir).create(texto, voice=voz, speed=velocidad or 1.0, lang=lang_de(voz))
    if sr != SR:
        import soxr
        audio = soxr.resample(audio, sr, SR)
    return np.asarray(audio, dtype=np.float32)


def sintetizar_qwen(texto, ref):
    """Adaptador Qwen3-TTS (modelo Base, clonación). ref = 'ruta.wav|transcripción exacta'."""
    global _qwen
    ruta, _, ref_txt = ref.partition("|")
    try:
        import torch
        from qwen_tts import Qwen3TTSModel
    except ImportError:
        raise RuntimeError("Qwen3-TTS no está instalado aquí (pip install qwen-tts). En Mac Intel usa el cuaderno de Colab.")
    if not torch.cuda.is_available():
        raise RuntimeError("Qwen3-TTS necesita GPU: en CPU Intel es ~100x más lento que el tiempo real. Usa Colab o Kokoro.")
    with _lock:
        if _qwen is None:
            m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map="cuda:0", dtype=torch.float16, attn_implementation="sdpa")
            _qwen = (m, m.create_voice_clone_prompt(ref_audio=ruta, ref_text=ref_txt))
        m, prompt = _qwen
        wavs, sr = m.generate_voice_clone(text=texto, language="Spanish", voice_clone_prompt=prompt, temperature=0.75)
    return np.asarray(wavs[0], dtype=np.float32)


class H(BaseHTTPRequestHandler):
    kdir = "."

    def _json(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b)))
        self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path.rstrip("/").endswith("/audio/voices"):
            vs = sorted(kokoro(self.kdir).get_voices())
            return self._json(200, {"voices": vs})
        return self._json(404, {"error": "no encontrado"})

    def do_POST(self):
        if not self.path.rstrip("/").endswith("/audio/speech"):
            return self._json(404, {"error": "no encontrado"})
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        try:
            audio = sintetizar(req.get("input", ""), req.get("voice", "em_alex"), req.get("speed"), self.kdir)
        except Exception as e:
            return self._json(500, {"error": str(e)})
        pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes()
        fmt = req.get("response_format", "pcm")
        if fmt == "wav":
            import soundfile as sf
            buf = io.BytesIO(); sf.write(buf, audio, SR, format="WAV", subtype="PCM_16"); pcm = buf.getvalue()
        self.send_response(200); self.send_header("Content-Type", "audio/wav" if fmt == "wav" else "audio/pcm")
        self.send_header("Content-Length", str(len(pcm))); self.end_headers(); self.wfile.write(pcm)

    def log_message(self, *a):
        sys.stderr.write("voz-local: " + (a[0] % a[1:]) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--kokoro-dir", required=True, help="carpeta con kokoro-v1.0.onnx y voices-v1.0.bin")
    ap.add_argument("--puerto", type=int, default=8880)
    a = ap.parse_args()
    H.kdir = a.kokoro_dir
    kokoro(a.kokoro_dir)  # carga al arrancar (unos segundos)
    print(f"voz-local escuchando en http://localhost:{a.puerto}/v1", flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.puerto), H).serve_forever()
