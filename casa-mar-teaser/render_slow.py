"""Casa Mar — teaser 2 « la visite » : lent, éditorial, lisible (1080x1920, 30 fps, 80 BPM, 24 s).
Usage : python render_slow.py <assets_dir> <out.mp4|preview_dir> <charte 1|2|3> [preview]
"""
import sys, os, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageChops

ASSETS, OUT = sys.argv[1], sys.argv[2]
IDENT = sys.argv[3] if len(sys.argv) > 3 else "1"
PREVIEW = len(sys.argv) > 4
sys.argv = [sys.argv[0], ASSETS, OUT, IDENT]          # helpers partagés avec le teaser 1
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R
from render import (W, H, FPS, KOKO, BOLD, LIGHT, text_img, paste_c, logo, waves,
                    clamp, eout, ein, hexrgb, font)

P = R.PAL
BPM = 80
BEAT = 60 / BPM                  # 0.75 s
DUR = 32 * BEAT                  # 24 s
NF = int(DUR * FPS)
M = 110                          # marge gauche éditoriale
WIPE = 0.9                       # durée de la transition vague

def ease_io(t): t = clamp(t); return t * t * (3 - 2 * t)

def fill(cv, c): cv.paste(Image.new("RGBA", (W, H), c))

def rise(cv, im, x, y, k, anchor="l"):
    """Texte qui monte derrière une ligne de masque (révélation par le bas)."""
    k = eout(k)
    if k <= 0: return
    h = im.height; vis = max(1, int(h * k))
    part = im.crop((0, 0, im.width, vis))
    xx = x - (im.width / 2 if anchor == "c" else (im.width if anchor == "r" else 0))
    cv.alpha_composite(part, (int(xx), int(y + h - vis)))

def fit(txt, path, maxw, maxh, color):
    im = text_img(txt, path, 300, color)
    s = min(maxw / im.width, maxh / im.height)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)

def rule(cv, x0, y, length, k, color, w=3):
    if k <= 0: return
    ImageDraw.Draw(cv).line((x0, y, x0 + length * eout(k), y), fill=color, width=w)

def header(cv, t, idx, label, ink):
    """Bandeau éditorial : 01  QUAND ........ CASA MAR"""
    a = eout(t / 0.6)
    num = text_img(idx, KOKO, 46, ink); lab = text_img(label, BOLD, 30, ink, tracking=8)
    brand = text_img("CASA MAR", BOLD, 26, ink, tracking=8)
    rise(cv, num, M, 238, t / 0.5); rise(cv, lab, M + num.width + 26, 246, (t - 0.1) / 0.5)
    rise(cv, brand, W - M, 248, (t - 0.2) / 0.5, anchor="r")
    rule(cv, M, 310, W - 2 * M, (t - 0.15) / 0.9, ink, 2)

def footer(cv, t, ink, text="JUIN 2028   NIMES"):
    rule(cv, M, 1560, W - 2 * M, (t - 0.3) / 0.9, ink, 2)
    im = text_img(text, BOLD, 26, ink, tracking=8)
    rise(cv, im, M, 1585, (t - 0.5) / 0.5)

# ------------------------------------------------------------------ scènes
def s_intro(cv, t):
    fill(cv, P["bg"])
    waves(cv, P["b"], 1650, t * 0.35, amp=10, wl=230, thick=4, rows=3, gap=34, alpha=int(110 * eout(t / 1.5)))
    rule(cv, W / 2 - 260 * eout((t - .2) / 1.2), 1120, 520 * eout((t - .2) / 1.2) or 0.1, 1, P["c"], 2) if t > .2 else None
    ic = logo("icon", P["a"], 330)
    k = eout((t - 0.5) / 1.3)
    if k > 0:
        vis = int(ic.height * k)
        cv.alpha_composite(ic.crop((0, 0, ic.width, vis)), (int(W / 2 - ic.width / 2), int(1080 - vis)))
    im = text_img("première edition", LIGHT, 58, P["c"], tracking=6)
    rise(cv, im, W / 2, 1160, (t - 1.2) / 0.7, anchor="c")
    im = text_img("CASA MAR", BOLD, 30, P["a"], tracking=14)
    rise(cv, im, W / 2, 1260, (t - 1.5) / 0.7, anchor="c")

def s_slogan(cv, t):
    fill(cv, P["c"]); ink = P["bg"]
    header(cv, t, "00", "LE SLOGAN", ink)
    l0 = fit("FAIS", KOKO, 520, 300, ink)
    l1 = fit("COMME", KOKO, 760, 300, ink)
    l2 = fit("CHEZ TOI", KOKO, W - 2 * M, 300, ink)
    y = 430
    for j, l in enumerate((l0, l1, l2)):
        rise(cv, l, M, y, (t - 0.3 - j * 0.25) / 0.8); y += l.height + 26
    y += 50
    if t > 1.0:
        waves(cv, P["a"], y, t * 0.5, amp=12, wl=120, thick=9, rows=2, gap=32, x0=M, x1=M + 330 * eout((t - 1) / 1))
    im = text_img("UNE MAISON   LA MER   LA NUIT", BOLD, 34, ink, tracking=10)
    rise(cv, im, M, y + 120, (t - 1.4) / 0.7)
    footer(cv, t, ink)

def s_quand(cv, t):
    fill(cv, P["c"]); ink = P["bg"]
    header(cv, t, "01", "QUAND", ink)
    j = fit("JUIN", KOKO, 640, 330, ink)
    y = fit("2028", KOKO, W - 2 * M, 360, ink)
    rise(cv, j, M, 470, (t - 0.25) / 0.8)
    rise(cv, y, M, 470 + j.height + 30, (t - 0.5) / 0.8)
    yy = 470 + j.height + 30 + y.height + 90
    h1 = text_img("12H", KOKO, 130, P["a"] if R.IDENT != 3 else ink)
    h2 = text_img("01H", KOKO, 130, P["a"] if R.IDENT != 3 else ink)
    rise(cv, h1, M, yy, (t - 1.0) / 0.6)
    ax0 = M + h1.width + 40; ax1 = W - M - h2.width - 40
    k = eout((t - 1.3) / 0.9)
    if k > 0:
        d = ImageDraw.Draw(cv); xe = ax0 + (ax1 - ax0) * k; cy = yy + h1.height / 2
        d.line((ax0, cy, xe, cy), fill=ink, width=4)
        if k > 0.95: d.line((xe - 26, cy - 20, xe, cy, xe - 26, cy + 20), fill=ink, width=4, joint="curve")
    rise(cv, h2, W - M, yy, (t - 2.0) / 0.6, anchor="r")
    im = text_img("DE MIDI A UNE HEURE DU MATIN", BOLD, 30, ink, tracking=8)
    rise(cv, im, M, yy + h1.height + 50, (t - 2.2) / 0.6)
    footer(cv, t, ink, "JOUR EXACT BIENTOT")

def s_lieu(cv, t):
    fill(cv, P["bg"]); ink = P["c"]
    # soleil rayé qui se lève (motif du tote bag)
    r = 260; cx, cy = W - 230, 1470 - 230 * ease_io(t / 3.5)
    sun = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0)); d = ImageDraw.Draw(sun)
    d.ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=hexrgb(P["a"]) + (255,))
    for i in range(6):
        yy = r + 20 + i * 44 + (t * 18) % 44
        d.rectangle((0, yy, 2 * r, yy + 12), fill=(0, 0, 0, 0))
    sun = Image.composite(sun, Image.new("RGBA", sun.size, (0, 0, 0, 0)), sun.getchannel("A"))
    cv.alpha_composite(sun, (int(cx - r), int(cy - r)))
    sea = Image.new("RGBA", (W, H - 1460), P["bg"]); cv.alpha_composite(sea, (0, 1460))
    waves(cv, P["b"], 1480, t * 0.4, amp=9, wl=200, thick=4, rows=2, gap=30, alpha=180)
    header(cv, t, "02", "LIEU", ink)
    l1 = fit("CLOS DE", KOKO, 700, 230, ink); l2 = fit("PROVENCE", KOKO, W - 2 * M, 260, ink)
    rise(cv, l1, M, 470, (t - 0.25) / 0.8); rise(cv, l2, M, 470 + l1.height + 26, (t - 0.5) / 0.8)
    im = text_img("nimes", LIGHT, 120, P["b"], tracking=10)
    rise(cv, im, M, 470 + l1.height + l2.height + 90, (t - 1.0) / 0.7)

def s_billets(cv, t):
    fill(cv, P["c"]); ink = P["bg"]
    header(cv, t, "03", "BILLETS", ink)
    rows = [("EARLY", "22€", "AVANT 14H"), ("PLEIN TARIF", "30€", "TOUTE LA JOURNEE"), ("VIP", "60€", "ACCES VIP")]
    y0 = 470
    for i, (name, price, sub) in enumerate(rows):
        st = 0.35 + i * 0.6; y = y0 + i * 300
        n = text_img(name, KOKO, 92, ink); pr = text_img(price, KOKO, 120, ink)
        rise(cv, n, M, y + (pr.height - n.height), (t - st) / 0.6)
        rise(cv, pr, W - M, y, (t - st - 0.1) / 0.6, anchor="r")
        k = eout((t - st - 0.2) / 0.8)
        if k > 0:                                   # points de conduite façon carte de restaurant
            d = ImageDraw.Draw(cv); xa = M + n.width + 30; xb = W - M - pr.width - 30
            yy = y + pr.height - 14
            for x in np.arange(xa, xa + (xb - xa) * k, 22): d.ellipse((x, yy, x + 7, yy + 7), fill=P["a"])
        s = text_img(sub, BOLD, 28, ink, tracking=8)
        rise(cv, s, M, y + pr.height + 26, (t - st - 0.3) / 0.5)
    # pastille majeurs
    k = eout((t - 2.4) / 0.6)
    if k > 0:
        tg = text_img("RESERVE AUX MAJEURS", BOLD, 30, ink, tracking=8)
        pw, ph = tg.width + 70, 76
        pill = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle((1, 1, pw - 2, ph - 2), 38, outline=ink, width=3)
        pill.alpha_composite(tg, (35, (ph - tg.height) // 2))
        rise(cv, pill, M, 1400, k)
    footer(cv, t, ink, "BILLETTERIE CASA MAR")

def s_lineup(cv, t):
    fill(cv, P["a"]); ink = P["on"]
    header(cv, t, "04", "LINE UP", ink)
    l1 = fit("LE LINE-UP", KOKO, W - 2 * M, 230, ink); l2 = fit("ARRIVE", KOKO, 700, 230, ink)
    rise(cv, l1, M, 430, (t - 0.25) / 0.8); rise(cv, l2, M, 430 + l1.height + 24, (t - 0.5) / 0.8)
    y0 = 430 + l1.height + l2.height + 110
    for i in range(5):
        y = y0 + i * 96; k = eout((t - 0.8 - i * 0.15) / 0.7)
        if k <= 0: continue
        num = text_img(f"0{i + 1}", BOLD, 30, ink, tracking=4); rise(cv, num, M, y + 12, k)
        bx0, bx1 = M + 110, M + 110 + (W - 2 * M - 110) * (0.55 + 0.4 * ((i * 37) % 10) / 10) * k
        bar = Image.new("RGBA", (int(bx1 - bx0) + 1, 56), (0, 0, 0, 0)); bd = ImageDraw.Draw(bar)
        bd.rounded_rectangle((0, 0, bar.width - 1, 55), 28, fill=hexrgb(ink) + (60,))
        sx = ((t * 380 + i * 140) % (bar.width + 400)) - 200      # reflet qui balaie la barre
        for dx in range(-90, 90, 6):
            a = int(70 * (1 - abs(dx) / 90))
            bd.line((sx + dx, 0, sx + dx - 30, 55), fill=hexrgb(ink) + (a,), width=6)
        m = Image.new("L", bar.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, bar.width - 1, 55), 28, fill=255)
        bar.putalpha(ImageChops.multiply(bar.getchannel("A"), m))
        cv.alpha_composite(bar, (int(bx0), int(y)))
    im = text_img("CINQ ARTISTES", BOLD, 30, ink, tracking=8)
    rise(cv, im, M, y0 + 5 * 96 + 50, (t - 1.8) / 0.6)
    im = text_img("ANNONCE TRES BIENTOT", BOLD, 30, ink, tracking=8)
    rise(cv, im, M, y0 + 5 * 96 + 100, (t - 2.0) / 0.6)

def s_outro(cv, t):
    fill(cv, P["bg"])
    waves(cv, P["b"], 1500, t * 0.35, amp=10, wl=230, thick=4, rows=4, gap=36, alpha=150)
    lg = logo("h", P["a"], 640)
    k = eout((t - 0.2) / 1.1)
    if k > 0:
        vis = int(lg.height * k)
        cv.alpha_composite(lg.crop((0, 0, lg.width, vis)), (int(W / 2 - lg.width / 2), int(980 - vis)))
    rule(cv, W / 2 - 200, 1050, 400, (t - 0.6) / 0.8, P["c"], 2)
    im = text_img("FAIS COMME CHEZ TOI", KOKO, 68, P["c"])
    rise(cv, im, W / 2, 1100, (t - 0.9) / 0.7, anchor="c")
    im = text_img("JUIN 2028   CLOS DE PROVENCE   NIMES", BOLD, 26, P["c"], tracking=8)
    rise(cv, im, W / 2, 1220, (t - 1.2) / 0.6, anchor="c")
    im = text_img("LINE-UP BIENTOT", KOKO, 40, P["b"])
    rise(cv, im, W / 2, 1290, (t - 1.5) / 0.6, anchor="c")
    if t > 2.5:
        cv.alpha_composite(Image.new("RGBA", (W, H), hexrgb(P["bg"]) + (int(255 * ein((t - 2.5) / 0.5)),)))

P["on"] = P["bg"]
SC = [(0, 4, s_intro), (4, 9, s_slogan), (9, 13, s_quand), (13, 18, s_lieu),
      (18, 24, s_billets), (24, 28, s_lineup), (28, 32, s_outro)]

def render_scene(idx, lt):
    cv = Image.new("RGBA", (W, H)); SC[idx][2](cv, lt); return cv

def frame(n):
    t = n / FPS
    for i, (a, b, fn) in enumerate(SC):
        if a * BEAT <= t < b * BEAT: break
    lt = t - a * BEAT
    cv = render_scene(i, lt)
    if i > 0 and lt < WIPE:                 # transition : la scène monte comme une vague
        prev = render_scene(i - 1, (SC[i - 1][1] - SC[i - 1][0]) * BEAT + lt)
        k = ease_io(lt / WIPE)
        edge = H * (1 - k)
        xs = np.arange(W)
        ys = np.arange(H)[:, None]
        e = edge + 28 * np.sin(xs / 95 + lt * 5) * math.sin(math.pi * k)
        mask = Image.fromarray(((ys > e) * 255).astype("uint8"))
        prev.paste(cv, (0, 0), mask)
        cv = prev
    rgb = cv.convert("RGB")
    g = R.GRAIN[n % len(R.GRAIN)]
    g = g.point(lambda v: 128 + (v - 128) * 0.6)
    return ImageChops.overlay(rgb, Image.merge("RGB", (g, g, g)))

# ------------------------------------------------------------------ musique : deep house lente, accords chauds
def audio(path, sr=44100):
    N = int(DUR * sr); out = np.zeros(N + sr); rng = np.random.default_rng(4)
    def add(sig, st):
        i = int(st * sr); j = min(len(out), i + len(sig)); out[i:j] += sig[:j - i]
    def note(f): return 440 * 2 ** ((f - 69) / 12)
    chords = [[57, 60, 64, 67, 71], [53, 57, 60, 64, 67], [48, 52, 55, 59, 62], [55, 59, 62, 64, 69]]  # Am9 Fmaj9 Cmaj9 G6/9
    bar = 4 * BEAT
    for b in range(8):
        ch = chords[b % 4]; x = np.arange(int(bar * sr * 1.15)) / sr
        env = np.minimum(1, x / 0.35) * np.exp(-x * 0.35)
        pad = sum(np.sin(2 * np.pi * note(m) * x * (1 + d)) for m in ch for d in (-0.0015, 0.0015)) / 10
        add(pad * env * 0.55, b * bar)
        add(np.sin(2 * np.pi * note(ch[0] - 24) * x) * np.minimum(1, x * 30) * np.exp(-x * 0.8) * 0.35, b * bar)
        # petites notes de piano électrique sur les contretemps
        for s in (1.5, 2.5, 3.5):
            xx = np.arange(int(1.2 * sr)) / sr; f = note(ch[int(s * 2) % len(ch)] + 12)
            add((np.sin(2 * np.pi * f * xx) + .3 * np.sin(4 * np.pi * f * xx)) * np.exp(-xx * 3.5) * 0.07, b * bar + s * BEAT)
    def kick():
        x = np.arange(int(0.4 * sr)) / sr; f = 48 + 90 * np.exp(-x * 35)
        return np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-x * 8) * 0.7
    def shaker():
        x = np.arange(int(0.09 * sr)) / sr; n = np.diff(np.concatenate([[0], rng.normal(0, 1, len(x))]))
        return n * np.sin(np.pi * x / x[-1]) * 0.05
    for b in range(4, 28):
        add(kick(), b * BEAT); add(shaker(), b * BEAT + BEAT / 2)
        if b % 2: add(shaker() * .6, b * BEAT + BEAT * .25)
    noise = np.convolve(rng.normal(0, 1, int(6 * sr)), np.ones(260) / 260, "same")
    sw = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(len(noise)) / sr * 0.22)
    add(noise * sw * 2.2, 0); add(noise * sw * 2.2, DUR - 6)
    out = out[:N]; f = int(1.2 * sr); out[-f:] *= np.linspace(1, 0, f); out[:int(.3 * sr)] *= np.linspace(0, 1, int(.3 * sr))
    out = np.tanh(out * 1.2); out /= np.abs(out).max() * 1.12
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((out * 32767).astype("<i2").tobytes())

if __name__ == "__main__":
    if PREVIEW:
        for b in [2.6, 6.5, 8.4, 11.6, 16.5, 19.5, 23.5, 26.7, 31.0, 13.4]:
            frame(int(b * BEAT * FPS)).save(os.path.join(OUT, f"slow{IDENT}_{b:04.1f}.png"))
        sys.exit()
    wav = OUT.replace(".mp4", ".wav"); audio(wav)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "22",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT],
                         stdin=subprocess.PIPE)
    for n in range(NF):
        p.stdin.write(frame(n).tobytes())
    p.stdin.close(); p.wait(); print("done", OUT)
