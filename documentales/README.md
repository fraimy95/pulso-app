# Sistema de producción de documentales verticales

Guion → voz → subtítulos → animación → video 1080×1920, todo con herramientas gratuitas y de código abierto, compatible con **MacBook Pro Intel 2019 (16 GB)**.

```
documentales/
├── motor/                  Plantilla Remotion reutilizable (todas las historias)
│   ├── src/componentes/    Camara, Globo (mapas), Subtitulos, Acabado (grano, títulos, notas)
│   ├── src/documentales/   Una carpeta por historia (composiciones)
│   └── public/<historia>/  Voz y subtítulos que usa cada composición
├── herramientas/
│   ├── revisar_mac.sh      Comprueba el Mac antes de instalar (solo lee)
│   ├── voz_local.py        Servidor TTS local (Kokoro; adaptador Qwen3-TTS) para skill-tts, sin Docker
│   ├── subtitulos_remotion.py  whisper.cpp JSON → subtítulos de Remotion
│   ├── producir.sh         Tubería completa: voz → subtítulos → render
│   └── whisper.cpp/        (se compila localmente; no va en git)
└── sosua-refugiados/       guion, investigacion, audio, fotografias, mapas, … renders, fuentes-y-licencias
```

## Piezas y por qué

| Pieza | Uso | Estado |
|---|---|---|
| **Remotion 4.0.543** + skills oficiales (`.claude/skills/remotion-*`) | Motor de animación | ✅ Probado |
| **d3-geo + Natural Earth** (`world-atlas`) | Mapas y globo animados, sin clave ni internet | ✅ Probado. Elegido en lugar de Mapbox (pide clave) o MapLibre (necesita servidor de teselas) |
| **skill-tts** (`.claude/skills/tts`) | Narración por escenas, WAV, manifiesto de tiempos | ✅ Probado con Kokoro |
| **voz_local.py** | Sustituye al Docker de Kokoro-FastAPI (pesado en Mac Intel) | ✅ Probado |
| **Kokoro** (`em_alex`, `ef_dora`, `em_santa`) | Voz gratuita local en español | ✅ Funciona en CPU Intel |
| **Qwen3-TTS** | Voz más natural | ⚠️ En CPU Intel ~100× más lento que el tiempo real (medido). Usar el cuaderno de Colab y luego importar el WAV; o el motor `qwen:` de voz_local.py en una máquina con GPU |
| **whisper.cpp** (modelo `small`) | Transcripción, SRT/JSON, tiempos por palabra | ✅ Probado: 15 s de audio en 7 s |
| **ffmpeg-skill** (`.claude/skills/ffmpeg-skill`) | Cortes, sonoridad, mezclas, exportaciones por plataforma | ✅ Instalada (Python + FFmpeg) |
| **HyperFrames** | Evaluado, **no instalado**: 400 MB, motor HTML propio que duplica a Remotion. Se puede añadir más adelante para bloques concretos | — |

**Licencia de Remotion:** gratis para personas y empresas de hasta 3 empleados; por encima hace falta licencia de empresa. Verifícalo en https://www.remotion.dev/docs/license antes de un uso comercial.

## Uso

```bash
bash documentales/herramientas/revisar_mac.sh
python3 documentales/herramientas/voz_local.py --kokoro-dir ~/lemo-opuscar/core/tts &
bash documentales/herramientas/producir.sh sosua-refugiados guion/prueba_15s.json SosuaPrueba15s preview
```

- **Vista previa (540×960):** `producir.sh … preview`. Usa `--scale=0.5`.
- **Final (1080×1920):** `producir.sh … final`.
- **Editar visualmente:** `cd documentales/motor && npm run studio`.

## Nueva historia

1. Copia `motor/src/documentales/sosua/` a `motor/src/documentales/<historia>/` y regístrala en `Root.tsx`.
2. Crea `documentales/<historia>/` con las mismas subcarpetas.
3. Escribe el guion como JSON de skill-tts: un segmento por escena, con cifras escritas como se pronuncian.
4. `producir.sh <historia> guion/<nombre>.json <Composicion> preview`.

Componentes reutilizables: `Camara` (push-in, pull-out, pan, tracking), `Enfoque` (rack focus simulado), `Globo` (zoom geográfico, rutas, marcadores, países resaltados, viraje frío/cálido), `Subtitulos` (dos líneas como máximo, palabras clave en dorado, zona segura), `TituloCine`, `Nota` (marca las rutas esquemáticas y las recreaciones) y `Acabado` (grano y viñeta).
