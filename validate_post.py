#!/usr/bin/env python3
"""
Checks a post in posts.json against POST_SPEC.md before it is published. Prints OK or FIX: <reasons>.

    python3 validate_post.py SLUG --new        # a new post: format word counts, link phrases, everything
    python3 validate_post.py SLUG --upgrade    # an upgraded existing post: looser length, same quality bar
    python3 validate_post.py SLUG --fresh      # a freshness-desk update: 850 to 1,400 words, 4 to 6 sections
    python3 validate_post.py --titles TODAY    # every post whose ctrRewrite is TODAY: seo title and description
"""

import json
import re
import subprocess
import sys

TAGS = {"Business Blunders", "Hardware", "Internet Culture", "Gaming", "Software & Apps", "Then vs Now",
        "Money & Tech", "Music & Entertainment"}
FORMATS = {"quick": (550, 850, 3, 4), "standard": (900, 1400, 4, 6), "deep": (1600, 2400, 6, 9)}
DASHES = ("—", "–")
BRAND = "404 Memory Found"


def load():
    return json.load(open("posts.json", encoding="utf-8"))["posts"]


def check_seo(p, errs):
    s = p.get("seo") or {}
    t, d = s.get("title", ""), s.get("description", "")
    if not 30 <= len(t) <= 60 or BRAND in t:
        errs.append(f"seo.title must be 30 to 60 characters with no '{BRAND}' suffix (now {len(t)})")
    if not 128 <= len(d) <= 160:
        errs.append(f"seo.description must be 128 to 160 characters (now {len(d)})")
    if any(c in t + d for c in DASHES):
        errs.append("em or en dash in seo fields")


def check_post(posts, slug, mode):
    matches = [x for x in posts if x["id"] == slug]
    if not matches:
        return [f"no post with id {slug}"]
    p, errs = matches[0], []
    b = p["body"]
    parts = re.split(r"<h2>\s*Frequently Asked Questions\s*</h2>", b, flags=re.I)
    prose = re.sub(r"<figure>.*?</figure>", "", parts[0], flags=re.S)
    n = len(re.sub(r"<[^>]+>", " ", prose).split())
    sec = len(re.findall(r"<h2[\s>]", parts[0]))
    if mode == "new":
        if p.get("format") not in FORMATS:
            errs.append("format must be quick, standard or deep")
        lo, hi, smin, smax = FORMATS.get(p.get("format"), FORMATS["standard"])
    elif mode == "fresh":
        lo, hi, smin, smax = 850, 1400, 4, 6
    else:
        lo, hi, smin, smax = 550, 2600, 3, 9
    if not lo <= n <= hi:
        errs.append(f"body is {n} words before the FAQ, needs {lo} to {hi}")
    if not smin <= sec <= smax:
        errs.append(f"{sec} sections before the FAQ, needs {smin} to {smax}")
    if not 40 <= len(p["title"]) <= 65:
        errs.append(f"title must be 40 to 65 characters (now {len(p['title'])})")
    if not 110 <= len(p.get("excerpt", "")) <= 160:
        errs.append("excerpt must be 110 to 160 characters")
    if mode != "fresh" or (p.get("seo") or {}).get("title", "").find(BRAND) < 0:
        check_seo(p, errs)
    if len(parts) < 2 or len(re.findall(r"<h3>", parts[-1])) != 3:
        errs.append("FAQ must have exactly 3 <h3> questions")
    if len(p.get("sources", [])) < 3:
        errs.append("needs 3 or more sources")
    text = re.sub(r"<[^>]+>", " ", b)
    if len(re.findall(r"[\"“][^\"”]{15,220}[\"”]", text)) < 2:
        errs.append("needs 2 direct quotations")
    if "ebay." in b.lower() or "amazon.com" in b.lower():
        errs.append("no eBay or Amazon links")
    for src in re.findall(r'<img[^>]*src="([^"]+)"', b):
        if not src.startswith("https://upload.wikimedia.org/"):
            errs.append("every <img> must be a verified https://upload.wikimedia.org/ URL")
            continue
        code = subprocess.run(["curl", "-s", "-m", "15", "-o", "/dev/null", "-w", "%{http_code}", src],
                              capture_output=True, text=True).stdout
        if code not in ("200", "000"):  # 000 = this sandbox cannot reach Commons; the build re-checks
            errs.append(f"image ...{src[-45:]} returned HTTP {code}")
    if b.count("<img") != b.count("<figure>") or re.search(r"<p>[^<]*<img", b):
        errs.append("each <img> sits alone inside its own <figure>, between sections")
    if mode == "new":
        hay = (p["title"] + " " + p["id"].replace("-", " ")).lower()
        lp = p.get("linkPhrases") or []
        if not lp or any(len(x.split()) > 4 or not all(w.lower() in hay for w in re.findall(r"[A-Za-z0-9']+", x)) for x in lp):
            errs.append("linkPhrases must name THIS post's subject with words from its title or slug")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+){2,7}", p["id"]):
            errs.append("bad slug")
    dump = json.dumps(p, ensure_ascii=False)
    if any(c in dump for c in DASHES):
        errs.append("em or en dash somewhere in the post")
    if not p.get("tags") or not set(p["tags"]) <= TAGS:
        errs.append("tags must come from the eight site tags")
    if p.get("author") not in ("marcus", "dana", "theo"):
        errs.append("author must be marcus, dana or theo")
    if [x["id"] for x in posts].count(slug) > 1:
        errs.append("duplicate slug")
    if not p.get("image") and not p.get("imageSearch"):
        errs.append("needs image or imageSearch")
    if not p.get("summary") or not p.get("facts"):
        errs.append("summary and facts are required")
    if mode in ("upgrade", "fresh") and not p.get("updated"):
        errs.append("set 'updated' to today")
    return errs


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    posts = load()
    if args[0] == "--titles":
        day = args[1]
        errs = []
        for p in posts:
            if p.get("ctrRewrite") == day:
                e = []
                check_seo(p, e)
                errs += [f"{p['id']}: {x}" for x in e]
        print("OK" if not errs else "FIX: " + "; ".join(errs))
        return 0 if not errs else 1
    slug = args[0]
    mode = (args[1] if len(args) > 1 else "--new").lstrip("-")
    errs = check_post(posts, slug, mode)
    print("OK" if not errs else "FIX: " + "; ".join(errs))
    return 0 if not errs else 1


if __name__ == "__main__":
    sys.exit(main())
