#!/usr/bin/env python3
"""Generate a royalty-free chiptune bed for the shorts: public/music.wav (stereo, 44.1 kHz).

Nothing is sampled; every note is synthesised here, so the track is owned outright and safe on every platform.
Style: soft 8-bit lo-fi, ~96 BPM, A minor, arpeggiated pads + round bass + a light hat. Quiet and
non-melodic on purpose so it sits under the voice.

  python3 gen_music.py            -> 48 s loop
  python3 gen_music.py 60 --seed 7
"""
import math
import os
import struct
import sys
import wave

try:
    import numpy as np
except ImportError:  # pragma: no cover
    sys.exit("numpy is required: pip3 install numpy")

SR = 44100
BPM = 96
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public", "music.wav")


def note(freq, seconds, wave_kind="square", vol=0.2, attack=0.01, release=0.08):
    n = int(SR * seconds)
    t = np.arange(n) / SR
    if wave_kind == "square":
        sig = np.sign(np.sin(2 * math.pi * freq * t)) * 0.5 + 0.25 * np.sin(2 * math.pi * freq * t)
    elif wave_kind == "tri":
        sig = 2 / math.pi * np.arcsin(np.sin(2 * math.pi * freq * t))
    else:
        sig = np.sin(2 * math.pi * freq * t)
    env = np.ones(n)
    a = int(attack * SR)
    r = int(release * SR)
    if a:
        env[:a] = np.linspace(0, 1, a)
    if r:
        env[-r:] = np.linspace(1, 0, r)
    return sig * env * vol


def hat(seconds, vol=0.06):
    n = int(SR * seconds)
    noise = np.random.uniform(-1, 1, n)
    env = np.exp(-np.arange(n) / (SR * 0.02))
    return noise * env * vol


def lowpass(x, k=6):
    kernel = np.ones(k) / k
    return np.convolve(x, kernel, mode="same")


def mix(buf, start, seg, gain=1.0):
    if start >= len(buf):
        return
    end = min(len(buf), start + len(seg))
    buf[start:end] += seg[: end - start] * gain


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def main():
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else 48.0
    seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else 4
    np.random.seed(seed)
    beat = 60 / BPM
    step = beat / 2  # eighth notes
    total = int(SR * seconds)
    left = np.zeros(total)
    right = np.zeros(total)

    # A minor progression, one chord per bar (4 beats): Am, F, C, G
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    bass_notes = [45, 41, 36, 43]
    pos = 0.0
    bar = 0
    while pos < seconds:
        chord = chords[bar % 4]
        bass = bass_notes[bar % 4]
        # bass: two long notes per bar, triangle wave
        for b in range(2):
            start = int((pos + b * 2 * beat) * SR)
            seg = note(midi(bass), 2 * beat * 0.95, "tri", vol=0.16, attack=0.02, release=0.3)
            mix(left, start, seg)
            mix(right, start, seg)
        # arpeggio: eighth notes cycling the chord, one octave up, slightly panned
        pattern = [0, 1, 2, 1, 0, 2, 1, 2]
        for i in range(8):
            if np.random.random() < 0.12:
                continue  # leave a few holes so it breathes
            start = int((pos + i * step) * SR)
            f = midi(chord[pattern[i]] + 12)
            seg = note(f, step * 0.9, "square", vol=0.07, attack=0.005, release=0.06)
            pan = 0.35 + 0.3 * (i % 2)
            mix(left, start, seg, 1 - pan)
            mix(right, start, seg, pan)
        # hat on the off-beats
        for i in range(8):
            if i % 2 == 1:
                start = int((pos + i * step) * SR)
                seg = hat(0.05, vol=0.05)
                mix(left, start, seg, 0.6)
                mix(right, start, seg, 0.6)
        pos += 4 * beat
        bar += 1

    left = lowpass(left)
    right = lowpass(right)
    # gentle fade in / out
    fade = int(SR * 1.0)
    for ch in (left, right):
        ch[:fade] *= np.linspace(0, 1, fade)
        ch[-fade:] *= np.linspace(1, 0, fade)
    peak = max(np.max(np.abs(left)), np.max(np.abs(right)), 1e-6)
    left = left / peak * 0.8
    right = right / peak * 0.8
    inter = np.empty(total * 2)
    inter[0::2] = left
    inter[1::2] = right
    data = (inter * 32767).astype("<i2").tobytes()
    with wave.open(OUT, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)
    print(f"wrote {OUT} ({seconds:.0f}s, {BPM} BPM, seed {seed})")


if __name__ == "__main__":
    main()
