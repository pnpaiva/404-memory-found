#!/usr/bin/env python3
"""
Synthesised sound effects for the shorts, written to public/sfx/*.wav (git-ignored, regenerate with
`python3 sfx.py`). Everything is made from sine, square and filtered noise, so there is nothing to
license and nothing a content-ID system can match.
"""

import os
import wave

import numpy as np

SR = 48000
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public", "sfx")
rng = np.random.default_rng(404)


def t(sec):
    return np.arange(int(sec * SR)) / SR


def env(n, attack=0.002, decay=0.1):
    x = np.arange(n) / SR
    a = np.clip(x / max(attack, 1e-4), 0, 1)
    return a * np.exp(-x / decay)


def lowpass(x, cutoff):
    # one-pole low-pass, good enough for shaping noise
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def bandpass(x, lo, hi):
    return lowpass(x, hi) - lowpass(x, lo)


def save(name, x, gain=0.9):
    x = x / (np.max(np.abs(x)) + 1e-9) * gain
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def pop():
    x = t(0.12)
    f = 500 + 900 * (x / x[-1])
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(x), 0.001, 0.035)
    click = rng.normal(0, 1, len(x)) * env(len(x), 0.0005, 0.004)
    return s + 0.4 * click


def thud():
    x = t(0.45)
    f = 120 * np.exp(-x * 9) + 45
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(x), 0.001, 0.16)
    slap = bandpass(rng.normal(0, 1, len(x)), 300, 2500) * env(len(x), 0.0005, 0.03)
    return body + 0.8 * slap


def click():
    x = t(0.05)
    return (np.sin(2 * np.pi * 3200 * x) * env(len(x), 0.0003, 0.006)
            + 0.6 * rng.normal(0, 1, len(x)) * env(len(x), 0.0002, 0.003))


def tick():
    x = t(0.04)
    return np.sin(2 * np.pi * 2100 * x) * env(len(x), 0.0002, 0.005)


def key():
    x = t(0.06)
    n = bandpass(rng.normal(0, 1, len(x)), 1500, 6000) * env(len(x), 0.0003, 0.008)
    return n + 0.3 * np.sin(2 * np.pi * 180 * x) * env(len(x), 0.0005, 0.02)


def whoosh(sec=0.5, lo=200, hi=2500):
    x = t(sec)
    shape = np.sin(np.pi * x / sec) ** 2
    return bandpass(rng.normal(0, 1, len(x)), lo, hi) * shape


def tapestop():
    x = t(0.6)
    f = 340 * np.exp(-x * 5.5) + 25
    ph = np.cumsum(f) / SR
    saw = 2 * (ph % 1) - 1
    return lowpass(saw, 1800) * np.clip(1.3 - x / 0.6, 0, 1)


def ding():
    x = t(1.4)
    return sum(a * np.sin(2 * np.pi * f * x) for f, a in [(1046.5, 1), (2093, 0.4), (3140, 0.2), (1568, 0.25)]) * env(len(x), 0.001, 0.35)


def chord():
    x = t(1.8)
    tones = sum(np.sin(2 * np.pi * f * x) + 0.3 * np.sin(4 * np.pi * f * x) for f in (261.6, 329.6, 392.0, 523.3))
    return tones * env(len(x), 0.02, 0.6)


def zap():
    x = t(0.7)
    f = 90 + 900 * (x / x[-1]) ** 2
    sq = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR))
    return (lowpass(sq, 3000) * 0.6 + 0.5 * rng.normal(0, 1, len(x))) * np.clip(1.1 - x / 0.7, 0, 1) * np.clip(x / 0.03, 0, 1)


def hum():
    x = t(1.6)
    s = np.sin(2 * np.pi * 60 * x) + 0.6 * np.sign(np.sin(2 * np.pi * 120 * x)) * 0.4 + 0.2 * np.sin(2 * np.pi * 180 * x)
    return s * np.clip(x / 0.25, 0, 1) * np.clip((1.6 - x) / 0.3, 0, 1)


def clunk():
    x = t(0.5)
    body = np.sin(2 * np.pi * 70 * x) * env(len(x), 0.001, 0.08)
    ring = np.sin(2 * np.pi * 1900 * x) * env(len(x), 0.001, 0.12) * 0.25
    return body + ring + 0.5 * bandpass(rng.normal(0, 1, len(x)), 800, 4000) * env(len(x), 0.0005, 0.02)


def riser():
    x = t(1.6)
    f = 200 + 2200 * (x / x[-1]) ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3
    noise = bandpass(rng.normal(0, 1, len(x)), 600, 6000) * (x / x[-1]) ** 2
    return (tone + noise) * (x / x[-1]) ** 1.5


def sparkle():
    out = np.zeros(int(0.9 * SR))
    for i, f in enumerate([1568, 2093, 2637, 3136, 4186]):
        x = t(0.5)
        s = np.sin(2 * np.pi * f * x) * env(len(x), 0.001, 0.12)
        o = int(i * 0.07 * SR)
        out[o:o + len(s)] += s[: len(out) - o]
    return out


def crt_on():
    x = t(0.5)
    whine = np.sin(2 * np.pi * 9000 * x) * env(len(x), 0.001, 0.25) * 0.3
    thump = np.sin(2 * np.pi * 55 * x) * env(len(x), 0.002, 0.09)
    return whine + thump + 0.4 * rng.normal(0, 1, len(x)) * env(len(x), 0.001, 0.05)


def crt_off():
    x = t(0.6)
    f = 4000 * np.exp(-x * 7) + 60
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(x), 0.001, 0.25)


def bassdrop():
    x = t(1.2)
    f = 90 * np.exp(-x * 3) + 32
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(x), 0.002, 0.45)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in [("pop", pop), ("thud", thud), ("click", click), ("tick", tick), ("key", key),
                     ("whoosh", whoosh), ("tapestop", tapestop), ("ding", ding), ("chord", chord),
                     ("zap", zap), ("hum", hum), ("clunk", clunk), ("riser", riser), ("sparkle", sparkle),
                     ("crt_on", crt_on), ("crt_off", crt_off), ("bassdrop", bassdrop)]:
        save(name, fn())
    save("whoosh_long", whoosh(0.9, 120, 1400))
    print("sfx:", sorted(os.listdir(OUT)))
