# usage: python3 alinear.py guion.txt whisper.json out_words.js
# Mantiene el TEXTO del guion (cifras y nombres bien escritos) y toma los TIEMPOS de Whisper.
import difflib, json, re, sys, unicodedata

guion, wjson, out = sys.argv[1:4]
norm = lambda w: re.sub(r"[^a-z0-9ñ]", "", unicodedata.normalize("NFD", w.lower()).encode("ascii", "ignore").decode() if False else
                        "".join(c for c in unicodedata.normalize("NFD", w.lower()) if unicodedata.category(c) != "Mn"))
G = open(guion, encoding="utf-8").read().split()
W = [w for seg in json.load(open(wjson)) for w in seg["words"]]
gn = [norm(w) for w in G]; wn = [norm(w["w"]) for w in W]
sm = difflib.SequenceMatcher(a=gn, b=wn, autojunk=False)
t = [None] * len(G)
for a, b, n in sm.get_matching_blocks():
    for k in range(n):
        t[a + k] = (W[b + k]["s"], W[b + k]["e"])
emparejadas = sum(x is not None for x in t)
# interpolar las no emparejadas entre vecinas
i = 0
while i < len(G):
    if t[i] is None:
        j = i
        while j < len(G) and t[j] is None: j += 1
        ini = t[i - 1][1] if i > 0 else 0.0
        fin = t[j][0] if j < len(G) else ini + 0.4 * (j - i)
        paso = (fin - ini) / (j - i)
        for k in range(i, j): t[k] = (ini + paso * (k - i), ini + paso * (k - i + 1))
        i = j
    else:
        i += 1
words = [{"w": g, "s": round(s, 3), "e": round(e, 3)} for g, (s, e) in zip(G, t)]
open(out, "w", encoding="utf-8").write("window.WORDS=" + json.dumps(words, ensure_ascii=False) + ";")
print(f"{emparejadas}/{len(G)} palabras emparejadas con Whisper; fin {words[-1]['e']}")
