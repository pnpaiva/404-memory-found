#!/usr/bin/env python3
"""
Tell IndexNow-enabled search engines (Bing, Yandex, Seznam, Naver; DuckDuckGo and Yahoo read Bing's index)
which URLs changed. Google does not use IndexNow; use Search Console for Google.

The key lives in indexnow.json and is served at https://404memoryfound.com/<key>.txt (committed at the repo root).

  python indexnow_ping.py          # hubs + posts published in the last 3 days (what the daily workflow runs)
  python indexnow_ping.py --all    # every URL in the sitemap (first run, or after a site-wide change)
"""

import argparse
import json
import os
import re
import sys
from datetime import date, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = os.path.dirname(os.path.abspath(__file__))
HOST = "404memoryfound.com"
ENDPOINT = "https://api.indexnow.org/indexnow"


def sitemap_urls():
    with open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8") as f:
        return re.findall(r"<loc>(.*?)</loc>", f.read())


def recent_post_urls(days):
    posts = json.load(open(os.path.join(ROOT, "posts.json"), encoding="utf-8"))["posts"]
    cutoff = str(date.today() - timedelta(days=days))
    return [f"https://{HOST}/posts/{p['id']}.html" for p in posts if p["date"] >= cutoff]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--days", type=int, default=3)
    args = ap.parse_args()

    cfg = json.load(open(os.path.join(ROOT, "indexnow.json"), encoding="utf-8"))
    everything = sitemap_urls()
    if args.all:
        urls = everything
    else:
        hubs = [u for u in everything if not u.startswith(f"https://{HOST}/posts/") or u.endswith("/posts/")]
        urls = sorted(set(hubs + recent_post_urls(args.days) + [f"https://{HOST}/feed.xml"]))
    if not urls:
        print("nothing to submit")
        return 0

    body = json.dumps({"host": HOST, "key": cfg["key"], "keyLocation": cfg["keyLocation"], "urlList": urls[:10000]}).encode()
    req = Request(ENDPOINT, data=body, headers={"Content-Type": "application/json; charset=utf-8",
                                                 "User-Agent": "404MemoryFound-build/1.0"})
    try:
        with urlopen(req, timeout=30) as r:
            print(f"IndexNow: HTTP {r.status} for {len(urls)} URLs")
    except HTTPError as e:
        print(f"IndexNow: HTTP {e.code} {e.read().decode()[:200]}")
        return 0  # never fail the publish because a search engine ping did
    return 0


if __name__ == "__main__":
    sys.exit(main())
