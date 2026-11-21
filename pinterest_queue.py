#!/usr/bin/env python3
"""
Pinterest queue and A/B test for the daily run in the owner's Chrome.

The API route needs Standard access (Trial pins are visible only to their creator), so a local scheduled
task makes the pins through the Pinterest website. This file decides what to pin and which variant each
pin gets, and keeps the score, so the browser part stays dumb.

What is tested (each pin gets one arm of every dimension, picked independently):
  cover  window | dialog | bold         three image designs (make_og_cards.PIN_COVERS)
  title  full | short | punchy          whole title, the part before the first "?" or ":", or the loud
                                       version ("What the Heck Happened to Nextel?")
  desc   answer | tease                 SEO description vs a curiosity line plus keywords
  slot   morning | evening              which daily run posted it (recorded, not chosen)

Arms are chosen by Thompson sampling on engagement (pin clicks + saves + outbound clicks per impression):
an arm that keeps winning gets picked more often, but every arm keeps getting some traffic so a lucky
early streak cannot lock the test. Until an arm has MIN_PINS pins with stats, arms are rotated evenly.
Outbound clicks are what pay; they are reported next to engagement, and once the account has enough
clicks (OUTBOUND_SWITCH) the sampler switches to outbound clicks per impression.

    python3 pinterest_queue.py next 4 [--slot morning]  # JSON lines for the browser run (also writes images)
    python3 pinterest_queue.py mark SLUG PIN_ID         # the pin went live; PIN_ID from its URL
    python3 pinterest_queue.py due-stats 25             # pin ids whose numbers should be read again
    python3 pinterest_queue.py stats PIN_ID IMPRESSIONS PIN_CLICKS SAVES OUTBOUND
    python3 pinterest_queue.py report                   # per-arm results and chance of being best
    python3 pinterest_queue.py boards

State lives in .pinterest-experiments.json and variant images in .pin-variants/, neither committed.
"""

import json
import os
import random
import re
import sys
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://404memoryfound.com"
STATE = os.path.join(ROOT, ".pinterest-experiments.json")
VARIANTS = os.path.join(ROOT, ".pin-variants")
REPIN_DAYS = 45          # a post can get a fresh pin (new variant) again after this long
STATS_EVERY_DAYS = 4     # re-read a pin's numbers this often
STATS_MAX_AGE = 60       # stop re-reading after this many days
MIN_PINS = 3             # rotate arms evenly until each has this many pins with stats
OUTBOUND_SWITCH = 30     # total outbound clicks before the sampler optimises for them

DIMENSIONS = {"cover": ["window", "dialog", "bold"], "title": ["full", "short", "punchy"], "desc": ["answer", "tease"]}

VALUE_BOARD = "Vintage Collectibles Worth Money"
STORES_BOARD = "Dead Stores and Defunct Brands"
TAG_BOARDS = {
    "Gaming": "Retro Video Games and Consoles",
    "Hardware": "Old Computers and Retro Tech",
    "Internet Culture": "Early Internet and Old Websites",
    "Software & Apps": "Early Internet and Old Websites",
    "Business Blunders": STORES_BOARD,
    "Money & Tech": STORES_BOARD,
    "Then vs Now": "90s and 2000s nostalgia",
    "Music & Entertainment": "90s and 2000s nostalgia",
}
VALUE_TITLE = re.compile(r"\b(Worth|Value|Prices?)\b")
STATUS_TITLE = re.compile(r"Still (in Business|Around|Open|Made|Sold|Online|Updating)|Who Owns|Stores? Left|"
                          r"Are Left|Failed|Shut Down|What Happened", re.I)


# --------------------------------------------------------------------------- state

def load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return default


def load_state():
    return load(STATE, {"pins": [], "pending": {}})


def save_state(state):
    json.dump(state, open(STATE, "w", encoding="utf-8"), indent=1, sort_keys=True)


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")


# --------------------------------------------------------------------------- copy

def board_for(post):
    if VALUE_TITLE.search(post["title"]):
        return VALUE_BOARD
    tags = post.get("tags", [])
    if "Business Blunders" in tags and STATUS_TITLE.search(post["title"]):
        return STORES_BOARD
    for tag in tags:
        if tag in TAG_BOARDS:
            return TAG_BOARDS[tag]
    return "90s and 2000s nostalgia"


def short_title(title):
    m = re.match(r"(.+?[?:])\s", title + " ")
    if not m:
        return None
    short = m.group(1).rstrip(":").strip()
    if not short.endswith("?"):
        short = short.rstrip(".")
    return short if len(short.split()) >= 3 and short != title else None


SUBJECT_RES = [
    r"^Who Owns (?:the )?(.+?) Now\b",
    r"^(?:Is|Are) (?:the |a |an )?(.+?) Still\b",
    r"^Does (?:the )?(.+?) Still\b",
    r"^Do They Still Make (.+?)\?",
    r"^What(?:ever)? Happened to (?:the )?(.+?)(?:\?|,|$)",
    r"^Why (?:the )?(.+?) (?:Failed|Died|Flopped|Collapsed|Disappeared|Went Bankrupt|Shut Down)\b",
    r"^How Many (.+?) Are (?:Left|Still)\b",
    r"^(.+?) (?:Price|Value|Explained)\b",
]
VALUE_RES = [r"^Are (?:Old )?(.+?) Worth\b", r"^Is (?:the |a |an )?(?:Old )?(.+?) Worth\b"]


def punchy_title(title):
    """The loud version for Pinterest: "What the Heck Happened to Nextel?", or for value posts
    "Are Your Old Pogs Worth Real Money Now?". None when the subject cannot be read off the title."""
    for rx in VALUE_RES:
        m = re.match(rx, title)
        if m and len(m.group(1).split()) <= 5:
            subj = m.group(1).strip()
            verb = "Are" if title.startswith("Are") else "Is"
            return f"{verb} Your Old {subj} Worth Real Money Now?"
    for rx in SUBJECT_RES:
        m = re.match(rx, title)
        if m:
            subj = re.sub(r" Stores$", "", m.group(1).strip().rstrip(",.:"))
            the = "the " if re.match(r"^(Is|Are|Who Owns|Why|Does|What Happened to) the ", title) else ""
            if 1 <= len(subj.split()) <= 5 and not re.search(r"\b(Still|Now|Worth)\b", subj):
                return f"What the Heck Happened to {the}{subj}?"
    return None


def tease(post):
    t = post["title"]
    if VALUE_TITLE.search(t):
        line = "What it cost new, what it sells for now and which versions collectors actually pay for."
    elif STATUS_TITLE.search(t):
        line = ("The real story behind it and what is left of it today." if "own" in t.lower()
                else "The real story, who owns it now and what is left of it today.")
    else:
        line = "The story most people never heard, with the numbers and where it stands today."
    keywords = [k for k in (post.get("seo") or {}).get("keywords", []) if len(k) < 45][:4]
    lead = short_title(t) or t
    text = f"{lead} {line}"
    if keywords:
        text += " Related: " + ", ".join(keywords) + "."
    return text


def copy_for(post, arms):
    full = re.sub(r"\s*\|\s*404 Memory Found$", "", post["title"])
    title = {"short": short_title(full), "punchy": punchy_title(full)}.get(arms["title"]) or full
    if arms["desc"] == "tease":
        desc = tease(post)
    else:
        desc = ((post.get("seo") or {}).get("description") or post.get("excerpt") or "").rstrip()
        desc += " The full story, with sources, is on 404 Memory Found."
    for s in (title, desc):
        assert "—" not in s and "–" not in s, f"dash in pin text for {post['id']}"
    return title[:100], desc[:480]


def tagged_url(slug, arms):
    content = f"{arms['cover']}-{arms['title']}-{arms['desc']}"
    return (f"{BASE}/posts/{slug}.html?utm_source=pinterest&utm_medium=social"
            f"&utm_campaign=pin_ab&utm_content={content}")


# --------------------------------------------------------------------------- the bandit

def rate(p, outbound):
    s = p.get("stats") or {}
    imp = s.get("impressions", 0)
    hits = s.get("outbound", 0) if outbound else s.get("pin_clicks", 0) + s.get("saves", 0) + s.get("outbound", 0)
    return imp, min(hits, imp)


def arm_totals(state, dim, outbound):
    totals = {a: {"pins": 0, "imp": 0, "hits": 0} for a in DIMENSIONS.get(dim, [])}
    for p in state["pins"]:
        a = p["arms"].get(dim)
        if a not in totals or not p.get("stats"):
            continue
        imp, hits = rate(p, outbound)
        totals[a]["pins"] += 1
        totals[a]["imp"] += imp
        totals[a]["hits"] += hits
    return totals


def use_outbound(state):
    return sum((p.get("stats") or {}).get("outbound", 0) for p in state["pins"]) >= OUTBOUND_SWITCH


def pick_arm(state, dim, allowed, already):
    outbound = use_outbound(state)
    totals = arm_totals(state, dim, outbound)
    # even rotation first: arms with too few measured pins, counting the ones already picked this run
    counts = {a: totals[a]["pins"] + already.get(a, 0) for a in allowed}
    young = [a for a in allowed if counts[a] < MIN_PINS]
    if young:
        low = min(counts[a] for a in young)
        return random.choice([a for a in young if counts[a] == low])
    draws = {a: random.betavariate(1 + totals[a]["hits"], 1 + totals[a]["imp"] - totals[a]["hits"]) for a in allowed}
    return max(draws, key=draws.get)


def prob_best(totals, n=4000):
    arms = [a for a in totals if totals[a]["pins"]]
    if len(arms) < 2:
        return {a: None for a in totals}
    wins = {a: 0 for a in arms}
    for _ in range(n):
        d = {a: random.betavariate(1 + totals[a]["hits"], 1 + totals[a]["imp"] - totals[a]["hits"]) for a in arms}
        wins[max(d, key=d.get)] += 1
    return {a: (wins[a] / n if a in wins else None) for a in totals}


def flatness(path):
    """Share of near-white pixels and contrast of a photo. Screenshots of mostly empty pages (the Ask.com
    home page) make covers that say nothing, so they lose to any real photo in the post."""
    from PIL import Image, ImageStat
    try:
        im = Image.open(path).convert("L").resize((96, 96))
    except Exception:
        return 1.0, 0.0
    px = list(im.getdata())
    return sum(1 for v in px if v > 232) / len(px), ImageStat.Stat(im).stddev[0]


def pin_photo(post, manifest, cards):
    """The photo a cover should use: the hero unless it is a flat, mostly white image, then the busiest
    real photo from the post's body. None means the post has nothing worth pinning yet."""
    def local(url):
        info = manifest.get(url, {})
        path = info.get("file", "").lstrip("/")
        return os.path.join(ROOT, path) if info.get("status") == "ok" and os.path.exists(os.path.join(ROOT, path)) else None
    hero = cards.hero_path(post, manifest)
    hero = os.path.join(ROOT, hero) if hero else None
    options = ([hero] if hero else []) + [local(u) for u in re.findall(r'<img[^>]+src="([^"]+)"', post.get("body", ""))]
    best, best_std = None, -1
    for path in [o for o in options if o]:
        white, std = flatness(path)
        if white < 0.5 and std > 38:
            return path
        if white < 0.7 and std > best_std:
            best, best_std = path, std
    return best if best_std > 30 else None


# --------------------------------------------------------------------------- picking posts

def candidates(state):
    posts = load(os.path.join(ROOT, "posts.json"), {}).get("posts", [])
    manifest = load(os.path.join(ROOT, "images-manifest.json"), {})
    seen = {row[0] for row in load(os.path.join(ROOT, "seo", "search-console.json"), {}).get("pages", [])}
    cutoff = str(date.today() - timedelta(days=REPIN_DAYS))
    last = {}
    for p in state["pins"]:
        last[p["slug"]] = max(last.get(p["slug"], ""), p["posted"][:10])
    out = []
    for p in posts:
        if not (p.get("image") and manifest.get(p["image"], {}).get("status") == "ok"):
            continue  # a pin with the "404" placeholder card gets no clicks
        if last.get(p["id"], "0") > cutoff or p["id"] in state["pending"]:
            continue
        score = (3 if p["id"] in seen else 0) + (2 if p.get("upgraded") else 0) \
            + (1 if VALUE_TITLE.search(p["title"]) or STATUS_TITLE.search(p["title"]) else 0)
        out.append((-score, random.random(), p))
    out.sort(key=lambda t: (t[0], t[1]))
    return [p for _, _, p in out]


def cmd_next(n, slot):
    import make_og_cards as cards
    state = load_state()
    manifest = load(os.path.join(ROOT, "images-manifest.json"), {})
    os.makedirs(VARIANTS, exist_ok=True)
    # pins picked by an earlier run that never went live come first, with the same variant
    for slug, pend in list(state["pending"].items()):
        if n <= 0:
            break
        if os.path.exists(pend.get("image", "")):
            print(json.dumps({"slug": slug, "url": pend["url"], "title": pend["title"], "description": pend["desc"],
                              "board": pend["board"], "image": pend["image"], "arms": pend["arms"]},
                             ensure_ascii=False))
            n -= 1
        else:
            del state["pending"][slug]
    picks, boards = [], set()
    pool = candidates(state)
    for p in pool:                       # spread a run over boards first
        if len(picks) < n and board_for(p) not in boards:
            picks.append(p)
            boards.add(board_for(p))
    for p in pool:
        if len(picks) < n and p not in picks:
            picks.append(p)
    photos = {}
    ok = []
    for post in picks + [p for p in pool if p not in picks]:
        if len(ok) == len(picks):
            break
        photo = pin_photo(post, manifest, cards)
        if photo:
            photos[post["id"]] = photo
            ok.append(post)
    picks = ok
    already = {dim: {} for dim in DIMENSIONS}
    for post in picks:
        arms = {}
        for dim, options in DIMENSIONS.items():
            allowed = options
            if dim == "title":
                allowed = ["full"] + (["short"] if short_title(post["title"]) else []) \
                    + (["punchy"] if punchy_title(post["title"]) else [])
            arms[dim] = pick_arm(state, dim, allowed, already[dim])
            already[dim][arms[dim]] = already[dim].get(arms[dim], 0) + 1
        arms["slot"] = slot
        title, desc = copy_for(post, arms)
        image = os.path.join(VARIANTS, f"{post['id']}-{arms['cover']}-{arms['title']}.jpg")
        cards.PIN_COVERS[arms["cover"]](post, photos[post["id"]], image, title=title)
        state["pending"][post["id"]] = {"arms": arms, "board": board_for(post), "title": title, "desc": desc,
                                       "picked": now(), "image": image, "url": tagged_url(post["id"], arms)}
        print(json.dumps({"slug": post["id"], "url": tagged_url(post["id"], arms), "title": title,
                          "description": desc, "board": board_for(post), "image": image, "arms": arms},
                         ensure_ascii=False))
    save_state(state)


def cmd_mark(slug, pin_id):
    state = load_state()
    pending = state["pending"].pop(slug, None)
    if not pending:
        sys.exit(f"{slug} is not pending: run next first")
    pending.pop("image", None)
    state["pins"].append({"slug": slug, "pin_id": str(pin_id), "posted": now(), **pending, "stats": None})
    save_state(state)
    print(f"pinned: {slug} -> {pin_id} {pending['arms']}")


def cmd_due_stats(n):
    state = load_state()
    today = datetime.now(timezone.utc)
    due = []
    for p in state["pins"]:
        posted = datetime.strptime(p["posted"], "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
        age = (today - posted).days
        if age < 2 or age > STATS_MAX_AGE:
            continue
        upd = (p.get("stats") or {}).get("updated")
        if upd and (today - datetime.strptime(upd, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)).days < STATS_EVERY_DAYS:
            continue
        due.append((upd or "", p["pin_id"]))
    for _, pid in sorted(due)[:n]:
        print(pid)


def cmd_stats(pin_id, imp, clicks, saves, outbound):
    state = load_state()
    for p in state["pins"]:
        if p["pin_id"] == str(pin_id):
            p["stats"] = {"impressions": int(imp), "pin_clicks": int(clicks), "saves": int(saves),
                          "outbound": int(outbound), "updated": now()}
            save_state(state)
            print(f"stats: {pin_id} {p['stats']}")
            return
    sys.exit(f"unknown pin {pin_id}")


def cmd_report():
    state = load_state()
    pins = state["pins"]
    measured = [p for p in pins if p.get("stats")]
    tot = {k: sum((p.get("stats") or {}).get(k, 0) for p in pins) for k in ("impressions", "pin_clicks", "saves", "outbound")}
    print(f"{len(pins)} test pins ({len(measured)} with numbers), {len(state['pending'])} pending. "
          f"Totals: {tot['impressions']} impressions, {tot['pin_clicks']} pin clicks, {tot['saves']} saves, "
          f"{tot['outbound']} clicks to the site.")
    goal = "outbound clicks" if use_outbound(state) else "engagement (pin clicks + saves + outbound)"
    print(f"Sampler optimises for: {goal}.")
    for dim in list(DIMENSIONS) + ["slot"]:
        arms = DIMENSIONS.get(dim, ["morning", "evening"])
        eng = {a: {"pins": 0, "imp": 0, "hits": 0} for a in arms}
        out = {a: {"pins": 0, "imp": 0, "hits": 0} for a in arms}
        for p in measured:
            a = p["arms"].get(dim)
            if a not in eng:
                continue
            for table, ob in ((eng, False), (out, True)):
                imp, hits = rate(p, ob)
                table[a]["pins"] += 1
                table[a]["imp"] += imp
                table[a]["hits"] += hits
        best = prob_best(out if use_outbound(state) else eng)
        print(f"\n{dim}:")
        for a in arms:
            e, o = eng[a], out[a]
            er = f"{100 * e['hits'] / e['imp']:.2f}%" if e["imp"] else "-"
            orr = f"{100 * o['hits'] / o['imp']:.2f}%" if o["imp"] else "-"
            pb = f"{100 * best[a]:.0f}%" if best.get(a) is not None else "-"
            print(f"  {a:8} pins {e['pins']:3}  impressions {e['imp']:6}  engagement {er:>7}  "
                  f"site clicks {o['hits']:4} ({orr:>6})  chance best {pb:>4}")
    if measured:
        top = sorted(measured, key=lambda p: (-(p["stats"]["outbound"]), -rate(p, False)[1]))[:5]
        print("\nTop pins:")
        for p in top:
            s = p["stats"]
            print(f"  {p['slug']} [{p['arms']['cover']}/{p['arms']['title']}/{p['arms']['desc']}] "
                  f"{s['impressions']} imp, {s['outbound']} site clicks")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["next"]:
        slot = args[args.index("--slot") + 1] if "--slot" in args else ("morning" if datetime.now().hour < 15 else "evening")
        nums = [a for a in args[1:] if a.isdigit()]
        cmd_next(int(nums[0]) if nums else 4, slot)
    elif args[:1] == ["mark"] and len(args) == 3:
        cmd_mark(args[1], args[2])
    elif args[:1] == ["due-stats"]:
        cmd_due_stats(int(args[1]) if len(args) > 1 else 25)
    elif args[:1] == ["stats"] and len(args) == 6:
        cmd_stats(*args[1:])
    elif args[:1] == ["report"]:
        cmd_report()
    elif args[:1] == ["boards"]:
        print("\n".join(sorted(set(TAG_BOARDS.values()) | {VALUE_BOARD, STORES_BOARD})))
    else:
        sys.exit(__doc__)
