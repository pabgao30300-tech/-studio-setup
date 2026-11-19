import sys, wave, numpy as np
sr = 44100; BEAT = 0.5; DUR = 15.0; N = int(DUR * sr); out = np.zeros(N + sr); r = np.random.default_rng(3)
def add(sig, st):
    i = int(st * sr); j = min(len(out), i + len(sig)); out[i:j] += sig[:j - i]
note = lambda m: 440 * 2 ** ((m - 69) / 12)
def saw(f, d, det=.005):
    x = np.arange(int(d * sr)) / sr; return sum(2 * ((x * f * (1 + k)) % 1) - 1 for k in (-det, 0, det)) / 3
def kick():
    x = np.arange(int(.42 * sr)) / sr; f = 46 + 110 * np.exp(-x * 32); return np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-x * 7)
def hat(g=.08):
    x = np.arange(int(.05 * sr)) / sr; n = np.diff(np.concatenate([[0], r.normal(0, 1, len(x))])); return n * np.exp(-x * 60) * g
def clap():
    x = np.arange(int(.22 * sr)) / sr; return np.convolve(r.normal(0, 1, len(x)), np.ones(5) / 5, "same") * np.exp(-x * 18) * .2
prog = [45, 41, 48, 43]; arp = [0, 7, 12, 15, 19, 15, 12, 7]
for b in range(30):
    st = b * BEAT; root = prog[(b // 4) % 4]
    for s in range(4):                                   # arpège tout du long
        m = root + 24 + arp[(b * 4 + s) % 8]
        add(saw(note(m), .11) * np.exp(-np.arange(int(.11 * sr)) / sr * 10) * (.06 if b < 12 else .1), st + s * BEAT / 4)
    if b >= 12 and b < 26:
        add(kick() * .9, st); add(hat(), st + BEAT / 2); add(hat(.05), st + BEAT / 4); add(hat(.05), st + 3 * BEAT / 4)
        if b % 2: add(clap(), st)
        for s in (1, 2, 3):
            x = np.arange(int(BEAT / 4 * sr)) / sr
            add((np.sin(2 * np.pi * note(root - 12) * x) + .4 * saw(note(root - 12), BEAT / 4)) * np.exp(-x * 14) * .26, st + s * BEAT / 4)
    elif b < 12 and b % 2 == 0 and b >= 4:
        add(kick() * .35, st)                             # cœur qui bat, au loin
for bar in range(8):
    x = np.arange(int(2.2 * sr)) / sr; root = prog[bar % 4]
    pad = sum(saw(note(m), x[-1] + 1 / sr, .007) for m in (root + 12, root + 19, root + 24, root + 27)) / 4
    add(pad * np.minimum(1, x / .5) * np.minimum(1, (x[-1] - x) / .5) * .12, bar * 2)
x = np.arange(int(4 * sr)) / sr                          # montée vers le drop
add(r.normal(0, 1, len(x)) * (x / x[-1]) ** 3 * .22, 2.0)
add(kick() * 1.3, 13.0)                                  # coup final
x = np.arange(int(2 * sr)) / sr
add(sum(np.sin(2 * np.pi * note(m) * x) for m in (57, 60, 64, 69)) * np.exp(-x * 1.4) * .08, 13.0)
sea = np.convolve(r.normal(0, 1, len(out)), np.ones(280) / 280, "same") * (0.6 + 0.4 * np.sin(np.arange(len(out)) / sr * 1.1)) * 2.2
tt = np.arange(len(out)) / sr
out += sea * np.where(tt < 6, 1, np.where(tt < 13, .25, .9))
# filtre qui s'ouvre jusqu'au drop
fc = np.clip(np.where(tt < 6, 300 + (tt / 6) ** 2 * 6000, 18000), 100, 18000); a = 1 - np.exp(-2 * np.pi * fc / sr)
y = np.empty_like(out); acc = 0.0
for i in range(len(out)): acc += a[i] * (out[i] - acc); y[i] = acc
y = y[:N]; f = int(1 * sr); y[-f:] *= np.linspace(1, 0, f)
y = np.tanh(y * 1.4); y /= np.abs(y).max() * 1.1
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((y * 32767).astype("<i2").tobytes())
print("ok")
