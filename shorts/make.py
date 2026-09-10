#!/usr/bin/env python3
"""Build one short end to end from an authored script in scripts/<slug>.json.

  python3 make.py is-kmart-still-open-stores-left          # voice (cached per slug) + render master + phone copy
  python3 make.py <slug> --revoice                          # force a new ElevenLabs take
  python3 make.py <slug> --stills                           # only render one check frame per scene

The authored script holds the six scene texts and the visual data (found, chart, props, timeline) plus
"images": {"hero": "<path or URL>", "hero2": "<path or URL>"}; paths are relative to the repo root (e.g. img/x.jpg).
Voice files and word timings are cached in public/<slug>/ so re-renders cost no credits.
"""
import json
import os
import shutil
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PUBLIC = os.path.join(HERE, "public")
UA = "404MemoryFound-build/1.0 (hello@404memoryfound.com)"


def fetch_image(src, dest):
    if src.startswith("http"):
        req = urllib.request.Request(src, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            open(dest, "wb").write(r.read())
    else:
        shutil.copy(os.path.join(REPO, src.lstrip("/")), dest)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: make.py <slug> [--revoice] [--stills]")
    slug = sys.argv[1]
    src_path = os.path.join(HERE, "scripts", f"{slug}.json")
    script = json.load(open(src_path, encoding="utf-8"))
    cache = os.path.join(PUBLIC, slug)
    os.makedirs(cache, exist_ok=True)

    # images -> public/<slug>/heroN.jpg, referenced from the script as "<slug>/heroN.jpg"
    for key in ("hero", "hero2"):
        src = (script.get("images") or {}).get(key)
        if src:
            dest = os.path.join(cache, f"{key}.jpg")
            if not os.path.exists(dest):
                fetch_image(src, dest)
            script[key] = f"{slug}/{key}.jpg"
    shutil.copy(os.path.join(REPO, "logo-512.png"), os.path.join(PUBLIC, "logo.png"))
    if not os.path.exists(os.path.join(PUBLIC, "music.wav")):
        subprocess.run([sys.executable, os.path.join(HERE, "gen_music.py"), "48"], check=True)

    if "--cover" in sys.argv:
        for sc in script["scenes"]:
            sc.setdefault("frames", 30); sc.setdefault("audio", ""); sc.setdefault("words", [])
        json.dump(script, open(os.path.join(HERE, "script.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
        subprocess.run(["npx", "remotion", "still", "src/index.ts", "Cover", f"out/{slug}-cover.png", "--frame=0"], cwd=HERE, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"out/{slug}-cover.png")
        return

    # voice: cached per slug unless --revoice or the text changed
    need_voice = "--revoice" in sys.argv or any(not sc.get("words") or not sc.get("audio") for sc in script["scenes"])
    if need_voice:
        active = os.path.join(HERE, "script.json")
        json.dump(script, open(active, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        subprocess.run([sys.executable, os.path.join(HERE, "tts.py")], check=True, cwd=HERE)
        script = json.load(open(active, encoding="utf-8"))
        for sc in script["scenes"]:  # move the audio into the slug cache
            name = os.path.basename(sc["audio"])
            shutil.move(os.path.join(PUBLIC, name), os.path.join(cache, name))
            sc["audio"] = f"{slug}/{name}"
        json.dump(script, open(src_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    # activate and render
    json.dump(script, open(os.path.join(HERE, "script.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    if "--stills" in sys.argv:
        f = 0
        for i, sc in enumerate(script["scenes"], 1):
            subprocess.run(["npx", "remotion", "still", "src/index.ts", "Short", f"out/{slug}-s{i}.png", f"--frame={f + 24}"], cwd=HERE, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            f += sc["frames"]
        print("stills in out/")
        return
    master = os.path.join(HERE, "out", f"{slug}.mp4")
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "Short", master, "--codec=h264", "--image-format=jpeg",
                    "--jpeg-quality=90", "--concurrency=2"], cwd=HERE, check=True, stdout=subprocess.DEVNULL)
    small = master.replace(".mp4", "-small.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", master, "-c:v", "libx264", "-crf", "26", "-preset", "medium",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", small], check=True)
    total = sum(sc["frames"] for sc in script["scenes"]) / script["fps"]
    print(f"{master} ({os.path.getsize(master) / 1e6:.1f} MB, {total:.1f}s) and {os.path.basename(small)}")


if __name__ == "__main__":
    main()
