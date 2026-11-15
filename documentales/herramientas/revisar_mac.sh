#!/usr/bin/env bash
# Revisa el Mac ANTES de instalar nada. Solo lee; no cambia ninguna configuración.
# Uso:  bash documentales/herramientas/revisar_mac.sh
set -u
ok(){ printf "  \033[32m✓\033[0m %s\n" "$*"; }; mal(){ printf "  \033[31m✗\033[0m %s\n" "$*"; }; aviso(){ printf "  \033[33m!\033[0m %s\n" "$*"; }

echo "== Equipo"
OSV=$(sw_vers -productVersion 2>/dev/null || echo "?"); ARCH=$(uname -m)
echo "  macOS $OSV · CPU $ARCH · $(sysctl -n machdep.cpu.brand_string 2>/dev/null) · RAM $(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1073741824 )) GB"
[ "$ARCH" = "x86_64" ] && aviso "Mac Intel: nada de MLX ni binarios solo-arm64. Todo lo de este proyecto tiene versión x86_64."
MAJ=${OSV%%.*}
if [ "${MAJ:-0}" -ge 13 ] 2>/dev/null; then ok "macOS $OSV: compatible con Node 22, Chrome para Remotion y Homebrew actual"
elif [ "${MAJ:-0}" -ge 12 ] 2>/dev/null; then aviso "macOS $OSV: Chrome actual aún funciona, pero Homebrew recomienda 13+. Si algo falla, usa Node 20 LTS."
else mal "macOS $OSV: Chrome (y por tanto Remotion) ya no da soporte; actualiza macOS si tu Mac lo permite"; fi
echo "  Disco libre: $(df -h ~ | tail -1 | awk '{print $4}') (necesitas ~6 GB)"

echo "== Herramientas"
v(){ command -v "$1" >/dev/null && "$@" 2>&1 | head -1 || echo "no instalado"; }
NODE=$(v node -v); echo "  Node:    $NODE"; case "$NODE" in v2[0-9]*) ok "Node 20+";; *) mal "Instala Node 22 LTS (nodejs.org, instalador x64) o 'brew install node@22'";; esac
echo "  npm:     $(v npm -v)"
PY=$(v python3 --version); echo "  Python:  $PY"; case "$PY" in *3.1[0-3]*) ok "Python 3.10–3.13 (kokoro-onnx necesita < 3.14)";; *) aviso "Recomendado Python 3.12: brew install python@3.12";; esac
FF=$(v ffmpeg -version); echo "  FFmpeg:  ${FF:0:40}"; [[ "$FF" == *"version"* ]] && ok "FFmpeg presente" || mal "Instala FFmpeg: brew install ffmpeg"
echo "  git:     $(v git --version)"
echo "  cmake:   $(v cmake --version)   (para compilar whisper.cpp: brew install cmake)"
echo "  brew:    $(v brew --version)"
command -v xcode-select >/dev/null && xcode-select -p >/dev/null 2>&1 && ok "Herramientas de línea de comandos de Xcode" || aviso "Instala: xcode-select --install (compilador para whisper.cpp)"

echo "== Compatibilidad Intel de cada pieza"
echo "  Remotion 4 ............ ✓ x86_64 (Node + Chrome Headless Shell)"
echo "  d3-geo / world-atlas .. ✓ JavaScript puro"
echo "  whisper.cpp ........... ✓ compila en Intel (AVX2); usar modelo 'small'"
echo "  Kokoro (kokoro-onnx) .. ✓ CPU x86_64, ~tiempo real"
echo "  skill-tts ............. ✓ binario darwin_amd64 verificado por SHA-256"
echo "  ffmpeg-skill .......... ✓ Python + FFmpeg"
echo "  Qwen3-TTS (MLX) ....... ✗ solo Apple Silicon → usar el cuaderno de Colab"
echo "  HyperFrames ........... — no instalado (ver documentales/README.md)"
