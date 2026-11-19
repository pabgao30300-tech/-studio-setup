#!/bin/bash
cd "$(dirname "$0")"  # nécessite: python3 -m http.server 8790 &
for i in 1 2 3; do
  rm -rf v2f$i
  PAGE=index2.html node render3d.js $i v2f$i 60 > v2log$i.txt 2>&1
  ffmpeg -v error -y -framerate 60 -i v2f$i/f%04d.jpg -i audio.wav \
    -vf "tmix=frames=2,select='not(mod(n\,2))',setpts=N/30/TB,noise=alls=6:allf=t,vignette=PI/5,format=yuv420p" \
    -r 30 -c:v libx264 -preset slow -crf 21 -c:a aac -b:a 192k -shortest -movflags +faststart casa3d_v2_$i.mp4
  echo "done $i"
done
