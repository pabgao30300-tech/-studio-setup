"""Casa Mar — TikTok teaser (1080x1920, 30 fps, 120 BPM, 16 s)."""
import math, subprocess, sys, os, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageChops

ASSETS = sys.argv[1]          # dir with fonts/ masks
OUT = sys.argv[2]             # output mp4
IDENT = int(sys.argv[3]) if len(sys.argv) > 3 else 1   # 1, 2 ou 3 : quelle charte
PREVIEW = len(sys.argv) > 4   # if set: dump a few stills only

W, H, FPS, BPM = 1080, 1920, 30, 120
BEAT = 60 / BPM               # 0.5 s
NBEATS = 32
DUR = NBEATS * BEAT           # 16 s
NF = int(DUR * FPS)

# ---------- palettes (charte graphique) ----------
P1 = dict(bg="#0B0F1E", a="#E8B04A", c="#FFFEF1", b="#7BB1DD")
P2 = dict(bg="#0D0D11", a="#D9203D", c="#FFFEF1", b="#F4A195")
P3 = dict(bg="#280D19", a="#E4A479", c="#FFFEEB", b="#E9F188")
PALS = [P1, P2, P3]
PAL = PALS[IDENT - 1]

F = lambda n: os.path.join(ASSETS, "fonts", n)
KOKO, BOLD, LIGHT = F("Kokoschka-casa.ttf"), F("Stolzl-Bold-casa.ttf"), F("Stolzl-Light-casa.ttf")
_fc = {}
def font(path, size):
    k = (path, int(size))
    if k not in _fc: _fc[k] = ImageFont.truetype(path, int(size))
    return _fc[k]

def masks(name):
    return Image.open(os.path.join(ASSETS, "build", f"mask_{name}.png")).convert("L")
M_H, M_V, M_ICON = masks("h"), masks("v"), masks("icon")

def hexrgb(h): h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eout(t): t = clamp(t); return 1 - (1 - t) ** 3
def eback(t, s=1.8): t = clamp(t) - 1; return 1 + t * t * ((s + 1) * t + s)
def ein(t): t = clamp(t); return t ** 3

# ---------- drawing helpers ----------
def text_img(txt, path, size, color, tracking=0):
    f = font(path, size)
    if tracking == 0:
        bb = f.getbbox(txt)
        im = Image.new("RGBA", (bb[2] - bb[0] + 4, bb[3] - bb[1] + 4), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((-bb[0] + 2, -bb[1] + 2), txt, font=f, fill=color)
        return im
    widths = [f.getlength(ch) for ch in txt]
    tw = int(sum(widths) + tracking * (len(txt) - 1)) + 8
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (tw, asc + desc + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im); x = 4
    for ch, w in zip(txt, widths):
        d.text((x, 4), ch, font=f, fill=color); x += w + tracking
    return im.crop(im.getbbox())

def paste_c(canvas, im, cx, cy, alpha=1.0, scale=1.0, rot=0.0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1.0:
        a = im.getchannel("A").point(lambda v: int(v * clamp(alpha)))
        im = im.copy(); im.putalpha(a)
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def big_text(canvas, txt, color, cy, maxw=940, maxh=520, path=KOKO, scale=1.0, alpha=1.0, rot=0):
    im = text_img(txt, path, 400, color)
    s = min(maxw / im.width, maxh / im.height) * scale
    paste_c(canvas, im, W / 2, cy, alpha, s, rot)

def mask_img(mask, color, width):
    s = width / mask.width
    m = mask.resize((int(mask.width * s), int(mask.height * s)), Image.LANCZOS)
    im = Image.new("RGBA", m.size, hexrgb(color) + (0,)); im.putalpha(m)
    return im

_mc = {}
def logo(kind, color, width):
    k = (kind, color, int(width))
    if k not in _mc: _mc[k] = mask_img({"h": M_H, "v": M_V, "icon": M_ICON}[kind], color, int(width))
    return _mc[k]

def waves(canvas, color, y, t, amp=22, wl=150, thick=14, rows=2, gap=46, x0=-40, x1=W + 40, phase=0.0, alpha=255):
    d = ImageDraw.Draw(canvas)
    col = hexrgb(color) + (alpha,)
    for r in range(rows):
        pts = []
        for x in range(int(x0), int(x1), 6):
            pts.append((x, y + r * gap + amp * math.sin(2 * math.pi * (x / wl) + t * 6 + phase)))
        d.line(pts, fill=col, width=thick, joint="curve")
        for p in (pts[0], pts[-1]):
            d.ellipse((p[0] - thick / 2, p[1] - thick / 2, p[0] + thick / 2, p[1] + thick / 2), fill=col)

def rrect(canvas, box, r, color):
    ImageDraw.Draw(canvas).rounded_rectangle(box, r, fill=color)

# film grain tiles (precomputed)
rng = np.random.default_rng(7)
GRAIN = [Image.fromarray(rng.normal(128, 20, (H // 2, W // 2)).clip(0, 255).astype("uint8")).resize((W, H)) for _ in range(6)]

# ---------- scenes ----------
def beat_of(t): return t / BEAT
def pulse(t, decay=7.0):
    """1 on each beat, decaying."""
    ph = (t / BEAT) % 1.0
    return math.exp(-ph * BEAT * decay)

def scene_intro(cv, t):        # beats 0-3 : la maison se dessine
    p = PAL
    cv.paste(Image.new("RGBA", (W, H), p["bg"]))
    # rising tide of waves at the bottom
    k = eout(t / 2.0)
    for i in range(5):
        waves(cv, p["b"], H - 180 - i * 90 * k, t + i * 0.3, amp=14, wl=180, thick=8, rows=1,
              alpha=int(60 + 30 * i * k))
    ic = logo("icon", p["a"], 520)
    reveal = eout((t - 0.15) / 1.2)
    h = int(ic.height * reveal)
    if h > 0:
        part = ic.crop((0, ic.height - h, ic.width, ic.height))
        cv.alpha_composite(part, (int(W / 2 - ic.width / 2), int(820 - ic.height / 2 + ic.height - h)))
    msg = "le line up arrive"
    n = int(clamp((t - 0.7) / 1.0) * len(msg))
    if n:
        im = text_img(msg[:n], BOLD, 54, p["c"], tracking=4)
        cv.alpha_composite(im, (int(W / 2 - text_img(msg, BOLD, 54, p["c"], 4).width / 2), 1180))
    if 1.75 < t < 2.0:                         # flash into drop
        a = (t - 1.75) / 0.25
        cv.alpha_composite(Image.new("RGBA", (W, H), hexrgb(p["c"]) + (int(255 * a),)))

WORDS = [("UNE", "a", "bg"), ("MAISON", "a", "bg"), ("LA", "b", "bg"), ("MER", "b", "bg"), ("LA", "bg", "c"), ("NUIT", "bg", "a")]
def scene_words(cv, t):        # beats 4-9 : UNE MAISON / LA MER / LA NUIT
    p = PAL
    i = int(beat_of(t)); lt = t - i * BEAT
    bgk, fgk = WORDS[i][1], WORDS[i][2]
    cv.paste(Image.new("RGBA", (W, H), p[bgk]))
    sub = {0: "une maison", 1: "une maison", 2: "la mer", 3: "la mer", 4: "la nuit", 5: "la nuit"}[i]
    if i in (2, 3):
        waves(cv, p["bg"], 1340, t, amp=26, wl=170, thick=18, rows=3, gap=60, alpha=255)
    if i in (4, 5):                         # night: little stars
        r = np.random.default_rng(3)
        d = ImageDraw.Draw(cv)
        for _ in range(40):
            x, y = r.integers(0, W), r.integers(0, H)
            tw = 0.5 + 0.5 * math.sin(t * 9 + x)
            s = 3 + 3 * tw
            d.ellipse((x - s, y - s, x + s, y + s), fill=hexrgb(p["c"]) + (int(120 + 120 * tw),))
    if i in (0, 1):
        ic = logo("icon", p["bg"], 260); cv.alpha_composite(ic, (int(W / 2 - ic.width / 2), 330))
    sc = 1.0 + 0.35 * (1 - eout(lt / 0.18))
    big_text(cv, WORDS[i][0], p[fgk], 900, maxw=940, maxh=430, scale=sc, rot=(-3 if i % 2 else 3) * (1 - eout(lt / 0.25)))
    im = text_img(sub, LIGHT, 64, p[fgk], tracking=6)
    paste_c(cv, im, W / 2, 1180, alpha=eout(lt / 0.2))

def scene_flicker(cv, t):      # beats 10-15 : le logo en variantes de la charte
    i = int(beat_of(t)); lt = t - i * BEAT
    P = PAL
    # (fond, logo, texte) : on alterne les couleurs de la même charte
    v = [("bg", "a", "c"), ("a", "bg", "bg"), ("b", "bg", "bg")][i % 3]
    p = dict(bg=P[v[0]], a=P[v[1]], c=P[v[2]], b=P[v[2]])
    pill_txt = P[v[0]]
    cv.paste(Image.new("RGBA", (W, H), p["bg"]))
    # repeating icons in background, scrolling
    small = logo("icon", p["a"], 120)
    off = (t * 140) % 220
    for row in range(-1, 10):
        for col in range(-1, 6):
            x = col * 220 + (110 if row % 2 else 0) - off
            y = row * 220 + off * 0.5
            a = small.copy(); a.putalpha(a.getchannel("A").point(lambda v: v * 0.13))
            cv.alpha_composite(a, (int(x), int(y)))
    sc = 1.0 + 0.12 * pulse(t, 9)
    lg = logo("v", p["a"], 540)
    paste_c(cv, lg, W / 2, 800, scale=sc)
    im = text_img("première edition", LIGHT, 74, p["c"], tracking=4)
    paste_c(cv, im, W / 2, 1300, alpha=eout((t) / 0.6))
    # lower tag pill
    tag = ["LINE-UP BIENTOT", "JUIN 2028", "NIMES"][i % 3]
    ti = text_img(tag, KOKO, 60, pill_txt)
    bw = ti.width + 80
    rrect(cv, (W / 2 - bw / 2, 1400, W / 2 + bw / 2, 1490), 45, p["b"])
    paste_c(cv, ti, W / 2, 1445)

def wristband(color, txtcol, length=1500, hgt=120):
    im = Image.new("RGBA", (length, hgt), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, length - 1, hgt - 1), hgt // 2, fill=color)
    ic = logo("icon", txtcol, 72)
    name = text_img("CASA MAR", KOKO, 62, txtcol)
    x = 50; k = 0
    while x < length - 60:
        if k % 4 == 3:
            im.alpha_composite(name, (x, (hgt - name.height) // 2)); x += name.width + 40
        else:
            im.alpha_composite(ic, (x, (hgt - ic.height) // 2)); x += ic.width + 40
        k += 1
    return im

def scene_merch(cv, t):        # beats 16-21 : bracelets + billet
    p = PAL
    cv.paste(Image.new("RGBA", (W, H), p["bg"]))
    bands = [(p["a"], p["bg"], "STAFF", 520), (p["c"], p["bg"], "VIP", 760), (p["b"], p["bg"], "EARLY", 1000)]
    tt = t
    for j, (c, tc, lab, y) in enumerate(bands):
        st = j * BEAT * 0.5
        k = eout((tt - st) / 0.5)
        band = wristband(c, tc)
        band = band.rotate(-8, resample=Image.BICUBIC, expand=True)
        dirn = -1 if j % 2 else 1
        x = (W / 2) + dirn * (1 - k) * 1600 + dirn * (tt * 40)
        out = clamp((tt - 1.45) / 0.35)
        x += dirn * ein(out) * -1700
        paste_c(cv, band, x, y)
        li = text_img(lab, KOKO, 54, c)
        paste_c(cv, li, x + 420 * (1), y + 120, alpha=k * (1 - out))
    # ticket slides up on beat 19
    tk = t - 3 * BEAT
    if tk > 0:
        k = eback(tk / 0.4, 1.2)
        card = ticket(p)
        y = H + card.height / 2 - k * (H / 2 + card.height / 2 - 30)
        paste_c(cv, card, W / 2, y, rot=-4 + 4 * eout(tk / 0.5))
    title = text_img("TON PASS", KOKO, 90, p["c"])
    paste_c(cv, title, W / 2, 260, alpha=eout(t / 0.3) * (1 - clamp((tk - 0.1) / 0.2)) if tk > 0 else eout(t / 0.3))

_ticket = {}
def ticket(p):
    if p["a"] in _ticket: return _ticket[p["a"]]
    w, h = 840, 1180
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 60, fill=p["a"])
    # perforation
    for x in range(40, w - 30, 46):
        d.ellipse((x, 830, x + 18, 848), fill=p["bg"])
    L = lambda s: text_img(s, LIGHT, 46, p["bg"], 2)
    B = lambda s, z=52: text_img(s, KOKO, z, p["bg"])
    def put(img, x, y): im.alpha_composite(img, (int(x), int(y)))
    put(L("event"), 70, 80); put(B("CASA MAR"), 70, 145)
    put(L("date"), 540, 80); put(B("JUIN 2028"), 540, 145)
    put(L("location"), 70, 280); put(B("CLOS DE PROVENCE"), 70, 345)
    e = text_img("EARLY AVANT 14H", BOLD, 40, p["bg"], 2); put(e, 70, 480)
    put(B("22€", 120), 70, 545)
    ic = logo("icon", p["bg"], 200); put(ic, w - 280, 520)
    put(B("CASA MAR", 120), (w - B("CASA MAR", 120).width) / 2, 935)
    _ticket[p["a"]] = im
    return im

def scene_info(cv, t):         # beats 22-27 : 22€ / location
    p = PAL
    i = int(beat_of(t)); lt = t - i * BEAT
    if i < 3:
        cv.paste(Image.new("RGBA", (W, H), p["bg"]))
        sc = 1.0 + 0.25 * (1 - eout(lt / 0.15))
        price, label, col = [("22€", "EARLY AVANT 14H", "a"), ("30€", "PLEIN TARIF", "c"), ("60€", "VIP", "b")][i]
        big_text(cv, price, p[col], 860, maxw=880, maxh=600, scale=sc)
        im = text_img(label, BOLD, 64, p["c"], tracking=6)
        paste_c(cv, im, W / 2, 1260, alpha=eout(lt / 0.15))
        waves(cv, p["b"], 1420, t, amp=16, wl=140, thick=10, rows=2, gap=40, x0=280, x1=800)
    else:
        cv.paste(Image.new("RGBA", (W, H), p["b"]))
        tt = t - 3 * BEAT
        im = text_img("location", LIGHT, 70, p["bg"], 6)
        paste_c(cv, im, W / 2, 640, alpha=eout(tt / 0.3))
        for j, word in enumerate(["CLOS DE", "PROVENCE"]):
            k = eout((tt - 0.12 - j * 0.15) / 0.35)
            big_text(cv, word, p["bg"], 840 + j * 250, maxw=900, maxh=230, scale=0.6 + 0.4 * k, alpha=k)
        im = text_img("nimes", LIGHT, 90, p["bg"], 8)
        paste_c(cv, im, W / 2, 1300, alpha=eout((tt - 0.35) / 0.3))
        pin = logo("icon", p["bg"], 160)
        paste_c(cv, pin, W / 2, 1460 + 16 * math.sin(t * 6), alpha=eout((tt - 0.5) / 0.3))

def scene_end(cv, t):          # beats 28-31 : lockup final
    p = PAL
    cv.paste(Image.new("RGBA", (W, H), p["bg"]))
    for i in range(4):
        waves(cv, p["b"], 1500 + i * 70, t + i * 0.4, amp=12, wl=200, thick=7, rows=1, alpha=70 + 40 * i)
    k = eback(t / 0.5, 1.4)
    lg = logo("h", p["a"], 780)
    paste_c(cv, lg, W / 2, 660, scale=0.6 + 0.4 * k, alpha=clamp(t / 0.15))
    big_text(cv, "JUIN 2028", p["c"], 1010, maxw=700, maxh=150, alpha=eout((t - 0.3) / 0.3))
    im = text_img("clos de provence  nimes", LIGHT, 56, p["c"], tracking=4)
    paste_c(cv, im, W / 2, 1120, alpha=eout((t - 0.45) / 0.3))
    tag = text_img("LINE-UP BIENTOT", KOKO, 76, p["bg"])
    bw = tag.width + 90
    a = eout((t - 0.6) / 0.25)
    if a > 0:
        pop = 1 + 0.15 * (1 - eout((t - 0.6) / 0.3)) + 0.05 * pulse(t)
        pill = Image.new("RGBA", (int(bw), 110), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle((0, 0, bw - 1, 109), 55, fill=p["b"])
        pill.alpha_composite(tag, (45, (110 - tag.height) // 2))
        paste_c(cv, pill, W / 2, 1260, scale=pop, rot=-3)
    im = text_img("MAJEURS UNIQUEMENT", BOLD, 40, p["a"], tracking=8)
    paste_c(cv, im, W / 2, 1390, alpha=eout((t - 0.9) / 0.3))
    if t > 1.9:                      # fade out the very end
        cv.alpha_composite(Image.new("RGBA", (W, H), hexrgb(p["bg"]) + (int(255 * ein((t - 1.9) / 0.1)),)))

SCENES = [(0, 4, scene_intro), (4, 10, scene_words), (10, 16, scene_flicker),
          (16, 22, scene_merch), (22, 28, scene_info), (28, 32, scene_end)]

def frame(n):
    t = n / FPS
    b = t / BEAT
    for s, e, fn in SCENES:
        if s <= b < e:
            cv = Image.new("RGBA", (W, H))
            fn(cv, t - s * BEAT)
            break
    # global beat zoom after the drop
    if 4 <= b < 30:
        z = 1 + 0.018 * pulse(t, 10)
        if z > 1.001:
            cw, ch = int(W / z), int(H / z)
            cv = cv.crop(((W - cw) // 2, (H - ch) // 2, (W - cw) // 2 + cw, (H - ch) // 2 + ch)).resize((W, H), Image.BILINEAR)
    rgb = cv.convert("RGB")
    g = GRAIN[n % len(GRAIN)]
    rgb = ImageChops.overlay(rgb, Image.merge("RGB", (g, g, g)))
    return rgb

# ---------- audio ----------
def audio(path, sr=44100):
    N = int(DUR * sr) + sr
    out = np.zeros(N)
    tt = np.arange(N) / sr
    rng = np.random.default_rng(1)
    def add(sig, start):
        i = int(start * sr); j = min(N, i + len(sig)); out[i:j] += sig[:j - i]
    # ocean intro (filtered noise swelling) beats 0-4
    noise = rng.normal(0, 1, int(2.2 * sr))
    k = np.ones(200) / 200; sea = np.convolve(noise, k, "same")
    env = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(len(sea)) / sr * 0.55)
    add(sea * env * 3.0, 0)
    # riser into drop
    rl = int(1.6 * sr); x = np.arange(rl) / sr
    riser = rng.normal(0, 1, rl) * (x / 1.6) ** 2 * 0.25 + np.sin(2 * np.pi * (200 + 600 * (x / 1.6) ** 2) * x) * (x / 1.6) ** 2 * 0.15
    add(riser, 0.4)
    def kick():
        x = np.arange(int(0.35 * sr)) / sr
        f = 50 + 120 * np.exp(-x * 30)
        return np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-x * 9) * 0.9
    def hat():
        x = np.arange(int(0.06 * sr)) / sr
        n = rng.normal(0, 1, len(x)); n = np.diff(np.concatenate([[0], n]))
        return n * np.exp(-x * 70) * 0.12
    def clap():
        x = np.arange(int(0.2 * sr)) / sr
        n = rng.normal(0, 1, len(x)); env = np.exp(-x * 25) + 0.6 * np.exp(-((x - 0.012) ** 2) / 1e-5)
        return np.convolve(n, np.ones(6) / 6, "same") * env * 0.25
    def bass(freq, d=0.22):
        x = np.arange(int(d * sr)) / sr
        s = np.sign(np.sin(2 * np.pi * freq * x)) * 0.5 + np.sin(2 * np.pi * freq * x)
        s = np.convolve(s, np.ones(18) / 18, "same")
        return s * np.minimum(1, x * 200) * np.exp(-x * 6) * 0.22
    def pluck(freq, d=0.4):
        x = np.arange(int(d * sr)) / sr
        return (np.sin(2 * np.pi * freq * x) + 0.4 * np.sin(4 * np.pi * freq * x)) * np.exp(-x * 7) * 0.12
    prog = [55.0, 55.0, 43.65, 49.0]                # A, A, F, G
    arp = [440.0, 523.25, 659.25, 523.25, 587.33, 659.25, 783.99, 659.25]
    for b in range(4, 30):
        st = b * BEAT
        add(kick(), st)
        add(hat(), st + BEAT / 2)
        if b % 2 == 1: add(clap(), st)
        root = prog[(b // 4) % 4]
        add(bass(root), st + BEAT / 2)
        if b >= 10:
            add(pluck(arp[(b * 2) % 8]), st); add(pluck(arp[(b * 2 + 1) % 8]) * 0.7, st + BEAT / 2)
        if 16 <= b < 28: add(hat() * 0.6, st + BEAT / 4); add(hat() * 0.6, st + 3 * BEAT / 4)
    # final hit
    add(kick() * 1.2, 28 * BEAT)
    x = np.arange(int(2.0 * sr)) / sr
    chord = sum(np.sin(2 * np.pi * f * x) for f in (220, 261.63, 329.63, 440)) * np.exp(-x * 1.6) * 0.08
    add(chord, 28 * BEAT)
    add(sea[: int(2 * sr)] * np.linspace(0, 1, int(2 * sr)) * 1.5, 28 * BEAT)
    out = out[: int(DUR * sr)]
    fade = int(0.25 * sr); out[-fade:] *= np.linspace(1, 0, fade)
    out = np.tanh(out * 1.3); out /= np.abs(out).max() * 1.12
    data = (out * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(data.tobytes())

if __name__ == "__main__":
    if PREVIEW:
        for b in [1.5, 3.2, 4.3, 5.3, 6.3, 7.3, 8.3, 9.3, 10.3, 12.3, 14.3, 16.6, 17.3, 19.2, 21.5, 23, 26, 30.5]:
            frame(int(b * BEAT * FPS)).save(os.path.join(OUT, f"prev{IDENT}_{b:05.1f}.png"))
        sys.exit()
    wav = OUT.replace(".mp4", ".wav")
    audio(wav)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                          "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT],
                         stdin=subprocess.PIPE)
    for n in range(NF):
        p.stdin.write(frame(n).tobytes())
        if n % 60 == 0: print("frame", n, "/", NF, flush=True)
    p.stdin.close(); p.wait()
    print("done", OUT)
