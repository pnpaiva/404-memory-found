#!/usr/bin/env python3
"""
Queue for the daily Search Console "Request indexing" run.

Google allows roughly ten manual indexing requests a day and has no public API for them, so a
scheduled task drives the Search Console page in Chrome. This file decides what that task asks for,
so the browser part stays dumb: it asks for the next URLs, tries them, and reports what happened.

    python3 indexing_queue.py next 12            # URLs to try today, best first
    python3 indexing_queue.py mark URL indexed   # Search Console said "URL is on Google"
    python3 indexing_queue.py mark URL requested # "Indexing requested" came back
    python3 indexing_queue.py mark URL failed    # anything else
    python3 indexing_queue.py report             # where the archive stands

State lives in .indexing-state.json next to this file and is not committed.

indexing-priority.txt (committed) is the fast lane: lines of "YYYY-MM-DD URL" written by the cloud
routines when a post is refreshed for an anniversary or a news story. Such a URL is asked for first
if it has not been requested since that date, even when an older request is still inside RETRY_DAYS.

Order: hub pages first (they lead Google to everything else), then posts that answer a status
question ("Is X still...", "Who owns...", "How many... left"), rewritten posts before untouched
ones, newest first. A URL requested less than RETRY_DAYS ago is not asked for again; after that, if
it is still not indexed, it goes back in the line.
"""

import json
import os
import re
import sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(ROOT, ".indexing-state.json")
BASE = "https://404memoryfound.com"
RETRY_DAYS = 21
PRIORITY = os.path.join(ROOT, "indexing-priority.txt")
HUBS = [f"{BASE}/dead-brand-index.html", f"{BASE}/posts/"]
STATUS_TITLE = re.compile(r"^(Is |Are |Does |Who Owns |How Many )|Still (Around|Open|in Business|Made|Sold)", re.I)


def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE, encoding="utf-8"))
    return {"urls": {}}


def save_state(state):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, sort_keys=True)
        f.write("\n")


def ranked_urls():
    posts = json.load(open(os.path.join(ROOT, "posts.json"), encoding="utf-8"))["posts"]

    def rank(p):
        return (0 if STATUS_TITLE.search(p["title"]) else 1,
                0 if p.get("updated") else 1,
                -int((p.get("updated") or p["date"]).replace("-", "")))

    return HUBS + [f"{BASE}/posts/{p['id']}.html" for p in sorted(posts, key=rank)]


def due(entry, today):
    if not entry:
        return True
    if entry["status"] == "indexed":
        return False
    if entry["status"] == "requested":
        return date.fromisoformat(entry["date"]) <= today - timedelta(days=RETRY_DAYS)
    return True  # failed earlier: try again


def priority_urls(state):
    """Fast-lane URLs not yet requested since they were flagged, oldest flag first."""
    if not os.path.exists(PRIORITY):
        return []
    picks = []
    for line in open(PRIORITY, encoding="utf-8"):
        parts = line.split()
        if len(parts) != 2 or not parts[1].startswith(BASE):
            continue
        flagged, url = parts
        entry = state["urls"].get(url)
        if entry and entry["status"] in ("requested", "indexed") and entry["date"] >= flagged:
            continue
        if url not in picks:
            picks.append(url)
    return picks


def cmd_next(n):
    state, today = load_state(), date.today()
    fast = priority_urls(state)
    rest = [u for u in ranked_urls() if u not in fast and due(state["urls"].get(u), today)]
    print("\n".join((fast + rest)[:n]))


def cmd_mark(url, status):
    if status not in ("indexed", "requested", "failed"):
        sys.exit("status must be indexed, requested or failed")
    state = load_state()
    prev = state["urls"].get(url, {})
    state["urls"][url] = {"status": status, "date": str(date.today()),
                          "requests": prev.get("requests", 0) + (status == "requested")}
    save_state(state)
    print(f"{status}: {url}")


def cmd_report():
    state, today = load_state(), date.today()
    urls = ranked_urls()
    counts = {"indexed": 0, "requested": 0, "failed": 0, "never tried": 0}
    for u in urls:
        e = state["urls"].get(u)
        counts[e["status"] if e else "never tried"] += 1
    waiting = sum(1 for u in urls if due(state["urls"].get(u), today))
    print(f"{len(urls)} URLs in the archive")
    for k, v in counts.items():
        print(f"  {k:12s} {v}")
    print(f"  due today    {waiting}  (about {-(-waiting // 9)} days at nine a day)")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["next"]:
        cmd_next(int(args[1]) if len(args) > 1 else 12)
    elif args[:1] == ["mark"] and len(args) == 3:
        cmd_mark(args[1], args[2])
    elif args[:1] == ["report"]:
        cmd_report()
    else:
        print(__doc__)
