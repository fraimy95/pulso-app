# usage: python3 mix.py voice.mp3 cues.json duration out.wav
# Synthesizes SFX + a soft documentary music bed and mixes them under the voice.
import sys, json, subprocess, numpy as np
from scipy.signal import butter, sosfilt
SR = 48000
voice_f, cues_f, dur, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
N = int(dur * SR)
rng = np.random.default_rng(7)

def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)

def env(n, a, r):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r)

def lp(x, f, order=2): return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)

def whoosh():
    n = int(.5 * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    out = np.zeros(n); step = 2400
    for i in range(0, n, step):  # sweeping band-pass in blocks
        c = 300 + 2600 * (i / n)
        seg = bp(noise[max(0, i - 2000):i + step], c * .6, min(c * 1.6, 20000))[-step:]
        out[i:i + len(seg)] = seg[:n - i]
    e = np.sin(np.pi * np.clip(t / .5, 0, 1)) ** 2
    return out * e * .35

def pop():
    n = int(.09 * SR); t = np.arange(n) / SR
    f = 950 - 450 * t / .09
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .002, .025) * .22

def thud():
    n = int(.45 * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * (75 - 30 * t) * t) * env(n, .002, .12)
    click = lp(rng.standard_normal(n), 1800) * env(n, .001, .02)
    return (body * .8 + click * .5) * .75

def tick():
    n = int(.03 * SR)
    return np.sin(2 * np.pi * 2100 * np.arange(n) / SR) * env(n, .001, .006) * .18

def strike():
    n = int(.3 * SR); t = np.arange(n) / SR
    s = bp(rng.standard_normal(n), 2000, 6000) * np.sin(np.pi * np.clip(t / .3, 0, 1))
    return s * .25

SFX = {"whoosh": whoosh(), "pop": pop(), "thud": thud(), "tick": tick(), "strike": strike()}

def bed(n):
    # A minor progression, 92 bpm, soft detuned-saw pad + low pulse
    bpm = 92; beat = 60 / bpm; bar = 4 * beat
    chords = [[45, 52, 57, 60, 64], [41, 48, 53, 57, 60], [48, 55, 60, 64, 67], [43, 50, 55, 59, 62]]
    t = np.arange(n) / SR; pad = np.zeros(n)
    seg = 2 * bar
    for k in range(int(n / SR / seg) + 1):
        ch = chords[k % 4]; s0 = int(k * seg * SR); s1 = min(n, int((k + 1) * seg * SR + .8 * SR))
        if s0 >= n: break
        tt = np.arange(s1 - s0) / SR
        e = np.minimum(1, tt / 1.2) * np.minimum(1, np.maximum(0, (seg + .8 - tt) / .8))
        for m in ch:
            f = 440 * 2 ** ((m - 69) / 12)
            for d in (-.12, .12):
                ph = 2 * np.pi * f * (1 + d / 100) * tt
                pad[s0:s1] += (2 * ((ph / (2 * np.pi)) % 1) - 1) * e * .05
    pad = lp(pad, 900, 4)
    pulse = np.zeros(n); kn = int(.35 * SR)
    kick = np.sin(2 * np.pi * 52 * np.arange(kn) / SR) * env(kn, .003, .09)
    for b in np.arange(0, n / SR, beat * 2):
        i = int(b * SR); j = min(n, i + kn); pulse[i:j] += kick[:j - i] * .5
    x = pad + pulse
    fade = np.minimum(1, t / 1.0) * np.minimum(1, np.maximum(0, (n / SR - t) / 1.5))
    return x * fade

voice = load(voice_f)
mix = np.zeros(N)
mix[:min(N, len(voice))] += voice[:N]
# duck the bed under the voice
vabs = lp(np.abs(np.pad(voice, (0, max(0, N - len(voice))))[:N]), 4)
duck = 1 - .55 * np.clip(vabs / (vabs.max() * .25 + 1e-9), 0, 1)
mix += bed(N) * .38 * duck
for t, name in json.load(open(cues_f)):
    s = SFX[name]; i = int(t * SR); j = min(N, i + len(s))
    if 0 <= i < N: mix[i:j] += s[:j - i]
peak = np.max(np.abs(mix)); mix = mix / peak * .89
pcm = (mix * 32767).astype(np.int16)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", out], input=pcm.tobytes(), check=True)
print("mixed", out)
