#!/usr/bin/env python3
"""
Build script for 404 Memory Found - Windows 95 themed static site generator.

Inputs
  src/index.html         the SPA (desktop + mobile UI, CSS and JS inline)
  posts.json             every post, body included (source of truth)
  authors.json           pen names: key -> {name, beat, bio, tags}
  site-config.json       monetization switches (AdSense id, ads.txt, affiliate ids)
  redirects.json         old slug -> new slug for posts that moved
  images-manifest.json   written by fetch_images.py: Wikimedia URL -> local copy
  og/<slug>.png          written by make_og_cards.py: per-post share image

Outputs (all committed, served by GitHub Pages)
  index.html             the SPA with SEO meta, pre-rendered post lists, external assets
  assets/site.css|js     the SPA's CSS and JS, cached once instead of inlined per page
  posts-index.json       lightweight list the homepage loads (no bodies)
  posts/<slug>.html      one static page per post, article rendered exactly once
  posts/<slug>.json      body only, fetched on demand when a post opens in the desktop
  posts/index.html       crawlable list of every post
  tags/<tag>.html        one hub page per category
  authors/<key>.html     one page per pen name
  about|contact|privacy|terms.html, 404.html, feed.xml, sitemap.xml, robots.txt, CNAME, ads.txt
"""

import hashlib
import html
import json
import os
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse

BASE_URL = "https://404memoryfound.com"
BLOG_NAME = "404 Memory Found"
OUTPUT_DIR = "."
ROOT = os.path.dirname(os.path.abspath(__file__))
SOURCE_PATH = os.path.join(ROOT, "src", "index.html")
DEFAULT_DESCRIPTION = ("404 Memory Found is a nostalgia blog about the technology, games, websites and companies "
                       "of the 90s and 2000s: what they cost, why they won or lost, and what happened to them.")
GA_ID = "G-GQX7R9W80G"
HUB_TAG_COUNT = 8
RELATED_COUNT = 5
MAX_AUTO_LINKS = 4
WORDS_PER_MINUTE = 230
DEFAULT_OG_IMAGE = f"{BASE_URL}/og-image.png"
LOGO = f"{BASE_URL}/logo-512.png"

HUB_PAGES = {
    # file            window id in the SPA    title bar                 page <title>
    "about.html":   ("about-window",     "ℹ️ About This Site",      "About 404 Memory Found"),
    "privacy.html": ("privacy-window",   "📄 Privacy Policy",       "Privacy Policy"),
    "terms.html":   ("terms-window",     "📋 Terms of Use",         "Terms of Use"),
    "contact.html": ("guestbook-window", "✍️ Contact & Guestbook",  "Contact 404 Memory Found"),
}
HUB_DESCRIPTIONS = {
    "about.html": "What 404 Memory Found is, who writes it under which pen names, and how to get in touch.",
    "privacy.html": "What 404 Memory Found collects, which cookies it sets, how ads work, and how to have your data removed.",
    "terms.html": "The terms that apply to reading 404 Memory Found, affiliate links, and using its guestbook and games.",
    "contact.html": "Email 404 Memory Found or sign the guestbook.",
}

# Phrases too generic to auto-link
LINK_STOPWORDS = {"history", "rise", "story", "everyone", "the", "internet", "when", "how", "why", "what", "night"}


# --------------------------------------------------------------------------- helpers

def read_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def esc(text):
    return html.escape(str(text), quote=True)


def tag_slug(tag):
    """Must match tagSlug() in src/index.html."""
    return re.sub(r"[^a-z0-9]+", "-", tag.lower().replace("&", " ")).strip("-")


def strip_tags(fragment):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment)).strip()


def word_count(body):
    return len([w for w in strip_tags(body).split(" ") if w])


def reading_label(body):
    """Must match getReadingTime() in src/index.html (Math.round semantics)."""
    minutes = max(1, int(word_count(body) / WORDS_PER_MINUTE + 0.5))
    return f"{minutes} min read"


def content_hash(*parts):
    h = hashlib.sha1()
    for p in parts:
        h.update(p.encode("utf-8"))
    return h.hexdigest()[:8]


def extract_css(source):
    m = re.search(r"<style>(.*?)</style>", source, re.DOTALL)
    return m.group(1).strip() if m else ""


def extract_javascript(source):
    start = source.rfind("<script>")
    end = source.find("</script>", start)
    return source[start + len("<script>"):end].strip() if start != -1 and end != -1 else ""


def extract_div_by_marker(source, marker):
    """Return the <div ...marker...>...</div> block, matching nested divs."""
    pos = source.find(marker)
    if pos == -1:
        return ""
    start = source.rfind("<div", 0, pos)
    depth, i = 0, start
    while i < len(source):
        if source.startswith("<div", i):
            depth += 1
        elif source.startswith("</div>", i):
            depth -= 1
            if depth == 0:
                return source[start:i + 6]
        i += 1
    return ""


def extract_window_content(source, window_id):
    """Inner HTML of <div class="window-content"> for a given window id."""
    block = extract_div_by_marker(source, f'id="{window_id}"')
    m = re.search(r'<div class="window-content"[^>]*>(.*)<div class="resize-handle resize-handle-n">', block, re.DOTALL)
    if not m:
        return ""
    inner = m.group(1).rstrip()
    return inner[:inner.rfind("</div>")] if inner.endswith("</div>") else inner


def extract_head_bits(source):
    csp = re.search(r'<meta http-equiv="Content-Security-Policy"[^>]*>', source)
    favicons = re.findall(r'<link rel="(?:icon|apple-touch-icon)"[^>]*>', source)
    return (csp.group(0) if csp else ""), "\n    ".join(favicons)


# --------------------------------------------------------------------------- images

def is_dead(info):
    """Only a confirmed 400/404 from Commons removes an image; rate limits and transient errors keep the hotlink."""
    return bool(info) and info.get("status") == "missing" and info.get("http") in (400, 404)


def credit_link(info):
    if info and info.get("commons"):
        return f'<a class="img-credit" href="{info["commons"]}" rel="noopener" target="_blank">Image: Wikimedia Commons</a>'
    return ""


def localize_images(body, manifest):
    """Point <img> tags at self-hosted copies, add dimensions, credit Wikimedia; drop dead images."""
    def fix_img(m):
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag)
        if not src:
            return tag
        info = manifest.get(src.group(1))
        if not info or info.get("status") != "ok":
            return "" if is_dead(info) else tag  # gone from Commons: remove; unknown or transient: keep hotlink
        tag = tag.replace(src.group(0), f'src="{info["file"]}"')
        tag = re.sub(r'\s(width|height)="[^"]*"', "", tag)
        tag = tag.replace("<img", f'<img width="{info["width"]}" height="{info["height"]}"', 1)
        if "loading=" not in tag:
            tag = tag.replace("<img", '<img loading="lazy" decoding="async"', 1)
        return tag

    def fix_figure(m):
        fig = m.group(0)
        img = re.search(r"<img[^>]*>", fig)
        if not img:
            return fig
        src = re.search(r'src="([^"]+)"', img.group(0))
        info = manifest.get(src.group(1)) if src else None
        if is_dead(info):
            return ""  # image gone from Commons: drop the whole figure
        fig = fig.replace(img.group(0), fix_img(img))
        credit = credit_link(info)
        if credit and "img-credit" not in fig:
            if "</figcaption>" in fig:
                fig = fig.replace("</figcaption>", " " + credit + "</figcaption>", 1)
            else:
                fig = fig.replace("</figure>", f"<figcaption>{credit}</figcaption></figure>", 1)
        return fig

    body = re.sub(r"<figure>.*?</figure>", fix_figure, body, flags=re.DOTALL)
    body = re.sub(r"<img[^>]*>", fix_img, body)
    return body


# --------------------------------------------------------------------------- monetization

def monetize_links(body, config):
    """Append affiliate ids to eBay / Amazon links and mark them sponsored. No-op until ids are configured."""
    ebay = config.get("ebay_campaign_id") or ""
    amazon = config.get("amazon_tag") or ""
    if not ebay and not amazon:
        return body

    def fix(m):
        tag = m.group(0)
        href = re.search(r'href="([^"]+)"', tag)
        if not href:
            return tag
        url = href.group(1)
        host = urlparse(url).netloc.lower()
        params = None
        if ebay and host.endswith("ebay.com"):
            params = {"mkcid": "1", "mkrid": "711-53200-19255-0", "campid": ebay, "toolid": "10001", "mkevt": "1"}
        elif amazon and host.endswith("amazon.com"):
            params = {"tag": amazon}
        if not params:
            return tag
        parts = urlparse(url)
        query = dict(parse_qsl(parts.query))
        query.update(params)
        new_url = urlunparse(parts._replace(query=urlencode(query)))
        tag = tag.replace(href.group(0), f'href="{new_url}"')
        tag = re.sub(r'\srel="[^"]*"', "", tag)
        return tag.replace("<a", '<a rel="sponsored nofollow noopener" target="_blank"', 1)

    return re.sub(r"<a [^>]*>", fix, body)


def verification_meta(config):
    """Site-verification tags for Search Console, Bing Webmaster Tools and Pinterest, pasted into site-config.json."""
    tags = []
    if config.get("google_verification"):
        tags.append(f'<meta name="google-site-verification" content="{esc(config["google_verification"])}">')
    if config.get("bing_verification"):
        tags.append(f'<meta name="msvalidate.01" content="{esc(config["bing_verification"])}">')
    if config.get("pinterest_verification"):
        tags.append(f'<meta name="p:domain_verify" content="{esc(config["pinterest_verification"])}">')
    return "".join("\n    " + t for t in tags)


def adsense_head(config):
    client = config.get("adsense_client") or ""
    if not client:
        return ""
    return (f'\n    <meta name="google-adsense-account" content="{client}">'
            f'\n    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={client}" '
            'crossorigin="anonymous"></script>')


# --------------------------------------------------------------------------- posts

def link_phrase_from_title(title):
    """'What Happened to the Game Genie, the $50 ...' -> 'Game Genie'. Used for automatic internal links."""
    m = re.match(r"What Happened to (?:the |a )?(.+?)(?:[,:?]| the | and |\s\(|$)", title, re.I)
    if not m:
        return None
    phrase = m.group(1).strip().rstrip(".")
    words = phrase.split()
    if not 1 <= len(words) <= 4 or len(phrase) < 4:
        return None
    if all(w.lower() in LINK_STOPWORDS for w in words):
        return None
    return phrase


def link_phrases(post):
    explicit = post.get("linkPhrases") or []
    if explicit:
        return [p for p in explicit if len(p) >= 3]
    auto = link_phrase_from_title(post["title"])
    return [auto] if auto else []


def add_internal_links(body, post, phrase_index):
    """Link the first plain-text mention of another post's subject. Skips headings, existing links, captions."""
    already = set(re.findall(r'href="/posts/([^".]+)\.html"', body))
    added = 0
    # Split into tag / text tokens and track context
    tokens = re.split(r"(<[^>]+>)", body)
    depth_skip = 0  # inside <a>, <h1-3>, <figcaption>, <aside>
    out = []
    for tok in tokens:
        if tok.startswith("<"):
            name = re.match(r"</?([a-zA-Z0-9]+)", tok)
            tag = name.group(1).lower() if name else ""
            if tag in ("a", "h1", "h2", "h3", "figcaption", "aside", "code"):
                depth_skip += -1 if tok.startswith("</") else 1
                depth_skip = max(0, depth_skip)
            out.append(tok)
            continue
        if depth_skip or added >= MAX_AUTO_LINKS or not tok.strip():
            out.append(tok)
            continue
        text = tok
        for phrase, slug in phrase_index:
            if slug == post["slug"] or slug in already or added >= MAX_AUTO_LINKS:
                continue
            m = re.search(r"(?<![\w-])" + re.escape(phrase) + r"(?![\w-])", text)
            if not m:
                continue
            text = text[:m.start()] + f'<a href="/posts/{slug}.html">{m.group(0)}</a>' + text[m.end():]
            already.add(slug)
            added += 1
        out.append(text)
    return "".join(out)


def load_posts(manifest, authors, config):
    data = read_json("posts.json", {"posts": []})
    posts = []
    for raw in data["posts"]:
        p = dict(raw)
        p["slug"] = p["id"]
        p["tags"] = p.get("tags") or []
        key = p.get("author") if p.get("author") in authors else None
        p["authorKey"] = key
        p["authorName"] = authors[key]["name"] if key else BLOG_NAME
        p["body"] = monetize_links(localize_images(p["body"], manifest), config)
        p["wordCount"] = word_count(p["body"])
        p["readingTime"] = reading_label(p["body"] + " " + (p.get("summary") or ""))
        seo = p.get("seo") or {}
        p["pageTitle"] = seo.get("title") or f"{p['title']} | {BLOG_NAME}"
        p["metaDescription"] = seo.get("description") or p["excerpt"]
        hero = manifest.get(p.get("image") or "", {})
        p["heroLocal"] = hero.get("file") if hero.get("status") == "ok" else None
        p["heroInfo"] = hero if hero.get("status") == "ok" else None
        p["thumb"] = hero.get("thumb") if hero.get("status") == "ok" else None
        if is_dead(hero):
            p["image"] = None  # hero gone from Commons: grey placeholder instead of a broken request
        p["heroUrl"] = f"{BASE_URL}{p['heroLocal']}" if p["heroLocal"] else (p.get("image") or None)
        og_local = os.path.join(OUTPUT_DIR, "og", f"{p['slug']}.png")
        p["ogImage"] = f"{BASE_URL}/og/{p['slug']}.png" if os.path.exists(og_local) else DEFAULT_OG_IMAGE
        p["url"] = f"{BASE_URL}/posts/{p['slug']}.html"
        p["path"] = f"/posts/{p['slug']}.html"
        posts.append(p)
    posts.sort(key=lambda x: x["date"], reverse=True)

    # Automatic internal links, longest phrases first so "Game Boy Camera" wins over "Game Boy"
    index = sorted(((ph, p["slug"]) for p in posts for ph in link_phrases(p)), key=lambda t: -len(t[0]))
    for p in posts:
        p["body"] = add_internal_links(p["body"], p, index)
    return posts


def top_tags(posts):
    counts = {}
    for p in posts:
        for t in p["tags"]:
            counts[t] = counts.get(t, 0) + 1
    return [t for t, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:HUB_TAG_COUNT]]


def related_posts(post, posts, count=RELATED_COUNT):
    tags = set(post["tags"])
    scored = [(len(tags & set(o["tags"])), o["date"], o) for o in posts if o["slug"] != post["slug"]]
    scored = [s for s in scored if s[0] > 0]
    scored.sort(key=lambda s: s[1], reverse=True)   # newest first...
    scored.sort(key=lambda s: -s[0])                # ...within the highest tag overlap (stable sort)
    return [s[2] for s in scored[:count]]


def extract_faq_schema(body):
    m = re.search(r"<h2[^>]*>.*?(?:FAQ|Frequently Asked).*?</h2>(.*)", body, re.DOTALL | re.IGNORECASE)
    if not m:
        return None
    section = m.group(1)
    nxt = re.search(r"<h2[^>]*>", section)
    if nxt:
        section = section[:nxt.start()]
    items = []
    for q, a in re.findall(r"<h3>(.*?)</h3>\s*<p>(.*?)</p>", section, re.DOTALL):
        q, a = strip_tags(q), strip_tags(a)
        if "?" in q and len(a) > 20:
            items.append({"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}})
    if len(items) < 2:
        return None
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": items}


# --------------------------------------------------------------------------- shared markup

def gtag_snippet():
    return f"""    <link rel="preconnect" href="https://www.googletagmanager.com" crossorigin>
    <link rel="dns-prefetch" href="https://www.googletagmanager.com">
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA_ID}');
    </script>"""


def head_html(ctx, *, title, description, canonical, og_type="website", og_image=DEFAULT_OG_IMAGE,
              extra_meta="", schemas=(), og_title=None):
    schema_tags = "\n".join(
        f'    <script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>' for s in schemas if s)
    og_title = og_title or title
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="referrer" content="no-referrer">
    {ctx['csp']}
{gtag_snippet()}{ctx['adsense']}{ctx['verification']}
    <title>{esc(title)}</title>
    <meta name="description" content="{esc(description)}">
    <link rel="canonical" href="{canonical}">
    <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
    <meta property="og:site_name" content="{BLOG_NAME}">
    <meta property="og:type" content="{og_type}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:title" content="{esc(og_title)}">
    <meta property="og:description" content="{esc(description)}">
    <meta property="og:image" content="{og_image}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{esc(og_title)}">
    <meta name="twitter:description" content="{esc(description)}">
    <meta name="twitter:image" content="{og_image}">{extra_meta}
    <link rel="alternate" type="application/rss+xml" title="{BLOG_NAME}" href="{BASE_URL}/feed.xml">
    {ctx['favicons']}
    <link rel="stylesheet" href="/assets/site.css?v={ctx['version']}">
{schema_tags}
</head>"""


def shell_html(ctx, head, *, body_class, window_icon, window_title, content, status_text, slug=""):
    """Every generated page is one open Win95 window on the desktop (full-screen window on mobile)."""
    close_js = "closeWindow('post-window'); if (window.opener || window.history.length <= 1) { window.close(); } else { window.location.href='/'; }"
    return f"""{head}
<body class="page-shell {body_class}">
    <main>
    <div class="desktop-container">
        <div class="desktop-area" onclick="document.querySelectorAll('.desktop-icon.selected').forEach(i => i.classList.remove('selected'))">
            {ctx['desktop_icons']}
            <div class="window" id="post-window" style="left:120px;top:15px;width:850px;height:620px;display:flex;">
                <div class="title-bar">
                    <div class="title-bar-title">{window_icon} <span>{esc(window_title)}</span></div>
                    <div class="title-bar-controls">
                        <button class="window-button" onclick="minimizeWindow('post-window')" aria-label="Minimize"><span class="btn-minimize"></span></button>
                        <button class="window-button" onclick="toggleMaximizeWindow('post-window')" aria-label="Maximize"><span class="btn-maximize"></span></button>
                        <button class="window-button" onclick="{close_js}" aria-label="Close"><span class="btn-close">×</span></button>
                    </div>
                </div>
                <div class="window-content">
                    <div class="page-card">
{content}
                    </div>
                </div>
                <div class="resize-handle resize-handle-n"></div>
                <div class="resize-handle resize-handle-s"></div>
                <div class="resize-handle resize-handle-e"></div>
                <div class="resize-handle resize-handle-w"></div>
                <div class="resize-handle resize-handle-ne"></div>
                <div class="resize-handle resize-handle-nw"></div>
                <div class="resize-handle resize-handle-se"></div>
                <div class="resize-handle resize-handle-sw"></div>
            </div>
        </div>
        {ctx['footer']}
        {ctx['start_menu']}
        {ctx['taskbar']}
    </div>
    <div class="mobile-footer page-mobile-footer">
        <div class="mobile-footer-left"><a href="/" class="mobile-footer-start"><span>🪟</span> Start</a></div>
        <div class="mobile-footer-status">{esc(status_text)}</div>
    </div>
    </main>
    <script>window.__BUILD__ = '{ctx['version']}'; var isPostPage = true; var postPageSlug = '{slug}';</script>
    <script src="/assets/site.js?v={ctx['version']}"></script>
</body>
</html>
"""


def nav_links_html(tags, current=None):
    items = ['<a href="/posts/">All posts</a>']
    for t in tags:
        cls = ' class="active"' if t == current else ""
        items.append(f'<a href="/tags/{tag_slug(t)}.html"{cls}>{esc(t)}</a>')
    return '<nav class="page-nav" aria-label="Browse">' + " ".join(items) + "</nav>"


def post_list_html(posts):
    items = []
    for p in posts:
        thumb = f'<span class="page-list-thumb" style="background-image:url(\'{p["thumb"]}\')"></span>' if p.get("thumb") else '<span class="page-list-thumb"></span>'
        tags = ", ".join(esc(t) for t in p["tags"][:3])
        items.append(
            f'<li><a href="{p["path"]}">{thumb}<span class="page-list-text">'
            f'<span class="page-list-title">{esc(p["title"])}</span>'
            f'<span class="page-list-meta">{p["date"]} · {esc(p["authorName"])} · {p["readingTime"]}{" · " + tags if tags else ""}</span>'
            f'<span class="page-list-excerpt">{esc(p["excerpt"])}</span></span></a></li>')
    return '<ul class="page-list">' + "\n".join(items) + "</ul>"


def author_person(ctx, key):
    a = ctx["authors"][key]
    return {"@type": "Person", "name": a["name"], "url": f"{BASE_URL}/authors/{key}.html", "description": a["bio"],
            "jobTitle": "Writer", "worksFor": {"@type": "Organization", "name": BLOG_NAME, "url": BASE_URL}}


def authors_block_html(ctx):
    cards = []
    for key, a in ctx["authors"].items():
        cards.append(f'<div class="author-card"><a class="author-name" href="/authors/{key}.html">{esc(a["name"])}</a>'
                     f'<div class="author-beat">{esc(a["beat"])}</div><p>{esc(a["bio"])}</p></div>')
    return ('<section class="authors-block"><h2>Who writes 404 Memory Found</h2>'
            '<p>The site is written by a small team under pen names. We publish no photos or personal details of our '
            'writers, only their beats. Every post is researched from primary sources, which are listed at the end of '
            'the article.</p>' + "".join(cards) + "</section>")


# --------------------------------------------------------------------------- pages

def post_extras_html(post):
    """Summary, hero image, quick facts (new-format posts). Older posts have none of these fields."""
    parts = []
    if post.get("summary"):
        parts.append(f'<p class="post-summary">{post["summary"]}</p>')
    if post.get("heroLocal") and "<img" not in post["body"]:
        info = post["heroInfo"]
        alt = esc(post.get("imageAlt") or post["title"])
        caption = post.get("imageCaption") or ""
        parts.append(
            f'<figure class="post-hero"><img src="{post["heroLocal"]}" alt="{alt}" width="{info["width"]}" '
            f'height="{info["height"]}" decoding="async"><figcaption>{caption} {credit_link(info)}</figcaption></figure>')
    facts = post.get("facts") or []
    if facts:
        rows = "".join(f'<div class="fact-row"><dt>{esc(f["label"])}</dt><dd>{f["value"]}</dd></div>' for f in facts)
        parts.append(f'<aside class="quick-facts" aria-label="Quick facts"><div class="quick-facts-title">Quick facts</div><dl>{rows}</dl></aside>')
    return "\n".join(parts)


def sources_html(post):
    sources = post.get("sources") or []
    if not sources:
        return ""
    items = "".join(
        f'<li><a href="{s["url"]}" rel="noopener" target="_blank">{esc(s["title"])}</a>'
        f' <span class="source-host">{esc(urlparse(s["url"]).netloc.replace("www.", ""))}</span></li>' for s in sources)
    return f'<section class="post-sources"><h2>Sources</h2><ul>{items}</ul></section>'


def build_post_page(ctx, post, posts):
    related = related_posts(post, posts)
    related_html = ""
    if related:
        related_html = ('<div class="related-posts"><div class="related-posts-title">Related Posts:</div>'
                        + "".join(f'<a class="related-post" href="{r["path"]}">{esc(r["title"])}</a>' for r in related)
                        + "</div>")
    tags_html = " ".join(f'<a href="/tags/{tag_slug(t)}.html">{esc(t)}</a>' for t in post["tags"] if t in ctx["tags"])
    key = post["authorKey"]
    byline = (f'<a href="/authors/{key}.html" rel="author">{esc(post["authorName"])}</a>' if key else esc(post["authorName"]))
    disclosure = ""
    if 'rel="sponsored' in post["body"] and ctx["config"].get("affiliate_disclosure"):
        disclosure = f'<p class="affiliate-disclosure">{esc(ctx["config"]["affiliate_disclosure"])}</p>'

    content = f"""<a class="page-back page-back-mobile" href="/">&larr; Back</a>
<article class="post-article">
    <header class="post-header">
        <h1>{esc(post['title'])}</h1>
        <div class="post-meta"><time datetime="{post['date']}">{post['date']}</time> | By {byline} | <span class="reading-time">{post['readingTime']}</span></div>
    </header>
    {post_extras_html(post)}
    <div class="post-body">
{post['body']}
    </div>
    {sources_html(post)}
    {disclosure}
    <footer class="post-footer">
        {'<div class="post-tags">Filed under: ' + tags_html + '</div>' if tags_html else ''}
        {related_html}
        <div class="page-back-row"><a class="page-back page-back-desktop" href="/">&larr; Back to Blog</a> <a class="page-back" href="/posts/">All posts</a></div>
    </footer>
</article>"""

    images = [post["ogImage"]] + ([post["heroUrl"]] if post.get("heroUrl") else [])
    author_schema = author_person(ctx, key) if key else {"@type": "Organization", "name": BLOG_NAME, "url": BASE_URL}
    blog_posting = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post["title"],
        "description": post["metaDescription"],
        "datePublished": post["date"],
        "dateModified": post.get("updated") or post["date"],
        "image": images,
        "wordCount": post["wordCount"],
        "keywords": post["tags"],
        "articleSection": post["tags"][0] if post["tags"] else "Technology",
        "author": author_schema,
        "publisher": {"@type": "Organization", "name": BLOG_NAME, "url": BASE_URL,
                      "logo": {"@type": "ImageObject", "url": LOGO, "width": 512, "height": 512}},
        "mainEntityOfPage": {"@type": "WebPage", "@id": post["url"]},
        "url": post["url"],
    }
    if post.get("sources"):
        blog_posting["citation"] = [s["url"] for s in post["sources"]]
    breadcrumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": "All posts", "item": f"{BASE_URL}/posts/"},
            {"@type": "ListItem", "position": 3, "name": post["title"], "item": post["url"]},
        ],
    }
    extra = (f'\n    <meta property="article:published_time" content="{post["date"]}T00:00:00Z">'
             f'\n    <meta property="article:modified_time" content="{post.get("updated") or post["date"]}T00:00:00Z">'
             f'\n    <meta property="article:section" content="{esc(post["tags"][0] if post["tags"] else "Technology")}">'
             + "".join(f'\n    <meta property="article:tag" content="{esc(t)}">' for t in post["tags"])
             + f'\n    <meta name="author" content="{esc(post["authorName"])}">')
    head = head_html(ctx, title=post["pageTitle"], description=post["metaDescription"], canonical=post["url"],
                     og_type="article", og_image=post["ogImage"], extra_meta=extra, og_title=post["title"],
                     schemas=(blog_posting, breadcrumbs, extract_faq_schema(post["body"])))
    return shell_html(ctx, head, body_class="post-page", window_icon="📖", window_title=post["title"],
                      content=content, status_text=post["date"], slug=post["slug"])


def build_hub_page(ctx, filename, posts):
    window_id, bar_title, page_title = HUB_PAGES[filename]
    inner = extract_window_content(ctx["source"], window_id)
    if filename == "contact.html":
        inner = ('<h2>Contact</h2><p>Email <a href="mailto:hello@404memoryfound.com">hello@404memoryfound.com</a> '
                 'for corrections, story ideas, or anything else. Or leave a note in the guestbook below.</p>'
                 '<h3>Sign the guestbook</h3>' + inner)
    inner = re.sub(r"<h2([^>]*)>(.*?)</h2>", r"<h1\1>\2</h1>", inner, count=1)
    if filename == "about.html":
        inner += authors_block_html(ctx)
    if filename == "terms.html":
        inner += ('<h3 style="font-size:14px;margin:10px 0 4px 0;">Affiliate links and advertising</h3>'
                  '<p style="font-size:13px;margin-bottom:8px;">' + esc(ctx["config"].get("affiliate_disclosure", "")) +
                  ' Pages may also carry advertising served by Google AdSense; those ads are labelled and never influence what we write.</p>')
    if filename == "privacy.html":
        inner += ('<h3 style="font-size:14px;margin:10px 0 4px 0;">Advertising</h3>'
                  '<p style="font-size:13px;margin-bottom:8px;">When advertising is enabled, Google AdSense and its partners may use '
                  'cookies to serve ads based on your prior visits to this or other websites. You can opt out of personalised '
                  'advertising at <a href="https://www.google.com/settings/ads" style="color:#0000ff;">Google Ads Settings</a>.</p>')
    content = f'<a class="page-back page-back-mobile" href="/">&larr; Back</a>\n<div class="page-copy">{inner}</div>\n' \
              f'{nav_links_html(ctx["tags"])}'
    url = f"{BASE_URL}/{filename}"
    head = head_html(ctx, title=f"{page_title} | {BLOG_NAME}", description=HUB_DESCRIPTIONS[filename], canonical=url,
                     schemas=({"@context": "https://schema.org", "@type": "WebPage", "name": page_title, "url": url},))
    icon, _, title_text = bar_title.partition(" ")
    return shell_html(ctx, head, body_class="hub-page", window_icon=icon, window_title=title_text, content=content,
                      status_text=f"{len(posts)} posts")


def build_author_page(ctx, key, posts):
    a = ctx["authors"][key]
    mine = [p for p in posts if p["authorKey"] == key]
    url = f"{BASE_URL}/authors/{key}.html"
    content = (f'<a class="page-back page-back-mobile" href="/">&larr; Back</a>\n'
               f'<h1>{esc(a["name"])}</h1>\n<p class="author-beat">{esc(a["beat"])}</p>\n'
               f'<p class="page-intro">{esc(a["bio"])} {esc(a["name"])} is a pen name; 404 Memory Found publishes no photos '
               f'or personal details of its writers.</p>\n{nav_links_html(ctx["tags"])}\n'
               f'<h2>{len(mine)} posts by {esc(a["name"])}</h2>\n{post_list_html(mine)}')
    schema = dict(author_person(ctx, key))
    schema["@context"] = "https://schema.org"
    schema["mainEntityOfPage"] = url
    head = head_html(ctx, title=f"{a['name']} | {BLOG_NAME}", canonical=url,
                     description=f"{a['name']} writes about {a['beat'].lower()} for {BLOG_NAME}. {len(mine)} posts.",
                     schemas=(schema,))
    return shell_html(ctx, head, body_class="hub-page", window_icon="✍️", window_title=a["name"], content=content,
                      status_text=f"{len(mine)} posts")


def build_posts_index_page(ctx, posts):
    by_month = {}
    for p in posts:
        by_month.setdefault(p["date"][:7], []).append(p)
    sections = []
    for key in sorted(by_month, reverse=True):
        label = datetime.strptime(key, "%Y-%m").strftime("%B %Y")
        sections.append(f"<h2>{label}</h2>\n{post_list_html(by_month[key])}")
    content = (f'<a class="page-back page-back-mobile" href="/">&larr; Back</a>\n'
               f'<h1>All posts</h1>\n<p class="page-intro">{len(posts)} stories about the technology, games and websites '
               f'of the 90s and 2000s, newest first.</p>\n{nav_links_html(ctx["tags"])}\n' + "\n".join(sections))
    url = f"{BASE_URL}/posts/"
    schema = {"@context": "https://schema.org", "@type": "CollectionPage", "name": f"All posts | {BLOG_NAME}", "url": url,
              "mainEntity": {"@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": i + 1, "url": p["url"], "name": p["title"]} for i, p in enumerate(posts)]}}
    head = head_html(ctx, title=f"All posts | {BLOG_NAME}", canonical=url,
                     description=f"Every story on {BLOG_NAME}: {len(posts)} articles about 90s and 2000s technology, games, websites and companies.",
                     schemas=(schema,))
    return shell_html(ctx, head, body_class="hub-page", window_icon="📝", window_title="All posts", content=content,
                      status_text=f"{len(posts)} posts")


def build_tag_page(ctx, tag, posts):
    tagged = [p for p in posts if tag in p["tags"]]
    url = f"{BASE_URL}/tags/{tag_slug(tag)}.html"
    content = (f'<a class="page-back page-back-mobile" href="/">&larr; Back</a>\n'
               f'<h1>{esc(tag)}</h1>\n<p class="page-intro">{len(tagged)} posts filed under {esc(tag)}.</p>\n'
               f'{nav_links_html(ctx["tags"], current=tag)}\n{post_list_html(tagged)}')
    schema = {"@context": "https://schema.org", "@type": "CollectionPage", "name": f"{tag} | {BLOG_NAME}", "url": url,
              "mainEntity": {"@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": i + 1, "url": p["url"], "name": p["title"]} for i, p in enumerate(tagged)]}}
    head = head_html(ctx, title=f"{tag} | {BLOG_NAME}", canonical=url,
                     description=f"{len(tagged)} stories about {tag.lower()} from the 90s and 2000s on {BLOG_NAME}.",
                     schemas=(schema,))
    return shell_html(ctx, head, body_class="hub-page", window_icon="📁", window_title=tag, content=content,
                      status_text=f"{len(tagged)} posts")


def build_404_page(ctx, posts):
    latest = post_list_html(posts[:5])
    content = (f'<a class="page-back page-back-mobile" href="/">&larr; Back</a>\n'
               '<h1>404: this memory was not found</h1>\n'
               '<p class="page-intro">The page you asked for is not here. It may have moved, or it never existed. '
               'Try the <a href="/posts/">list of every post</a>, or start with one of the latest:</p>\n' + latest
               + nav_links_html(ctx["tags"]))
    head = head_html(ctx, title=f"Page not found | {BLOG_NAME}", description="This page does not exist on 404 Memory Found.",
                     canonical=f"{BASE_URL}/404.html")
    head = head.replace('<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">',
                        '<meta name="robots" content="noindex">')
    return shell_html(ctx, head, body_class="hub-page", window_icon="❌", window_title="Page not found", content=content,
                      status_text="404")


def build_redirect_stub(old_slug, target):
    url = target["url"]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{esc(target['title'])}</title>
    <link rel="canonical" href="{url}">
    <meta http-equiv="refresh" content="0; url={url}">
</head>
<body>
    <p>This post moved to <a href="{url}">{esc(target['title'])}</a>.</p>
</body>
</html>
"""


# --------------------------------------------------------------------------- homepage

def render_desktop_list(posts):
    items = []
    for p in posts:
        thumb = p.get("thumb") or p.get("image") or ""
        data_attr = f' data-bg="{thumb}"' if thumb else ""
        items.append(f"""
                <li class="blog-post-item">
                    <a href="{p['path']}" onclick="event.preventDefault(); openPost('{p['slug']}')">
                        <div class="blog-post-thumb"{data_attr} style="background-color:#c0c0c0;"></div>
                        <div class="blog-post-text">
                            <h3>{esc(p['title'])}</h3>
                            <div class="date">{p['date']} <span class="reading-time">{p['readingTime']}</span></div>
                            <div class="excerpt">{esc(p['excerpt'])}</div>
                            <div class="tags">{esc(', '.join(p['tags']))}</div>
                        </div>
                    </a>
                </li>""")
    return "".join(items)


def render_mobile_list(posts):
    items = []
    for p in posts:
        thumb = p.get("thumb") or p.get("image") or ""
        data_attr = f' data-bg="{thumb}"' if thumb else ""
        items.append(f"""
                <li class="mobile-post-item">
                    <a href="{p['path']}" onclick="event.preventDefault(); openPost('{p['slug']}')">
                    <div class="mobile-post-thumb"{data_attr} style="background-color:#c0c0c0;"></div>
                    <div class="mobile-post-info">
                        <h3>{esc(p['title'])}</h3>
                        <div class="mobile-post-date">{p['date']} · {p['readingTime']}</div>
                        <div class="mobile-post-excerpt">{esc(p['excerpt'])}</div>
                        <div class="mobile-post-tags">{esc(' · '.join(p['tags'][:3]))}</div>
                    </div>
                    </a>
                </li>""")
    return "".join(items)


def render_tag_filters(tags, cls, fn):
    return "".join(
        f'\n                <a class="{cls}" href="/tags/{tag_slug(t)}.html" onclick="event.preventDefault(); {fn}(\'{esc(t)}\')">{esc(t)}</a>'
        for t in tags)


def render_archives(posts):
    by_month = {}
    for p in posts:
        by_month.setdefault(p["date"][:7], []).append(p)
    out = []
    for key in sorted(by_month, reverse=True):
        label = datetime.strptime(key, "%Y-%m").strftime("%B %Y")
        entries = "".join(
            f"""
                            <li class="archive-post">
                                <a href="{p['path']}" onclick="event.preventDefault(); openPost('{p['slug']}')">
                                    <div class="title">{esc(p['title'])}</div>
                                    <div class="date">{p['date']}</div>
                                </a>
                            </li>""" for p in by_month[key])
        out.append(f"""
                <li class="archive-tag">
                    <div class="archive-tag-name">📅 {label}</div>
                    <ul class="archive-posts">{entries}
                    </ul>
                </li>""")
    return "".join(out)


def build_index_html(ctx, posts):
    source = ctx["source"]
    tags = ctx["tags"]
    blog_schema = {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": BLOG_NAME,
        "description": DEFAULT_DESCRIPTION,
        "url": BASE_URL + "/",
        "image": DEFAULT_OG_IMAGE,
        "publisher": {"@type": "Organization", "name": BLOG_NAME, "url": BASE_URL,
                      "logo": {"@type": "ImageObject", "url": LOGO}},
        "blogPost": [{"@type": "BlogPosting", "headline": p["title"], "url": p["url"], "datePublished": p["date"],
                      "author": {"@type": "Person", "name": p["authorName"]}}
                     for p in posts[:20]],
    }
    website_schema = {"@context": "https://schema.org", "@type": "WebSite", "name": BLOG_NAME, "url": BASE_URL + "/"}
    seo_meta = f"""    <meta name="description" content="{esc(DEFAULT_DESCRIPTION)}">
    <link rel="canonical" href="{BASE_URL}/">
    <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
    <meta property="og:site_name" content="{BLOG_NAME}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{BASE_URL}/">
    <meta property="og:title" content="{BLOG_NAME} - Windows 95 Nostalgia Blog">
    <meta property="og:description" content="{esc(DEFAULT_DESCRIPTION)}">
    <meta property="og:image" content="{DEFAULT_OG_IMAGE}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{BLOG_NAME}">
    <meta name="twitter:description" content="{esc(DEFAULT_DESCRIPTION)}">
    <meta name="twitter:image" content="{DEFAULT_OG_IMAGE}">
    <link rel="alternate" type="application/rss+xml" title="{BLOG_NAME}" href="{BASE_URL}/feed.xml">{ctx['adsense']}{ctx['verification']}
    <script type="application/ld+json">{json.dumps(website_schema, ensure_ascii=False)}</script>
    <script type="application/ld+json">{json.dumps(blog_schema, ensure_ascii=False)}</script>
    <script type="application/ld+json" id="schema-markup"></script>"""

    out = source.replace("    <!-- SEO meta tags are injected by build.py - do not duplicate here -->", seo_meta, 1)
    if ctx["adsense"]:
        out = re.sub(r'\s*<meta http-equiv="Content-Security-Policy"[^>]*>', "", out, count=1)

    # External assets instead of inline CSS/JS
    out = re.sub(r"<style>.*?</style>", f'<link rel="stylesheet" href="/assets/site.css?v={ctx["version"]}">', out, count=1, flags=re.DOTALL)
    start = out.rfind("<script>")
    end = out.find("</script>", start) + len("</script>")
    out = out[:start] + f"<script>window.__BUILD__ = '{ctx['version']}';</script>\n    <script src=\"/assets/site.js?v={ctx['version']}\"></script>" + out[end:]

    # Pre-rendered lists: crawlable before any JavaScript runs; the SPA re-renders the same markup after it loads
    replacements = [
        ('<ul class="blog-posts-list" id="blog-posts-list"></ul>',
         f'<ul class="blog-posts-list" id="blog-posts-list">{render_desktop_list(posts)}\n                    </ul>'),
        ('<ul class="mobile-post-list" id="mobile-post-list"></ul>',
         f'<ul class="mobile-post-list" id="mobile-post-list">{render_mobile_list(posts)}\n            </ul>'),
        ('<div class="blog-filters" id="tag-filters" role="group" aria-label="Filter by tag"></div>',
         f'<div class="blog-filters" id="tag-filters" role="group" aria-label="Filter by tag">{render_tag_filters(tags, "tag-button", "toggleTag")}\n                    </div>'),
        ('<div class="mobile-tag-filters" id="mobile-tag-filters" role="group" aria-label="Filter by tag"></div>',
         f'<div class="mobile-tag-filters" id="mobile-tag-filters" role="group" aria-label="Filter by tag">{render_tag_filters(tags, "mobile-tag-btn", "toggleMobileTag")}\n            </div>'),
        ('<ul class="archives-list" id="archives-list"></ul>',
         f'<ul class="archives-list" id="archives-list">{render_archives(posts)}\n                    </ul>'),
    ]
    for old, new in replacements:
        if old not in out:
            raise SystemExit(f"build: expected placeholder not found in src/index.html: {old}")
        out = out.replace(old, new, 1)
    return out


# --------------------------------------------------------------------------- feeds and data

def build_sitemap(posts, tags, authors, today):
    latest = posts[0]["date"] if posts else today

    def url(loc, lastmod, freq, prio):
        return f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>{freq}</changefreq>\n    <priority>{prio}</priority>\n  </url>\n"

    body = url(f"{BASE_URL}/", latest, "daily", "1.0")
    body += url(f"{BASE_URL}/posts/", latest, "daily", "0.9")
    for t in tags:
        tagged = [p for p in posts if t in p["tags"]]
        body += url(f"{BASE_URL}/tags/{tag_slug(t)}.html", tagged[0]["date"] if tagged else latest, "weekly", "0.7")
    for p in posts:
        body += url(p["url"], p.get("updated") or p["date"], "monthly", "0.8")
    for key in authors:
        mine = [p for p in posts if p["authorKey"] == key]
        body += url(f"{BASE_URL}/authors/{key}.html", mine[0]["date"] if mine else latest, "weekly", "0.4")
    for page in ("about.html", "contact.html", "privacy.html", "terms.html"):
        body += url(f"{BASE_URL}/{page}", latest, "yearly", "0.3")
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "</urlset>\n"


def build_feed(posts):
    def rfc822(date):
        return format_datetime(datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc))

    items = []
    for p in posts[:20]:
        cats = "".join(f"      <category>{esc(t)}</category>\n" for t in p["tags"])
        media = ""
        og_local = os.path.join(OUTPUT_DIR, "og", f"{p['slug']}.png")
        if os.path.exists(og_local):
            size = os.path.getsize(og_local)
            media = (f'      <enclosure url="{p["ogImage"]}" length="{size}" type="image/png"/>\n'
                     f'      <media:content url="{p["ogImage"]}" medium="image" type="image/png" width="1200" height="630"/>\n')
        items.append(f"""    <item>
      <title>{esc(p['title'])}</title>
      <link>{p['url']}</link>
      <guid isPermaLink="true">{p['url']}</guid>
      <pubDate>{rfc822(p['date'])}</pubDate>
      <dc:creator>{esc(p['authorName'])}</dc:creator>
      <description>{esc(p['excerpt'])}</description>
{media}{cats}    </item>""")
    latest = rfc822(posts[0]["date"]) if posts else rfc822("2026-01-01")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>{BLOG_NAME}</title>
    <link>{BASE_URL}/</link>
    <description>{esc(DEFAULT_DESCRIPTION)}</description>
    <language>en</language>
    <lastBuildDate>{latest}</lastBuildDate>
    <atom:link href="{BASE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(items)}
  </channel>
</rss>
"""


def posts_index_json(posts):
    return {"posts": [{
        "id": p["slug"], "title": p["title"], "date": p["date"], "excerpt": p["excerpt"], "tags": p["tags"],
        "image": p.get("heroLocal") or p.get("image"), "thumb": p.get("thumb") or p.get("heroLocal") or p.get("image"),
        "readingTime": p["readingTime"], "authorName": p["authorName"], "authorKey": p["authorKey"],
    } for p in posts]}


def post_json(p):
    """Body for the in-app view: summary, hero and quick facts inlined so the desktop window shows the same article."""
    body = post_extras_html(p) + "\n" + p["body"] + "\n" + sources_html(p)
    return {"id": p["slug"], "title": p["title"], "date": p["date"], "tags": p["tags"], "readingTime": p["readingTime"],
            "authorName": p["authorName"], "body": body}


# --------------------------------------------------------------------------- CSS for generated pages

PAGE_SHELL_CSS = """
/* ---- Generated pages (posts, tags, authors, about...): one open window, article rendered once ---- */
.page-shell .page-back { display: inline-block; padding: 5px 12px; background: #c0c0c0; color: #000; text-decoration: none;
    border: 2px solid; border-top-color: #fff; border-left-color: #fff; border-right-color: #808080; border-bottom-color: #808080;
    font-family: "MS Sans Serif", Tahoma, Arial, sans-serif; font-size: 13px; margin: 0 6px 10px 0; }
.page-shell .page-back:active { border-top-color: #808080; border-left-color: #808080; border-right-color: #fff; border-bottom-color: #fff; }
.page-shell .page-back-row { margin-top: 16px; }
.page-shell .post-tags { margin: 18px 0 6px; font-size: 13px; color: #444; }
.page-shell .post-tags a { color: #000080; margin-left: 4px; }
.page-shell .post-meta a { color: #000080; }
.page-shell .img-credit { font-size: 11px; color: #666; text-decoration: none; margin-left: 6px; }
.page-shell .img-credit:hover { text-decoration: underline; }
.page-shell .post-body figure, .page-shell .post-hero { margin: 16px auto; max-width: 560px; }
.page-shell .post-body figure img, .page-shell .post-hero img { max-width: 100%; height: auto; display: block; }
.page-shell .post-body figcaption, .page-shell .post-hero figcaption { font-size: 12px; color: #555; margin-top: 4px; line-height: 1.4; }
.page-shell .page-copy h1, .page-shell .hub-page h1 { font-size: 20px; color: #000080; margin-bottom: 8px; line-height: 1.3; }
.page-shell .page-intro { margin-bottom: 12px; color: #333; }
.page-shell .author-beat { font-size: 13px; color: #666; margin-bottom: 8px; }
.page-shell .page-nav { display: flex; flex-wrap: wrap; gap: 4px; margin: 8px 0 14px; }
.page-shell .page-nav a { padding: 2px 8px; background: #dfdfdf; color: #000; text-decoration: none; font-size: 13px;
    border: 2px solid; border-top-color: #fff; border-left-color: #fff; border-right-color: #808080; border-bottom-color: #808080;
    font-family: "MS Sans Serif", Tahoma, Arial, sans-serif; }
.page-shell .page-nav a.active { background: #000080; color: #fff; }
.page-shell .hub-page h2 { font-size: 15px; margin: 16px 0 6px; color: #000080; }
.page-shell .page-list { list-style: none; margin: 0; padding: 0; }
.page-shell .page-list li { background: #fff; border-bottom: 1px solid #c0c0c0; margin-bottom: 4px; }
.page-shell .page-list li:hover { background: #e8e8ff; }
.page-shell .page-list a { display: flex; align-items: stretch; color: inherit; text-decoration: none; }
.page-shell .page-list-thumb { width: 72px; min-height: 58px; flex-shrink: 0; background: #c0c0c0 center / contain no-repeat; border-right: 1px solid #a0a0a0; }
.page-shell .page-list-text { flex: 1; min-width: 0; padding: 8px; display: block; }
.page-shell .page-list-title { display: block; font-size: 14px; font-weight: bold; color: #0000ff; }
.page-shell .page-list-meta { display: block; font-size: 11px; color: #666; margin-top: 2px; }
.page-shell .page-list-excerpt { display: block; font-size: 12px; color: #333; margin-top: 3px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.page-shell .page-copy p, .page-shell .page-copy h3 { margin-bottom: 8px; }
.page-shell .page-copy h3 { margin-top: 12px; }
.page-shell .authors-block { margin-top: 18px; padding-top: 12px; border-top: 1px solid #c0c0c0; }
.page-shell .author-card { background: #fff; border: 1px solid #c0c0c0; padding: 8px 10px; margin: 8px 0; }
.page-shell .author-name { font-weight: bold; color: #000080; text-decoration: none; font-size: 14px; }
.page-shell .author-card .author-beat { margin: 2px 0 4px; }
.page-shell .author-card p { font-size: 13px; margin: 0; }

/* New-format post parts: summary, quick facts, sources (also rendered inside the desktop post window) */
.post-summary { font-size: 1.05em; line-height: 1.55; padding: 10px 12px; margin: 0 0 12px; background: #ffffe1;
    border: 1px solid #c8c86a; border-left: 4px solid #000080; }
.quick-facts { background: #f4f4f4; border: 1px solid #a0a0a0; padding: 8px 12px; margin: 12px 0 16px; font-size: 13px; }
.quick-facts-title { font-weight: bold; margin-bottom: 6px; color: #000080; font-family: "MS Sans Serif", Tahoma, Arial, sans-serif; }
.quick-facts dl { margin: 0; }
.quick-facts .fact-row { display: flex; gap: 8px; padding: 3px 0; border-top: 1px dotted #c0c0c0; }
.quick-facts .fact-row:first-child { border-top: 0; }
.quick-facts dt { flex: 0 0 34%; font-weight: bold; color: #333; margin: 0; }
.quick-facts dd { flex: 1; margin: 0; }
.post-sources { margin-top: 20px; padding-top: 10px; border-top: 1px solid #c0c0c0; font-size: 13px; }
.post-sources h2 { font-size: 15px; margin-bottom: 6px; }
.post-sources ul { margin: 0; padding-left: 18px; }
.post-sources li { margin-bottom: 4px; }
.post-sources a { color: #000080; }
.source-host { color: #777; font-size: 11px; margin-left: 4px; }
.affiliate-disclosure { font-size: 11px; color: #666; margin-top: 10px; font-style: italic; }

@media (min-width: 769px) {
    .page-shell .page-back-mobile { display: none; }
    .page-shell .page-mobile-footer { display: none; }
    .page-shell .post-header h1 { font-size: 20px; line-height: 1.3; }
    .page-shell .post-meta { font-size: 13px; }
    .page-shell .post-body { user-select: text; }
    .page-shell .page-card { padding: 4px 8px; }
}

@media (max-width: 768px) {
    .page-shell .desktop-container { display: flex; flex-direction: column; height: 100vh; }
    .page-shell .desktop-area { flex: 1; min-height: 0; display: flex; flex-direction: column; position: relative; }
    .page-shell .desktop-icons, .page-shell .taskbar, .page-shell .footer, .page-shell .start-menu,
    .page-shell .resize-handle, .page-shell .window-button { display: none !important; }
    .page-shell #post-window { position: static !important; left: auto !important; top: auto !important;
        width: 100% !important; height: 100% !important; flex: 1; min-height: 0; display: flex !important; flex-direction: column; background: #008080; }
    .page-shell .title-bar { background: linear-gradient(90deg, #000080 0%, #1084d0 100%); color: #fff; padding: 8px 12px;
        display: flex; align-items: center; justify-content: space-between; flex-shrink: 0;
        font-family: "MS Sans Serif", Tahoma, Arial, sans-serif; border-bottom: 2px solid #000; }
    .page-shell .title-bar-title { font-size: 15px; font-weight: bold; display: flex; align-items: center; gap: 6px; overflow: hidden; min-width: 0; }
    .page-shell .title-bar-title span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .page-shell .window-content { flex: 1; min-height: 0; overflow-y: auto; -webkit-overflow-scrolling: touch; background: #c0c0c0; padding: 0; }
    .page-shell .page-card { background: #fff; margin: 6px; padding: 12px; border: 2px solid;
        border-top-color: #fff; border-left-color: #fff; border-right-color: #808080; border-bottom-color: #808080; }
    .page-shell .post-header h1 { font-size: 18px; color: #000080; margin-bottom: 4px; line-height: 1.3; font-weight: bold; }
    .page-shell .post-meta { font-size: 12px; color: #666; margin-bottom: 14px; padding-bottom: 8px; border-bottom: 1px solid #c0c0c0; }
    .page-shell .post-body { font-size: 15px; line-height: 1.7; color: #333; }
    .page-shell .post-body img, .page-shell .post-hero img { max-width: 100%; height: auto; margin: 10px 0; border: 2px solid;
        border-top-color: #808080; border-left-color: #808080; border-right-color: #fff; border-bottom-color: #fff; }
    .page-shell .post-body p { margin-bottom: 12px; }
    .page-shell .post-body h2, .page-shell .post-body h3 { margin-top: 18px; margin-bottom: 8px; color: #000080; }
    .page-shell .post-body a { color: #000080; text-decoration: underline; }
    .page-shell .related-posts { margin-top: 20px; padding-top: 12px; border-top: 2px solid #c0c0c0; }
    .page-shell .related-posts-title { font-size: 14px; font-weight: bold; color: #000; margin-bottom: 8px; }
    .page-shell a.related-post { display: block; padding: 8px; color: #000080; text-decoration: none; font-size: 13px;
        background: #f0f0f0; border: 1px solid #c0c0c0; margin-bottom: 4px; }
    .page-shell .page-back-desktop { display: none; }
    .page-shell .page-mobile-footer { display: flex; }
    .page-shell .mobile-footer-start { text-decoration: none; color: #000; }
    .page-shell .page-copy { font-size: 14px; line-height: 1.6; }
    .quick-facts dt { flex-basis: 40%; }
}
"""


# --------------------------------------------------------------------------- main

def write(path, text):
    full = os.path.join(OUTPUT_DIR, path)
    os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    print("🔨 Building 404 Memory Found...")
    with open(SOURCE_PATH, encoding="utf-8") as f:
        source = f.read()
    manifest = read_json("images-manifest.json", {})
    redirects = {k: v for k, v in read_json("redirects.json", {}).items() if not k.startswith("_")}
    authors = {k: v for k, v in read_json("authors.json", {}).items() if not k.startswith("_")}
    config = {k: v for k, v in read_json("site-config.json", {}).items() if not k.startswith("_")}
    posts = load_posts(manifest, authors, config)
    by_slug = {p["slug"]: p for p in posts}
    tags = top_tags(posts)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    css = extract_css(source) + "\n" + PAGE_SHELL_CSS
    js = extract_javascript(source)
    version = content_hash(css, js)
    csp, favicons = extract_head_bits(source)
    adsense = adsense_head(config)
    ctx = {
        "source": source, "version": version, "tags": tags, "authors": authors, "config": config,
        "csp": "" if adsense else csp,  # a meta CSP would block ad networks; drop it once ads are on
        "favicons": favicons, "adsense": adsense, "verification": verification_meta(config),
        "desktop_icons": extract_div_by_marker(source, 'class="desktop-icons">'),
        "taskbar": extract_div_by_marker(source, 'class="taskbar">'),
        "footer": extract_div_by_marker(source, 'class="footer">'),
        "start_menu": extract_div_by_marker(source, 'class="start-menu" id="start-menu">'),
    }

    print(f"📦 assets/site.css + site.js (v{version})")
    write("assets/site.css", css)
    write("assets/site.js", js)

    print("📄 index.html")
    write("index.html", build_index_html(ctx, posts))
    write("posts-index.json", json.dumps(posts_index_json(posts), ensure_ascii=False))

    auto_links = sum(len(re.findall(r'href="/posts/', p["body"])) for p in posts)
    print(f"📝 {len(posts)} posts ({auto_links} internal links in bodies)")
    for p in posts:
        write(f"posts/{p['slug']}.html", build_post_page(ctx, p, posts))
        write(f"posts/{p['slug']}.json", json.dumps(post_json(p), ensure_ascii=False))
    write("posts/index.html", build_posts_index_page(ctx, posts))

    print(f"📁 {len(tags)} tag pages: {', '.join(tags)}")
    for t in tags:
        write(f"tags/{tag_slug(t)}.html", build_tag_page(ctx, t, posts))

    print(f"✍️  {len(authors)} author pages: {', '.join(a['name'] for a in authors.values())}")
    for key in authors:
        write(f"authors/{key}.html", build_author_page(ctx, key, posts))

    print("ℹ️  about, contact, privacy, terms, 404")
    for filename in HUB_PAGES:
        write(filename, build_hub_page(ctx, filename, posts))
    write("404.html", build_404_page(ctx, posts))

    print(f"↪️  {len(redirects)} redirect stubs")
    for old, new in redirects.items():
        if new in by_slug:
            write(f"posts/{old}.html", build_redirect_stub(old, by_slug[new]))
        else:
            print(f"   ! redirect target missing for {old} -> {new}")

    keep = {f"{s}.html" for s in by_slug} | {f"{s}.json" for s in by_slug} | {f"{o}.html" for o in redirects} | {"index.html"}
    for name in os.listdir(os.path.join(OUTPUT_DIR, "posts")):
        if name not in keep and (name.endswith(".html") or name.endswith(".json")):
            os.remove(os.path.join(OUTPUT_DIR, "posts", name))
            print(f"   🗑  removed stale posts/{name}")

    print("🗺️  sitemap.xml, feed.xml, robots.txt, CNAME" + (", ads.txt" if config.get("ads_txt") else ""))
    write("sitemap.xml", build_sitemap(posts, tags, authors, today))
    write("feed.xml", build_feed(posts))
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
    write("CNAME", "404memoryfound.com")
    if config.get("ads_txt"):
        write("ads.txt", config["ads_txt"].strip() + "\n")

    dead = [u for u, v in manifest.items() if is_dead(v)]
    if dead:
        print(f"⚠️  {len(dead)} images no longer exist on Commons and are dropped from bodies (see images-manifest.json)")
    print(f"\n✅ Build complete: {len(posts)} posts, {len(tags)} tag pages, {len(authors)} author pages, "
          f"{len(HUB_PAGES) + 2} hub pages, version {version}")


if __name__ == "__main__":
    main()
