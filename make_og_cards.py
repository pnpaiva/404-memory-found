#!/usr/bin/env python3
"""
Generate share images per post in the site's Windows 95 window style:

  og/<slug>.jpg    1200 x 630   Open Graph / Twitter card (link previews)
  pins/<slug>.jpg  1000 x 1500  vertical card for Pinterest (feed media + pinterest_publish.py)

Each card shows the post's hero photo (the local copy from images-manifest.json) next to or above the title.
Posts without a photo get a text-only card. Also writes logo-512.png for schema.org publisher.

Run locally after adding posts:  python3 make_og_cards.py        (only missing cards)
                                 python3 make_og_cards.py --force  (redraw everything)
Cards are regenerated automatically when a post's image changes (the card records the photo it used).
"""

import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

OG_DIR = "og"
PIN_DIR = "pins"
OG_SIZE = (1200, 630)
PIN_SIZE = (1000, 1500)
TEAL = (0, 128, 128)
TEAL_DARK = (16, 107, 107)
GREY = (192, 192, 192)
WHITE = (255, 255, 255)
DARK = (128, 128, 128)
BLACK = (0, 0, 0)
NAVY = (0, 0, 128)
NAVY_LIGHT = (16, 132, 208)
META = (90, 90, 90)


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


def background(size):
    w, h = size
    im = Image.new("RGB", size, TEAL)
    px = im.load()
    for y in range(h):
        t = y / h
        c = tuple(round(TEAL[i] + (TEAL_DARK[i] - TEAL[i]) * t) for i in range(3))
        for x in range(w):
            px[x, y] = c
    d = ImageDraw.Draw(im, "RGBA")
    for y in range(0, h, 4):
        d.line([(0, y), (w, y)], fill=(0, 0, 0, 18))
    return im


def title_bar(draw, box, text, f):
    x0, y0, x1, y1 = box
    for x in range(x0, x1):
        t = (x - x0) / max(1, x1 - x0)
        c = tuple(round(NAVY[i] + (NAVY_LIGHT[i] - NAVY[i]) * t) for i in range(3))
        draw.line([(x, y0), (x, y1)], fill=c)
    draw.text((x0 + 16, y0 + (y1 - y0 - f.size) // 2 - 2), text, font=f, fill=WHITE)
    btn = max(24, y1 - y0 - 16)
    for i, glyph in enumerate(("_", "□", "×")):
        bx1 = x1 - 8 - (2 - i) * (btn + 6)
        b = (bx1 - btn, y0 + 8, bx1, y0 + 8 + btn)
        bevel(draw, b, raised=True)
        gf = font(int(btn * 0.75), bold=True)
        draw.text((b[0] + btn // 2 - gf.size // 3, b[1] - btn // 8), glyph, font=gf, fill=BLACK)


def wrap(title, f, max_width, draw):
    words, lines, cur = title.split(), [], ""
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


def fit_title(draw, title, max_width, max_lines, start, floor):
    size = start
    while True:
        f = font(size, bold=True)
        lines = wrap(title, f, max_width, draw)
        if len(lines) <= max_lines or size <= floor:
            return f, lines, int(size * 1.15)
        size -= 3


def photo_panel(im, path, box):
    """Cover-crop the hero into box with a sunken Win95 border."""
    x0, y0, x1, y1 = box
    try:
        ph = Image.open(path).convert("RGB")
    except OSError:
        return False
    ph = ImageOps.fit(ph, (x1 - x0 - 6, y1 - y0 - 6), Image.LANCZOS, centering=(0.5, 0.4))
    d = ImageDraw.Draw(im)
    bevel(d, box, raised=False)
    im.paste(ph, (x0 + 3, y0 + 3))
    return True


STOP = {"what", "happened", "the", "that", "with", "from", "and", "how", "why", "who", "its", "was", "for", "into",
        "then", "now", "story", "history", "real", "behind", "actually", "failed", "lost", "still", "ever", "made"}


def subject_words(post):
    words = set(re.findall(r"[a-z0-9]+", post["title"].lower()))
    for phrase in post.get("linkPhrases") or []:
        words |= set(re.findall(r"[a-z0-9]+", phrase.lower()))
    return {w for w in words if len(w) >= 4 and w not in STOP}


def hero_path(post, manifest):
    """Local hero photo. Falls back to a body photo only when its alt text names the post's subject,
    so a Clippy card never ends up wearing a Netscape screenshot."""
    def local(url):
        info = manifest.get(url, {})
        if info.get("status") == "ok":
            path = info["file"].lstrip("/")
            return path if os.path.exists(path) else None
        return None

    hero = local(post.get("image") or "")
    if hero:
        return hero
    words = subject_words(post)
    for tag in re.findall(r"<img[^>]*>", post.get("body", "")):
        src = re.search(r'src="([^"]+)"', tag)
        alt = re.search(r'alt="([^"]*)"', tag)
        if not src or not alt:
            continue
        alt_words = set(re.findall(r"[a-z0-9]+", alt.group(1).lower()))
        if words & alt_words:
            path = local(src.group(1))
            if path:
                return path
    return None


def make_og(post, photo, path):
    im = background(OG_SIZE)
    d = ImageDraw.Draw(im)
    W, H = OG_SIZE
    win = (40, 36, W - 40, H - 36)
    bevel(d, win, raised=True)
    tb = (win[0] + 6, win[1] + 6, win[2] - 6, win[1] + 56)
    title_bar(d, tb, "404 Memory Found", font(26, bold=True))
    ca = (win[0] + 14, tb[3] + 12, win[2] - 14, win[3] - 14)
    d.rectangle(ca, fill=WHITE)
    text_right = ca[2] - 40
    if photo:
        pw = int((ca[2] - ca[0]) * 0.46)
        pbox = (ca[2] - 16 - pw, ca[1] + 16, ca[2] - 16, ca[3] - 16)
        if photo_panel(im, photo, pbox):
            text_right = pbox[0] - 28
            d = ImageDraw.Draw(im)
    f, lines, lh = fit_title(d, post["title"], text_right - ca[0] - 40, 5, 54, 30)
    y = ca[1] + 34
    for line in lines:
        d.text((ca[0] + 36, y), line, font=f, fill=NAVY)
        y += lh
    tags = " · ".join(post.get("tags", [])[:2])
    d.text((ca[0] + 36, ca[3] - 62), f"{post['date']}    {tags}", font=font(22), fill=META)
    sf = font(22, bold=True)
    d.text((text_right - d.textlength("404memoryfound.com", font=sf), ca[3] - 62), "404memoryfound.com", font=sf, fill=TEAL)
    im.save(path, "JPEG", quality=86, optimize=True, progressive=True)


def make_pin(post, photo, path):
    im = background(PIN_SIZE)
    d = ImageDraw.Draw(im)
    W, H = PIN_SIZE
    win = (36, 36, W - 36, H - 36)
    bevel(d, win, raised=True)
    tb = (win[0] + 6, win[1] + 6, win[2] - 6, win[1] + 64)
    title_bar(d, tb, "404 Memory Found", font(30, bold=True))
    ca = (win[0] + 14, tb[3] + 12, win[2] - 14, win[3] - 14)
    d.rectangle(ca, fill=WHITE)
    top = ca[1] + 20
    if photo:
        pbox = (ca[0] + 20, ca[1] + 20, ca[2] - 20, ca[1] + 20 + 760)
        if photo_panel(im, photo, pbox):
            top = pbox[3] + 34
            d = ImageDraw.Draw(im)
    else:
        # text-only pin: a big 404 glyph keeps the card from looking empty
        gf = font(260, bold=True)
        d.text(((W - d.textlength("404", font=gf)) / 2, ca[1] + 120), "404", font=gf, fill=(225, 225, 225))
        top = ca[1] + 520
    f, lines, lh = fit_title(d, post["title"], ca[2] - ca[0] - 80, 5, 66, 40)
    y = top
    for line in lines:
        d.text((ca[0] + 40, y), line, font=f, fill=NAVY)
        y += lh
    summary = (post.get("summary") or post.get("excerpt") or "").strip()
    if summary and y < ca[3] - 200:
        sf = font(30)
        for line in wrap(summary, sf, ca[2] - ca[0] - 80, d)[:4]:
            if y > ca[3] - 120:
                break
            d.text((ca[0] + 40, y + 12), line, font=sf, fill=(60, 60, 60))
            y += 40
    tags = " · ".join(post.get("tags", [])[:2])
    d.text((ca[0] + 40, ca[3] - 60), tags, font=font(24), fill=META)
    bf = font(26, bold=True)
    d.text((ca[2] - 40 - d.textlength("404memoryfound.com", font=bf), ca[3] - 62), "404memoryfound.com", font=bf, fill=TEAL)
    im.save(path, "JPEG", quality=86, optimize=True, progressive=True)


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
    os.makedirs(PIN_DIR, exist_ok=True)
    posts = json.load(open("posts.json", encoding="utf-8"))["posts"]
    manifest = json.load(open("images-manifest.json", encoding="utf-8")) if os.path.exists("images-manifest.json") else {}
    stamp_path = os.path.join(OG_DIR, ".photos.json")
    stamps = json.load(open(stamp_path)) if os.path.exists(stamp_path) and not force else {}
    made = 0
    for p in posts:
        photo = hero_path(p, manifest)
        og = os.path.join(OG_DIR, f"{p['id']}.jpg")
        pin = os.path.join(PIN_DIR, f"{p['id']}.jpg")
        current = stamps.get(p["id"])
        if force or not os.path.exists(og) or not os.path.exists(pin) or current != (photo or ""):
            make_og(p, photo, og)
            make_pin(p, photo, pin)
            stamps[p["id"]] = photo or ""
            made += 1
    json.dump(stamps, open(stamp_path, "w"), indent=0, sort_keys=True)
    if force or not os.path.exists("logo-512.png"):
        make_logo("logo-512.png")
    print(f"{made} cards (re)generated, {len(posts)} posts, in /{OG_DIR} and /{PIN_DIR}")


if __name__ == "__main__":
    main()
