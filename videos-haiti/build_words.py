# usage: python3 build_words.py tx.json start end out.js
# Cuts a Whisper word list to [start,end], fixes known mis-hearings, shifts times to 0.
import json, re, sys
src, a, b, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
words = [{"w": w["w"].strip(), "s": w["s"], "e": w["e"]} for seg in json.load(open(src)) for w in seg["words"]]
words = [w for w in words if w["s"] >= a - .05 and w["e"] <= b + .3]
SEQ = [  # (tokens heard, tokens wanted) compared without punctuation/case
    (["vive", "en", "saint"], ["Viv", "Ansanm"]),
    (["khoa", "de", "bouquet"], ["Croix-des-Bouquets"]),
    (["fils-hemé"], ["Fils-Aimé"]),
    (["artibonit"], ["Artibonite"]),
    (["binu"], ["BINUH"]),
    (["kumbit"], ["konbit"]),
    (["compa"], ["kompa"]),
]
bare = lambda s: re.sub(r"[^\wáéíóúñü%-]", "", s.lower())
i = 0; res = []
while i < len(words):
    hit = False
    for old, new in SEQ:
        if [bare(w["w"]) for w in words[i:i + len(old)]] == old:
            span = words[i:i + len(old)]; trail = re.sub(r"^.*?([.,:;?!]*)$", r"\1", span[-1]["w"])
            s0, e0 = span[0]["s"], span[-1]["e"]; d = (e0 - s0) / len(new)
            for k, n in enumerate(new):
                res.append({"w": n + (trail if k == len(new) - 1 else ""), "s": s0 + k * d, "e": s0 + (k + 1) * d})
            i += len(old); hit = True; break
    if not hit: res.append(words[i]); i += 1
merged = []
for w in res:
    if merged and re.match(r"^[,.]\d|^%", w["w"]):
        merged[-1]["w"] += w["w"]; merged[-1]["e"] = w["e"]
    else: merged.append(dict(w))
res = merged
for w in res:
    w["w"] = re.sub(r"(\d),(\d{3})\b", r"\1.\2", w["w"])  # 310,000 -> 310.000
    w["s"] = round(max(0, w["s"] - a), 3); w["e"] = round(max(0, w["e"] - a), 3)
open(out, "w").write("window.WORDS=" + json.dumps(res, ensure_ascii=False) + ";")
print(out, len(res), "words |", " ".join(w["w"] for w in res)[:2000])
