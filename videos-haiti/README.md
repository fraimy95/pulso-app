# Motor de videos animados (Haití 2026)

Páginas HTML animadas fotograma a fotograma con Playwright + ffmpeg.

- `common.js` / `common.css`: motor (subtítulos palabra a palabra, mapa, figuras humanas, iconos, sonidos automáticos).
- `capas.js` + `wide.css`: capas 16:9 (cámara, cortinillas de capítulo, banderas, rótulos, minimapas, grano).
- `reel_*.html`: reels verticales 9:16. `video_bukele_v2.html`: video 16:9.
- `words_*.js`: tiempos por palabra (Whisper + `alinear.py`).

Render (audio no incluido en el repo):

```bash
PAGE=video_bukele_v2.html VW=1920 VH=1080 ./make.sh bk2 a_bk.wav 314.3 salida.mp4
```

Requiere Node + Playwright (Chromium), Python 3 con numpy/scipy, y ffmpeg. `geo.js` se genera con `build_geo.py` a partir de Natural Earth (dominio público).
