#!/usr/bin/env python3
"""
Refresh seo/search-console.json from rows copied out of Search Console (the weekly local task does this
in the owner's browser, because Search Console data never reaches the cloud routines otherwise).

    python3 seo_snapshot.py --pages pages.txt [--queries queries.txt] [--crawled crawled.txt] \
        --totals "CLICKS IMPRESSIONS CTR POSITION" --index "INDEXED DISCOVERED CRAWLED"

pages.txt    one row per line, as the Performance table shows it with the page breakdown:
             https://404memoryfound.com/posts/x.html|clicks|impressions|ctr|position
queries.txt  one row per line: <slug>|query|clicks|impressions|ctr|position  (queries for the top pages)
crawled.txt  one URL or slug per line from Page indexing > Crawled - currently not indexed
CTR may be given as 0.3% or 0.003. Lessons already in the file are kept.
"""

import argparse
import json
import os
import re
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "seo", "search-console.json")


def slug_of(url):
    url = url.strip().replace("https://404memoryfound.com", "").replace("http://404memoryfound.com", "")
    if url in ("", "/"):
        return "home"
    return re.sub(r"\.html$", "", url.strip("/").split("/")[-1])


def num(x):
    x = x.strip().replace(",", "")
    if x.endswith("%"):
        return round(float(x[:-1]) / 100, 4)
    return float(x) if "." in x else int(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", required=True)
    ap.add_argument("--queries")
    ap.add_argument("--crawled")
    ap.add_argument("--totals", required=True, help="clicks impressions ctr position")
    ap.add_argument("--index", required=True, help="indexed discovered_not_indexed crawled_not_indexed")
    a = ap.parse_args()

    old = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    pages = []
    for line in open(a.pages, encoding="utf-8"):
        cells = [c for c in line.strip().split("|") if c.strip()]
        if len(cells) >= 5:
            pages.append([slug_of(cells[0]), num(cells[1]), num(cells[2]), num(cells[4])])
    pages.sort(key=lambda r: -r[2])

    qmap = {}
    if a.queries and os.path.exists(a.queries):
        for line in open(a.queries, encoding="utf-8"):
            cells = line.rstrip("\n").split("|")
            if len(cells) >= 6:
                qmap.setdefault(slug_of(cells[0]), []).append(f"{cells[1].strip()} ({num(cells[5])})")
    crawled = []
    if a.crawled and os.path.exists(a.crawled):
        crawled = [slug_of(x) for x in open(a.crawled, encoding="utf-8") if x.strip()]

    t = a.totals.split()
    i = a.index.split()
    snap = {
        "snapshot": date.today().isoformat(),
        "window_days": 90,
        "note": old.get("note", "Search Console export used by the upgrade desk."),
        "totals": {"clicks": num(t[0]), "impressions": num(t[1]), "ctr": num(t[2]), "position": num(t[3]),
                   "indexed": num(i[0]), "discovered_not_indexed": num(i[1]), "crawled_not_indexed": num(i[2])},
        "pages": pages,
        "page_columns": ["slug", "clicks", "impressions", "position"],
        "queries_by_page": qmap or old.get("queries_by_page", {}),
        "crawled_not_indexed": crawled or old.get("crawled_not_indexed", []),
        "lessons": old.get("lessons", []),
        "history": (old.get("history", []) + [{"date": old["snapshot"], **old["totals"]}])[-26:] if old.get("totals") else [],
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(snap, open(OUT, "w", encoding="utf-8"), indent=1)
    print(f"seo/search-console.json: {len(pages)} pages, {sum(len(v) for v in snap['queries_by_page'].values())} queries, "
          f"{len(snap['crawled_not_indexed'])} crawled-not-indexed, totals {snap['totals']}")


if __name__ == "__main__":
    main()
