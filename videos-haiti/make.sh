#!/bin/bash
# usage: make.sh reel_id audio.wav duration out.mp4
cd "$(dirname "$0")"
node cues.js ${PAGE:-reel_$1.html} cues_$1.json && python3 mix.py $2 cues_$1.json $3 mix_$1.wav && VW=${VW:-1080} VH=${VH:-1920} node render.js ${PAGE:-reel_$1.html} mix_$1.wav $4 $3 30 | tail -1
