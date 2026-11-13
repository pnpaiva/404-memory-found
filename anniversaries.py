#!/usr/bin/env python3
"""
Nostalgia runs on a calendar. When a console turns 25 or a toy turns 30, newspapers write about it,
Google Discover pushes "X turns 30" stories and searches for the subject jump for a few days, with
far less competition than the evergreen query. This finds those dates in the archive.

    python3 anniversaries.py upcoming            # events 2 to 14 days ahead, best first
    python3 anniversaries.py upcoming 0 30       # any window, in days from today

Dates come from each post's quick facts ("Launched: November 23, 1996, Bandai ..."), so a post only
appears here once it carries a full date. Round ages (every 5 years) rank first, because those are
the ones the press actually covers.
"""

import json
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
MONTHS = "January February March April May June July August September October November December".split()
DATE = re.compile(r"\b(" + "|".join(MONTHS) + r")\s+(\d{1,2}),\s+(\d{4})")
EVENT_LABELS = ("launch", "release", "found", "open", "debut", "shut", "close", "discontinu", "end",
                "bankrupt", "last", "died", "ipo", "sold", "acquir")


def events():
    posts = json.load(open(os.path.join(ROOT, "posts.json"), encoding="utf-8"))["posts"]
    found = []
    for p in posts:
        for fact in p.get("facts", []):
            label = fact["label"]
            if not any(k in label.lower() for k in EVENT_LABELS):
                continue
            m = DATE.search(re.sub(r"<[^>]+>", "", fact["value"]))
            if not m:
                continue
            year = int(m.group(3))
            if year < 1950 or year >= date.today().year:
                continue
            found.append({"slug": p["id"], "title": p["title"], "label": label,
                          "month": MONTHS.index(m.group(1)) + 1, "day": int(m.group(2)), "year": year,
                          "updated": p.get("updated") or p["date"]})
    return found


def next_occurrence(e, today):
    for y in (today.year, today.year + 1):
        try:
            d = date(y, e["month"], e["day"])
        except ValueError:
            continue
        if d >= today:
            return d
    return None


def upcoming(start=2, end=14):
    today = date.today()
    rows = []
    for e in events():
        d = next_occurrence(e, today)
        if not d:
            continue
        ahead = (d - today).days
        if start <= ahead <= end:
            age = d.year - e["year"]
            rows.append({**e, "on": str(d), "days_ahead": ahead, "age": age,
                         "round": age % 5 == 0, "url": f"https://404memoryfound.com/posts/{e['slug']}.html"})
    rows.sort(key=lambda r: (not r["round"], r["days_ahead"]))
    return rows


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["upcoming"]:
        lo = int(args[1]) if len(args) > 1 else 2
        hi = int(args[2]) if len(args) > 2 else 14
        for r in upcoming(lo, hi):
            flag = "ROUND" if r["round"] else "     "
            print(f"{r['on']}  in {r['days_ahead']:2d}d  {flag} {r['age']:2d} years  {r['label']:<14.14}  {r['slug']}  |  {r['title']}")
    else:
        print(__doc__)
