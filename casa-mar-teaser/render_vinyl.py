"""Casa Mar — annonce artiste, style « Le vinyle » (1080x1920, 30 fps, 120 BPM, 30 s).

Chaque artiste du line-up est un disque : la pochette arrive, le vinyle sort, se met à tourner,
le diamant se pose (craquements puis musique), le nom écrit en cercle sur l'étiquette devient net,
on plonge dans l'étiquette et le nom tombe sur le drop.

Usage : python render_vinyl.py <assets_dir> <out.mp4|preview_dir> <charte 1|2|3> "<NOM ARTISTE>"
              [--num=1] [--real] [--music=morceau.mp3 --drop-at=SECONDES] [preview]
"""
import sys, os, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageChops, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_artist as A                    # réutilise la palette, les polices, la nuit étoilée et le son
from render_artist import (W, H, FPS, BEAT, NB, DUR, NF, DROP, P, C, NIGHT, KOKO, BOLD, LIGHT, ARTIST, REAL, PREVIEW,
                           text_img, paste_c, logo, clamp, eout, ein, ease_io, words, starfield, beat_pulse)
R = A.R
NUM = int(A.OPT.get("num", "1"))
OUT, IDENT = A.OUT, A.IDENT
rgb = lambda k, a=255: tuple(int(v) for v in C[k]) + (a,)

# ------------------------------------------------------------------ éléments
DS = 1000                                    # disque dessiné à 1000 px, redimensionné au besoin
LABEL_R = 0.30

def make_disc():
    im = Image.new("RGBA", (DS, DS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    base = tuple(int(v) for v in NIGHT * 0.55)
    d.ellipse((0, 0, DS - 1, DS - 1), fill=base + (255,))
    for r in range(int(DS * 0.48), int(DS * LABEL_R * 0.5) + 30, -5):          # sillons
        g = 10 + (r * 7919 % 13)
        d.ellipse((DS / 2 - r, DS / 2 - r, DS / 2 + r, DS / 2 + r), outline=tuple(min(255, c + g) for c in base) + (255,), width=1)
    lr = DS * LABEL_R / 2 * 2                                                  # étiquette
    d.ellipse((DS / 2 - lr, DS / 2 - lr, DS / 2 + lr, DS / 2 + lr), fill=rgb("a"))
    ic = logo("icon", P["bg"], int(lr * 0.75))
    im.alpha_composite(ic, (int(DS / 2 - ic.width / 2), int(DS / 2 - lr * 0.62)))
    t1 = text_img("CASA MAR", KOKO, int(lr * 0.2), P["bg"]); im.alpha_composite(t1, (int(DS / 2 - t1.width / 2), int(DS / 2 + lr * 0.12)))
    t2 = text_img(f"FACE A   0{NUM}", BOLD, int(lr * 0.09), P["bg"], tracking=6)
    im.alpha_composite(t2, (int(DS / 2 - t2.width / 2), int(DS / 2 + lr * 0.42)))
    d.ellipse((DS / 2 - 12, DS / 2 - 12, DS / 2 + 12, DS / 2 + 12), fill=base + (255,))
    return im

def make_ring(blur):
    """Le nom écrit en cercle autour de l'étiquette."""
    im = Image.new("RGBA", (DS, DS), (0, 0, 0, 0))
    txt = f"{ARTIST}  *  {ARTIST}  *  "
    rr = DS * LABEL_R * 0.86
    size = int(DS * 0.042)
    widths = [text_img(ch, KOKO, size, P["bg"]).width if ch != " " else size * 0.35 for ch in txt]
    total = sum(widths) + 4 * len(txt)
    ang = -math.pi / 2
    for ch, w in zip(txt, widths):
        da = (w + 4) / total * 2 * math.pi
        if ch not in " ":
            g = text_img("-" if ch == "*" else ch, KOKO, size, P["bg"])
            g = g.rotate(-math.degrees(ang + da / 2) - 90, resample=Image.BICUBIC, expand=True)
            x = DS / 2 + math.cos(ang + da / 2) * rr; y = DS / 2 + math.sin(ang + da / 2) * rr
            im.alpha_composite(g, (int(x - g.width / 2), int(y - g.height / 2)))
        ang += da
    return im.filter(ImageFilter.GaussianBlur(blur)) if blur > 0.3 else im

DISC = make_disc()
RINGS = {b: make_ring(b) for b in (14, 10, 7, 5, 3.5, 2.2, 1.2, 0.5, 0)}
SHEEN = Image.new("RGBA", (DS, DS), (0, 0, 0, 0))
_sd = ImageDraw.Draw(SHEEN)
for a0 in (25, 205):
    _sd.pieslice((0, 0, DS - 1, DS - 1), a0, a0 + 34, fill=(255, 255, 255, 26))
SHEEN = SHEEN.filter(ImageFilter.GaussianBlur(22))
_m = Image.new("L", (DS, DS), 0); ImageDraw.Draw(_m).ellipse((0, 0, DS - 1, DS - 1), fill=255)
SHEEN.putalpha(ImageChops.multiply(SHEEN.getchannel("A"), _m))
_lm = Image.new("L", (DS, DS), 255); lr = DS * LABEL_R
ImageDraw.Draw(_lm).ellipse((DS / 2 - lr, DS / 2 - lr, DS / 2 + lr, DS / 2 + lr), fill=0)
SHEEN.putalpha(ImageChops.multiply(SHEEN.getchannel("A"), _lm))

def disc_frame(angle, blur):
    keys = sorted(RINGS)
    k = min(keys, key=lambda v: abs(v - blur))
    im = DISC.copy(); im.alpha_composite(RINGS[k])
    im = im.rotate(angle, resample=Image.BICUBIC)
    im.alpha_composite(SHEEN)
    return im

def make_sleeve(s=780):
    im = Image.new("RGBA", (s, s), rgb("c")); d = ImageDraw.Draw(im)
    m = int(s * 0.07)
    d.rectangle((m, m, s - m, s - m), outline=rgb("bg"), width=2)
    ic = logo("icon", P["a"], int(s * 0.42)); im.alpha_composite(ic, (int(s / 2 - ic.width / 2), int(s * 0.17)))
    t = text_img("CASA MAR", KOKO, int(s * 0.1), P["bg"]); im.alpha_composite(t, (int(s / 2 - t.width / 2), int(s * 0.62)))
    t = text_img(f"LINE UP   0{NUM} SUR 05", BOLD, int(s * 0.032), P["bg"], tracking=8)
    im.alpha_composite(t, (int(s / 2 - t.width / 2), int(s * 0.78)))
    t = text_img("JUIN 2028   NIMES", BOLD, int(s * 0.026), P["bg"], tracking=8)
    im.alpha_composite(t, (int(s / 2 - t.width / 2), int(s * 0.85)))
    return im
SLEEVE = make_sleeve()

def shadow(size, blur=30, alpha=120):
    sh = Image.new("RGBA", (size[0] // 4 + 40, size[1] // 4 + 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((20, 20, sh.width - 20, sh.height - 20), fill=(0, 0, 0, alpha))
    return sh.filter(ImageFilter.GaussianBlur(blur / 4)).resize((size[0] + 160, size[1] + 160), Image.BILINEAR)

def tonearm(cv, k):
    """Bras de lecture au trait, k 0 = repos, 1 = posé sur le disque."""
    d = ImageDraw.Draw(cv, "RGBA"); px, py = W - 120, 520
    ang = math.radians(100 + 22 * ease_io(k)); L = 760
    hx, hy = px + math.cos(ang) * L, py + math.sin(ang) * L
    d.ellipse((px - 34, py - 34, px + 34, py + 34), outline=rgb("c", 230), width=3)
    d.ellipse((px - 10, py - 10, px + 10, py + 10), fill=rgb("c", 230))
    d.line((px, py, hx, hy), fill=rgb("c", 230), width=5)
    d.line((hx, hy, hx - 30, hy + 40), fill=rgb("c", 230), width=9)

def header(cv, a):
    if a <= 0: return
    ink = P["c"]
    t1 = text_img("CASA MAR", BOLD, 26, ink, tracking=10); t2 = text_img(f"LINE UP   0{NUM} SUR 05", BOLD, 26, ink, tracking=10)
    paste_c(cv, t1, 110 + t1.width / 2, 260, alpha=a); paste_c(cv, t2, W - 110 - t2.width / 2, 260, alpha=a)
    ImageDraw.Draw(cv, "RGBA").line((110, 300, 110 + (W - 220) * eout(a), 300), fill=rgb("c", int(200 * a)), width=2)

# ------------------------------------------------------------------ images
SPIN = [0.0]
def frame(n):
    t = n / FPS; b = t / BEAT
    cv = Image.new("RGBA", (W, H), rgb("bg"))
    if b < DROP:
        starfield(cv, t, speed=0.015 + (0.05 * clamp((b - 22) / 14) ** 2), strength=0.55)
        header(cv, clamp((t - 0.3) / 0.8))
        # vitesse de rotation : démarre à 6, monte à 33 tours/min « visuels »
        rpm = 0 if b < 8 else (8 + 25 * ease_io((b - 8) / 10))
        angle = -(t * rpm * 6) % 360
        blur = 14 * (1 - ease_io((b - 22) / 13)) if b > 22 else 14
        cx, cy = W / 2, 1000
        # pochette : arrive par le bas puis sort à gauche
        sx = W / 2 - 1300 * ease_io((b - 14) / 6)
        sy = cy + 1200 * (1 - eout((t - 0.2) / 1.6))
        # disque : sort de la pochette vers la droite, puis se recentre et grossit
        out = ease_io((b - 6) / 6)
        dx = sx + 330 * out if b < 14 else W / 2 + (sx + 330 - W / 2) * (1 - ease_io((b - 14) / 6))
        dsz = 740 + 140 * ease_io((b - 14) / 6)
        zoom = 1 + 1.4 * ease_io((b - 24) / 10) + 30 * ein((b - 34) / 2)      # plongée dans l'étiquette
        dsz *= zoom
        if b >= 14 or out > 0:
            disc = disc_frame(angle, blur)
            if dsz < 6000:
                dd = disc.resize((int(dsz), int(dsz)), Image.BILINEAR) if dsz <= 2600 else None
                if dd is None:                                                 # très gros plan : on recadre avant d'agrandir
                    f = DS / dsz; cw, ch = W * f, H * f
                    crop = disc.crop((int(DS / 2 - cw / 2), int(DS / 2 - ch / 2), int(DS / 2 + cw / 2), int(DS / 2 + ch / 2)))
                    cv.alpha_composite(crop.resize((W, H), Image.BILINEAR))
                else:
                    sh = shadow((int(dsz * 0.9), int(dsz * 0.9)), alpha=110)
                    cv.alpha_composite(sh, (int(dx - sh.width / 2), int(cy - sh.height / 2 + 30)))
                    cv.alpha_composite(dd, (int(dx - dsz / 2), int(cy - dsz / 2)))
            else:
                cv.paste(Image.new("RGBA", (W, H), rgb("a")))
        if sx > -900:
            sh = shadow(SLEEVE.size)
            cv.alpha_composite(sh, (int(sx - sh.width / 2), int(sy - sh.height / 2 + 30)))
            cv.alpha_composite(SLEEVE, (int(sx - SLEEVE.width / 2), int(sy - SLEEVE.height / 2)))
        if 16 <= b < 26:                                     # le bras se pose, puis sort du cadre avec le zoom
            tonearm(cv, ease_io((b - 17) / 4)) if b < 24 else None
        words(cv, "le premier nom", LIGHT, 68, P["c"], 430, (b - 2) / 1.6 * (1 - clamp((b - 13) / 1.2)))
        words(cv, "pose le diamant", LIGHT, 68, P["c"], 430, (b - 15) / 1.6 * (1 - clamp((b - 21.5) / 1)))
        words(cv, "tu le reconnais", LIGHT, 68, P["c"], 430, (b - 23) / 1.6 * (1 - clamp((b - 33) / 1)))
    elif b < 44:                                            # drop : aplat de la couleur de l'étiquette
        lt = t - DROP * BEAT
        cv.paste(Image.new("RGBA", (W, H), rgb("a")))
        small = disc_frame(-(t * 200) % 360, 0).resize((230, 230), Image.BILINEAR)
        cv.alpha_composite(small, (W - 110 - 230, 1500))
        t1 = text_img(f"FACE A   0{NUM} SUR 05", BOLD, 32, P["bg"], tracking=10)
        paste_c(cv, t1, 110 + t1.width / 2, 300, alpha=eout(lt / 0.4))
        ImageDraw.Draw(cv).line((110, 345, W - 110, 345), fill=P["bg"], width=2)
        A.big_name(cv, lt - 0.05, 560, cols=(P["bg"], P["bg"]))
        words(cv, "REJOINT LE LINE UP", BOLD, 40, P["bg"], 1300, (lt - 0.7) / 0.5, tracking=12)
        R.waves(cv, P["bg"], 1560, t * 0.6, amp=10, wl=130, thick=5, rows=2, gap=30, x0=110, x1=470)
    elif b < 52:                                            # infos
        lt2 = t - 44 * BEAT
        starfield(cv, t, speed=0.02, strength=0.6, cy=760)
        A.big_name(cv, 9, 360, slam=False)
        d = ImageDraw.Draw(cv)
        d.line((140, 1010, W - 140, 1010), fill=P["c"], width=2)
        words(cv, "JUIN 2028", KOKO, 110, P["c"], 1110, lt2 / 0.4, tracking=0)
        words(cv, "CLOS DE PROVENCE   NIMES", BOLD, 36, P["c"], 1230, (lt2 - 0.3) / 0.4, tracking=10)
        k = eout((lt2 - 0.6) / 0.6)
        if k > 0:
            for i in range(5):
                x0 = 190 + i * 146
                d.rounded_rectangle((x0, 1320, x0 + 126, 1344), 12, outline=P["c"], width=3, fill=P["a"] if i < NUM else None)
            words(cv, f"{NUM} SUR 5 ARTISTES DEVOILES", BOLD, 30, P["c"], 1395, k, tracking=10)
    else:                                                   # sortie : la pochette, rangée dans la collection
        lt = t - 52 * BEAT
        starfield(cv, t, speed=0.01, strength=0.5)
        for i in range(5):                                  # cinq pochettes, une seule dévoilée
            x = 110 + i * 176; y = 560
            if i < NUM:
                sl = SLEEVE.resize((160, 160), Image.LANCZOS); cv.alpha_composite(sl, (x, y))
            else:
                ImageDraw.Draw(cv, "RGBA").rectangle((x, y, x + 159, y + 159), outline=rgb("c", 150), width=2)
                q = text_img(f"0{i + 1}", KOKO, 46, P["c"]); paste_c(cv, q, x + 80, y + 80, alpha=0.5)
        words(cv, "LE LINE UP SE REMPLIT", BOLD, 30, P["c"], 800, lt / 0.5, tracking=10)
        lg = logo("h", P["a"], 560); paste_c(cv, lg, W / 2, 1010, alpha=eout((lt - 0.3) / 0.6))
        k = eout((lt - 0.8) / 0.5)
        if k > 0:
            tg = text_img("BILLETS DES 22€", KOKO, 60, P["bg"])
            pw = tg.width + 80; pill = Image.new("RGBA", (pw, 100), (0, 0, 0, 0))
            ImageDraw.Draw(pill).rounded_rectangle((0, 0, pw - 1, 99), 50, fill=P["a"])
            pill.alpha_composite(tg, (40, (100 - tg.height) // 2))
            paste_c(cv, pill, W / 2, 1270, alpha=k)
        words(cv, "RESERVE AUX MAJEURS", BOLD, 26, P["c"], 1370, (lt - 1.1) / 0.5, tracking=10)
        if lt > 3.4:
            cv.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * ein((lt - 3.4) / 0.6)))))
    if not REAL:
        tag = text_img("EXEMPLE", BOLD, 24, P["c"], tracking=10)
        pill = Image.new("RGBA", (tag.width + 40, 50), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle((0, 0, pill.width - 1, 49), 25, outline=P["c"], width=2)
        pill.alpha_composite(tag, (20, (50 - tag.height) // 2))
        pill.putalpha(pill.getchannel("A").point(lambda v: int(v * 0.75)))
        cv.alpha_composite(pill, (70, 160))
    out = cv.convert("RGB")
    g = R.GRAIN[n % len(R.GRAIN)]
    return ImageChops.overlay(out, Image.merge("RGB", (g, g, g)))

# ------------------------------------------------------------------ son : même structure que l'annonce, + craquements de vinyle
def audio(path, sr=44100):
    A.audio(path, sr)
    with wave.open(path) as w: x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float) / 32767
    r = np.random.default_rng(9); n = len(x); tt = np.arange(n) / sr; bb = tt / BEAT
    crack = np.zeros(n)
    idx = r.choice(n, int(DUR * 22), replace=False); crack[idx] = r.uniform(-1, 1, len(idx))
    crack = np.convolve(crack, np.exp(-np.arange(40) / 6), "same") * 0.35
    hiss = np.convolve(r.normal(0, 1, n), [1, -0.9], "same") * 0.02
    env = np.clip((bb - 8) / 4, 0, 1) * np.where(bb < DROP, 1, np.where(bb < 52, 0.25, 0.6))
    x = x * np.where(bb < 22, 0.25, 1.0) + (crack + hiss) * env       # avant le diamant : surtout le disque qui tourne
    i = int(22 * BEAT * sr); thump = np.sin(2 * np.pi * 60 * np.arange(4000) / sr) * np.exp(-np.arange(4000) / 600) * 0.6
    x[i:i + 4000] += thump                                            # le diamant se pose
    x = np.tanh(x * 1.1); x /= np.abs(x).max() * 1.1
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((x * 32767).astype("<i2").tobytes())

if __name__ == "__main__":
    if PREVIEW:
        for b in [3, 9, 15, 19, 26, 32, 35.3, 37, 46, 55]:
            frame(int(b * BEAT * FPS)).save(os.path.join(OUT, f"vin{IDENT}_{b:04.1f}.png"))
        sys.exit()
    wav = OUT.replace(".mp4", ".wav"); audio(wav)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "21",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT],
                         stdin=subprocess.PIPE)
    for n in range(NF):
        p.stdin.write(frame(n).tobytes())
    p.stdin.close(); p.wait(); print("done", OUT)
