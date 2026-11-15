#!/bin/bash
# usage: sheet.sh page.html out.jpg t1,t2,...  (up to 15 stills, 5 per row)
P=$1; OUT=$2; T=$3; D=$(mktemp -d)
cd "$(dirname "$0")"
node render.js "$P" x x 1 30 --stills "$T" >/dev/null 2>&1 || node render.js "$P" x x 1 30 --stills "$T"
IFS=, read -ra TS <<< "$T"; n=${#TS[@]}; args=(); f=""
for i in "${!TS[@]}"; do args+=(-i "still_${TS[$i]}.jpg"); f+="[$i]scale=360:640[v$i];"; done
rows=$(( (n+4)/5 )); r=""
for ((k=0;k<rows;k++)); do s=""; c=0; for ((j=k*5;j<k*5+5 && j<n;j++)); do s+="[v$j]"; c=$((c+1)); done
  if [ $c -lt 5 ]; then for ((m=c;m<5;m++)); do f+="color=c=black:s=360x640:d=1[pad$k$m];"; s+="[pad$k$m]"; done; fi
  f+="${s}hstack=5[r$k];"; r+="[r$k]"; done
if [ $rows -gt 1 ]; then f+="${r}vstack=$rows"; else f="${f%;}"; f="${f%\[r0\]}"; fi
ffmpeg -hide_banner -loglevel error -y "${args[@]}" -filter_complex "$f" -frames:v 1 "$OUT"
rm -f still_*.jpg
