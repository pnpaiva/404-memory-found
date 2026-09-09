#!/usr/bin/env python3
"""
Pin new posts to Pinterest through the Pinterest API (v5).

Runs in the daily workflow after the build. Does nothing unless PINTEREST_ACCESS_TOKEN and PINTEREST_BOARD_ID
are set. Remembers what it pinned in pinterest-state.json (committed by the workflow) so nothing is pinned twice.

  python pinterest_publish.py             # pin posts from the last 3 days that are not in the state file
  python pinterest_publish.py --backfill 5   # also pin the 5 most recent older posts (drip the archive out slowly)

Setup (owner, once): a Pinterest business account for the site, claim the website (paste the tag into
site-config.json → pinterest_verification), create a board, create an app at developers.pinterest.com, generate
an access token with the pins:write and boards:read scopes, then add the two repository secrets.
"""

import argparse
import json
import os
import sys
import time
from datetime import date, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://404memoryfound.com"
API = "https://api.pinterest.com/v5/pins"
STATE = os.path.join(ROOT, "pinterest-state.json")


def load_state():
    return json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else {"pinned": {}}


def save_state(state):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")


def pin_description(post):
    tags = " ".join("#" + t.replace(" & ", "").replace(" ", "") for t in post.get("tags", []))
    text = post.get("summary") or post["excerpt"]
    return f"{text} {tags} #90s #nostalgia #retrotech"[:500]


def create_pin(token, board_id, post):
    payload = {
        "board_id": board_id,
        "title": post["title"][:100],
        "description": pin_description(post),
        "link": f"{BASE_URL}/posts/{post['id']}.html",
        "alt_text": (post.get("imageAlt") or post["title"])[:500],
        "media_source": {"source_type": "image_url", "url": f"{BASE_URL}/pins/{post['id']}.jpg"},
    }
    req = Request(API, data=json.dumps(payload).encode(), method="POST",
                  headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urlopen(req, timeout=60) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--backfill", type=int, default=0, help="also pin this many not-yet-pinned older posts")
    args = ap.parse_args()

    token = os.environ.get("PINTEREST_ACCESS_TOKEN")
    board = os.environ.get("PINTEREST_BOARD_ID")
    if not token or not board:
        print("Pinterest: PINTEREST_ACCESS_TOKEN / PINTEREST_BOARD_ID not set, skipping")
        return 0

    posts = sorted(json.load(open(os.path.join(ROOT, "posts.json"), encoding="utf-8"))["posts"],
                   key=lambda p: p["date"], reverse=True)
    state = load_state()
    cutoff = str(date.today() - timedelta(days=args.days))
    fresh = [p for p in posts if p["date"] >= cutoff and p["id"] not in state["pinned"]]
    older = [p for p in posts if p["date"] < cutoff and p["id"] not in state["pinned"]][:args.backfill]

    for post in fresh + older:
        if not os.path.exists(os.path.join(ROOT, "pins", f"{post['id']}.jpg")):
            print(f"  no share card for {post['id']}, skipping")
            continue
        try:
            result = create_pin(token, board, post)
            state["pinned"][post["id"]] = {"pin_id": result.get("id"), "date": str(date.today())}
            save_state(state)
            print(f"  pinned {post['id']} -> {result.get('id')}")
            time.sleep(2)
        except HTTPError as e:
            print(f"  Pinterest error for {post['id']}: HTTP {e.code} {e.read().decode()[:300]}")
            if e.code in (401, 403):
                return 0  # token problem: stop, but never fail the publish
    print(f"Pinterest: {len(state['pinned'])} posts pinned in total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
