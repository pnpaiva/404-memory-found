#!/usr/bin/env python3
"""
Which existing post the upgrade desk should improve next.

    python3 seo_queue.py next        # the next post to upgrade, with the reason and the queries it is tested for
    python3 seo_queue.py list 15     # the first N of the queue
    python3 seo_queue.py report      # how much of the archive has been upgraded

Order of the queue:
  1. pages Google already shows (seo/search-console.json) at positions 3 to 35 with 3+ impressions,
     most impressions first: they are one good rewrite away from the first page;
  2. pages Google crawled and refused to index: a quality verdict, so they need real improvement;
  3. everything else that has never been upgraded, posts without an in-body photo first, oldest first.
A post counts as upgraded when its "upgraded" field is set; it can come back after RECHECK_DAYS.
"""

import json
import os
import sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
RECHECK_DAYS = 60


def load():
    posts = json.load(open(os.path.join(ROOT, "posts.json"), encoding="utf-8"))["posts"]
    path = os.path.join(ROOT, "seo", "search-console.json")
    gsc = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    return posts, gsc


def fresh(p):
    up = p.get("upgraded")
    return bool(up) and up >= (date.today() - timedelta(days=RECHECK_DAYS)).isoformat()


def queue():
    posts, gsc = load()
    by = {p["id"]: p for p in posts}
    out, seen = [], set()

    def add(slug, reason, queries=()):
        if slug in by and slug not in seen and not fresh(by[slug]):
            seen.add(slug)
            out.append((slug, reason, list(queries)))

    qmap = gsc.get("queries_by_page", {})
    pages = [r for r in gsc.get("pages", []) if r[0] in by and r[2] >= 3 and 3 <= r[3] <= 35]
    for slug, clicks, imp, pos in sorted(pages, key=lambda r: -r[2]):
        add(slug, f"in search: {imp} impressions at position {pos}, {clicks} clicks", qmap.get(slug, ()))
    for slug in gsc.get("crawled_not_indexed", []):
        add(slug, "crawled but not indexed: Google judged it not good enough yet", qmap.get(slug, ()))
    rest = sorted(posts, key=lambda p: ("<figure" in p["body"], p.get("updated") or p["date"]))
    for p in rest:
        add(p["id"], "not upgraded yet" + ("" if "<figure" in p["body"] else ", no in-body photo"))
    return out, by


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "next"
    items, by = queue()
    if cmd == "next":
        if not items:
            print("queue empty")
            return
        slug, reason, queries = items[0]
        p = by[slug]
        print(f"{slug}\n  title: {p['title']}\n  why: {reason}")
        if queries:
            print("  queries it is tested for (average position): " + "; ".join(queries))
    elif cmd == "list":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 15
        for slug, reason, _ in items[:n]:
            print(f"{slug:60s} {reason}")
    elif cmd == "report":
        posts = list(by.values())
        done = sum(1 for p in posts if p.get("upgraded"))
        figs = sum(1 for p in posts if "<figure" in p["body"])
        print(f"{len(posts)} posts, {done} upgraded, {figs} with an in-body photo, {len(items)} in the queue")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
