#!/usr/bin/env python3
"""
Which existing post the upgrade desk should improve next.

    python3 seo_queue.py next        # the next post to upgrade, with the reason and the queries it is tested for
    python3 seo_queue.py list 15     # the first N of the queue
    python3 seo_queue.py report      # how much of the archive has been upgraded

Order of the queue (tiers 1 to 3 take turns, one post each; tier 4 follows):
  1. pages Google already shows (seo/search-console.json) at positions 3 to 35 with 3+ impressions,
     most impressions first: they are one good rewrite away from the first page;
  2. pages with an entry in seo/upgrade-notes.json (search-results gaps, posts competing with each other);
  3. pages Google crawled and refused to index: a quality verdict, so they need real improvement;
  4. everything else that has never been upgraded, posts without an in-body photo first, oldest first.
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
    npath = os.path.join(ROOT, "seo", "upgrade-notes.json")
    notes = json.load(open(npath, encoding="utf-8")).get("notes", {}) if os.path.exists(npath) else {}
    by = {p["id"]: p for p in posts}
    # A note is spent once the post has been upgraded on or after the day the note was written.
    gsc["_notes"] = {k: v for k, v in notes.items()
                     if not (k in by and (by[k].get("upgraded") or "") >= v.get("date", ""))}
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
    in_search = [(slug, f"in search: {imp} impressions at position {pos}, {clicks} clicks")
                 for slug, clicks, imp, pos in sorted(pages, key=lambda r: -r[2])]
    noted = [(slug, f"upgrade note ({n.get('source', 'notes')})") for slug, n in gsc["_notes"].items()]
    crawled = [(slug, "crawled but not indexed: Google judged it not good enough yet")
               for slug in gsc.get("crawled_not_indexed", [])]
    # Round robin over the three tiers: ranking pages, noted gaps and refused pages each get a turn, so the pages
    # Google crawled and turned down are not stuck behind months of the other two (they are the indexing lever).
    tiers = [in_search, crawled, noted]
    while any(tiers):
        for tier in tiers:
            if tier:
                slug, reason = tier.pop(0)
                add(slug, reason, qmap.get(slug, ()))
    rest = sorted(posts, key=lambda p: ("<figure" in p["body"], p.get("updated") or p["date"]))
    for p in rest:
        add(p["id"], "not upgraded yet" + ("" if "<figure" in p["body"] else ", no in-body photo"))
    return out, by


def print_note(slug):
    note = load()[1]["_notes"].get(slug)
    if not note:
        return
    print("  UPGRADE NOTE from a search-results review. Apply every item, verifying each fact and number against a source:")
    for key in ("fix_first", "retarget", "primary", "competition", "note"):
        if note.get(key):
            print(f"    {key}: {note[key]}")
    for key in ("do", "add", "cut", "questions"):
        for item in note.get(key, []):
            print(f"    {key}: {item}")


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
        print_note(slug)
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
