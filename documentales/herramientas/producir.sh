#!/usr/bin/env bash
# Tubería completa de un documental:  guion JSON → voz → subtítulos → render.
# Voz externa (Qwen/Colab): VOZ_EXTERNA=1 y deja los WAV por escena en <proyecto>/audio/<nombre-guion>/
# Uso: bash documentales/herramientas/producir.sh <proyecto> <guion.json> <IdComposicion> [preview|final]
#   ej.: bash documentales/herramientas/producir.sh sosua-refugiados guion/prueba_15s.json SosuaPrueba15s preview
set -euo pipefail
DOC=$(cd "$(dirname "$0")/.." && pwd); P="$DOC/$1"; GUION="$2"; COMP="$3"; MODO="${4:-preview}"
NOMBRE=$(basename "$GUION" .json); AUD="$P/audio/$NOMBRE"; SUB="$P/subtitulos/$NOMBRE"
TTS="$DOC/../.claude/skills/tts/scripts/tts"; W="$DOC/herramientas/whisper.cpp"
echo "1/4 Narración (skill-tts → voz-local/Kokoro)"
if [ "${VOZ_EXTERNA:-}" = 1 ]; then
  # Narración ya generada (p. ej. Qwen3-TTS en Colab): WAV por escena en audio/<nombre>/
  python3 "$DOC/herramientas/unir_segmentos.py" "$AUD"
else
  curl -s localhost:8880/v1/audio/voices >/dev/null || { echo "Arranca primero: python $DOC/herramientas/voz_local.py --kokoro-dir <carpeta modelos>"; exit 1; }
  (cd "$P" && "$TTS" render "$GUION" -o "audio/$NOMBRE")
fi
echo "2/4 Subtítulos palabra por palabra (whisper.cpp)"
ffmpeg -v error -y -i "$AUD/voiceover.wav" -ar 16000 -ac 1 "$SUB.16k.wav"
"$W/build/bin/whisper-cli" -m "$W/models/ggml-small.bin" -f "$SUB.16k.wav" -l es -t 4 -ml 1 -sow -oj -osrt -of "$SUB" >/dev/null 2>&1
python3 "$DOC/herramientas/subtitulos_remotion.py" "$SUB.json" "$DOC/motor/public/${1%%-*}/${NOMBRE}_subtitulos.json"
cp "$AUD/voiceover.wav" "$DOC/motor/public/${1%%-*}/${NOMBRE}_voz.wav"
echo "3/4 Render $MODO"
ESC=$([ "$MODO" = preview ] && echo "--scale=0.5" || echo ""); SUF=$([ "$MODO" = preview ] && echo "540x960" || echo "1080x1920")
(cd "$DOC/motor" && npx remotion render src/index.ts "$COMP" "$P/renders/${NOMBRE}_${SUF}.mp4" $ESC --log=error)
echo "4/4 Listo: $P/renders/${NOMBRE}_${SUF}.mp4"
