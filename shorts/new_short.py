#!/usr/bin/env python3
"""Scaffold script.json for a short from a post in ../posts.json.

  python3 new_short.py is-blockbuster-still-open-last-store

Copies the post's local hero image to public/hero.jpg, and writes a draft script.json with the post's
title, six placeholder scenes (hook, found, chart, props, timeline, outro), the post's facts as
"props" rows, and the sources for reference. The six "text" lines still have to be written by hand
from the post (they are what gets spoken and captioned), then run tts.py and render.
"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: new_short.py <post-slug>")
    slug = sys.argv[1]
    posts = json.load(open(os.path.join(REPO, "posts.json"), encoding="utf-8"))["posts"]
    post = next((p for p in posts if p["id"] == slug), None)
    if not post:
        sys.exit(f"no post with id {slug}")
    manifest = json.load(open(os.path.join(REPO, "images-manifest.json"), encoding="utf-8"))
    hero = manifest.get(post.get("image") or "", {}).get("file")
    os.makedirs(os.path.join(HERE, "public"), exist_ok=True)
    if hero and os.path.exists(os.path.join(REPO, hero.lstrip("/"))):
        shutil.copy(os.path.join(REPO, hero.lstrip("/")), os.path.join(HERE, "public", "hero.jpg"))
        print("hero ->", hero)
    else:
        print("no local hero image; put one at public/hero.jpg")
    shutil.copy(os.path.join(REPO, "logo-512.png"), os.path.join(HERE, "public", "logo.png"))

    summary = post.get("summary") or re.sub(r"<[^>]+>", " ", post["body"])[:300]
    facts = post.get("facts") or []
    kinds = ["hook", "found", "chart", "props", "timeline", "outro"]
    scenes = []
    for k in kinds:
        text = {
            "hook": post["title"].split(":")[0].rstrip("?") + "?",
            "outro": "Full story at 404memoryfound.com. Follow for more of the internet you grew up with.",
        }.get(k, "WRITE ME from the post: " + summary[:120])
        scenes.append({"kind": k, "text": text, "lines": [], "audio": "", "frames": 90})
    script = {
        "fps": 30, "width": 1080, "height": 1920, "hero": "hero.jpg", "hero2": "hero2.jpg",
        "title": post["title"], "slug": slug, "scenes": scenes,
        "chart": [{"label": "Peak", "value": 0, "text": "0"}, {"label": "Now", "value": 0, "text": "0"}],
        "props": [[f["label"], f["value"]] for f in facts[:4]] or [["Owner", ""], ["Bought", ""], ["Price", ""], ["Status", ""]],
        "timeline": [["YYYY", "event"]] * 4,
        "_sources": [s["url"] for s in post.get("sources") or []],
        "_summary": summary,
    }
    json.dump(script, open(os.path.join(HERE, "script.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("script.json drafted for", post["title"])
    print("next: write the six text lines, fill chart/props/timeline, then: python3 tts.py && npm run render")


if __name__ == "__main__":
    main()
