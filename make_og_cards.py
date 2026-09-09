#!/usr/bin/env python3
"""
Generate a 1200x630 Open Graph card per post (og/<slug>.png) in the site's
Windows 95 window style, plus a square logo (logo-512.png) for schema.org publisher.

Run locally after adding posts:  python3 make_og_cards.py
Idempotent: existing cards are kept unless --force is passed.
"""

import json
import os
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFont

OG_DIR = "og"
W, H = 1200, 630
TEAL = (0, 128, 128)
TEAL_DARK = (16, 107, 107)
GREY = (192, 192, 192)
WHITE = (255, 255, 255)
DARK = (128, 128, 128)
BLACK = (0, 0, 0)
NAVY = (0, 0, 128)
NAVY_LIGHT = (16, 132, 208)


def font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def bevel(draw, box, raised=True):
    x0, y0, x1, y1 = box
    light, shadow = (WHITE, DARK) if raised else (DARK, WHITE)
    draw.rectangle(box, fill=GREY)
    draw.line([(x0, y0), (x1, y0)], fill=light, width=3)
    draw.line([(x0, y0), (x0, y1)], fill=light, width=3)
    draw.line([(x0, y1), (x1, y1)], fill=shadow, width=3)
    draw.line([(x1, y0), (x1, y1)], fill=shadow, width=3)


def background():
    im = Image.new("RGB", (W, H), TEAL)
    px = im.load()
    for y in range(H):
        t = y / H
        c = tuple(round(TEAL[i] + (TEAL_DARK[i] - TEAL[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = c
    # subtle scanlines
    d = ImageDraw.Draw(im, "RGBA")
    for y in range(0, H, 4):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, 18))
    return im


def title_bar(draw, box, text, f):
    x0, y0, x1, y1 = box
    # gradient navy → light blue
    for x in range(x0, x1):
        t = (x - x0) / max(1, x1 - x0)
        c = tuple(round(NAVY[i] + (NAVY_LIGHT[i] - NAVY[i]) * t) for i in range(3))
        draw.line([(x, y0), (x, y1)], fill=c)
    draw.text((x0 + 16, y0 + 10), text, font=f, fill=WHITE)
    # window buttons
    bx = x1 - 40
    for glyph in ("×", "□", "_")[::-1]:
        pass
    for i, glyph in enumerate(("_", "□", "×")):
        b = (x1 - 40 * (3 - i) - 8, y0 + 8, x1 - 40 * (2 - i) - 14, y1 - 8)
        bevel(draw, b, raised=True)
        gx = (b[0] + b[2]) // 2 - 7
        draw.text((gx, b[1] - 2), glyph, font=font(24, bold=True), fill=BLACK)


def wrap_title(title, f, max_width, draw):
    words = title.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=f) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def make_card(post, path):
    im = background()
    d = ImageDraw.Draw(im)
    # window frame
    win = (70, 60, W - 70, H - 60)
    bevel(d, win, raised=True)
    tb = (win[0] + 6, win[1] + 6, win[2] - 6, win[1] + 56)
    title_bar(d, tb, "404 Memory Found", font(26, bold=True))
    # content area
    ca = (win[0] + 14, tb[3] + 12, win[2] - 14, win[3] - 14)
    d.rectangle(ca, fill=WHITE)
    d.line([(ca[0], ca[1]), (ca[2], ca[1])], fill=DARK, width=2)
    d.line([(ca[0], ca[1]), (ca[0], ca[3])], fill=DARK, width=2)

    # title text, shrink until it fits in 4 lines
    size = 60
    while True:
        f = font(size, bold=True)
        lines = wrap_title(post["title"], f, ca[2] - ca[0] - 80, d)
        if len(lines) <= 4 or size <= 34:
            break
        size -= 4
    line_h = int(size * 1.18)
    y = ca[1] + 44
    for line in lines:
        d.text((ca[0] + 40, y), line, font=f, fill=NAVY)
        y += line_h

    # footer line: date + tags
    tags = " · ".join(post.get("tags", [])[:3])
    meta = f"{post['date']}    {tags}".strip()
    d.text((ca[0] + 40, ca[3] - 70), meta, font=font(24), fill=(90, 90, 90))
    d.text((ca[2] - 40 - d.textlength("404memoryfound.com", font=font(24, bold=True)), ca[3] - 70),
           "404memoryfound.com", font=font(24, bold=True), fill=TEAL)
    im.save(path, "PNG", optimize=True)


def make_logo(path):
    S = 512
    im = Image.new("RGB", (S, S), TEAL)
    d = ImageDraw.Draw(im)
    win = (48, 96, S - 48, S - 96)
    bevel(d, win, raised=True)
    tb = (win[0] + 6, win[1] + 6, win[2] - 6, win[1] + 52)
    title_bar(d, tb, "404", font(28, bold=True))
    f = font(150, bold=True)
    d.text((S / 2 - d.textlength("404", font=f) / 2, win[1] + 90), "404", font=f, fill=NAVY)
    f2 = font(34, bold=True)
    d.text((S / 2 - d.textlength("memory found", font=f2) / 2, win[3] - 80), "memory found", font=f2, fill=BLACK)
    im.save(path, "PNG", optimize=True)


def main():
    force = "--force" in sys.argv
    os.makedirs(OG_DIR, exist_ok=True)
    posts = json.load(open("posts.json", encoding="utf-8"))["posts"]
    made = 0
    for p in posts:
        path = os.path.join(OG_DIR, f"{p['id']}.png")
        if force or not os.path.exists(path):
            make_card(p, path)
            made += 1
    if force or not os.path.exists("logo-512.png"):
        make_logo("logo-512.png")
    print(f"{made} OG cards generated, {len(posts)} total in /{OG_DIR}")


if __name__ == "__main__":
    main()
