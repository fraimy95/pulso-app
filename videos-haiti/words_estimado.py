# Palabras con tiempos ESTIMADOS (provisionales hasta tener el audio real)
import json, re, sys
txt = open(sys.argv[1], encoding="utf-8").read()
t, out = 0.4, []
for p in [x for x in txt.split("\n\n") if x.strip()]:
    for w in p.split():
        d = 0.16 + 0.055 * len(re.sub(r"\W", "", w))
        if re.search(r"\d", w): d += 0.35
        out.append({"w": w, "s": round(t, 3), "e": round(t + d, 3)}); t += d + 0.03
        if re.search(r"[.?!:;]$", w): t += 0.35
        elif w.endswith(","): t += 0.15
    t += 0.6
open(sys.argv[2], "w", encoding="utf-8").write("window.WORDS=" + json.dumps(out, ensure_ascii=False) + ";")
print(len(out), "palabras, duración estimada", round(t, 1), "s")
