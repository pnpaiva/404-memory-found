#!/usr/bin/env python3
"""
Write seo/analytics.json from the GA4 channel table the Monday indexing run reads.

    python3 seo_analytics.py --channels .seo-scratch/channels.txt --start 2026-10-27 --end 2026-11-23

channels.txt has one line per Session default channel group: channel|sessions|engaged_sessions
(numbers may carry thousands separators). The file keeps the latest 28-day window plus a short history
so the weekly report can compare real visits week over week.

Real visits = Organic Search + AI assistant / AI referral + Referral + Organic Social. Direct and
Unassigned are left out on purpose: on this site they are mostly bots.
"""

import argparse
import json
import os
import re
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "seo", "analytics.json")
GOAL = 200          # real visits per 28 days, the first milestone
HISTORY_MAX = 26    # about half a year of Mondays


def is_real(channel):
    c = channel.lower()
    return c in ("organic search", "referral", "organic social") or bool(re.search(r"\bai\b", c))


def num(text):
    text = text.strip().replace(",", "").replace(" ", "").replace(" ", "")
    return int(float(text)) if text else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channels", required=True)
    ap.add_argument("--start", required=True, help="first day of the GA window, YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="last day of the GA window, YYYY-MM-DD")
    a = ap.parse_args()
    date.fromisoformat(a.start), date.fromisoformat(a.end)

    channels = {}
    for line in open(a.channels, encoding="utf-8"):
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3 or not parts[0] or parts[0].lower() in ("total", "totals"):
            continue
        try:
            channels[parts[0]] = {"sessions": num(parts[1]), "engaged_sessions": num(parts[2])}
        except ValueError:
            continue
    if not channels:
        raise SystemExit("no channel rows read; nothing written")

    real = sum(v["sessions"] for k, v in channels.items() if is_real(k))
    real_engaged = sum(v["engaged_sessions"] for k, v in channels.items() if is_real(k))
    today = str(date.today())

    old = {}
    if os.path.exists(OUT):
        try:
            old = json.load(open(OUT, encoding="utf-8"))
        except ValueError:
            old = {}
    history = [h for h in old.get("history", []) if h.get("date") != today]
    history.append({"date": today, "window": f"{a.start}..{a.end}", "real_visits": real,
                    "real_engaged": real_engaged, "sessions": sum(v["sessions"] for v in channels.values())})
    history = history[-HISTORY_MAX:]

    data = {
        "date": today,
        "window": {"start": a.start, "end": a.end, "days": (date.fromisoformat(a.end) - date.fromisoformat(a.start)).days + 1},
        "source": "GA4 Reports > Acquisition > Traffic acquisition, Session default channel group",
        "real_visit_channels": "Organic Search + AI assistant/AI referral + Referral + Organic Social",
        "goal_real_visits": GOAL,
        "channels": dict(sorted(channels.items(), key=lambda kv: -kv[1]["sessions"])),
        "real_visits": real,
        "real_engaged": real_engaged,
        "history": history,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")
    prev = history[-2]["real_visits"] if len(history) > 1 else None
    print(f"real visits {real} (engaged {real_engaged}) of goal {GOAL}" + (f", previous {prev}" if prev is not None else ""))


if __name__ == "__main__":
    main()
