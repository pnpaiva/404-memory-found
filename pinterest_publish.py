#!/usr/bin/env python3
"""
Pin new posts to Pinterest through the Pinterest API (v5).

Runs in the daily workflow after the build. Does nothing unless the Pinterest secrets are set.
Remembers what it pinned in pinterest-state.json (committed by the workflow) so nothing is pinned twice.

Pinterest access tokens expire after 30 days, so none is stored. The workflow keeps PINTEREST_APP_ID,
PINTEREST_APP_SECRET and PINTEREST_REFRESH_TOKEN, and a fresh access token is minted on every run.
Run pinterest_auth.py once to produce those values. A plain PINTEREST_ACCESS_TOKEN still works if set,
which is useful for a one-off manual run.

  python pinterest_publish.py             # pin posts from the last 3 days that are not in the state file
  python pinterest_publish.py --backfill 5   # also pin the 5 most recent older posts (drip the archive out slowly)

Setup (owner, once): a Pinterest business account for the site, claim the website (paste the tag into
site-config.json → pinterest_verification), create a board, get an app approved for Trial access at
developers.pinterest.com, then run `python3 pinterest_auth.py` and store the four secrets it prints.
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.parse
from datetime import date, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://404memoryfound.com"
API = "https://api.pinterest.com/v5/pins"
TOKEN_URL = "https://api.pinterest.com/v5/oauth/token"
STATE = os.path.join(ROOT, "pinterest-state.json")


def load_state():
    return json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else {"pinned": {}}


def save_state(state):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")


def access_token():
    """A 30-day access token minted from the refresh token, so nothing has to be rotated by hand."""
    token = os.environ.get("PINTEREST_ACCESS_TOKEN")
    if token:
        return token
    app_id = os.environ.get("PINTEREST_APP_ID")
    secret = os.environ.get("PINTEREST_APP_SECRET")
    refresh = os.environ.get("PINTEREST_REFRESH_TOKEN")
    if not (app_id and secret and refresh):
        return None
    auth = base64.b64encode(f"{app_id}:{secret}".encode()).decode()
    data = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": refresh}).encode()
    req = Request(TOKEN_URL, data=data, method="POST",
                  headers={"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urlopen(req, timeout=60) as r:
            body = json.load(r)
    except HTTPError as e:
        print(f"Pinterest: refresh failed, HTTP {e.code} {e.read().decode()[:200]}")
        print("  Run pinterest_auth.py again and update PINTEREST_REFRESH_TOKEN.")
        return None
    if body.get("refresh_token") and body["refresh_token"] != refresh:
        # Continuous refresh tokens rotate. The old one keeps working inside its 60 day window, but
        # print the new one so a stale secret can be replaced before that window runs out.
        print("Pinterest: a rotated refresh token was issued (store it if pinning ever starts failing):")
        print(f"  {body['refresh_token']}")
    return body.get("access_token")


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

    board = os.environ.get("PINTEREST_BOARD_ID")
    if not board:
        print("Pinterest: PINTEREST_BOARD_ID not set, skipping (run pinterest_auth.py to set the secrets)")
        return 0
    token = access_token()
    if not token:
        print("Pinterest: no usable token, skipping (run pinterest_auth.py to set the secrets)")
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
