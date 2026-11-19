import sys, numpy as np, potrace
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
a = np.asarray(Image.open(src).convert('RGB')).astype(float)
bg = np.median(a.reshape(-1, 3), 0); fg = np.array([0xE8, 0xB0, 0x4A], float)
t = ((a - bg) @ (fg - bg)) / ((fg - bg) @ (fg - bg))
m = t > 0.5; m[:30] = m[-30:] = False; m[:, :30] = m[:, -30:] = False
ys, xs = np.where(m); y0, y1, x0, x1 = ys.min() - 4, ys.max() + 5, xs.min() - 4, xs.max() + 5
m = m[y0:y1, x0:x1]
plist = potrace.Bitmap(~m).trace(turdsize=10, alphamax=1.0, opttolerance=0.3)
d = []
f = lambda p: f"{p.x:.1f} {p.y:.1f}"
for c in plist:
    d.append("M" + f(c.start_point))
    for s in c.segments:
        if s.is_corner: d.append("L" + f(s.c) + "L" + f(s.end_point))
        else: d.append("C" + f(s.c1) + " " + f(s.c2) + " " + f(s.end_point))
    d.append("Z")
H, W = m.shape
open(out, 'w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}"><path fill="currentColor" fill-rule="evenodd" d="{"".join(d)}"/></svg>')
print(out, W, H, len("".join(d)))
