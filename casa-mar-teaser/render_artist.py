"""Casa Mar — teaser « annonce artiste », immersif (1080x1920, 30 fps, 120 BPM, 30 s).

Arrivée en vue subjective : coucher de soleil sur la mer, la maison au loin qu'on entend
étouffée, on s'approche, on entre, le son s'ouvre et le nom tombe sur le drop.

Usage : python render_artist.py <assets_dir> <out.mp4|preview_dir> <charte 1|2|3> "<NOM ARTISTE>"
              [--real] [--music=morceau.mp3 --drop-at=SECONDES] [preview]
--music : remplace la musique générée par ton morceau (sous licence). --drop-at : la seconde du
morceau qui doit tomber pile sur l'apparition du nom (18 s dans la vidéo).
Sans --real, une mention « EXEMPLE » est incrustée (annonce fictive, à ne pas publier).
"""
import sys, os, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageChops, ImageFilter

args = [a for a in sys.argv[1:] if a not in ("--real", "preview") and not a.startswith("--")]
REAL = "--real" in sys.argv
OPT = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
MUSIC = OPT.get("music")                      # morceau fourni (droits à ta charge)
DROP_AT = float(OPT.get("drop-at", "0"))      # seconde du morceau qui doit tomber sur le drop
PREVIEW = "preview" in sys.argv
ASSETS, OUT, IDENT, ARTIST = args[0], args[1], args[2], args[3].upper()
sys.argv = [sys.argv[0], ASSETS, OUT, IDENT]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R
from render import (W, H, FPS, KOKO, BOLD, LIGHT, text_img, paste_c, logo, clamp, eout, ein, hexrgb)

P = R.PAL
BPM = 120; BEAT = 0.5; NB = 60; DUR = NB * BEAT; NF = int(DUR * FPS)
DROP = 36                                   # temps du drop
C = {k: np.array(hexrgb(v), float) for k, v in P.items()}
NIGHT = C["bg"] * 0.55                       # ciel de nuit, plus profond que le fond
rng = np.random.default_rng(11)

def ease_io(t): t = clamp(t); return t * t * (3 - 2 * t)
def lerp(a, b, k): return a + (b - a) * k
def beat_pulse(t, decay=6.0):
    return math.exp(-((t / BEAT) % 1.0) * BEAT * decay)

# ------------------------------------------------------------------ extérieur : ciel, soleil, mer
HZ = 1080                                    # ligne d'horizon
YY = np.linspace(0, 1, HZ)[:, None]
def sky(k_night):
    """Dégradé : horizon chaud (accent) -> haut nuit. k_night 0 = coucher de soleil, 1 = nuit."""
    top = lerp(lerp(C["bg"], C["b"] * 0.6 + C["bg"] * 0.4, 0.35), NIGHT, k_night)
    hor = lerp(C["a"], C["a"] * 0.35 + C["bg"] * 0.65, k_night)
    g = (YY ** 1.8)[..., None]
    arr = lerp(top, hor, g)
    return np.repeat(arr, W, axis=1).astype("uint8")
SKY = [Image.fromarray(sky(k)).convert("RGBA") for k in np.linspace(0, 1, 24)]
STARS = [(rng.integers(0, W), rng.integers(0, HZ - 120), rng.uniform(1.5, 4), rng.uniform(0, 6)) for _ in range(140)]

def draw_exterior(cv, t, zoom):
    """t secondes depuis le début, zoom = avancée de la caméra vers la maison (0..1)."""
    kn = ease_io(t / 11)                                     # le soleil se couche sur 11 s
    cv.paste(SKY[int(kn * 23)], (0, 0))
    d = ImageDraw.Draw(cv, "RGBA")
    for x, y, s, ph in STARS:                                # étoiles
        a = int(255 * clamp((kn - 0.35) / 0.4) * (0.55 + 0.45 * math.sin(t * 2 + ph)))
        if a > 4: d.ellipse((x - s, y - s, x + s, y + s), fill=(255, 254, 241, a))
    # soleil rayé (motif tote bag) qui descend derrière l'horizon
    r = 230; sy = HZ - 120 + 330 * ease_io(t / 10)
    sun = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0)); sd = ImageDraw.Draw(sun)
    sd.ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=tuple(int(v) for v in C["a"]) + (255,))
    for i in range(7):
        yy = r + 10 + i * 38 + (t * 14) % 38
        sd.rectangle((0, yy, 2 * r, yy + 8 + i * 1.5), fill=(0, 0, 0, 0))
    gs = r // 2; glow = Image.new("RGBA", (gs, gs), tuple(int(v) for v in C["a"]) + (0,))
    gm = Image.new("L", (gs, gs), 0); ImageDraw.Draw(gm).ellipse((gs * .3, gs * .3, gs * .7, gs * .7), fill=int(255 * 0.45 * (1 - kn * 0.7)))
    glow.putalpha(gm.filter(ImageFilter.GaussianBlur(gs * .12))); glow = glow.resize((4 * r, 4 * r), Image.BILINEAR)
    cv.alpha_composite(glow, (int(W / 2 - 2 * r), int(sy - 2 * r)))
    top = cv.crop((0, 0, W, HZ)); top.alpha_composite(sun, (int(W / 2 - r), int(sy - r)))
    cv.paste(top, (0, 0))
    # maison au loin, halo qui pulse au rythme du kick étouffé
    hw = 150 * math.exp(zoom * 1.5)
    if hw < 3600:
        pulse = beat_pulse(t, 5) if t > 1.5 else 0
        hs = 0.25                                   # halo calculé en basse résolution, avec marge
        hwid, hhei = int(hw * 3.2 * hs), int(hw * 2.8 * hs)
        halo = Image.new("RGBA", (hwid, hhei), tuple(int(v) for v in C["a"]) + (0,))
        hm = Image.new("L", (hwid, hhei), 0)
        ImageDraw.Draw(hm).ellipse((hwid * .17, hhei * .2, hwid * .83, hhei * .8), fill=int(90 + 70 * pulse))
        halo.putalpha(hm.filter(ImageFilter.GaussianBlur(max(2, hw * 0.25 * hs))))
        halo = halo.resize((int(hw * 3.2), int(hw * 2.8)), Image.BILINEAR)
        hy = HZ - hw * 0.62
        cv.alpha_composite(halo, (int(W / 2 - halo.width / 2), int(hy - halo.height / 2)))
        ic = logo("icon", P["c"], int(hw))
        cv.alpha_composite(ic, (int(W / 2 - ic.width / 2), int(HZ - ic.height + hw * 0.05)))
    # mer en perspective : les lignes de vagues arrivent vers nous
    sea = Image.new("RGBA", (W, H - HZ), tuple(int(v) for v in lerp(C["bg"], NIGHT, 0.5)) + (255,))
    cv.paste(sea, (0, HZ))
    speed = 0.25 + zoom * 1.4
    for i in range(26):
        k = ((i / 26) + t * speed * 0.12) % 1.0                # profondeur 0 (loin) -> 1 (près)
        y = HZ + (H - HZ) * k ** 2.2
        amp = 2 + 26 * k ** 2; wl = 60 + 260 * k; th = max(1, int(1 + 7 * k ** 1.5))
        col = tuple(int(v) for v in lerp(C["b"], C["c"], 0.2)) + (int(40 + 200 * k),)
        pts = [(x, y + amp * math.sin(x / wl + t * 2.2 + i)) for x in range(-20, W + 30, 14)]
        d.line(pts, fill=col, width=th)
    # reflet du soleil
    for i in range(14):
        k = ((i / 14) + t * 0.08) % 1.0; y = HZ + 8 + (H - HZ) * k ** 2.2 * 0.8
        w = (40 + 300 * k) * (1 - kn * 0.8) * (0.6 + 0.4 * math.sin(t * 3 + i * 2))
        if w > 4: d.rounded_rectangle((W / 2 - w / 2, y, W / 2 + w / 2, y + 3 + 6 * k), 4, fill=tuple(int(v) for v in C["a"]) + (int(150 * (1 - kn * 0.6)),))

# ------------------------------------------------------------------ intérieur : tunnel de maisons au trait
HOUSE = [(-0.5, 0.45), (-0.5, -0.12), (0, -0.55), (0.5, -0.12), (0.5, 0.45)]
def house_line(d, cx, cy, size, color, alpha, width=2):
    pts = [(cx + x * size, cy + y * size) for x, y in HOUSE]
    d.line(pts, fill=tuple(int(v) for v in color) + (int(alpha),), width=width, joint="curve")

def tunnel(cv, t, speed=0.18, n=9, color=None, strength=1.0, cy=960):
    """Contours de la maison qui grandissent vers nous : on avance dans la maison."""
    color = C["c"] if color is None else color
    d = ImageDraw.Draw(cv, "RGBA")
    for i in range(n):
        k = ((i / n) + t * speed) % 1.0
        size = 90 * math.exp(k * 4.2)
        a = 150 * strength * math.sin(math.pi * k) ** 1.2
        if a > 2: house_line(d, W / 2, cy, size, color, a, width=2 if k < .7 else 3)

# nuit étoilée : points aux couleurs de la charte, qui scintillent et dérivent doucement vers nous
NIGHT_STARS = [(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0, 1), rng.integers(0, 3), rng.uniform(0, 6.3))
               for _ in range(260)]
def starfield(cv, t, speed=0.03, strength=1.0, cy=960):
    d = ImageDraw.Draw(cv, "RGBA")
    cols = [C["a"], C["b"], C["c"]]
    for x, y, z0, ci, ph in NIGHT_STARS:
        z = (z0 + t * speed) % 1.0                       # profondeur : 0 loin -> 1 près
        sc = 0.35 + 1.4 * z ** 1.6
        px, py = W / 2 + x * W * 0.62 * sc, cy + y * H * 0.55 * sc
        r = 1.6 + 4.2 * z ** 2
        tw = 0.55 + 0.45 * math.sin(t * (1.5 + ci) + ph)
        a = int(255 * strength * tw * min(1, z * 4) * min(1, (1 - z) * 6))
        if a > 6: d.ellipse((px - r, py - r, px + r, py + r), fill=tuple(int(v) for v in cols[ci]) + (a,))

def interior_bg(cv, color=None):
    cv.paste(Image.new("RGBA", (W, H), tuple(int(v) for v in (NIGHT * 0.8 if color is None else color)) + (255,)))

# ------------------------------------------------------------------ texte
def words(cv, txt, path, size, color, cy, a, tracking=6):
    if a <= 0: return
    im = text_img(txt, path, size, color, tracking=tracking)
    paste_c(cv, im, W / 2, cy + 18 * (1 - eout(a)), alpha=eout(a))

def name_lines():
    parts = ARTIST.split()
    return parts if len(parts) > 1 else [ARTIST]

def tiles(cv, t_beats):
    """Le nom en tuiles : quelques lettres se retournent avant le drop."""
    lines = name_lines()
    order = [(li, ci) for li, l in enumerate(lines) for ci, ch in enumerate(l)]
    r = np.random.default_rng(5); r.shuffle(order)
    shown = set(order[:max(0, int((t_beats - 26) / 2.2))][:5])   # 5 lettres max avant le drop
    for li, l in enumerate(lines):
        n = len(l); ts = min(96, int((W - 120) / n) - 8)
        x0 = W / 2 - (n * (ts + 8) - 8) / 2; y = 860 + li * (ts * 1.3 + 16)
        for ci, ch in enumerate(l):
            x = x0 + ci * (ts + 8)
            tile = Image.new("RGBA", (ts, int(ts * 1.3)), (0, 0, 0, 0)); td = ImageDraw.Draw(tile)
            if (li, ci) in shown:
                td.rounded_rectangle((0, 0, ts - 1, tile.height - 1), 12, fill=P["a"])
                g = text_img(ch, KOKO, int(ts * 0.85), P["bg"])
                tile.alpha_composite(g, ((ts - g.width) // 2, (tile.height - g.height) // 2))
            else:
                td.rounded_rectangle((0, 0, ts - 1, tile.height - 1), 12, fill=tuple(int(v) for v in NIGHT * 0.8) + (255,), outline=P["c"], width=3)
                a = int(80 + 60 * math.sin(t_beats * 1.5 + ci))
                td.rounded_rectangle((6, 6, ts - 7, tile.height - 7), 8, fill=tuple(int(v) for v in C["c"]) + (a // 4,))
            cv.alpha_composite(tile, (int(x), int(y)))

def big_name(cv, t, cy=820, slam=True, cols=None):
    lines = name_lines(); y = cy
    cols = cols or (P["c"], P["a"])
    for j, l in enumerate(lines):
        im = text_img(l, KOKO, 400, cols[0] if j == 0 else cols[1])
        s = min((W - 120) / im.width, (360 if j else 300) / im.height)
        lt = t - j * 0.12
        sc = s * (1 + (0.25 * (1 - eout(lt / 0.35)) if slam else 0))
        if lt > 0:
            paste_c(cv, im, W / 2, y + im.height * s / 2, scale=sc, alpha=clamp(lt / 0.08))
        y += im.height * s + 26

# ------------------------------------------------------------------ séquences
def frame(n):
    t = n / FPS; b = t / BEAT
    cv = Image.new("RGBA", (W, H))
    if b < 22:                                               # dehors : coucher de soleil, on s'approche
        zoom = ease_io((b - 8) / 14) if b > 8 else 0
        draw_exterior(cv, t, zoom)
        words(cv, "JUIN 2028", BOLD, 46, P["c"], 360, (t - 0.8) / 0.8 * (1 - clamp((t - 4.2) / 0.5)))
        words(cv, "le soleil tombe sur nimes", LIGHT, 64, P["c"], 360, (t - 4.7) / 0.8 * (1 - clamp((t - 8.0) / 0.5)))
        words(cv, "et la maison s allume", LIGHT, 64, P["c"], 360, (t - 8.5) / 0.8 * (1 - clamp((t - 10.2) / 0.4)))
        if b > 20:                                          # on passe la porte : fondu dans le noir
            cv.alpha_composite(Image.new("RGBA", (W, H), tuple(int(v) for v in NIGHT * 0.8) + (int(255 * ease_io((b - 20) / 2)),)))
    elif b < DROP:                                          # dedans : on avance dans la maison
        k = (b - 22) / (DROP - 22)
        interior_bg(cv)
        starfield(cv, t, speed=0.025 + 0.06 * k ** 2, strength=0.7 + 0.3 * k)
        words(cv, "ce soir", LIGHT, 70, P["c"], 560, (b - 22.5) / 1.6 * (1 - clamp((b - 27.5) / 1)))
        words(cv, "tu le connais", LIGHT, 70, P["c"], 560, (b - 28.5) / 1.6)
        tiles(cv, b)
    elif b < 52:                                            # drop
        lt = t - DROP * BEAT
        if b < 44:                                          # aplat de couleur, le nom en grand
            interior_bg(cv, C["a"])
            wipe = eout(lt / 0.35)                          # le bloc couleur monte depuis le bas
            if wipe < 1:
                cover = Image.new("RGBA", (W, int(H * (1 - wipe)) + 1), tuple(int(v) for v in NIGHT * 0.8) + (255,))
                cv.alpha_composite(cover, (0, 0))
            words(cv, "CASA MAR ACCUEILLE", BOLD, 38, P["bg"], 560, (lt - 0.15) / 0.4, tracking=12)
            big_name(cv, lt - 0.1, 680, cols=(P["bg"], P["bg"]))
            words(cv, "REJOINT LE LINE UP", BOLD, 40, P["bg"], 1360, (lt - 0.8) / 0.5, tracking=12)
            R.waves(cv, P["bg"], 1500, t * 0.6, amp=10, wl=130, thick=5, rows=2, gap=30, x0=W / 2 - 160, x1=W / 2 + 160)
        else:
            lt2 = t - 44 * BEAT
            interior_bg(cv)
            starfield(cv, t, speed=0.02, strength=0.8, cy=760)
            big_name(cv, 9, 360, slam=False)
            d = ImageDraw.Draw(cv)
            d.line((140, 1010, W - 140, 1010), fill=P["c"], width=2)
            words(cv, "JUIN 2028", KOKO, 110, P["c"], 1110, lt2 / 0.4, tracking=0)
            words(cv, "CLOS DE PROVENCE   NIMES", BOLD, 36, P["c"], 1230, (lt2 - 0.3) / 0.4, tracking=10)
            k = eout((lt2 - 0.6) / 0.6)
            if k > 0:
                for i in range(5):
                    x0 = 190 + i * 146
                    d.rounded_rectangle((x0, 1320, x0 + 126, 1344), 12, outline=P["c"], width=3,
                                        fill=P["a"] if i == 0 else None)
                words(cv, "1 SUR 5 ARTISTES DEVOILES", BOLD, 30, P["c"], 1395, k, tracking=10)
    else:                                                   # sortie : retour sur la mer, infos
        lt = t - 52 * BEAT
        draw_exterior(cv, 11 + lt, 0.0)
        veil = Image.new("RGBA", (W, H), tuple(int(v) for v in NIGHT * 0.7) + (150,)); cv.alpha_composite(veil)
        lg = logo("h", P["a"], 620); paste_c(cv, lg, W / 2, 620, alpha=eout(lt / 0.6))
        words(cv, ARTIST, KOKO, 76, P["c"], 920, (lt - 0.3) / 0.5, tracking=0)
        words(cv, "JUIN 2028   CLOS DE PROVENCE   NIMES", BOLD, 30, P["c"], 1010, (lt - 0.5) / 0.5, tracking=8)
        k = eout((lt - 0.8) / 0.5)
        if k > 0:
            tg = text_img("BILLETS DES 22€", KOKO, 64, P["bg"])
            pw = tg.width + 80; pill = Image.new("RGBA", (pw, 104), (0, 0, 0, 0))
            ImageDraw.Draw(pill).rounded_rectangle((0, 0, pw - 1, 103), 52, fill=P["a"])
            pill.alpha_composite(tg, (40, (104 - tg.height) // 2))
            paste_c(cv, pill, W / 2, 1140, alpha=k, scale=0.9 + 0.1 * k)
        words(cv, "RESERVE AUX MAJEURS", BOLD, 26, P["c"], 1250, (lt - 1.1) / 0.5, tracking=10)
        if lt > 3.4:
            cv.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * ein((lt - 3.4) / 0.6)))))
    if not REAL:                                            # garde-fou : annonce fictive
        tag = text_img("EXEMPLE", BOLD, 24, P["c"], tracking=10)
        pill = Image.new("RGBA", (tag.width + 40, 50), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle((0, 0, pill.width - 1, 49), 25, outline=P["c"], width=2)
        pill.alpha_composite(tag, (20, (50 - tag.height) // 2))
        pill.putalpha(pill.getchannel("A").point(lambda v: int(v * 0.75)))
        cv.alpha_composite(pill, (70, 200))
    rgb = cv.convert("RGB")
    g = R.GRAIN[n % len(R.GRAIN)]
    return ImageChops.overlay(rgb, Image.merge("RGB", (g, g, g)))

# ------------------------------------------------------------------ son : techno mélodique, filtre qui s'ouvre
def onepole_lp(x, fc, sr):
    """Passe-bas à une pôle, fréquence de coupure variable (tableau)."""
    a = 1 - np.exp(-2 * np.pi * np.asarray(fc) / sr)
    a = np.broadcast_to(a, x.shape)
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc); y[i] = acc
    return y

def audio(path, sr=44100):
    N = int(DUR * sr); music = np.zeros(N + sr); amb = np.zeros(N + sr)
    r = np.random.default_rng(2)
    def add(buf, sig, st):
        i = int(st * sr); j = min(len(buf), i + len(sig)); buf[i:j] += sig[:j - i]
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def kick():
        x = np.arange(int(0.42 * sr)) / sr; f = 46 + 110 * np.exp(-x * 32)
        return np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-x * 7) * 0.95
    def hat(d=0.05, g=0.1):
        x = np.arange(int(d * sr)) / sr; n = np.diff(np.concatenate([[0], r.normal(0, 1, len(x))]))
        return n * np.exp(-x * 60) * g
    def clap():
        x = np.arange(int(0.25 * sr)) / sr; n = np.convolve(r.normal(0, 1, len(x)), np.ones(5) / 5, "same")
        return n * (np.exp(-x * 18) + 0.5 * np.exp(-((x - .01) ** 2) / 2e-5)) * 0.22
    def saw(f, d, det=0.004):
        x = np.arange(int(d * sr)) / sr
        return sum(2 * ((x * f * (1 + k)) % 1) - 1 for k in (-det, 0, det)) / 3
    prog = [45, 41, 48, 43]                         # A  F  C  G (racines graves)
    arp = [0, 7, 12, 15, 19, 15, 12, 7]             # arpège mineur
    for b in range(NB - 4):
        st = b * BEAT; bar = (b // 4) % 4; root = prog[bar]
        if b < DROP - 2 or b >= DROP:
            add(music, kick(), st)
        if b >= 12 and (b < DROP - 2 or b >= DROP):
            add(music, hat(), st + BEAT / 2)
        if b >= DROP:
            add(music, hat(0.03, 0.06), st + BEAT / 4); add(music, hat(0.03, 0.06), st + 3 * BEAT / 4)
            if b % 2: add(music, clap(), st)
        if b >= 16:                                 # basse roulante en doubles croches
            for s in (1, 2, 3):
                x = np.arange(int(BEAT / 4 * sr)) / sr
                bs = np.sin(2 * np.pi * note(root - 12) * x) + 0.4 * saw(note(root - 12), BEAT / 4)
                add(music, bs * np.exp(-x * 14) * 0.28, st + s * BEAT / 4)
        if b >= 8:                                  # arpège (le filtre fera le travail)
            for s in range(4):
                m = root + 24 + arp[(b * 4 + s) % 8]
                sig = saw(note(m), BEAT / 4 * 0.95) * np.exp(-np.arange(int(BEAT / 4 * 0.95 * sr)) / sr * 9) * 0.16
                add(music, sig, st + s * BEAT / 4)
    for bar in range(NB // 4):                      # nappes
        st = bar * 4 * BEAT; root = prog[bar % 4]
        x = np.arange(int(4 * BEAT * sr * 1.1)) / sr
        ch = [root + 12, root + 19, root + 24, root + 27 if root in (45,) else root + 28]
        pad = sum(saw(note(m), x[-1] + 1 / sr, 0.006) for m in ch) / 4
        env = np.minimum(1, x / 0.6) * np.minimum(1, (x[-1] - x) / 0.6 + 0.2)
        add(music, pad * env * (0.22 if DROP <= bar * 4 < 52 else 0.13), st)
    # montée avant le drop : bruit blanc + roulement
    x = np.arange(int(6 * BEAT * sr)) / sr
    add(music, r.normal(0, 1, len(x)) * (x / x[-1]) ** 2 * 0.25, (DROP - 6) * BEAT)
    for i in range(16):
        add(music, clap() * (0.4 + i / 20), (DROP - 4) * BEAT + i * BEAT / 4)
    if MUSIC:                                       # morceau fourni : il remplace la musique générée
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", MUSIC, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        trk = np.frombuffer(raw, "<f4").astype(float)
        start = int((DROP_AT - DROP * BEAT) * sr)      # le drop de la vidéo tombe sur DROP_AT
        seg = np.zeros(len(music))
        a0, b0 = max(0, start), min(len(trk), start + len(music))
        if b0 > a0: seg[a0 - start:b0 - start] = trk[a0:b0]
        music = seg / (np.abs(seg).max() + 1e-9) * 0.9
    # ambiance : vagues
    sea = np.convolve(r.normal(0, 1, N + sr), np.ones(300) / 300, "same")
    lfo = 0.55 + 0.45 * np.sin(2 * np.pi * np.arange(len(sea)) / sr * 0.16)
    amb += sea * lfo * 2.6
    # filtre : étouffé dehors (on entend la maison au loin), s'ouvre en entrant, grand ouvert au drop
    tt = np.arange(len(music)) / sr; bb = tt / BEAT
    fc = np.where(bb < 8, 260, np.where(bb < 22, 260 + (bb - 8) / 14 * 900,
         np.where(bb < DROP, 1160 + ((bb - 22) / (DROP - 22)) ** 2 * 7000, np.where(bb < 52, 18000, 18000 - (bb - 52) / 8 * 17000))))
    fc = np.clip(fc, 120, 18000)
    music = onepole_lp(onepole_lp(music, fc, sr), fc, sr)
    vol = np.where(bb < 22, 0.35 + 0.35 * bb / 22, 1.0)
    amb_g = np.where(bb < 22, 1.0, np.where(bb < 52, 0.12, 0.9))
    out = (music * vol + amb * amb_g)[:N]
    f = int(1.2 * sr); out[-f:] *= np.linspace(1, 0, f)
    out = np.tanh(out * 1.4); out /= np.abs(out).max() * 1.1
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((out * 32767).astype("<i2").tobytes())

if __name__ == "__main__":
    if PREVIEW:
        for b in [3, 11, 17, 21, 25, 31, 35.5, 36.2, 40, 47, 55]:
            frame(int(b * BEAT * FPS)).save(os.path.join(OUT, f"art{IDENT}_{b:04.1f}.png"))
        sys.exit()
    wav = OUT.replace(".mp4", ".wav"); audio(wav)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "21",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT],
                         stdin=subprocess.PIPE)
    for n in range(NF):
        p.stdin.write(frame(n).tobytes())
    p.stdin.close(); p.wait(); print("done", OUT)
