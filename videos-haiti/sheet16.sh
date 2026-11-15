#!/bin/bash
# usage: sheet16.sh page.html out.jpg t1,t2,... (3 por fila)
P=$1; OUT=$2; T=$3; cd "$(dirname "$0")"
VW=1920 VH=1080 node render.js "$P" x x 1 30 --stills "$T" >/dev/null 2>&1 || VW=1920 VH=1080 node render.js "$P" x x 1 30 --stills "$T"
IFS=, read -ra TS <<< "$T"; n=${#TS[@]}; args=(); f=""
for i in "${!TS[@]}"; do args+=(-i "still_${TS[$i]}.jpg"); f+="[$i]scale=640:360[v$i];"; done
rows=$(( (n+2)/3 )); r=""
for ((k=0;k<rows;k++)); do s=""; c=0; for ((j=k*3;j<k*3+3 && j<n;j++)); do s+="[v$j]"; c=$((c+1)); done
  for ((m=c;m<3;m++)); do f+="color=c=black:s=640x360:d=1[pad$k$m];"; s+="[pad$k$m]"; done
  f+="${s}hstack=3[r$k];"; r+="[r$k]"; done
if [ $rows -gt 1 ]; then f+="${r}vstack=$rows"; else f="${f%[r0];}"; fi
ffmpeg -hide_banner -loglevel error -y "${args[@]}" -filter_complex "$f" -frames:v 1 "$OUT"; rm -f still_*.jpg
