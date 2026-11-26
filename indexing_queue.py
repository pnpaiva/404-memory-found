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
    python3 indexing_queue.py mark URL quota     # "Quota Exceeded": nothing spent, budget drops to 0 for a while
    python3 indexing_queue.py budget             # requests still allowed now (rolling 24h window)
    python3 indexing_queue.py report             # where the archive stands

State lives in .indexing-state.json next to this file and is not committed.

indexing-priority.txt (committed) is the fast lane: lines of "YYYY-MM-DD URL" written by the cloud
routines when a post is refreshed for an anniversary or a news story. Such a URL is asked for first
if it has not been requested since that date, even when an older request is still inside RETRY_DAYS.

Order: hub pages first (they lead Google to everything else), then posts not yet passed over by Google
("Crawled, currently not indexed" waits until the post is upgraded), posts already carrying a table (the current
spec), then posts that answer a status question ("Is X still...", "Who owns...", "How many... left"), rewritten posts before untouched
ones, newest first. A URL requested less than RETRY_DAYS ago is not asked for again; after that, if
it is still not indexed, it goes back in the line.

Budget: Google counts the quota over a rolling 24 hours, not per calendar day (24/11/2026: a run at 13:30 UTC
hit "Quota Exceeded" 23h48m after the previous run's 11 requests). Every successful request is logged with
its UTC time; `budget` returns CAP minus the requests in the last WINDOW, and `next` never hands out more.
A "Quota Exceeded" sets the budget to 0 for QUOTA_COOLDOWN, since requests made elsewhere are not logged.
"""

import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(ROOT, ".indexing-state.json")
BASE = "https://404memoryfound.com"
RETRY_DAYS = 21
PRIORITY = os.path.join(ROOT, "indexing-priority.txt")
HUBS = [f"{BASE}/dead-brand-index.html", f"{BASE}/posts/"]
CAP = 9                                   # Google allows about ten; keep one spare
WINDOW = timedelta(hours=24, minutes=20)  # rolling quota window plus a margin for the run's own length
QUOTA_COOLDOWN = timedelta(hours=6)
STATUS_TITLE = re.compile(r"^(Is |Are |Does |Who Owns |How Many )|Still (Around|Open|in Business|Made|Sold)", re.I)


def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE, encoding="utf-8"))
    return {"urls": {}}


def save_state(state):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, sort_keys=True)
        f.write("\n")


def search_console():
    try:
        return json.load(open(os.path.join(ROOT, "seo", "search-console.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def known_indexed():
    """Pages with impressions in the latest Search Console snapshot are on Google already: a manual request there
    spends one of the ~ten daily slots on a page that does not need it (the fast lane still re-asks after a rewrite)."""
    return {f"{BASE}/" if row[0] == "home" else f"{BASE}/{row[0]}.html" if row[0] == "dead-brand-index"
            else f"{BASE}/posts/{row[0]}.html" for row in search_console().get("pages", [])}


def ranked_urls():
    posts = json.load(open(os.path.join(ROOT, "posts.json"), encoding="utf-8"))["posts"]
    crawled = set(search_console().get("crawled_not_indexed", []))

    def rank(p):
        # Google already crawled and passed on these; a request rarely changes its mind until the post is upgraded
        stale_crawl = p["id"] in crawled and not p.get("upgraded")
        return (1 if stale_crawl else 0,
                0 if "<table" in p.get("body", "") else 1,   # upgraded to the current spec: the best version to show
                0 if STATUS_TITLE.search(p["title"]) else 1,
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


def now_utc():
    return datetime.now(timezone.utc)


def parse_ts(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def budget(state, now=None):
    """(requests allowed now, reason) under the rolling 24h quota."""
    now = now or now_utc()
    hit = state.get("quota_hit")
    if hit and now - parse_ts(hit) < QUOTA_COOLDOWN:
        return 0, f"Quota Exceeded at {hit}; waiting until {(parse_ts(hit) + QUOTA_COOLDOWN):%Y-%m-%dT%H:%MZ}"
    recent = sorted(parse_ts(t) for t in state.get("log", []) if now - parse_ts(t) < WINDOW)
    left = max(0, CAP - len(recent))
    why = f"{len(recent)} requests in the last {WINDOW}"
    if recent and left < CAP:
        why += f"; the oldest frees up at {(recent[0] + WINDOW):%Y-%m-%dT%H:%MZ}"
    return left, why


def cmd_budget(verbose):
    left, why = budget(load_state())
    print(left)
    if verbose:
        print(why)


def cmd_next(n):
    state, today = load_state(), date.today()
    n = min(n, budget(state)[0])
    if n <= 0:
        return
    fast = priority_urls(state)
    skip = known_indexed()
    rest = [u for u in ranked_urls() if u not in fast and u not in skip and due(state["urls"].get(u), today)]
    # A rewritten page that already has impressions gets recrawled soon on its own (sitemap lastmod); a page
    # Google has never shown needs the slot more. Rewrites of pages not yet on Google keep the front of the line.
    fast_new = [u for u in fast if u not in skip]
    fast_known = [u for u in fast if u in skip]
    print("\n".join((fast_new + rest + fast_known)[:n]))


def cmd_mark(url, status):
    if status not in ("indexed", "requested", "failed", "quota"):
        sys.exit("status must be indexed, requested, failed or quota")
    state = load_state()
    stamp = now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")
    if status == "quota":   # the request was refused: nothing spent, URL keeps its place in the line
        state["quota_hit"] = stamp
        save_state(state)
        print(f"quota exceeded at {stamp}: {url} stays in the queue")
        return
    if status == "requested":
        cutoff = now_utc() - timedelta(days=7)
        state["log"] = [t for t in state.get("log", []) if parse_ts(t) > cutoff] + [stamp]
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
    print(f"  due today    {waiting}  (about {-(-waiting // CAP)} days at {CAP} a day)")
    left, why = budget(state)
    print(f"  budget now   {left}  ({why})")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["next"]:
        cmd_next(int(args[1]) if len(args) > 1 else 12)
    elif args[:1] == ["mark"] and len(args) == 3:
        cmd_mark(args[1], args[2])
    elif args[:1] == ["budget"]:
        cmd_budget("-v" in args or "--why" in args)
    elif args[:1] == ["report"]:
        cmd_report()
    else:
        print(__doc__)
