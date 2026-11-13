#!/usr/bin/env python3
"""
Turn a raw voiceover recording into a tight, clean narration track plus word timings for captions.

    python3 vo_cut.py clippy                       # reads public/clippy/vo-raw.wav
    python3 vo_cut.py clippy --gap 0.16 --beat "The strange" --beat "So, in" ...

1. Cleans the voice with ffmpeg: rumble cut, gentle denoise, presence lift, compression, -16 LUFS.
2. Transcribes it with whisper.cpp (word timestamps) unless public/<slug>/vo-words.json already exists.
3. Removes dead air found in the signal itself (frames under the noise floor for MIN_PAUSE or more):
   each pause shrinks to --gap seconds, or --beat-gap before a phrase passed with --beat (the dramatic
   turns), with short fades at each cut so nothing clicks. Word timings are remapped through the cuts.
4. Writes public/<slug>/vo.wav (git-ignored) and scripts/<slug>-vo.json (words re-timed to the cut).
"""

import argparse
import json
import os
import subprocess
import wave

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.expanduser(os.environ.get("WHISPER_MODEL", "~/.cache/whisper/ggml-large-v3-turbo.bin"))
MIN_PAUSE = 0.20  # shorter silences are part of the sentence and stay
DTW_LAG = 0.10    # whisper DTW onsets land about 0.1 s after the energy onset
FADE = 0.008


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def read_wav(path):
    with wave.open(path) as w:
        sr, n = w.getframerate(), w.getnframes()
        data = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
    return sr, data


def write_wav(path, sr, data):
    pcm = (np.clip(data, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def transcribe(src16, out_base):
    run(["whisper-cli", "-m", MODEL, "-f", src16, "-l", "en", "-ml", "1", "-sow", "-ojf", "-of", out_base, "-t", "8"])
    words = []
    for seg in json.load(open(out_base + ".json"))["transcription"]:
        t = seg["text"].strip()
        if t:
            words.append({"w": t, "s": seg["offsets"]["from"] / 1000, "e": seg["offsets"]["to"] / 1000})
    return words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--gap", type=float, default=0.16)
    ap.add_argument("--beat-gap", type=float, default=0.38)
    ap.add_argument("--beat", action="append", default=[], help="phrase that opens a dramatic turn")
    ap.add_argument("--fix", action="append", default=[], help="caption fix, old=new (e.g. Taped=Tap)")
    ap.add_argument("--remove", action="append", default=[], help="retake to cut, START-END[:GAP] on the tightened timeline")
    a = ap.parse_args()

    d = os.path.join(ROOT, "public", a.slug)
    raw, clean = os.path.join(d, "vo-raw.wav"), os.path.join(d, "vo-clean.wav")
    # Shape and compress first, then a single fixed gain to -16 LUFS. One-pass loudnorm rides the gain
    # like an automatic volume and lifts the room noise in every pause, so it is not used here.
    shaped = os.path.join(d, "vo-shaped.wav")
    run(["ffmpeg", "-y", "-i", raw, "-af",
         "highpass=f=85,afftdn=nr=22:nf=-34:tn=1,anlmdn=s=0.0008:p=0.002:r=0.006,equalizer=f=220:t=q:w=1.2:g=-2,"
         "equalizer=f=3800:t=q:w=1.4:g=3,acompressor=threshold=-22dB:ratio=3:attack=8:release=140:makeup=2",
         "-ar", "48000", "-ac", "1", shaped])
    probe = subprocess.run(["ffmpeg", "-i", shaped, "-af", "ebur128", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
    measured = float(probe.rsplit("I:", 1)[1].split("LUFS")[0])
    run(["ffmpeg", "-y", "-i", shaped, "-af", f"volume={-16 - measured:.2f}dB,alimiter=limit=0.84:level=false",
         "-ar", "48000", "-ac", "1", clean])

    words_path = os.path.join(d, "vo-words.json")
    if os.path.exists(words_path):
        words = json.load(open(words_path))
        if isinstance(words, dict):
            words = [{"w": s["text"].strip(), "s": s["offsets"]["from"] / 1000, "e": s["offsets"]["to"] / 1000}
                     for s in words["transcription"] if s["text"].strip()]
    else:
        src16 = os.path.join(d, "vo16.wav")
        run(["ffmpeg", "-y", "-i", raw, "-ar", "16000", "-ac", "1", src16])
        words = transcribe(src16, os.path.join(d, "vo-words"))

    fixes = dict(f.split("=", 1) for f in a.fix)
    for w in words:
        core = w["w"].strip(".,!?")
        if core in fixes:
            w["w"] = w["w"].replace(core, fixes[core])

    # Find real pauses in the audio itself. Whisper stretches each word over the silence after it,
    # so its timings cannot tell where the speaker breathed; the signal level can.
    sr, audio = read_wav(clean)
    hop = int(0.01 * sr)
    frames = len(audio) // hop
    rms = np.array([np.sqrt(np.mean(audio[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(frames)])
    db = 20 * np.log10(rms)
    thr = max(np.percentile(db, 12) + 9, -46.0)
    quiet = db < thr
    pauses = []
    i = 0
    while i < frames:
        if quiet[i]:
            j = i
            while j < frames and quiet[j]:
                j += 1
            if (j - i) * 0.01 >= MIN_PAUSE:
                pauses.append([i * 0.01, j * 0.01])
            i = j
        else:
            i += 1

    beat_starts = []
    lower = [w["w"].lower() for w in words]
    for b in [x.lower().split() for x in a.beat]:
        for k in range(len(lower)):
            if all(k + m < len(lower) and lower[k + m].startswith(b[m].rstrip(",")) for m in range(len(b))):
                beat_starts.append(words[k]["s"])
                break

    def is_beat(p):
        return any(p[0] - 0.4 <= bs <= p[1] + 0.6 for bs in beat_starts)

    # Duck the room tone inside each pause (never inside speech), with ramps so it breathes naturally
    gain = np.ones(len(audio), dtype=np.float32)
    ramp = int(0.025 * sr)
    for p0, p1 in pauses:
        s0, s1 = int((p0 + 0.03) * sr), int((p1 - 0.03) * sr)
        if s1 - s0 > 2 * ramp:
            gain[s0:s1] = 0.2
            gain[s0:s0 + ramp] = np.linspace(1, 0.2, ramp)
            gain[s1 - ramp:s1] = np.linspace(0.2, 1, ramp)
    audio = audio * gain

    # keep everything except the middle of each pause, shrunk to the target gap
    keep, cursor = [], 0.0
    for p in pauses:
        target = a.beat_gap if is_beat(p) else a.gap
        if p[0] < 0.05:                      # leading silence: drop it all
            cursor = max(cursor, p[1] - 0.04)
            continue
        if p[1] - p[0] <= target:
            continue
        keep.append([cursor, p[0] + target / 2])
        cursor = p[1] - target / 2
    total = len(audio) / sr
    trailing = pauses and pauses[-1][1] >= total - 0.02
    keep.append([cursor, (pauses[-1][0] + 0.12) if trailing else total])

    fade = int(FADE * sr)
    out = []
    for s0, e0 in keep:
        chunk = audio[int(s0 * sr):int(e0 * sr)].copy()
        if len(chunk) > 2 * fade:
            chunk[:fade] *= np.linspace(0, 1, fade)
            chunk[-fade:] *= np.linspace(1, 0, fade)
        out.append(chunk)

    tight = np.concatenate(out)

    # Retakes: cut ranges given on the tightened timeline (read them off the transcript this script
    # prints), each replaced by a short pause. Cut at energy valleys, not at word times.
    for spec in sorted(a.remove, key=lambda x: -float(x.split("-")[0])):
        rng, _, g = spec.partition(":")
        r0, r1 = (float(x) for x in rng.split("-"))
        gap = float(g) if g else a.gap
        i0, i1 = int(r0 * sr), int(r1 * sr)
        left, right = tight[:i0].copy(), tight[i1:].copy()
        left[-fade:] *= np.linspace(1, 0, fade)
        right[:fade] *= np.linspace(0, 1, fade)
        tight = np.concatenate([left, np.zeros(int(gap * sr), dtype=np.float32), right])

    final = np.concatenate([tight, np.zeros(int(0.3 * sr), dtype=np.float32)])
    out_wav = os.path.join(d, "vo.wav")
    write_wav(out_wav, sr, final)
    print(f"pauses found: {len(pauses)}, threshold {thr:.1f} dB, beats matched: {len(beat_starts)}/{len(a.beat)}, retakes cut: {len(a.remove)}")

    # Caption timings come from the FINAL audio, aligned with whisper's DTW mode, which tracks word
    # onsets far better than its default timestamps (those once hid a whole retake inside one word).
    f16 = os.path.join(d, "vo-final16.wav")
    run(["ffmpeg", "-y", "-i", out_wav, "-ar", "16000", "-ac", "1", f16])
    base = os.path.join(d, "vo-final-dtw")
    run(["whisper-cli", "-m", MODEL, "-f", f16, "-l", "en", "-ml", "1", "-sow", "-nfa", "-dtw", "large.v3.turbo",
         "-ojf", "-of", base, "-t", "8"])
    words2 = []
    for seg in json.load(open(base + ".json"))["transcription"]:
        text = seg["text"].strip()
        toks = [k for k in seg.get("tokens", []) if not k["text"].startswith("[") and k.get("t_dtw", -1) >= 0]
        if not text or not toks:
            continue
        core = text.strip(".,!?")
        if core in fixes:
            text = text.replace(core, fixes[core])
        words2.append({"w": text, "s": max(0.0, toks[0]["t_dtw"] / 100 - DTW_LAG)})
    for i, w in enumerate(words2):
        nxt = words2[i + 1]["s"] if i + 1 < len(words2) else len(final) / sr
        w["e"] = round(min(nxt - 0.02, w["s"] + 0.7), 3)
        w["s"] = round(w["s"], 3)

    meta = {"slug": a.slug, "duration": round(len(final) / sr, 3), "words": words2}
    os.makedirs(os.path.join(ROOT, "scripts"), exist_ok=True)
    json.dump(meta, open(os.path.join(ROOT, "scripts", f"{a.slug}-vo.json"), "w"), indent=1)
    print(f"{a.slug}: {total:.1f}s raw -> {meta['duration']:.1f}s, {len(words2)} words")
    line, last = [], -1.0
    for w in words2:
        if w["s"] - last > 0.45 and line:
            print(f"  {line[0]['s']:6.2f}  " + " ".join(x["w"] for x in line))
            line = []
        line.append(w)
        last = w["s"]
    print(f"  {line[0]['s']:6.2f}  " + " ".join(x["w"] for x in line))


if __name__ == "__main__":
    main()
