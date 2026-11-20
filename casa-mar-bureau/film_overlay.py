"""Titres du film « le bureau se remplit » : incruste titres, compteur de m² et bandeaux sur les images rendues.
Usage : python film_overlay.py <frames_dir> <fonts_dir> <out_dir>
"""
import sys, os, glob
from PIL import Image, ImageDraw, ImageFont

FR, FONTS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
W, H, FPS = 1080, 1920, 30
NAVY, ORANGE, CREAM, BLUE = (11, 15, 30), (232, 176, 74), (255, 254, 241), (123, 177, 221)
KOKO = os.path.join(FONTS, "Kokoschka-casa.ttf")
STB = os.path.join(FONTS, "Stolzl-Bold-casa.ttf")
INTER_L = "/usr/share/fonts/opentype/inter/Inter-Light.otf"
INTER_S = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
_f = {}
def F(p, s):
    if (p, s) not in _f: _f[(p, s)] = ImageFont.truetype(p, s)
    return _f[(p, s)]

# (début, fin, titre Kokoschka, sous-titre)
CAPS = [
    (0.2, 1.4, "LE PLATEAU", "10,00 × 8,00 m · 3,00 m sous plafond"),
    (1.4, 3.2, "LES MURS", "Façade rue au nord, mitoyen à l'ouest"),
    (3.2, 5.2, "LES VITRAGES", "Plein sud sur le jardin, cloisons toute hauteur"),
    (5.2, 7.0, "LA MAISON", "Un portique en chêne au profil du logo"),
    (7.0, 9.2, "LE SALON", "Entrée & salon · 14,96 m²"),
    (9.2, 11.2, "LA CUISINE", "Kitchenette & café · 8,32 m²"),
    (11.2, 13.8, "OPEN SPACE", "Six postes autour d'une table · 22,44 m²"),
    (13.8, 16.0, "REUNION", "Salle vitrée, huit places · 12,92 m²"),
    (16.0, 18.6, "DIRECTION", "Bureau de direction · 10,88 m²"),
    (18.6, 21.0, "LA LUMIERE", "Le soleil se couche, la maison s'allume"),
]
# (début, fin, surface) : le compteur avance pendant que chaque pièce se meuble
AREAS = [(7.0, 9.2, 14.96), (9.2, 11.2, 8.32), (11.2, 13.8, 22.44), (13.8, 16.0, 12.92), (16.0, 16.9, 3.40), (16.9, 18.7, 10.88), (18.6, 19.6, 7.08)]

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease(k): k = clamp(k); return 1 - (1 - k) ** 3

def gradient(h, top_alpha, bottom_alpha, flip=False):
    g = Image.new("L", (1, h))
    for y in range(h):
        k = y / (h - 1); g.putpixel((0, y), int(255 * (top_alpha + (bottom_alpha - top_alpha) * k)))
    g = g.resize((W, h))
    im = Image.new("RGBA", (W, h), NAVY + (0,)); im.putalpha(g); return im
BOTTOM = gradient(640, 0.0, .88)
TOP = gradient(300, .7, 0.0)

def text(d, xy, s, font, fill, alpha=255, anchor="la", tracking=0):
    if tracking:
        x, y = xy
        if anchor[0] == "r": x -= sum(font.getlength(c) + tracking for c in s) - tracking
        for c in s:
            d.text((x, y), c, font=font, fill=fill + (alpha,), anchor="l" + anchor[1]); x += font.getlength(c) + tracking
    else:
        d.text(xy, s, font=font, fill=fill + (alpha,), anchor=anchor)

def area_at(t):
    a = 0.
    for s, e, v in AREAS: a += v * ease((t - s) / (e - s))
    return a

frames = sorted(glob.glob(os.path.join(FR, "f*.jpg")))
for n, fp in enumerate(frames):
    t = n / FPS
    im = Image.open(fp).convert("RGBA")
    im.alpha_composite(TOP, (0, 0)); im.alpha_composite(BOTTOM, (0, H - 640))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    fin = clamp((t - 21.0) / .6)
    # en-tête
    text(d, (64, 92), "CASA MAR STUDIO", F(STB, 30), CREAM, tracking=6)
    text(d, (W - 64, 96), "Bureaux · 80 m²", F(INTER_L, 30), CREAM, anchor="ra")
    d.line((64, 146, W - 64, 146), fill=CREAM + (120,), width=2)
    # légende de l'étape
    if fin < 1:
        for s, e, title, sub in CAPS:
            if s - .1 <= t <= e + .25:
                k_in, k_out = ease((t - s) / .45), clamp((t - (e - .05)) / .3)
                a = int(255 * k_in * (1 - k_out) * (1 - fin)); dy = 30 * (1 - k_in)
                if a <= 0: continue
                text(d, (64, 1560 + dy), title, F(KOKO, 104), ORANGE, a)
                text(d, (68, 1690 + dy), sub, F(INTER_L, 38), CREAM, a)
        # compteur
        A = area_at(t)
        if A > .01:
            ca = int(255 * clamp((t - 7.0) / .5) * (1 - fin))
            text(d, (W - 64, 1795), f"{A:.2f}".replace(".", ",") + " m²", F(INTER_S, 52), CREAM, ca, anchor="rs")
            text(d, (W - 64, 1830), "aménagés", F(INTER_L, 26), CREAM, int(ca * .75), anchor="rs")
            bw = W - 128; d.rounded_rectangle((64, 1856, 64 + bw, 1864), 4, fill=CREAM + (int(ca * .25),))
            d.rounded_rectangle((64, 1856, 64 + max(8, bw * A / 80), 1864), 4, fill=ORANGE + (ca,))
    # final
    if fin > 0:
        a = int(255 * fin)
        text(d, (W / 2, 1530 + 20 * (1 - fin)), "FAIS COMME", F(KOKO, 118), ORANGE, a, anchor="mm")
        text(d, (W / 2, 1650 + 20 * (1 - fin)), "CHEZ TOI", F(KOKO, 118), ORANGE, a, anchor="mm")
        text(d, (W / 2, 1765), "Casa Mar Studio · 80,00 m² · 6 postes · salle de réunion · salon", F(INTER_L, 30), CREAM, a, anchor="mm")
    im.alpha_composite(layer)
    if t > 23.5:
        im.alpha_composite(Image.new("RGBA", (W, H), NAVY + (int(255 * clamp((t - 23.5) / .5)),)))
    im.convert("RGB").save(os.path.join(OUT, os.path.basename(fp)), quality=93)
print("ok", len(frames))
