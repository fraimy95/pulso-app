#!/usr/bin/env bash
# Instalación del narrador en un Mac con Apple Silicon (M1/M2/M3/M4).
# Uso:  bash setup.sh            (instala y descarga los modelos recomendados, ~9 GB)
#       bash setup.sh --minimo   (solo voz diseñada + clonación, ~6 GB, sin Whisper)
set -euo pipefail
cd "$(dirname "$0")"

rojo(){ printf "\033[31m%s\033[0m\n" "$*"; }; verde(){ printf "\033[32m%s\033[0m\n" "$*"; }

# 1. Comprobaciones
[[ "$(uname -s)" == "Darwin" ]] || { rojo "Este instalador es para macOS."; exit 1; }
[[ "$(uname -m)" == "arm64" ]] || { rojo "MLX necesita Apple Silicon (M1 o posterior). Este Mac es $(uname -m)."; exit 1; }
MEM_GB=$(( $(sysctl -n hw.memsize) / 1073741824 ))
echo "Memoria: ${MEM_GB} GB"
(( MEM_GB >= 16 )) || echo "Aviso: con menos de 16 GB usa --rapido (modelo 0.6B) para no quedarte sin memoria."

PY=""
for c in python3.12 python3.11 python3.13 python3; do
  if command -v "$c" >/dev/null && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)'; then PY=$c; break; fi
done
if [[ -z "$PY" ]]; then
  rojo "Necesitas Python 3.10 o superior. Instálalo con:  brew install python@3.12"; exit 1
fi
echo "Python: $($PY --version)"

if ! command -v ffmpeg >/dev/null; then
  if command -v brew >/dev/null; then echo "Instalando ffmpeg (para exportar MP3/AAC además de WAV)…"; brew install ffmpeg || true
  else echo "Aviso: sin Homebrew no instalo ffmpeg. El WAV funciona igual; para MP3 instala https://brew.sh"; fi
fi

# 2. Entorno virtual
[[ -d .venv ]] || "$PY" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip -q
pip install -r requirements.txt

# 3. Modelos (se guardan en ~/.cache/huggingface; solo se descargan una vez)
MODELOS=(
  "mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit"   # diseña la voz (3,1 GB)
  "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit"          # clona la voz para cada párrafo (3,1 GB)
)
if [[ "${1:-}" != "--minimo" ]]; then
  MODELOS+=("mlx-community/whisper-large-v3-turbo")        # pruebas de pronunciación (1,6 GB)
fi
for m in "${MODELOS[@]}"; do
  echo "Descargando $m …"
  python -c "from huggingface_hub import snapshot_download; snapshot_download('$m')"
done

# 4. Prueba rápida de que MLX ve la GPU
python - <<'EOF'
import mlx.core as mx
print("MLX", mx.__version__, "· dispositivo:", mx.default_device())
EOF

verde "Instalación completa."
echo "Siguientes pasos:"
echo "  source .venv/bin/activate"
echo "  python narrar.py --disenar --voz narrador_documental     # escucha la voz"
echo "  python app.py                                            # interfaz en el navegador"
