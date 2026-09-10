#!/usr/bin/env python3
"""
Download every Wikimedia image referenced in posts.json, resize it, and store it
in /img so the site serves its own images instead of hotlinking.

Writes images-manifest.json:  { original_url: {file, thumb, width, height, status, commons} }

Run locally whenever posts are added:  python3 fetch_images.py
Idempotent: URLs already in the manifest with status "ok" are skipped.
build.py reads the manifest and rewrites <img src> to the local copies.
"""

import hashlib
import io
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import unquote, quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from PIL import Image

IMG_DIR = "img"
THUMB_DIR = os.path.join(IMG_DIR, "thumb")
MANIFEST = "images-manifest.json"
MAX_WIDTH = 1280  # Google Discover wants at least 1200px wide
THUMB_WIDTH = 240
USER_AGENT = "404MemoryFound-build/1.0 (https://404memoryfound.com; hello@404memoryfound.com)"


def collect_urls(posts):
    urls = set()
    for p in posts:
        for m in re.finditer(r'<img[^>]*src="([^"]+)"', p.get("body", "")):
            urls.add(m.group(1))
        if p.get("image"):
            urls.add(p["image"])
    return sorted(urls)


def commons_page(url):
    """Derive the Wikimedia Commons file page from an upload URL."""
    m = re.search(r"/wikipedia/commons/(.*)$", url)
    if not m:
        return None
    parts = m.group(1).split("/")
    if parts and parts[0] == "thumb" and len(parts) >= 4:
        name = parts[3]
    elif len(parts) >= 3:
        name = parts[2]
    else:
        return None
    return "https://commons.wikimedia.org/wiki/File:" + name


def local_name(url):
    """Stable, readable file name derived from the Commons file name plus a short hash."""
    page = commons_page(url) or url
    raw = unquote(page.rsplit("File:", 1)[-1])
    base = re.sub(r"\.[A-Za-z0-9]+$", "", raw)
    slug = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")[:60] or "image"
    return f"{slug}-{hashlib.sha1(url.encode()).hexdigest()[:6]}"


def fetch(url):
    """GET with polite retries: Wikimedia answers 429 when hit too fast."""
    req = Request(quote(url, safe=":/%?=&"), headers={"User-Agent": USER_AGENT})
    for attempt in range(6):
        try:
            with urlopen(req, timeout=60) as r:
                data = r.read()
            time.sleep(0.4)
            return data
        except HTTPError as e:
            if e.code == 429 and attempt < 5:
                time.sleep(4 * (attempt + 1))
                continue
            raise
    raise RuntimeError("unreachable")


def save_variants(data, name):
    im = Image.open(io.BytesIO(data))
    im.load()
    has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
    if has_alpha:
        im = im.convert("RGBA")
        # Drop alpha if it is fully opaque anyway
        if im.getchannel("A").getextrema()[0] == 255:
            im = im.convert("RGB")
            has_alpha = False
    else:
        im = im.convert("RGB")

    def resized(img, width):
        if img.width <= width:
            return img.copy()
        h = round(img.height * width / img.width)
        return img.resize((width, h), Image.LANCZOS)

    main = resized(im, MAX_WIDTH)
    thumb = resized(im, THUMB_WIDTH)

    if has_alpha:
        ext = "png"
        main_path = os.path.join(IMG_DIR, f"{name}.png")
        main.save(main_path, "PNG", optimize=True)
        thumb_path = os.path.join(THUMB_DIR, f"{name}.png")
        thumb.save(thumb_path, "PNG", optimize=True)
    else:
        ext = "jpg"
        main_path = os.path.join(IMG_DIR, f"{name}.jpg")
        main.save(main_path, "JPEG", quality=84, optimize=True, progressive=True)
        thumb_path = os.path.join(THUMB_DIR, f"{name}.jpg")
        thumb.save(thumb_path, "JPEG", quality=80, optimize=True)

    return {
        "file": "/" + main_path.replace(os.sep, "/"),
        "thumb": "/" + thumb_path.replace(os.sep, "/"),
        "width": main.width,
        "height": main.height,
        "ext": ext,
    }


def original_url(url):
    """Thumb URL -> original upload URL (works when the requested thumb size is refused)."""
    m = re.match(r"(https://upload\.wikimedia\.org/wikipedia/commons)/thumb/([^/]+/[^/]+/[^/]+)/[^/]+$", url)
    return f"{m.group(1)}/{m.group(2)}" if m else None


def upsized_url(url):
    """Ask Commons for a MAX_WIDTH thumb instead of the size the post referenced (usually 960px)."""
    return re.sub(r"/\d+px-", f"/{MAX_WIDTH}px-", url, count=1) if "/thumb/" in url else url


def process(url):
    name = local_name(url)
    candidates = []
    for c in (upsized_url(url), url, original_url(url)):
        if c and c not in candidates:
            candidates.append(c)
    data, last = None, None
    for c in candidates:
        try:
            data = fetch(c)
            break
        except HTTPError as e:
            last = e
            if e.code not in (400, 404, 429):
                return url, {"status": "missing", "http": e.code, "commons": commons_page(url)}
        except Exception as e:  # noqa: BLE001
            return url, {"status": "error", "error": str(e), "commons": commons_page(url)}
    if data is None:
        return url, {"status": "missing", "http": getattr(last, "code", None), "commons": commons_page(url)}
    try:
        info = save_variants(data, name)
    except Exception as e:  # noqa: BLE001
        return url, {"status": "error", "error": f"decode: {e}", "commons": commons_page(url)}
    info.update({"status": "ok", "commons": commons_page(url), "requested": MAX_WIDTH})
    return url, info


FREE_LICENCES = ("cc0", "cc by", "cc-by", "public domain", "pd", "attribution")
STOP = {"the", "and", "with", "from", "for", "toy", "photo", "image", "picture", "original"}


def commons_lookup(query):
    """Conservative Commons search: every significant query word must appear in the file title or description."""
    api = ("https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrlimit=12"
           f"&gsrsearch={quote(query)}&prop=imageinfo&iiprop=url%7Cextmetadata%7Csize%7Cmime&iiurlwidth=960&format=json")
    with urlopen(Request(api, headers={"User-Agent": USER_AGENT}), timeout=30) as r:
        data = json.load(r)
    words = [w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) > 2 and w not in STOP]
    for page in sorted(data.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99)):
        ii = page["imageinfo"][0]
        meta = ii.get("extmetadata", {})
        licence = (meta.get("LicenseShortName", {}).get("value") or "").lower()
        if ii.get("mime") not in ("image/jpeg", "image/png") or ii.get("width", 0) < 640:
            continue
        if not any(k in licence for k in FREE_LICENCES):
            continue
        hay = (page["title"] + " " + re.sub(r"<[^>]+>", " ", meta.get("ImageDescription", {}).get("value") or "")).lower()
        if all(w in hay for w in words):
            url = (ii.get("thumburl") or ii.get("url")).split("?")[0]
            return re.sub(r"^https://thumb\.wikimedia\.org/", "https://upload.wikimedia.org/", url), page["title"]
    return None, None


def resolve_missing_heroes(posts):
    """Posts written where Commons was unreachable carry imageSearch queries instead of an image URL."""
    changed = False
    for p in posts:
        if p.get("image") or not p.get("imageSearch"):
            continue
        for q in p["imageSearch"][:4]:
            try:
                url, title = commons_lookup(q)
            except Exception as e:  # noqa: BLE001
                print(f"  commons lookup failed for {q!r}: {e}")
                url = None
            if url:
                p["image"] = url
                if not p.get("imageCaption"):
                    p["imageCaption"] = title.replace("File:", "").rsplit(".", 1)[0].replace("_", " ")
                print(f"  hero for {p['id']}: {title}  (query: {q})")
                changed = True
                break
            time.sleep(1)
        if not p.get("image"):
            print(f"  no matching free image for {p['id']} (queries: {p['imageSearch']})")
    return changed


def main():
    os.makedirs(THUMB_DIR, exist_ok=True)
    data = json.load(open("posts.json", encoding="utf-8"))
    posts = data["posts"]
    if resolve_missing_heroes(posts):
        with open("posts.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
    urls = collect_urls(posts)
    manifest = {}
    if os.path.exists(MANIFEST):
        manifest = json.load(open(MANIFEST, encoding="utf-8"))

    def needs_fetch(u):
        m = manifest.get(u, {})
        if m.get("status") != "ok" or not os.path.exists(m.get("file", "/nonexistent").lstrip("/")):
            return True
        # Re-fetch copies stored before the Discover-size change, once
        return m.get("width", 0) < 1200 and m.get("requested", 0) < MAX_WIDTH

    todo = [u for u in urls if needs_fetch(u)]
    print(f"{len(urls)} image URLs referenced, {len(todo)} to fetch")

    done = 0
    with ThreadPoolExecutor(max_workers=2) as ex:
        futures = [ex.submit(process, u) for u in todo]
        for fut in as_completed(futures):
            url, info = fut.result()
            manifest[url] = info
            done += 1
            flag = "ok " if info["status"] == "ok" else "!! "
            print(f"[{done}/{len(todo)}] {flag}{url[-70:]}")
            if done % 10 == 0:
                json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), indent=1, sort_keys=True)

    json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), indent=1, sort_keys=True)
    ok = sum(1 for v in manifest.values() if v["status"] == "ok")
    bad = [u for u, v in manifest.items() if v["status"] != "ok"]
    total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(IMG_DIR) for f in fs)
    print(f"\n{ok} images stored ({total/1e6:.1f} MB in /{IMG_DIR}), {len(bad)} unavailable")
    for u in bad:
        print("   missing:", u)
    return 0


if __name__ == "__main__":
    sys.exit(main())
