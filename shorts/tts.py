#!/usr/bin/env python3
"""Voice-over for the shorts, with per-word timings for the captions.

Reads script.json, writes one audio file per scene into public/ and fills in
scenes[].words = [{"w": "Blockbuster", "s": 0.32, "e": 0.71}, ...] and scenes[].frames.

Voice provider:
  - ElevenLabs when a key is available, looked up in this order: ELEVENLABS_API_KEY in the environment,
    the macOS Keychain (account "404mf", service "elevenlabs"), then shorts/.env (one KEY=value per line).
    Uses the with-timestamps endpoint, so word timings are exact.
    Optional: ELEVENLABS_VOICE_ID (default "nPczCjzI2devNBz1zQrb", the premade voice "Brian"),
              ELEVENLABS_MODEL (default "eleven_multilingual_v2").
  - macOS `say` otherwise (voice Samantha). Word timings are then estimated in proportion to word length,
    which is close enough for captions but not exact.

Usage:  python3 tts.py            (regenerates every scene)
        python3 tts.py --keep     (skips scenes whose audio file already exists)
"""
import base64
import json
import os
import re
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(HERE, "public")
SCRIPT = os.path.join(HERE, "script.json")
PAD_SECONDS = 0.06   # gap after each sentence; the audio is also trimmed of leading/trailing silence


def load_keychain():
    """macOS Keychain entry created by:  security add-generic-password -a 404mf -s elevenlabs -w <key> -U
    The key is encrypted by the OS and tied to the login user; nothing is stored in a file or the repo."""
    if os.environ.get("ELEVENLABS_API_KEY"):
        return
    try:
        out = subprocess.run(["security", "find-generic-password", "-a", "404mf", "-s", "elevenlabs", "-w"],
                             capture_output=True, text=True, timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            os.environ["ELEVENLABS_API_KEY"] = out.stdout.strip()
    except Exception:  # noqa: BLE001
        pass


def load_env():
    load_keychain()
    path = os.path.join(HERE, ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))



# ---------------------------------------------------------------- numbers spoken as words
ONES = ["zero","one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve","thirteen","fourteen",
        "fifteen","sixteen","seventeen","eighteen","nineteen"]
TENS = ["","","twenty","thirty","forty","fifty","sixty","seventy","eighty","ninety"]
ORD = {1:"first",2:"second",3:"third",4:"fourth",5:"fifth",6:"sixth",7:"seventh",8:"eighth",9:"ninth",10:"tenth",11:"eleventh",
       12:"twelfth",13:"thirteenth",14:"fourteenth",15:"fifteenth",16:"sixteenth",17:"seventeenth",18:"eighteenth",19:"nineteenth",
       20:"twentieth",21:"twenty-first",22:"twenty-second",23:"twenty-third",24:"twenty-fourth",25:"twenty-fifth",26:"twenty-sixth",
       27:"twenty-seventh",28:"twenty-eighth",29:"twenty-ninth",30:"thirtieth",31:"thirty-first"}
MONTHS = {"january","february","march","april","may","june","july","august","september","october","november","december"}


def int_words(n):
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("-" + ONES[n % 10] if n % 10 else "")
    if n < 1000:
        return ONES[n // 100] + " hundred" + (" " + int_words(n % 100) if n % 100 else "")
    for div, name in ((10**9, "billion"), (10**6, "million"), (1000, "thousand")):
        if n >= div:
            rest = n % div
            return int_words(n // div) + " " + name + (" " + int_words(rest) if rest else "")
    return str(n)


def year_words(n):
    if 2000 <= n <= 2009:
        return "two thousand" + (" " + ONES[n - 2000] if n > 2000 else "")
    if 1100 <= n <= 1999 or 2010 <= n <= 2099:
        hi, lo = divmod(n, 100)
        return int_words(hi) + (" " + int_words(lo) if lo >= 10 else (" oh " + ONES[lo] if lo else " hundred"))
    return int_words(n)


def number_words(tok, prev, nxt):
    """One display token -> spoken words. Handles $, commas, decimals, years, ordinals after a month name."""
    core = tok.strip(".,;:!?()")
    trail = tok[len(tok.rstrip(".,;:!?()")):]
    dollars = core.startswith("$")
    num = core.lstrip("$").replace(",", "")
    if not re.fullmatch(r"\d+(\.\d+)?", num):
        return None
    if "." in num:
        a, b = num.split(".")
        words = int_words(int(a)) + " point " + " ".join(ONES[int(d)] for d in b)
    else:
        n = int(a := num)
        if not dollars and 1100 <= n <= 2099 and "," not in core and len(num) == 4:
            words = year_words(n)
        elif not dollars and prev and prev.lower().strip(".,") in MONTHS and 1 <= n <= 31:
            words = ORD[n]
        else:
            words = int_words(n)
    if dollars:
        scale = nxt.lower().strip(".,;:") if nxt else ""
        if scale in ("million", "billion", "thousand"):
            return words  # "million dollars" is appended when the scale word is processed
        words += " dollars"
    return words + trail


def spoken_tokens(text):
    """[(display_token, spoken_string)] so caption words can be timed from the spoken words."""
    toks = words_of(text)
    out = []
    for i, tok in enumerate(toks):
        prev = toks[i - 1] if i else ""
        nxt = toks[i + 1] if i + 1 < len(toks) else ""
        sp = number_words(tok, prev, nxt)
        if sp is None:
            low = tok.lower().strip(".,;:!?")
            if low in ("million", "billion", "thousand") and prev.startswith("$"):
                sp = tok + " dollars" if not tok.endswith((".", ",")) else tok[:-1] + " dollars" + tok[-1]
            elif "404memoryfound.com" in low:
                sp = "four oh four memory found dot com" + tok[len(tok.rstrip(".,")):]
            else:
                sp = tok
        out.append((tok, sp))
    return out


def regroup(pairs, spoken_words):
    """spoken_words: [{"w","s","e"}] aligned to the spoken string; returns timings per display token."""
    out, k = [], 0
    for disp, sp in pairs:
        n = len(sp.split())
        chunk = spoken_words[k:k + n]
        k += n
        if not chunk:
            continue
        out.append({"w": disp, "s": chunk[0]["s"], "e": chunk[-1]["e"]})
    return out


def audio_seconds(path):
    out = subprocess.run(["afinfo", path], capture_output=True, text=True).stdout
    for l in out.splitlines():
        if "estimated duration" in l:
            return float(l.split(":")[1].split("sec")[0])
    raise RuntimeError(f"no duration for {path}")


def words_of(text):
    return [w for w in re.split(r"\s+", text.strip()) if w]


def elevenlabs(text, out_mp3):
    key = os.environ["ELEVENLABS_API_KEY"]
    voice = os.environ.get("ELEVENLABS_VOICE_ID", "nPczCjzI2devNBz1zQrb")
    model = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128"
    body = json.dumps({
        "text": text,
        "model_id": model,
        "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": True},
    }).encode()
    req = urllib.request.Request(url, data=body, headers={"xi-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.load(r)
    open(out_mp3, "wb").write(base64.b64decode(data["audio_base64"]))
    al = data["alignment"]
    chars, starts, ends = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    words, cur, s0 = [], "", None
    for c, s, e in zip(chars, starts, ends):
        if c.isspace():
            if cur:
                words.append({"w": cur, "s": round(s0, 3), "e": round(last_e, 3)})
                cur, s0 = "", None
            continue
        if s0 is None:
            s0 = s
        cur += c
        last_e = e
    if cur:
        words.append({"w": cur, "s": round(s0, 3), "e": round(last_e, 3)})
    return words


def mac_say(text, out_wav):
    aiff = out_wav.replace(".wav", ".aiff")
    subprocess.run(["say", "-v", os.environ.get("SAY_VOICE", "Samantha"), "-r", "172", "-o", aiff, text], check=True)
    subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@44100", aiff, out_wav], check=True)
    os.remove(aiff)
    total = audio_seconds(out_wav)
    ws = words_of(text)
    weights = [len(re.sub(r"[^A-Za-z0-9]", "", w)) + 1.5 + (1.2 if w[-1] in ".,?!" else 0) for w in ws]
    scale = (total - 0.12) / sum(weights)
    t, words = 0.06, []
    for w, wt in zip(ws, weights):
        words.append({"w": w, "s": round(t, 3), "e": round(t + wt * scale, 3)})
        t += wt * scale
    return words


def trim_silence(path, words):
    """Cut leading and trailing silence (below -38 dB) so sentences follow each other tightly,
    and shift the word timings by the amount removed at the start."""
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "silencedetect=noise=-38dB:d=0.08", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
    ends = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", probe)]
    starts = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", probe)]
    total = audio_seconds(path)
    lead = ends[0] if starts and starts[0] < 0.05 and ends else 0.0
    tail = starts[-1] if starts and (not ends or starts[-1] > (ends[-1] if ends else 0)) and total - starts[-1] > 0.1 else total
    lead = max(0.0, lead - 0.04)
    tail = min(total, tail + 0.06)
    if lead < 0.03 and tail > total - 0.03:
        return words
    tmp = path + ".trim" + os.path.splitext(path)[1]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-ss", f"{lead:.3f}", "-to", f"{tail:.3f}", "-c:a", "libmp3lame" if path.endswith(".mp3") else "pcm_s16le", tmp], check=True)
    os.replace(tmp, path)
    return [{"w": w["w"], "s": round(max(0.0, w["s"] - lead), 3), "e": round(max(0.0, w["e"] - lead), 3)} for w in words]


def main():
    load_env()
    keep = "--keep" in sys.argv
    use_eleven = bool(os.environ.get("ELEVENLABS_API_KEY"))
    print("voice provider:", "ElevenLabs" if use_eleven else "macOS say (set ELEVENLABS_API_KEY for a real voice)")
    script = json.load(open(SCRIPT, encoding="utf-8"))
    fps = script["fps"]
    os.makedirs(PUBLIC, exist_ok=True)
    for i, sc in enumerate(script["scenes"], 1):
        text = sc.get("text") or sc["say"]
        ext = "mp3" if use_eleven else "wav"
        out = os.path.join(PUBLIC, f"seg{i}.{ext}")
        cached = sc.get("audio") and os.path.exists(os.path.join(PUBLIC, sc["audio"]))
        if keep and cached and sc.get("words"):
            print(f"scene {i}: cached")
            continue
        for old in (f"seg{i}.mp3", f"seg{i}.wav"):
            p = os.path.join(PUBLIC, old)
            if os.path.exists(p):
                os.remove(p)
        pairs = spoken_tokens(text)
        spoken = " ".join(sp for _, sp in pairs)
        raw = elevenlabs(spoken, out) if use_eleven else mac_say(spoken, out)
        sc["spoken"] = spoken
        sc["words"] = regroup(pairs, raw)
        if "--no-trim" not in sys.argv:
            sc["words"] = trim_silence(out, sc["words"])
        dur = audio_seconds(out)
        sc["audio"] = os.path.basename(out)
        sc["seconds"] = round(dur, 2)
        sc["frames"] = int((dur + PAD_SECONDS) * fps)
        print(f"scene {i}: {dur:.2f}s, {len(sc['words'])} words -> {sc['audio']}")
    script["voice"] = "elevenlabs" if use_eleven else "say"
    json.dump(script, open(SCRIPT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    total = sum(s["frames"] for s in script["scenes"]) / fps
    print(f"total {total:.1f}s")


if __name__ == "__main__":
    main()
