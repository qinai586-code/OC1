#!/usr/bin/env python3
"""Original soundtrack and sound effects for the film, synthesized in code (no samples).

Usage:  python3 make_audio.py cues.js soundtrack.wav

Every event time is read from the same cues.js that film.html draws from, so the
sounds land on the frames they belong to.
"""
import json
import math
import sys
import wave

import numpy as np

SR = 48000
src = open(sys.argv[1], encoding="utf-8").read()
CUE = json.loads(src[src.index("{"): src.rindex("}") + 1])
T = CUE["T"]
DUR = T["duration"]
N = int((DUR + 0.5) * SR)
mix = np.zeros((N, 2))
rng = np.random.default_rng(20261008)


def put(sig, t0, gain=1.0, pan=0.0):
    """Mix a mono signal into the stereo bus at time t0 (seconds), equal-power pan."""
    i0 = int(round(t0 * SR))
    if i0 < 0 or i0 >= N:
        return
    n = min(len(sig), N - i0)
    ang = (pan + 1) * math.pi / 4
    mix[i0:i0 + n, 0] += sig[:n] * gain * math.cos(ang)
    mix[i0:i0 + n, 1] += sig[:n] * gain * math.sin(ang)


def tvec(d):
    return np.arange(int(d * SR)) / SR


def tone(f, d, decay=6.0, f_end=None, partials=(1.0,), attack=0.002):
    t = tvec(d)
    f0 = np.full_like(t, f) if f_end is None else f + (f_end - f) * t / d
    ph = 2 * np.pi * np.cumsum(f0) / SR
    s = sum(a * np.sin((k + 1) * ph) for k, a in enumerate(partials))
    return s * np.exp(-decay * t) * np.minimum(1.0, t / attack)


def noise(d, decay=30.0):
    t = tvec(d)
    return rng.standard_normal(len(t)) * np.exp(-decay * t)


def sweep_lowpass(x, f_from, f_to):
    """One-pole lowpass whose cutoff glides from f_from to f_to Hz."""
    y = np.zeros_like(x)
    acc = 0.0
    fc = np.linspace(f_from, f_to, len(x))
    a = 1 - np.exp(-2 * np.pi * fc / SR)
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def pad(f, d):
    t = tvec(d)
    env = np.minimum(1.0, t / 0.5) * np.clip((d - t) / 1.0, 0, 1)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * env


# ---- sound effects -----------------------------------------------------------------
def flick(t0, pan):                       # paper slap as a note lands
    x = np.diff(noise(0.06, decay=70), prepend=0) * 2.5
    put(x + 0.4 * tone(1500, 0.06, decay=90), t0, gain=0.22, pan=pan)


def tick(t0, pan=0.0, f=2600, g=0.10):
    put(tone(f, 0.03, decay=160), t0, gain=g, pan=pan)


def click(t0, pan=0.0):                   # one typed character
    x = np.diff(noise(0.012, decay=400), prepend=0) * 1.5 + 0.3 * tone(3400, 0.012, decay=300)
    put(x, t0, gain=0.09, pan=pan)


def boing(t0):                            # spark lands
    put(tone(560, 0.5, decay=7, f_end=170, partials=(1, 0.35, 0.12)), t0, gain=0.5)


def chirp(t0):                            # a thought
    put(tone(1100, 0.1, decay=28, f_end=1500), t0, gain=0.14, pan=-0.3)


def ding(t0, f, g=0.3):                   # passing check
    put(tone(f, 1.6, decay=3.2, partials=(1, 0, 0.22, 0, 0.08)), t0, gain=g)


def bonk(t0):                             # failing check
    x = tone(190, 0.28, decay=11, f_end=120, partials=(1, 0.8, 0.45, 0.25))
    put(np.tanh(2.2 * x) * 0.5, t0, gain=0.55)


def oops(t0):                             # two falling notes
    put(tone(523.25, 0.25, decay=7, partials=(1, 0.3)), t0, gain=0.28)
    put(tone(392.0, 0.5, decay=4.5, partials=(1, 0.3)), t0 + 0.2, gain=0.28)


def whoosh(t0, d, g=0.22, up=True, pan=0.0):
    x = rng.standard_normal(int(d * SR))
    env = np.sin(np.pi * np.linspace(0, 1, len(x))) ** 2
    y = sweep_lowpass(x, 300, 3600) if up else sweep_lowpass(x, 3600, 300)
    y = y * env
    y = y / (np.max(np.abs(y)) + 1e-9)
    put(y, t0, gain=g, pan=pan)


def pop(t0):
    put(tone(900, 0.3, decay=16, f_end=180, partials=(1, 0.3)), t0, gain=0.55)
    put(noise(0.02, decay=200), t0, gain=0.4)


def zap(t0, d):
    x = np.diff(rng.standard_normal(int(d * SR)), prepend=0)
    env = np.sin(np.pi * np.linspace(0, 1, len(x))) ** 0.5 * (rng.random(len(x)) > 0.3)
    put(x * env / (np.max(np.abs(x)) + 1e-9) * 0.5, t0, gain=0.35)


def thump(t0):
    put(tone(120, 0.5, decay=8, f_end=45, partials=(1, 0.2)), t0, gain=0.8)


def sparkle(t0):
    for k, f in enumerate([2093, 2637, 3136, 3951]):
        put(tone(f, 0.5, decay=9), t0 + k * 0.055, gain=0.09, pan=(k - 1.5) * 0.4)


def bloop(t0):
    put(tone(300, 0.16, decay=10, f_end=640), t0, gain=0.32)


# ---- sound design from the timeline ---------------------------------------------------
# Notes land: one paper slap each.
for i in range(5):
    flick(T["notesIn"] + i * T["noteStep"] + 0.5, pan=(i - 2) * 0.3)
whoosh(T["tangle"], 0.6, g=0.10, up=False)
tick(T["cap1"], pan=-0.2)
boing(T["land"])
for k in range(3):
    chirp(T["think"] + 0.15 * k)
# Notes slide into the plan list.
whoosh(T["move"] - 0.1, 0.9, g=0.16, up=True, pan=-0.5)
for i, off in enumerate(T["moveOffs"]):
    tick(T["move"] + off + T["moveDur"] * 0.9, pan=-0.6 + 0.4 * i, f=2000 + 200 * i, g=0.08)
# Editor slides in.
whoosh(T["edIn"], 0.7, g=0.2, up=True, pan=0.4)

# Typing: one click every third character.
BEFORE = CUE["CODE_BEFORE"]
L = len(BEFORE)
for k, ch in enumerate(BEFORE):
    if ch.strip() and k % 3 == 0:
        t_char = T["typeStart"] + (k + 1) / L * (T["typeEnd"] - T["typeStart"])
        click(t_char, pan=rng.uniform(-0.4, 0.4))

# Checks run. Two passes, then the failure with a sad two-note "oops".
for t_pass in T["resolve1"][:2]:
    ding(t_pass, 1046.5, g=0.22)
bonk(T["resolve1"][2])
oops(T["oops"] + 0.05)

# The fix: delete the tail, then type the new one.
before_lines = BEFORE.split("\n")
after_lines = CUE["CODE_AFTER"].split("\n")
edit_idx = next(i for i, (a, b) in enumerate(zip(before_lines, after_lines)) if a != b)
prefix = 0
while before_lines[edit_idx][prefix] == after_lines[edit_idx][prefix]:
    prefix += 1
n_del = len(before_lines[edit_idx]) - prefix
n_type = len(after_lines[edit_idx]) - prefix
for k in range(0, n_del, 2):
    t_char = T["editStart"] + (k + 1) / n_del * (T["editDel"] - T["editStart"])
    click(t_char, pan=rng.uniform(-0.3, 0.3))
for k in range(0, n_type, 2):
    t_char = T["editDel"] + (k + 1) / n_type * (T["editEnd"] - T["editDel"])
    click(t_char, pan=rng.uniform(-0.3, 0.3))
whoosh(T["editEnd"] + 0.05, 0.35, g=0.15, up=True, pan=0.0)

# Rerun: three passes sound as a little chord rising.
whoosh(T["rerun"], 0.35, g=0.08, up=True)
for t_pass, f in zip(T["resolve2"], [523.25, 659.25, 783.99]):
    ding(t_pass, f, g=0.26)
sparkle(T["happy"])

# Chart arrives, the make-it-pop zap, the pop, then bars bloop up.
whoosh(T["chartIn"], 0.6, g=0.16, up=True, pan=0.4)
zap(T["zap"], 0.25)
pop(T["pop"])
for i in range(3):
    bloop(T["bars"] + i * T["barStep"])

# Outro: a swoosh, the spark lands with a thump, a wink, and a chord under the wordmark.
whoosh(T["outro"], 0.5, g=0.12, up=False)
whoosh(T["lockStart"], 0.6, g=0.12, up=True, pan=-0.2)
thump(T["lockEnd"])
sparkle(T["wink"])
for f in (261.63, 329.63, 392.00, 493.88, 587.33):
    put(pad(f, 3.0), T["wordIn"], gain=0.05)
ding(T["tagIn"], 1318.5, g=0.12)
tick(T["discIn"], f=3000, g=0.05)

# ---- underscore: a soft four-chord loop (C maj7, A min7, F maj7, G) ------------------------
BPM = 84
beat = 60 / BPM
chord_len = 2 * 4 * beat
CHORDS = [
    ([261.63, 329.63, 392.00, 493.88], 130.81),
    ([220.00, 261.63, 329.63, 392.00], 110.00),
    ([174.61, 220.00, 261.63, 329.63], 87.31),
    ([196.00, 246.94, 293.66, 329.63], 98.00),
]
ARP = [0, 1, 2, 3, 2, 1, 2, 3]
t_chord = 0.6
k = 0
while t_chord < DUR:
    tones, bass = CHORDS[k % len(CHORDS)]
    for f in tones:
        put(pad(f / 2, chord_len + 0.5), t_chord, gain=0.035, pan=0.0)
    eighth = beat / 2
    for s in range(int(chord_len / eighth)):
        ts = t_chord + s * eighth
        if ts >= DUR:
            break
        f = tones[ARP[s % 8]] * (2 if (s // 8) % 2 else 1)
        put(tone(f, 0.9, decay=4.0, partials=(1, 0.5, 0.2)), ts, gain=0.10, pan=0.5 * math.sin(s * 0.9))
    for b in range(int(chord_len / beat)):
        ts = t_chord + b * beat
        if ts >= DUR:
            break
        put(tone(bass, 0.7, decay=3.0, partials=(1, 0.2)), ts, gain=0.20)
    t_chord += chord_len
    k += 1

# ---- master ---------------------------------------------------------------------------
t_all = np.arange(N) / SR
fade_in = np.clip(t_all / 0.1, 0, 1)
fade_out = np.clip((DUR + 0.4 - t_all) / 0.8, 0, 1)
mix *= (fade_in * fade_out)[:, None]
mix = np.tanh(mix * 1.2) * 0.7                     # soft limit; headroom for AAC overshoot
pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2")
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"wrote {sys.argv[2]}: {N / SR:.2f} s, peak {np.max(np.abs(mix)):.3f}")
