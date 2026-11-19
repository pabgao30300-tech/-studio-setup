# Casa Mar — reel 3D (15 s)

Scène three.js rendue image par image dans Chromium (headless), puis montée avec ffmpeg.

```
cd casa-mar-teaser/3d
npm i three@0.160.0
mkdir -p assets && cp ../../casa-mar-site/assets/logo-*.svg ../../casa-mar-site/assets/fonts/*.woff2 assets/
python3 -m http.server 8790 &          # la page doit être servie en http
python3 audio3d.py audio.wav
node render3d.js 1 frames1 30          # 1, 2 ou 3 = charte
ffmpeg -framerate 30 -i frames1/f%04d.jpg -i audio.wav -vf "noise=alls=6:allf=t,format=yuv420p" \
       -c:v libx264 -crf 23 -c:a aac -shortest casa3d_1.mp4
```

## Version 2 (`index2.html`)
Reflet dans l'eau, gerbes d'eau, lettres « CASA MAR » qui sortent une par une, titres en surimpression.
Rendu en 60 i/s puis fusion en 30 i/s (flou de mouvement), vignettage et grain :
```
python3 -m http.server 8790 &
python3 audio3d.py audio.wav
./run_all.sh            # produit casa3d_v2_1.mp4, _2, _3
```
