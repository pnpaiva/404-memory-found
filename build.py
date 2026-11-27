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
  og/<slug>.jpg, pins/   written by make_og_cards.py: per-post share images

Outputs (all committed, served by GitHub Pages)
  index.html             the SPA with SEO meta, pre-rendered post lists, external assets
  assets/site.css|js     the SPA's CSS and JS, cached once instead of inlined per page
  posts-index.json       lightweight list the homepage loads (no bodies)
  posts/<slug>.html      one static page per post, article rendered exactly once
  posts/index.html       crawlable list of every post
  tags/<tag>.html        one hub page per category
  authors/<key>.html     one page per pen name
  about|contact|privacy|terms.html, 404.html, feed.xml, sitemap.xml, robots.txt, CNAME, ads.txt
"""

import hashlib
import html
import csv
import io
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
DEFAULT_DESCRIPTION = ("What happened to the gadgets, games, stores and websites of the 90s and 2000s: who owns them now, "
                       "what they're worth, and how to still play, use or visit them today.")
GA_ID = "G-GQX7R9W80G"
# "Decline" on the cookie banner has to mean something: a visitor who declined gets analytics and ad
# storage denied (Google Consent Mode) and non-personalized AdSense ads, on every page, before any tag runs.
CONSENT_JS = ("var __declined=false;try{__declined=localStorage.getItem('cookie-consent')==='declined';}catch(e){}"
              "var __c=__declined?'denied':'granted';"
              "gtag('consent','default',{analytics_storage:__c,ad_storage:__c,ad_user_data:__c,ad_personalization:__c});"
              "if(__declined){(window.adsbygoogle=window.adsbygoogle||[]).requestNonPersonalizedAds=1;}")
# Visits that must not load analytics or ads: the owner (open any page once with ?noads=1 on each browser;
# ?noads=0 undoes it), automated browsers (navigator.webdriver) and non-Google crawlers that run JavaScript
# (an SEO crawler from Singapore was half of all AdSense page views). Google's own crawlers are left alone.
QUIET_JS = ("(function(){var q=false,u=navigator.userAgent||'';"
            "try{var p=new URLSearchParams(location.search).get('noads');"
            "if(p==='1')localStorage.setItem('404mf-quiet','1');if(p==='0')localStorage.removeItem('404mf-quiet');"
            "q=localStorage.getItem('404mf-quiet')==='1';}catch(e){}"
            "if(!/google|mediapartners/i.test(u)&&(navigator.webdriver||"
            "/bot|crawl|spider|slurp|headless|ahrefs|semrush|mj12|petal|bytespider|python|curl|wget|phantom|puppeteer|playwright|selenium/i.test(u)))q=true;"
            "window.__404quiet=q;"
            # Analytics and ads wait for the first real input (mouse, touch, wheel or key). Bots that render
            # JavaScript but never touch the page (77% of GA "users" in Nov 2026, a Chrome farm in Singapore)
            # no longer count as sessions or ask for ads, which keeps RPM honest and AdSense clear of invalid
            # traffic. People reading an article always move, scroll or tap within seconds.
            "var Q=[],go=false,EV=['pointerdown','pointermove','keydown','touchstart','wheel'];"
            "function inj(a){var s=document.createElement('script');s.async=true;s.src=a[0];"
            "if(a[1])s.crossOrigin='anonymous';document.head.appendChild(s);}"
            "function start(e){if(go||(e&&e.isTrusted===false))return;go=true;"
            "EV.forEach(function(t){removeEventListener(t,start,true);});Q.forEach(inj);Q=[];}"
            "EV.forEach(function(t){addEventListener(t,start,{capture:true,passive:true});});"
            "window.__404load=function(src,cors){var a=[src,cors];if(go)inj(a);else Q.push(a);};})();")
HUB_TAG_COUNT = 8
RELATED_COUNT = 5
MAX_AUTO_LINKS = 6
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
            # No verified local copy means the URL may be invented, so never ship it to a reader.
            return ""
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
        if not info or info.get("status") != "ok":
            return ""  # no verified local copy: drop the whole figure
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

def affiliate_partners(config):
    """Partner table from site-config.json. A partner is active only when its id (and merchant_id, if the template
    needs one) has been pasted in; until then its links are left as plain outbound links."""
    out = []
    for p in config.get("affiliates", []):
        if not isinstance(p, dict) or not p.get("domains"):
            continue
        pid = (p.get("id") or "").strip()
        tmpl = p.get("template") or ""
        needs_mid = "{merchant_id}" in tmpl
        active = bool(pid) and (not needs_mid or bool((p.get("merchant_id") or "").strip()))
        out.append({**p, "id": pid, "active": active})
    return out


def affiliate_url(url, partner):
    """Rewrite one merchant URL with the partner's tracking. Templates may use {url}, {url_encoded}, {path},
    {id} and {merchant_id}; a partner with a 'param' instead of a template gets that query parameter appended."""
    parts = urlparse(url)
    if partner.get("param"):
        query = dict(parse_qsl(parts.query))
        query[partner["param"]] = partner["id"]
        return urlunparse(parts._replace(query=urlencode(query)))
    tmpl = partner.get("template") or ""
    if not tmpl:
        return url
    from urllib.parse import quote
    path = parts.path + (("?" + parts.query) if parts.query else "")
    return tmpl.format(url=url, url_encoded=quote(url, safe=""), path=path or "/",
                       id=partner["id"], merchant_id=(partner.get("merchant_id") or "").strip())


def normalize_internal_links(body):
    """GitHub Pages serves every post at /posts/x and /posts/x.html, so a link that omits .html
    creates a second crawlable URL for the same page. Force the .html form at build time."""
    return re.sub(r'href="(/posts/[a-z0-9][a-z0-9-]*)"', r'href="\1.html"', body)


def monetize_links(body, config):
    """Tag links to configured affiliate partners. Active partners (id pasted in site-config.json) get tracking plus
    rel="sponsored nofollow"; partners without an id are still marked nofollow so the build never leaks link equity
    to a shop. Everything else is left alone."""
    partners = affiliate_partners(config)
    if not partners:
        return body

    def match(host):
        for p in partners:
            for d in p["domains"]:
                d = d.lower()
                if host == d or host.endswith("." + d):
                    return p
        return None

    def fix(m):
        tag = m.group(0)
        href = re.search(r'href="([^"]+)"', tag)
        if not href:
            return tag
        url = href.group(1)
        if not url.startswith("http"):
            return tag
        host = urlparse(url).netloc.lower()
        partner = match(host)
        if not partner:
            return tag
        rel = "nofollow noopener"
        if partner["active"]:
            tag = tag.replace(href.group(0), f'href="{affiliate_url(url, partner)}"')
            rel = "sponsored nofollow noopener"
        tag = re.sub(r'\srel="[^"]*"', "", tag)
        tag = re.sub(r'\starget="[^"]*"', "", tag)
        return tag.replace("<a", f'<a rel="{rel}" target="_blank"', 1)

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
    # Loaded through __404load so the owner's own visits, test browsers and non-Google crawlers never request
    # ads: they were most of the page views AdSense counted and they drag page RPM down (and risk invalid traffic).
    return (f'\n    <meta name="google-adsense-account" content="{client}">'
            f'\n    <script>if(!window.__404quiet)__404load("https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={client}",1);</script>')


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
        p["body"] = normalize_internal_links(monetize_links(localize_images(p["body"], manifest), config))
        p["body"] = re.sub(r"<table>(.*?)</table>", r'<div class="table-wrap" style="overflow-x:auto"><table>\1</table></div>', p["body"], flags=re.S)
        p["wordCount"] = word_count(p["body"])
        p["readingTime"] = reading_label(p["body"] + " " + (p.get("summary") or ""))
        seo = p.get("seo") or {}
        # Google cuts titles near 60 characters and shows the site name above the result anyway, so the
        # brand suffix is added only when it still fits; otherwise the searcher's words get all the room.
        base_title = (seo.get("title") or p["title"]).replace(f" | {BLOG_NAME}", "").strip()
        p["pageTitle"] = f"{base_title} | {BLOG_NAME}" if len(base_title) + len(BLOG_NAME) + 3 <= 60 else base_title
        # The title readers see everywhere on the site (lists, cards, feed) matches the H1 and the search result,
        # so a list never gives away the answer the page is careful to keep for the click
        p["displayTitle"] = base_title
        p["metaDescription"] = seo.get("description") or p["excerpt"]
        hero = manifest.get(p.get("image") or "", {})
        p["heroLocal"] = hero.get("file") if hero.get("status") == "ok" else None
        p["heroInfo"] = hero if hero.get("status") == "ok" else None
        p["thumb"] = hero.get("thumb") if hero.get("status") == "ok" else None
        if not p["heroLocal"]:
            p["image"] = None  # no verified local copy: grey placeholder instead of a broken request
        p["heroUrl"] = f"{BASE_URL}{p['heroLocal']}" if p["heroLocal"] else None
        og_local = os.path.join(OUTPUT_DIR, "og", f"{p['slug']}.jpg")
        p["ogImage"] = f"{BASE_URL}/og/{p['slug']}.jpg" if os.path.exists(og_local) else DEFAULT_OG_IMAGE
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


RELATED_MAP = {}


def build_related_map(posts, count=RELATED_COUNT):
    """Pick each post's related list so link equity spreads instead of piling on the newest posts.

    Sorting candidates by recency alone gave the last few weeks every internal link and left older
    posts with none, which is how a page ends up discovered and never crawled. Each post still only
    sees same-tag candidates, but among them the ones with the fewest inbound slots so far win, so
    every post in the archive collects links from its own neighbourhood.
    """
    inbound = {p["slug"]: 0 for p in posts}
    # Pages Google already shows in search get crawled often; their related cards lean toward pages it has not
    # indexed yet, so the crawler reaches them through pages it actually visits (Search Console snapshot).
    seen = set()
    try:
        seen = {row[0] for row in json.load(open(os.path.join(ROOT, "seo", "search-console.json"), encoding="utf-8")).get("pages", [])}
    except (OSError, ValueError):
        pass
    stop = {"what", "happened", "still", "around", "who", "owns", "now", "the", "and", "how", "why", "did",
            "does", "is", "are", "was", "in", "of", "to", "a", "an", "it", "its", "2026", "today", "for", "on"}
    words = {p["slug"]: {w for w in re.findall(r"[a-z0-9]+", p["title"].lower()) if w not in stop and len(w) > 2}
             for p in posts}
    order = sorted(posts, key=lambda p: p["date"])  # oldest first: the newest still get fresh links
    for post in order:
        tags = set(post["tags"])
        text = strip_tags(post["body"]).lower()

        def relevance(o):
            # A reader who finished a post about Sears wants Kmart or Montgomery Ward next, not whatever
            # shares the broad "Business Blunders" tag: subjects this post names and shared title words
            # count for more than the tag.
            named = any(ph.lower() in text for ph in (o.get("linkPhrases") or []) if len(ph) > 3)
            return 2 * len(tags & set(o["tags"])) + 3 * named + len(words[post["slug"]] & words[o["slug"]])

        cands = [(relevance(o), o) for o in posts if o["slug"] != post["slug"] and (tags & set(o["tags"]))]
        # The first pick (the mid-article "Keep reading" card) is simply the most relevant story; the rest
        # still favour whoever is starved of inbound links so link equity spreads across the archive.
        cands.sort(key=lambda c: (-c[0], -int(c[1]["date"].replace("-", ""))))
        first = [cands[0][1]] if cands else []
        source_seen = post["slug"] in seen
        rest = sorted(cands[1:], key=lambda c: (-min(c[0], 4), source_seen and c[1]["slug"] in seen,
                                               inbound[c[1]["slug"]], -int(c[1]["date"].replace("-", ""))))
        picked = first + [c[1] for c in rest[:count - 1]]
        for r in picked:
            inbound[r["slug"]] += 1
        RELATED_MAP[post["slug"]] = picked
    return inbound


def related_posts(post, posts, count=RELATED_COUNT):
    if post["slug"] in RELATED_MAP:
        return RELATED_MAP[post["slug"]][:count]
    tags = set(post["tags"])
    scored = [(len(tags & set(o["tags"])), o["date"], o) for o in posts if o["slug"] != post["slug"]]
    scored = [s for s in scored if s[0] > 0]
    scored.sort(key=lambda s: s[1], reverse=True)
    scored.sort(key=lambda s: -s[0])
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
    <script>{QUIET_JS}</script>
    <script>
      if(!window.__404quiet)__404load('https://www.googletagmanager.com/gtag/js?id={GA_ID}');
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      {CONSENT_JS}
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
    <meta name="referrer" content="strict-origin-when-cross-origin">
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
    <link rel="alternate" type="text/plain" title="llms.txt" href="{BASE_URL}/llms.txt">
    {ctx['favicons']}
    <link rel="stylesheet" href="/assets/site.css?v={ctx['version']}">
{schema_tags}
</head>"""


# Post pages: a Win95 progress meter in the taskbar shows how far through the story the reader is, and
# GA4 gets read_progress (25/50/75/100) plus clicks on the reading-flow cards, so retention is measurable.
READING_JS = """    <script>
    (function () {
        var body = document.querySelector('.post-body');
        if (!body) return;
        var html = '<span class="read-meter" aria-hidden="true"><span class="read-meter-track"><span class="read-meter-fill"></span></span><span class="read-meter-pct">0%</span></span>';
        var spacer = document.querySelector('.taskbar .taskbar-spacer');
        if (spacer) spacer.insertAdjacentHTML('afterend', html);
        var mob = document.querySelector('.page-mobile-footer .mobile-footer-status');
        if (mob) mob.innerHTML = html;
        var fills = document.querySelectorAll('.read-meter-fill'), pcts = document.querySelectorAll('.read-meter-pct');
        var sent = {}, ticking = false, slug = window.postPageSlug || '';
        function send(name, params) { if (typeof gtag === 'function') gtag('event', name, params); }
        function update() {
            ticking = false;
            var r = body.getBoundingClientRect();
            var seen = Math.min(Math.max(window.innerHeight - r.top, 0), r.height);
            var p = r.height ? Math.round(seen / r.height * 100) : 0;
            for (var i = 0; i < fills.length; i++) fills[i].style.width = p + '%';
            for (var j = 0; j < pcts.length; j++) pcts[j].textContent = p + '%';
            [25, 50, 75, 100].forEach(function (t) {
                if (p >= t && !sent[t]) {
                    sent[t] = 1;
                    send('read_progress', { percent: t, post_slug: slug });
                    if (t === 100) send('read_complete', { post_slug: slug });
                }
            });
        }
        document.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true, capture: true });
        window.addEventListener('resize', update);
        update();
        document.addEventListener('click', function (e) {
            var a = e.target.closest && e.target.closest('a[data-ev]');
            if (a) send(a.getAttribute('data-ev'), { link_url: a.href, post_slug: slug, transport_type: 'beacon' });
        });
    })();
    </script>"""


def branded(title):
    """Page title with the site name appended only when it adds something and still fits in Google's ~60 characters."""
    if BLOG_NAME in title or len(title) + len(BLOG_NAME) + 3 > 60:
        return title
    return f"{title} | {BLOG_NAME}"


def shell_html(ctx, head, *, body_class, window_icon, window_title, content, status_text, slug=""):
    """Every generated page is one open Win95 window on the desktop (full-screen window on mobile)."""
    # Every control on the window either works or is visibly unavailable. Minimize leaves a taskbar button that
    # brings the page back (data-was-open), Close goes to the desktop (window.close() is ignored in a tab opened
    # from search, which used to leave readers on an empty desktop), and Maximize is greyed out because the page
    # already fills the reading width, like a fixed-size Win95 dialog.
    # Back buttons return to the previous page on this site when there is one (site.js), else they go home
    content = content.replace('class="page-back page-back-mobile"', 'class="page-back page-back-mobile" data-back')
    content = content.replace('class="page-back page-back-desktop"', 'class="page-back page-back-desktop" data-back')
    return f"""{head}
<body class="page-shell {body_class}">
    <a class="skip-link" href="#content">Skip to content</a>
    <main>
    <div class="desktop-container">
        <div class="desktop-area" onclick="document.querySelectorAll('.desktop-icon.selected').forEach(i => i.classList.remove('selected'))">
            {ctx['desktop_icons']}
            <div class="window" id="post-window" data-was-open="true" data-title="{window_icon} {esc(window_title)}" style="left:120px;top:15px;width:850px;height:620px;display:flex;">
                <div class="title-bar">
                    <div class="title-bar-title">{window_icon} <span>{esc(window_title)}</span></div>
                    <div class="title-bar-controls">
                        <button class="window-button" onclick="minimizeWindow('post-window')" aria-label="Minimize to the taskbar" title="Minimize to the taskbar"><span class="btn-minimize"></span></button>
                        <button class="window-button" disabled aria-label="Maximize (this window is already full width)" title="Already full width"><span class="btn-maximize"></span></button>
                        <button class="window-button" onclick="location.href='/'" aria-label="Close and go to the desktop" title="Close (back to the desktop)"><span class="btn-close">×</span></button>
                    </div>
                </div>
                <div class="window-content">
                    <div class="page-card" id="content" tabindex="-1">
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
        <div class="mobile-footer-left"><a href="/" class="mobile-footer-start" role="button" aria-expanded="false" aria-controls="mobile-start-menu" onclick="return toggleMobileStart(event)"><span>🪟</span> Start</a></div>
        <div class="mobile-footer-status">{esc(status_text)}</div>
    </div>
    {ctx['mobile_start_menu']}
    </main>
    <script>window.__BUILD__ = '{ctx['version']}'; var isPostPage = true; var postPageSlug = '{slug}';</script>
    <script src="/assets/site.js?v={ctx['version']}"></script>
{READING_JS if body_class == "post-page" else ""}
</body>
</html>
"""


def nav_links_html(tags, current=None):
    items = ['<a href="/posts/">All posts</a>', '<a href="/dead-brand-index.html">Dead brand index</a>']
    for t in tags:
        cls = ' class="active"' if t == current else ""
        items.append(f'<a href="/tags/{tag_slug(t)}.html"{cls}>{esc(t)}</a>')
    return '<nav class="page-nav" aria-label="Browse">' + " ".join(items) + "</nav>"


def post_list_html(posts):
    items = []
    for p in posts:
        thumb = (f'<span class="page-list-thumb"><img src="{p["thumb"]}" alt="" width="96" height="72" loading="lazy" decoding="async"></span>'
                 if p.get("thumb") else '<span class="page-list-thumb"></span>')
        tags = ", ".join(esc(t) for t in p["tags"][:3])
        items.append(
            f'<li><a href="{p["path"]}">{thumb}<span class="page-list-text">'
            f'<span class="page-list-title">{esc(p["displayTitle"])}</span>'
            f'<span class="page-list-meta">{p["date"]} · {esc(p["authorName"])} · {p["readingTime"]}{" · " + tags if tags else ""}</span>'
            f'<span class="page-list-excerpt">{esc(p["excerpt"])}</span></span></a></li>')
    return '<ul class="page-list">' + "\n".join(items) + "</ul>"


ORG_ID = BASE_URL + "/#organization"


def organization(ctx, full=False):
    """The publisher entity. Every schema block references it by @id so the graph is connected; the about page
    carries the full node with sameAs profiles from site-config.json (social_profiles)."""
    node = {"@type": "Organization", "@id": ORG_ID, "name": BLOG_NAME, "url": BASE_URL + "/",
            "logo": {"@type": "ImageObject", "url": LOGO, "width": 512, "height": 512}}
    if full:
        node["description"] = DEFAULT_DESCRIPTION
        node["email"] = "hello@404memoryfound.com"
        node["foundingDate"] = "2026"
        node["publishingPrinciples"] = BASE_URL + "/about.html"
        profiles = [u for u in ctx["config"].get("social_profiles", []) if isinstance(u, str) and u.startswith("http")]
        if profiles:
            node["sameAs"] = profiles
    return node


def author_person(ctx, key):
    a = ctx["authors"][key]
    return {"@type": "Person", "@id": f"{BASE_URL}/authors/{key}.html#person", "name": a["name"],
            "url": f"{BASE_URL}/authors/{key}.html", "description": a["bio"], "jobTitle": "Writer",
            "worksFor": {"@id": ORG_ID}}


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

def post_summary_html(post):
    return f'<p class="post-summary">{post["summary"]}</p>' if post.get("summary") else ""


# Section headings that only restate the answer the summary already gave ("Who owns X today?") make poor teasers.
ANSWER_HEADING = re.compile(r"\b(who owns|still (around|open|in business|exist|exists|work|works|updating|going|available|alive|made)"
                            r"|today|now\b|in 20\d\d|frequently asked)", re.I)


def ahead_html(headings):
    """One line under the summary that points at the strangest part of the story still to come, taken from the
    post's own section headings. The summary answers the search; this gives the reader a reason to keep going."""
    cands = []
    for i, (slug, text) in enumerate(headings):
        if i == 0 or ANSWER_HEADING.search(text):
            continue
        # A scene ("The day...", "The 30-hour auction that...") beats an explainer, a statement beats a question.
        score = (3 if re.match(r"The\b", text) else 0) + (0 if text.rstrip().endswith("?") else 1) \
            + (1 if re.search(r"\d", text) else 0) + (1 if i <= max(1, len(headings) * 2 // 3) else 0)
        cands.append((score, -i, slug, text))
    if not cands:
        return ""
    _, _, slug, text = max(cands)
    return (f'<p class="post-ahead" data-nosnippet>Still ahead in this story: '
            f'<a href="#{slug}" data-ev="ahead_click">{esc(text)}</a></p>')


def quick_facts_html(post):
    facts = post.get("facts") or []
    if not facts:
        return ""
    rows = "".join(f'<div class="fact-row"><dt>{esc(f["label"])}</dt><dd>{f["value"]}</dd></div>' for f in facts)
    return f'<aside class="quick-facts" aria-label="Quick facts"><div class="quick-facts-title">Quick facts</div><dl>{rows}</dl></aside>'


def post_extras_html(post):
    """Summary, hero, quick facts in one block: the homepage reader's JSON. Article pages place them separately."""
    return "\n".join(x for x in (post_summary_html(post), post_hero_html(post), quick_facts_html(post)) if x)


def post_hero_html(post):
    """The lead photo, unless the body already carries its own images."""
    parts = []
    if post.get("heroLocal") and "<img" not in post["body"]:
        info = post["heroInfo"]
        alt = esc(post.get("imageAlt") or post["title"])
        caption = post.get("imageCaption") or ""
        # The hero is usually the largest thing on screen, so it loads first; phones get the 720px copy.
        medium = "/img/m/" + os.path.basename(post["heroLocal"])
        srcset, source = "", ""
        ratio = info["width"] / max(1, info["height"])
        # Drawn size: phones fit the photo in a 220px-tall box, desktop in 560 x 400 (PAGE_SHELL_CSS)
        phone_w = round(220 * ratio)
        phone = f"{phone_w}px" if phone_w < 343 else "calc(100vw - 32px)"
        desk = min(560, round(400 * ratio), info["width"])
        sizes = f' sizes="(max-width: 768px) {phone}, {desk}px"'
        has_medium = os.path.exists(os.path.join(OUTPUT_DIR, medium.lstrip("/")))
        if has_medium:
            srcset = f' srcset="{medium} 720w, {post["heroLocal"]} {info["width"]}w"{sizes}'
        # WebP twins (fetch_images.ensure_webp) are about a third lighter; the JPEG/PNG stays as the fallback
        webp = lambda p: re.sub(r"\.(jpe?g|png)$", ".webp", p, flags=re.I)
        if os.path.exists(os.path.join(OUTPUT_DIR, webp(post["heroLocal"]).lstrip("/"))):
            if has_medium and os.path.exists(os.path.join(OUTPUT_DIR, webp(medium).lstrip("/"))):
                source = f'<source type="image/webp" srcset="{webp(medium)} 720w, {webp(post["heroLocal"])} {info["width"]}w"{sizes}>'
            elif not has_medium:
                source = f'<source type="image/webp" srcset="{webp(post["heroLocal"])}">'
        img = (f'<img src="{post["heroLocal"]}"{srcset} alt="{alt}" width="{info["width"]}" '
               f'height="{info["height"]}" fetchpriority="high" decoding="async">')
        picture = f"<picture>{source}{img}</picture>" if source else img
        parts.append(
            f'<figure class="post-hero">{picture}<figcaption>{caption} {credit_link(info)}</figcaption></figure>')
    return "\n".join(parts)


def sources_html(post):
    sources = post.get("sources") or []
    if not sources:
        return ""
    items = "".join(
        f'<li><a href="{s["url"]}" rel="noopener" target="_blank">{esc(s["title"])}</a>'
        f' <span class="source-host">{esc(urlparse(s["url"]).netloc.replace("www.", ""))}</span></li>' for s in sources)
    return f'<section class="post-sources"><h2>Sources</h2><ul>{items}</ul></section>'


def human_date(iso):
    """2026-09-27 -> September 27, 2026 (what a US reader expects to see)."""
    try:
        d = datetime.strptime(iso, "%Y-%m-%d")
    except (TypeError, ValueError):
        return iso or ""
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def add_heading_ids(body):
    """Give every <h2> a stable id so the table of contents (and Google's jump links) can point at it."""
    used, out = set(), []

    def repl(m):
        attrs, inner = m.group(1), m.group(2)
        if "id=" in attrs:
            return m.group(0)
        base = re.sub(r"[^a-z0-9]+", "-", strip_tags(inner).lower()).strip("-")[:60] or "section"
        slug, n = base, 2
        while slug in used:
            slug, n = f"{base}-{n}", n + 1
        used.add(slug)
        out.append((slug, strip_tags(inner)))
        return f'<h2{attrs} id="{slug}">{inner}</h2>'

    body = re.sub(r"<h2([^>]*)>(.*?)</h2>", repl, body, flags=re.S)
    return body, out


def toc_html(headings):
    """"In this article" box: only worth showing when there is something to navigate."""
    if len(headings) < 4:
        return ""
    items = "".join(f'<li><a href="#{slug}">{esc(text)}</a></li>' for slug, text in headings)
    return f'<nav class="post-toc" aria-label="In this article"><div class="post-toc-title">Jump to:</div><ol>{items}</ol></nav>'


def insert_before_faq(body, html):
    """Put the next-story cards where the story ends, ahead of the FAQ and the sources: that is the moment a
    reader decides whether to open a second page, and the first links they meet used to point off the site."""
    if not html:
        return body
    faq = re.search(r"<h2[^>]*>\s*Frequently Asked Questions", body, flags=re.I)
    at = faq.start() if faq else len(body)
    return body[:at] + html + "\n" + body[at:]


def archive_card(r, event):
    """One related post as a small Win95 'file' card: thumbnail, curiosity title, one-line teaser."""
    thumb = (f'<img src="{r["thumb"]}" alt="" width="96" height="72" loading="lazy" decoding="async">'
             if r.get("thumb") else '<span class="archive-card-icon" aria-hidden="true">📄</span>')
    teaser = strip_tags(r.get("summary") or r.get("excerpt") or "")
    teaser = teaser if len(teaser) <= 120 else teaser[:117].rsplit(" ", 1)[0] + "..."
    return (f'<a class="archive-card" href="{r["path"]}" data-ev="{event}">{thumb}'
            f'<span class="archive-card-text"><strong>{esc(r["displayTitle"])}</strong><span>{esc(teaser)}</span></span></a>')


def insert_keep_reading(body, card):
    """Drop the card before the middle section heading, so a reader who is losing interest halfway down
    sees one good next story instead of the bottom of the page."""
    faq = re.search(r"<h2[^>]*>\s*Frequently Asked Questions", body, flags=re.I)
    limit = faq.start() if faq else len(body)
    heads = [m.start() for m in re.finditer(r"<h2[\s>]", body) if m.start() < limit]
    if len(heads) < 3 or not card:
        return body
    at = heads[len(heads) // 2]
    box = (f'<aside class="keep-reading" data-nosnippet><div class="keep-reading-bar">📂 Keep reading</div>{card}</aside>\n')
    return body[:at] + box + body[at:]


def build_post_page(ctx, post, posts):
    related = related_posts(post, posts)
    related_html = ""
    if len(related) > 1:
        related_html = ('<nav class="related-posts" data-nosnippet aria-label="Next in the archive">'
                        '<div class="related-posts-title">📁 Next in the archive</div>'
                        + "".join(archive_card(r, "next_click") for r in related[1:5]) + "</nav>")
    tags_html = " ".join(f'<a href="/tags/{tag_slug(t)}.html">{esc(t)}</a>' for t in post["tags"] if t in ctx["tags"])
    key = post["authorKey"]
    byline = (f'<a href="/authors/{key}.html" rel="author">{esc(post["authorName"])}</a>' if key else esc(post["authorName"]))
    disclosure = ""
    if 'rel="sponsored' in post["body"] and ctx["config"].get("affiliate_disclosure"):
        disclosure = f'<p class="affiliate-disclosure">{esc(ctx["config"]["affiliate_disclosure"])}</p>'

    body_with_ids, headings = add_heading_ids(post["body"])
    if related:
        body_with_ids = insert_keep_reading(body_with_ids, archive_card(related[0], "keep_reading_click"))
    body_with_ids = insert_before_faq(body_with_ids, related_html)
    # The headline on the page matches the title Google shows (seo.title), so the click lands where it promised.
    display_title = ((post.get("seo") or {}).get("title") or post["title"]).replace(f" | {BLOG_NAME}", "").strip()
    first_tag = post["tags"][0] if post["tags"] else None
    crumb_mid = (f'<a href="/tags/{tag_slug(first_tag)}.html">{esc(first_tag)}</a>' if first_tag
                 else '<a href="/posts/">All posts</a>')
    if post.get("updated") and post["updated"] != post["date"]:
        dates = (f'Updated <time datetime="{post["updated"]}">{human_date(post["updated"])}</time>'
                 f' <span class="post-meta-sep">&middot;</span> First published <time datetime="{post["date"]}">{human_date(post["date"])}</time>')
    else:
        dates = f'Published <time datetime="{post["date"]}">{human_date(post["date"])}</time>'

    content = f"""<a class="page-back page-back-mobile" href="/">&larr; Back</a>
<article class="post-article">
    <header class="post-header">
        <nav class="post-breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a> <span aria-hidden="true">&rsaquo;</span> {crumb_mid}</nav>
        <h1>{esc(display_title)}</h1>
        <div class="post-meta">By {byline} <span class="post-meta-sep">&middot;</span> {dates} <span class="post-meta-sep">&middot;</span> <span class="reading-time">{post['readingTime']}</span></div>
    </header>
    {post_summary_html(post)}
    {ahead_html(headings) if post.get("summary") else ""}
    {post_hero_html(post)}
    {toc_html(headings)}
    {disclosure}
    <div class="post-body">
{body_with_ids}
    </div>
    {quick_facts_html(post)}
    {sources_html(post)}
    <footer class="post-footer">
        {'<div class="post-tags">Filed under: ' + tags_html + '</div>' if tags_html else ''}
        <div class="page-back-row"><button type="button" class="page-back share-post" data-share><span aria-hidden="true">📤</span> Send this story to a friend</button> <a class="page-back page-back-desktop" href="/">&larr; Back to Blog</a> <a class="page-back" href="/posts/">All posts</a></div>
    </footer>
</article>"""

    images = [post["ogImage"]] + ([post["heroUrl"]] if post.get("heroUrl") else [])
    author_schema = author_person(ctx, key) if key else {"@id": ORG_ID}
    blog_posting = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": display_title,
        "description": post["metaDescription"],
        "datePublished": post["date"],
        "dateModified": post.get("updated") or post["date"],
        "image": images,
        "wordCount": post["wordCount"],
        "keywords": post["tags"],
        "articleSection": post["tags"][0] if post["tags"] else "Technology",
        "author": author_schema,
        "publisher": organization(ctx),
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
            {"@type": "ListItem", "position": 2, "name": post["tags"][0] if post["tags"] else "All posts",
             "item": f"{BASE_URL}/tags/{tag_slug(post['tags'][0])}.html" if post["tags"] else f"{BASE_URL}/posts/"},
            {"@type": "ListItem", "position": 3, "name": display_title, "item": post["url"]},
        ],
    }
    extra = (f'\n    <meta property="article:published_time" content="{post["date"]}T00:00:00Z">'
             f'\n    <meta property="article:modified_time" content="{post.get("updated") or post["date"]}T00:00:00Z">'
             f'\n    <meta property="article:section" content="{esc(post["tags"][0] if post["tags"] else "Technology")}">'
             + "".join(f'\n    <meta property="article:tag" content="{esc(t)}">' for t in post["tags"])
             + f'\n    <meta name="author" content="{esc(post["authorName"])}">')
    head = head_html(ctx, title=post["pageTitle"], description=post["metaDescription"], canonical=post["url"],
                     og_type="article", og_image=post["ogImage"], extra_meta=extra, og_title=post["displayTitle"],
                     schemas=(blog_posting, breadcrumbs, extract_faq_schema(post["body"])))
    return shell_html(ctx, head, body_class="post-page", window_icon="📖", window_title=display_title,
                      content=content, status_text=human_date(post.get("updated") or post["date"]), slug=post["slug"])


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
        inner += ('<section class="editorial-policy"><h2>How we research and correct</h2>'
                  '<p>Every article starts from primary material: company filings, court records, contemporary newspaper '
                  'reports, museum collections and the companies\' own announcements. The sources we relied on are listed at '
                  'the end of each post, and any figure we could not trace to one of them is left out rather than estimated. '
                  'Posts carry their publication date and, when revised, an update date.</p>'
                  '<p>We write under pen names and publish no personal details about our writers. If you find an error, email '
                  '<a href="mailto:hello@404memoryfound.com">hello@404memoryfound.com</a> with the page and the source; '
                  'corrections are made in the article and dated.</p>'
                  f'<p>Machine-readable summaries of the whole site are available at <a href="/llms.txt">/llms.txt</a> and '
                  f'<a href="/llms-full.txt">/llms-full.txt</a>.</p></section>')
    if filename == "terms.html":
        inner += ('<h3 style="font-size:14px;margin:10px 0 4px 0;">Affiliate links and advertising</h3>'
                  '<p style="font-size:13px;margin-bottom:8px;">' + esc(ctx["config"].get("affiliate_disclosure", "")) +
                  ' Pages may also carry advertising served by Google AdSense; those ads are labelled and never influence what we write.</p>')
    content = f'<a class="page-back page-back-mobile" href="/">&larr; Back</a>\n<div class="page-copy">{inner}</div>\n' \
              f'{nav_links_html(ctx["tags"])}'
    url = f"{BASE_URL}/{filename}"
    head = head_html(ctx, title=branded(f"{page_title}"), description=HUB_DESCRIPTIONS[filename], canonical=url,
                     schemas=({"@context": "https://schema.org", "@type": "WebPage", "name": page_title, "url": url,
                               "isPartOf": {"@id": BASE_URL + "/#website"}, "publisher": {"@id": ORG_ID}},
                              ({"@context": "https://schema.org", **organization(ctx, full=True)} if filename == "about.html" else None)))
    icon, _, title_text = bar_title.partition(" ")
    return shell_html(ctx, head, body_class="hub-page", window_icon=icon, window_title=title_text, content=content,
                      status_text=f"{len(posts)} posts")


def breadcrumb_schema(*items):
    """BreadcrumbList from (name, url) pairs, Home first."""
    trail = [("Home", BASE_URL + "/")] + list(items)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(trail)]}


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
    head = head_html(ctx, title=branded(f"{a['name']}"), canonical=url,
                     description=f"{a['name']} writes about {a['beat'].lower()} for {BLOG_NAME}. {len(mine)} posts.",
                     schemas=(schema, breadcrumb_schema(("About", f"{BASE_URL}/about.html"), (a["name"], url))))
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
                  {"@type": "ListItem", "position": i + 1, "url": p["url"], "name": p["displayTitle"]} for i, p in enumerate(posts)]}}
    head = head_html(ctx, title=branded(f"All posts"), canonical=url,
                     description=f"Every story on {BLOG_NAME}: {len(posts)} articles about 90s and 2000s technology, games, websites and companies.",
                     schemas=(schema, breadcrumb_schema(("All posts", url))))
    return shell_html(ctx, head, body_class="hub-page", window_icon="📝", window_title="All posts", content=content,
                      status_text=f"{len(posts)} posts")


BRAND_INDEX_JS = """
<script>
(function () {
    var table = document.getElementById('brand-index');
    if (!table) return;
    var body = table.tBodies[0], rows = Array.prototype.slice.call(body.rows);
    var count = document.getElementById('brand-count'), total = rows.length;
    var filter = document.getElementById('brand-filter');
    if (filter) filter.addEventListener('input', function () {
        var q = filter.value.toLowerCase(), shown = 0;
        rows.forEach(function (r) {
            var hit = r.textContent.toLowerCase().indexOf(q) !== -1;
            r.style.display = hit ? '' : 'none';
            if (hit) shown++;
        });
        if (count) count.firstChild.nodeValue = shown === total
            ? 'Showing all ' + total + ' entries. The archive holds '
            : 'Showing ' + shown + ' of ' + total + ' entries. The archive holds ';
    });
    var asc = {};
    Array.prototype.forEach.call(table.tHead.rows[0].cells, function (th, i) {
        th.addEventListener('click', function () {
            asc[i] = !asc[i];
            rows.sort(function (a, b) {
                var x = a.cells[i].textContent.trim().toLowerCase();
                var y = b.cells[i].textContent.trim().toLowerCase();
                if (!x || !y) return x === y ? 0 : (x ? -1 : 1);  // blank cells stay at the bottom either way
                return (x < y ? -1 : x > y ? 1 : 0) * (asc[i] ? 1 : -1);
            });
            rows.forEach(function (r) { body.appendChild(r); });
            Array.prototype.forEach.call(table.tHead.rows[0].cells, function (o) { o.className = ''; o.setAttribute('aria-sort', 'none'); });
            th.className = asc[i] ? 'sorted asc' : 'sorted';
            th.setAttribute('aria-sort', asc[i] ? 'ascending' : 'descending');
        });
    });
})();
</script>
"""


# The index needs the brand alone. Titles are patterned ("Who Owns X Now?", "How Many X Are Left?") and
# linkPhrases name the post's own subject, so between the two there is almost always a clean entity.
INDEX_LEAD = (r"^(?:How Many|Who Owns|Who Was|What Happened to|Whatever Happened to|Where Is|Where to Buy|"
              r"When Did|Can You Still Get|Is an|Is the|Is|Was the|Was|Are the|Are|Does|Did|"
              r"Do They Still Make|Why the|Why|How to Run|How to|How|When|The)\s+")
INDEX_CUT = (r"\s+Still\b", r"\s+Are\s+Left\b", r"\s+Is\s+Left\b", r"\s+Left\b", r"\s+Now\b", r"\s+in\s+20\d\d",
             r"\s+Stores\b", r"\s+Locations\b", r"\s+Explained\b", r"\s+vs\b", r"\s+Really\b", r"\s+Actually\b",
             r"\s+That\b", r"\s+Which\b", r"\s+After\b", r"\s+Went\b", r"\s+Died\b", r"\s+Failed\b", r"\s+Saved\b",
             r"\s+Worth\b", r"\s+Sold\b", r"\s+Turn(?:ed)?\b", r"\s+Lost\b", r"\s+Kill(?:ed)?\b", r"\s+Tried\b",
             r"\s+Stop(?:ped)?\b", r"\s+Shut\b", r"\s+Open\b", r"\s+Updating\b", r"\s+On TV\b", r"\s+Exist\b",
             r"\s+Available\b", r"\s+Online\b", r"\s+in Business\b", r"\s+Worth It\b", r"\s+Make\b", r"\s+Mailing\b")
INDEX_STOPWORD = {"do", "they", "it", "them", "you", "your", "this", "that", "there", "here", "what", "where",
                  "when", "why", "how", "who", "an", "a", "the", "of", "for", "to", "in", "on", "still",
                  "really", "actually", "first", "last", "best", "worst", "new", "old"}


def index_clean(name):
    name = re.sub(r"^(?:buy|get|find|run|play|use|using)\s+", "", name.strip(), flags=re.I)
    name = re.sub(r"^(?:a|an|the)\s+", "", name.strip(), flags=re.I)
    name = re.sub(r"\s+(?:bankruptcy|acquisition|collapse|failure|shutdown|history|story|deal|ipo|crash|era|"
                  r"today|now|games|game|playable|handheld|console|consoles|websites|website)$", "",
                  name.strip(), flags=re.I)
    return name.strip(" ,-'")


def index_valid(name):
    """A brand name: at most three words, no question words, and it starts like a name (eBay counts)."""
    if not name:
        return None
    words = name.split()
    if not words or len(words) > 3:
        return None
    if any(w.lower() in INDEX_STOPWORD for w in words):
        return None
    if not re.match(r"^[A-Z0-9]", name) and not (re.search(r"[A-Z]", name[1:4]) or "." in words[0]):
        return None   # eBay, iPod and theGlobe.com pass; a plain lowercase phrase does not
    if re.match(r"^\d", name) and not re.search(r"[A-Za-z]", name[:4]):
        return None   # "$1,000 in 1999" is an amount, not a brand
    if re.match(r"^[\d']{1,2}\d?0s\b", name):
        return None   # "90s PC", "'80s gadgets": an era, not a brand
    return name


def index_name_from_title(title):
    text = re.split(r"[:?,]", title)[0]
    text = re.sub(INDEX_LEAD, "", text).strip()
    for cut in INDEX_CUT:
        text = re.split(cut, text)[0]
    parts = re.split(r"\s+and\b", text, maxsplit=1)
    if len(parts) == 2 and len(parts[0].split()) >= 2:
        text = parts[0]   # "Montgomery Ward ... and Who Owns It" cuts; "Barnes and Noble" does not
    return index_valid(index_clean(text))


def index_name(post):
    # posts.json "indexName" overrides the guess; an empty string keeps a non-brand post (Y2K, dial-up sound) out
    if "indexName" in post:
        return post["indexName"] or None
    cands = [n for n in (index_valid(index_clean(x)) for x in (post.get("linkPhrases") or [])) if n]
    from_title = index_name_from_title(post["title"])
    if from_title:
        cands.append(from_title)
    if not cands:
        return None
    title = post["title"].lower()
    cands.sort(key=lambda c: (c.lower() not in title, -len(c.split()), len(c)))
    return cands[0]


def brand_index_rows(posts):
    """Every post that answers a status question about a named brand, as one row of the reference table."""
    rows, seen = [], {}
    for p in posts:
        facts = {f["label"].lower(): f["value"] for f in p.get("facts", [])}
        status = facts.get("status today") or facts.get("status")
        if not status:
            continue
        name = index_name(p)
        if not name:
            continue
        key = name.lower()
        if key in seen:   # two posts on the same brand: keep the one whose title leads with it
            if not p["title"].lower().startswith(key):
                continue
            rows.remove(seen[key])
        row = {"name": name, "status": status, "owner": facts.get("owner today") or facts.get("company") or "",
               "started": facts.get("launched") or facts.get("founded") or facts.get("released") or facts.get("created") or "",
               "url": p["path"], "title": p["title"], "tags": p["tags"]}
        seen[key] = row
        rows.append(row)
    rows.sort(key=lambda r: r["name"].lower())
    return rows


def build_brand_index_page(ctx, posts):
    rows = brand_index_rows(posts)
    body_rows = "".join(
        f'<tr><td data-label="Name"><a href="{r["url"]}">{esc(r["name"])}</a></td>'
        f'<td data-label="Started">{esc(r["started"])}</td>'
        f'<td data-label="Status in 2026">{esc(r["status"])}</td>'
        f'<td data-label="Who owns it now">{esc(r["owner"])}</td></tr>' for r in rows)
    content = (
        '<a class="page-back page-back-mobile" href="/">&larr; Back</a>\n'
        f'<h1>The dead brand index</h1>\n'
        f'<p class="page-intro">{len(rows)} companies, stores, gadgets and websites from the 1990s and 2000s, '
        'with what became of each one and who holds the name in 2026. Every row links to the full story, '
        'sourced and dated. Sort by clicking a column, or filter by typing.</p>\n'
        f'{nav_links_html(ctx["tags"])}\n'
        '<div class="brand-index-tools"><label for="brand-filter">Filter</label>'
        '<input id="brand-filter" type="search" placeholder="Type a name, an owner or a year" autocomplete="off"></div>\n'
        '<table class="brand-index" id="brand-index"><thead><tr>'
        '<th data-sort="0" aria-sort="none"><button type="button">Name</button></th>'
        '<th data-sort="1" aria-sort="none"><button type="button">Started</button></th>'
        '<th data-sort="2" aria-sort="none"><button type="button">Status in 2026</button></th>'
        '<th data-sort="3" aria-sort="none"><button type="button">Who owns it now</button></th>'
        f'</tr></thead><tbody>{body_rows}</tbody></table>\n'
        f'<p class="brand-index-note" id="brand-count">Showing all {len(rows)} entries. The archive holds '
        f'<a href="/posts/">{len(posts)} posts</a> in total, including the ones that do not answer a status question.</p>'
        '<div class="brand-index-reuse"><h2>Using this table</h2>'
        f'<p>Last checked {esc(ctx["today_label"])}. Every status is taken from the linked post, where the sources are listed. '
        'The data is free to reuse, including in articles and research, under '
        '<a href="https://creativecommons.org/licenses/by/4.0/" rel="license">CC BY 4.0</a>: credit 404 Memory Found and link back to this page.</p>'
        '<p class="brand-index-method"><strong>How it is built:</strong> one row per brand the archive has a full post on. '
        '&ldquo;Started&rdquo; is the launch or founding year, &ldquo;Status in 2026&rdquo; and &ldquo;Who owns it now&rdquo; come from the '
        'sources cited in that post (company filings, court records, trademark records and contemporary news). '
        'Every post is rechecked on a rolling schedule, and the table is rebuilt from the posts each time the site is published.</p>'
        '<p class="brand-index-downloads">Download: <a href="/dead-brand-index.csv" download>CSV</a> '
        '<a href="/dead-brand-index.json" download>JSON</a></p>'
        '<p class="brand-index-cite"><strong>Cite it as:</strong> 404 Memory Found, &ldquo;The dead brand index&rdquo;, '
        f'{esc(ctx["today_label"])}, https://404memoryfound.com/dead-brand-index.html</p>'
        '<p class="brand-index-embed"><strong>Link to it:</strong></p>'
        '<pre class="brand-index-snippet"><code>&lt;a href="https://404memoryfound.com/dead-brand-index.html"&gt;'
        'The dead brand index (404 Memory Found, CC BY 4.0)&lt;/a&gt;</code></pre></div>'
        + BRAND_INDEX_JS)
    url = f"{BASE_URL}/dead-brand-index.html"
    schema = {"@context": "https://schema.org", "@type": "Dataset",
              "name": "The dead brand index", "url": url,
              "description": f"What happened to {len(rows)} companies, stores, gadgets and websites of the 1990s and 2000s, and who owns each name in 2026.",
              # Google's Dataset report wants a typed creator and a license; the page already grants reuse with credit,
              # which is CC BY 4.0, and saying so in the markup is what lets Dataset Search list it.
              "creator": {"@type": "Organization", "@id": ORG_ID, "name": BLOG_NAME, "url": BASE_URL + "/"},
              "license": "https://creativecommons.org/licenses/by/4.0/", "isAccessibleForFree": True,
              "dateModified": ctx["today"],
              "distribution": [{"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": BASE_URL + "/dead-brand-index.csv"},
                               {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": BASE_URL + "/dead-brand-index.json"}],
              "keywords": ["defunct brands", "dead retail chains", "who owns it now", "1990s companies", "2000s websites"]}
    head = head_html(ctx, title=branded(f"Defunct 90s and 2000s Brands: Who Owns All {len(rows)} Names Now"),
                     canonical=url,
                     description=f"Sort or search {len(rows)} brands of the 90s and 2000s by start year or status, see who owns each name in 2026, and download the full list as CSV or JSON.",
                     schemas=(schema, breadcrumb_schema(("The dead brand index", url))))
    return shell_html(ctx, head, body_class="hub-page", window_icon="\U0001f5c3\ufe0f", window_title="Dead brand index",
                      content=content, status_text=f"{len(rows)} brands")


# Each category page needs its own reason to rank and to be clicked; "20 stories about X" was thin
# enough that Google pulled random sentences from the list into the snippet instead.
TAG_COPY = {
    "Business Blunders": ("The stores, startups and giants of the 90s and 2000s that fell apart: what went wrong, the day it ended, and who owns the name now.",
                          "The chains, dot-coms and tech giants that had it all and lost it. Each story covers the mistake, the date it ended and who owns what is left."),
    "Hardware": ("Consoles, handhelds, PCs, phones and gadgets of the 90s and 2000s: why they won or flopped, what they cost then and what they sell for now.",
                 "The machines people saved up for: consoles, handhelds, PCs, phones and gadgets. Why each one won or flopped, and what a working one sells for today."),
    "Internet Culture": ("The websites, chat apps and online habits of the 90s and 2000s: who built them, what killed them and where their old pages survive.",
                         "The early web as people lived it: chat rooms, homepages, message boards and the sites everyone had open. What happened to each one."),
    "Gaming": ("Video games and consoles of the 90s and 2000s: the hits, the flops, who owns them now, what they're worth and how to play them today.",
               "The games and consoles of the 90s and 2000s: who made them, who owns them now, what the cartridges and discs are worth, and how to play them today."),
    "Software & Apps": ("Programs people installed from floppy and CD-ROM in the 90s and 2000s: what they did, why they vanished and how to run them now.",
                        "The software that came on floppies and CD-ROMs, from encyclopedias to media players. Why each one vanished and how to run it on a modern computer."),
    "Then vs Now": ("What things cost and how they worked in the 90s and 2000s compared with today, with prices adjusted and the numbers sourced.",
                    "Side-by-side looks at the 90s and 2000s and today: what things cost, how long they lasted and what replaced them, with every figure sourced."),
    "Money & Tech": ("The money behind 90s and 2000s tech: buyouts, bankruptcies, brand sales and what old gadgets and collectibles are worth in 2026.",
                     "Follow the money: the buyouts, bankruptcies and brand auctions behind famous names, and what their old products sell for now."),
    "Music & Entertainment": ("Record stores, video rental, music players and TV of the 90s and 2000s: how they ended, who owns the names and where to find them now.",
                              "Record stores, video rental chains, music players and TV blocks of the 90s and 2000s. How each one ended and where to find what is left."),
}


def build_tag_page(ctx, tag, posts):
    tagged = [p for p in posts if tag in p["tags"]]
    url = f"{BASE_URL}/tags/{tag_slug(tag)}.html"
    content = (f'<a class="page-back page-back-mobile" href="/">&larr; Back</a>\n'
               f'<h1>{esc(tag)}</h1>\n<p class="page-intro">{esc(TAG_COPY.get(tag, ("", ""))[1] or "")} {len(tagged)} stories.</p>\n'
               f'{nav_links_html(ctx["tags"], current=tag)}\n{post_list_html(tagged)}')
    schema = {"@context": "https://schema.org", "@type": "CollectionPage", "name": f"{tag} | {BLOG_NAME}", "url": url,
              "mainEntity": {"@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": i + 1, "url": p["url"], "name": p["displayTitle"]} for i, p in enumerate(tagged)]}}
    head = head_html(ctx, title=branded(f"{tag}"), canonical=url,
                     description=TAG_COPY.get(tag, (f"{len(tagged)} stories about {tag.lower()} from the 90s and 2000s on {BLOG_NAME}.",))[0],
                     schemas=(schema, breadcrumb_schema(("All posts", f"{BASE_URL}/posts/"), (tag, url))))
    return shell_html(ctx, head, body_class="hub-page", window_icon="📁", window_title=tag, content=content,
                      status_text=f"{len(tagged)} posts")


def build_404_page(ctx, posts):
    latest = post_list_html(posts[:5])
    content = (f'<a class="page-back page-back-mobile" href="/">&larr; Back</a>\n'
               '<h1>404: this memory was not found</h1>\n'
               '<p class="page-intro">The page you asked for is not here. It may have moved, or it never existed. '
               'Try the <a href="/posts/">list of every post</a>, or start with one of the latest:</p>\n' + latest
               + nav_links_html(ctx["tags"]))
    head = head_html(ctx, title=branded(f"Page not found"), description="This page does not exist on 404 Memory Found.",
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

# The homepage lists render one page of posts; "Show more" (src/index.html LIST_STEP) adds the rest. Every post is still
# linked from the homepage through the Archives list, and from /posts/ and the topic pages.
LIST_STEP = 24


def list_more_html(total, fn):
    remaining = total - LIST_STEP
    if remaining <= 0:
        return ""
    return (f'\n                <li class="list-more"><button type="button" class="list-more-btn" onclick="{fn}()">'
            f'Show {min(remaining, LIST_STEP)} more posts <span class="list-more-left">({remaining} left)</span></button></li>')


def render_desktop_list(posts):
    items = []
    for p in posts[:LIST_STEP]:
        thumb = p.get("thumb") or p.get("image") or ""
        data_attr = f' data-bg="{thumb}"' if thumb else ""
        items.append(f"""
                <li class="blog-post-item">
                    <a href="{p['path']}">
                        <div class="blog-post-thumb"{data_attr} style="background-color:#c0c0c0;"></div>
                        <div class="blog-post-text">
                            <h3>{esc(p['displayTitle'])}</h3>
                            <div class="date">{p['date']} <span class="reading-time">{p['readingTime']}</span></div>
                            <div class="excerpt">{esc(p['excerpt'])}</div>
                            <div class="tags">{esc(', '.join(p['tags']))}</div>
                        </div>
                    </a>
                </li>""")
    return "".join(items) + list_more_html(len(posts), "showMoreDesktop")


def render_mobile_list(posts):
    items = []
    for p in posts[:LIST_STEP]:
        thumb = p.get("thumb") or p.get("image") or ""
        data_attr = f' data-bg="{thumb}"' if thumb else ""
        items.append(f"""
                <li class="mobile-post-item">
                    <a href="{p['path']}">
                    <div class="mobile-post-thumb"{data_attr} style="background-color:#c0c0c0;"></div>
                    <div class="mobile-post-info">
                        <h3>{esc(p['displayTitle'])}</h3>
                        <div class="mobile-post-date">{p['date']} · {p['readingTime']}</div>
                        <div class="mobile-post-excerpt">{esc(p['excerpt'])}</div>
                        <div class="mobile-post-tags">{esc(' · '.join(p['tags'][:3]))}</div>
                    </div>
                    </a>
                </li>""")
    return "".join(items) + list_more_html(len(posts), "showMoreMobile")


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
                                <a href="{p['path']}">
                                    <div class="title">{esc(p['displayTitle'])}</div>
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


def start_topics_html(tags):
    return "".join(f'<a class="start-menu-item" role="menuitem" href="/tags/{tag_slug(t)}.html">{esc(t)}</a>' for t in tags)


def mobile_start_menu_html(tags):
    topics = "".join(f'<li class="mobile-start-topic"><a href="/tags/{tag_slug(t)}.html">{esc(t)}</a></li>' for t in tags)
    return ('<nav class="mobile-start-menu" id="mobile-start-menu" aria-label="Start menu">'
            '<div class="mobile-start-sidebar" aria-hidden="true"><span>404 Memory Found</span></div><ul>'
            '<li><a href="/"><span aria-hidden="true">🏠</span> Latest posts</a></li>'
            '<li><a href="/posts/"><span aria-hidden="true">📰</span> All posts</a></li>'
            '<li><a href="/dead-brand-index.html"><span aria-hidden="true">🗃️</span> Dead Brand Index</a></li>'
            '<li class="mobile-start-sep" role="separator"></li>'
            '<li class="mobile-start-head"><span aria-hidden="true">📂</span> Topics</li>'
            f'{topics}'
            '<li class="mobile-start-sep" role="separator"></li>'
            '<li><a href="/about.html"><span aria-hidden="true">ℹ️</span> About this site</a></li>'
            '</ul></nav>')


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
        "publisher": organization(ctx),
        "blogPost": [{"@type": "BlogPosting", "headline": p["displayTitle"], "url": p["url"], "datePublished": p["date"],
                      "author": {"@type": "Person", "name": p["authorName"]}}
                     for p in posts[:20]],
    }
    website_schema = {"@context": "https://schema.org", "@type": "WebSite", "@id": BASE_URL + "/#website",
                      "name": BLOG_NAME, "url": BASE_URL + "/", "publisher": {"@id": ORG_ID}}
    seo_meta = f"""    <meta name="description" content="{esc(DEFAULT_DESCRIPTION)}">
    <link rel="canonical" href="{BASE_URL}/">
    <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
    <meta property="og:site_name" content="{BLOG_NAME}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{BASE_URL}/">
    <meta property="og:title" content="{BLOG_NAME}: What Happened to 90s and 2000s Tech">
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
    # The source keeps a plain gtag tag for local previews; the built page gets the same gated loader as every
    # other page, which must run before the AdSense loader in seo_meta.
    gated = gtag_snippet().split("\n", 2)[2].strip()
    out, n = re.subn(r'<script async src="https://www\.googletagmanager\.com/gtag/js\?id=[^"]+"></script>\s*<script>.*?</script>',
                     lambda m: gated, out, count=1, flags=re.DOTALL)
    assert n == 1, "homepage gtag block not found"
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
    replacements += [("<!-- MOBILE_START_MENU -->", mobile_start_menu_html(tags)),
                     ("<!-- START_TOPICS -->", start_topics_html(tags))]
    for old, new in replacements:
        if old not in out:
            raise SystemExit(f"build: expected placeholder not found in src/index.html: {old}")
        out = out.replace(old, new, 1)
    return out


# --------------------------------------------------------------------------- feeds and data

def build_sitemap(posts, tags, authors, today):
    latest = posts[0]["date"] if posts else today

    def url(loc, lastmod, freq, prio, images=()):
        imgs = "".join(f"    <image:image><image:loc>{BASE_URL}{i}</image:loc></image:image>\n" for i in images)
        return f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>{freq}</changefreq>\n    <priority>{prio}</priority>\n{imgs}  </url>\n"

    def post_images(p):
        """Self-hosted photos on the page, so Google Images can index them: people search for pictures of old
        gadgets, and an image result is a click from a real person."""
        found = ([p["heroLocal"]] if p.get("heroLocal") and "<img" not in p["body"] else []) + \
            re.findall(r'<img[^>]+src="(/img/[^"]+)"', p["body"])
        return list(dict.fromkeys(found))[:6]

    body = url(f"{BASE_URL}/", latest, "daily", "1.0")
    body += url(f"{BASE_URL}/posts/", latest, "daily", "0.9")
    body += url(f"{BASE_URL}/dead-brand-index.html", latest, "weekly", "0.9")
    for t in tags:
        tagged = [p for p in posts if t in p["tags"]]
        body += url(f"{BASE_URL}/tags/{tag_slug(t)}.html", tagged[0]["date"] if tagged else latest, "weekly", "0.7")
    for p in posts:
        body += url(p["url"], p.get("updated") or p["date"], "monthly", "0.8", post_images(p))
    for key in authors:
        mine = [p for p in posts if p["authorKey"] == key]
        body += url(f"{BASE_URL}/authors/{key}.html", mine[0]["date"] if mine else latest, "weekly", "0.4")
    for page in ("about.html", "contact.html", "privacy.html", "terms.html"):
        body += url(f"{BASE_URL}/{page}", latest, "yearly", "0.3")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + body + "</urlset>\n")


def build_feed(posts):
    def rfc822(date):
        return format_datetime(datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc))

    items = []
    for p in posts[:20]:
        cats = "".join(f"      <category>{esc(t)}</category>\n" for t in p["tags"])
        media = ""
        pin_local = os.path.join(OUTPUT_DIR, "pins", f"{p['slug']}.jpg")
        og_local = os.path.join(OUTPUT_DIR, "og", f"{p['slug']}.jpg")
        if os.path.exists(pin_local):  # vertical card: what Pinterest and feed readers show
            url, size, w, h = f"{BASE_URL}/pins/{p['slug']}.jpg", os.path.getsize(pin_local), 1000, 1500
        elif os.path.exists(og_local):
            url, size, w, h = p["ogImage"], os.path.getsize(og_local), 1200, 630
        else:
            url = None
        if url:
            media = (f'      <enclosure url="{url}" length="{size}" type="image/jpeg"/>\n'
                     f'      <media:content url="{url}" medium="image" type="image/jpeg" width="{w}" height="{h}"/>\n')
        items.append(f"""    <item>
      <title>{esc(p['displayTitle'])}</title>
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
    <atom:link href="https://pubsubhubbub.appspot.com/" rel="hub"/>
{chr(10).join(items)}
  </channel>
</rss>
"""


# Crawlers that send readers or put the site in front of people: search engines, AI answer engines that cite
# and link their sources, the AdSense crawlers, and link-preview fetchers (Pinterest rich pins, Facebook, X).
# GPTBot and ClaudeBot only train models, but that is how assistants come to know the site exists.
HELPFUL_BOTS = ["Googlebot", "Mediapartners-Google", "AdsBot-Google", "Google-Extended", "Bingbot", "DuckDuckBot",
                "Applebot", "Applebot-Extended", "OAI-SearchBot", "ChatGPT-User", "GPTBot", "Claude-SearchBot",
                "Claude-User", "ClaudeBot", "Claude-Web", "anthropic-ai", "PerplexityBot", "Perplexity-User",
                "DuckAssistBot", "YouBot", "MistralAI-User", "Amazonbot", "CCBot", "Pinterestbot",
                "facebookexternalhit", "Twitterbot"]
# Crawlers that give nothing back (Pedro, 27/11/2026: "the ones that aren't, block them"): SEO tool spiders,
# scrapers that only build training sets or data products, and search engines with no US audience.
# robots.txt only stops the ones that obey it; the JavaScript gate in QUIET_JS keeps the rest away from
# analytics and ads.
BLOCKED_BOTS = ["AhrefsBot", "SemrushBot", "SemrushBot-SA", "MJ12bot", "DotBot", "BLEXBot", "DataForSeoBot",
                "SeekportBot", "serpstatbot", "MegaIndex.ru", "Barkrowler", "SEOkicks", "Bytespider",
                "Meta-ExternalAgent", "FacebookBot", "cohere-ai", "cohere-training-data-crawler", "Diffbot",
                "ImagesiftBot", "Timpibot", "omgili", "omgilibot", "img2dataset", "Scrapy", "PetalBot",
                "PanguBot", "Baiduspider", "Sogou", "Kangaroo Bot", "ISSCyberRiskCrawler"]


def build_robots():
    """Helpful crawlers are named and allowed; the useless ones are named and shut out; anything else may crawl."""
    out = ["User-agent: *", "Allow: /", ""]
    for bot in HELPFUL_BOTS:
        out += [f"User-agent: {bot}", "Allow: /", ""]
    for bot in BLOCKED_BOTS:
        out += [f"User-agent: {bot}", "Disallow: /", ""]
    out += [f"Sitemap: {BASE_URL}/sitemap.xml", f"Sitemap: {BASE_URL}/feed.xml", ""]
    return "\n".join(out)


def html_to_text(fragment):
    """Post body HTML -> Markdown-flavoured plain text for llms-full.txt."""
    t = fragment
    t = re.sub(r"<h2[^>]*>(.*?)</h2>", lambda m: "\n\n## " + strip_tags(m.group(1)) + "\n\n", t, flags=re.S)
    t = re.sub(r"<h3[^>]*>(.*?)</h3>", lambda m: "\n\n### " + strip_tags(m.group(1)) + "\n\n", t, flags=re.S)
    t = re.sub(r"<li[^>]*>(.*?)</li>", lambda m: "- " + strip_tags(m.group(1)) + "\n", t, flags=re.S)
    t = re.sub(r"<a [^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>",
               lambda m: f"{strip_tags(m.group(2))} ({m.group(1) if m.group(1).startswith('http') else BASE_URL + m.group(1)})", t, flags=re.S)
    t = re.sub(r"</p>|<br\s*/?>", "\n\n", t)
    t = re.sub(r"<figcaption[^>]*>.*?</figcaption>", "", t, flags=re.S)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def build_llms_txt(posts, tags, authors):
    lines = [f"# {BLOG_NAME}", "", f"> {DEFAULT_DESCRIPTION}", "",
             "Every article is written under a pen name by the site's editorial team, sourced from primary documents "
             "(company filings, court records, contemporary reporting, museum collections) listed at the end of each post, "
             f"and dated. Full text of every article, in Markdown: {BASE_URL}/llms-full.txt", "",
             "## Hub pages", f"- [All posts]({BASE_URL}/posts/): every article, newest first",
             f"- [About and editorial policy]({BASE_URL}/about.html)", f"- [RSS feed]({BASE_URL}/feed.xml)", ""]
    for t in tags:
        lines += [f"## {t}"]
        for p in posts:
            if t in p["tags"]:
                lines.append(f"- [{p['title']}]({p['url']}): {p['excerpt']}")
        lines.append("")
    lines += ["## Writers"] + [f"- [{a['name']}]({BASE_URL}/authors/{k}.html): {a['beat']}" for k, a in authors.items()] + [""]
    return "\n".join(lines)


def build_llms_full(posts):
    parts = [f"# {BLOG_NAME}: full text of every article", "", f"> {DEFAULT_DESCRIPTION}", "",
             f"Source: {BASE_URL}. Each article below carries its URL, author, publication date, last update, a direct-answer summary, key facts, the article text and its sources.", ""]
    for p in posts:
        head = [f"# {p['title']}", "", f"URL: {p['url']}", f"Author: {p['authorName']} ({BLOG_NAME})",
                f"Published: {p['date']}" + (f"  Updated: {p['updated']}" if p.get("updated") else ""),
                f"Topics: {', '.join(p['tags'])}", ""]
        if p.get("summary"):
            head += ["**Summary:** " + strip_tags(p["summary"]), ""]
        if p.get("facts"):
            head += ["**Key facts:**"] + [f"- {f['label']}: {strip_tags(f['value'])}" for f in p["facts"]] + [""]
        body = html_to_text(p["body"])
        srcs = [""] + (["**Sources:**"] + [f"- {s['title']}: {s['url']}" for s in p.get("sources", [])] if p.get("sources") else [])
        parts += head + [body] + srcs + ["", "---", ""]
    return "\n".join(parts)


def posts_index_json(posts):
    return {"posts": [{
        "id": p["slug"], "title": p["displayTitle"], "date": p["date"], "excerpt": p["excerpt"], "tags": p["tags"],
        "image": p.get("heroLocal") or p.get("image"), "thumb": p.get("thumb") or p.get("heroLocal") or p.get("image"),
        "readingTime": p["readingTime"], "authorName": p["authorName"], "authorKey": p["authorKey"],
    } for p in posts]}


PUBLIC_ENTRIES = {
    "index.html", "404.html", "about.html", "contact.html", "privacy.html", "terms.html",
    "dead-brand-index.html", "dead-brand-index.csv", "dead-brand-index.json", "posts-index.json",
    "assets", "posts", "tags", "authors", "img", "og", "pins",
    "feed.xml", "sitemap.xml", "robots.txt", "llms.txt", "llms-full.txt", "CNAME", "ads.txt",
    "favicon.ico", "favicon-16x16.png", "favicon-32x32.png", "apple-touch-icon.png", "logo-512.png", "og-image.png",
}


def build_jekyll_config():
    """GitHub Pages (branch deploy) runs Jekyll over the repository: everything not listed here stays unpublished.
    Search-engine ownership files (IndexNow key, google*.html, BingSiteAuth.xml) are kept public by pattern."""
    keep_pattern = re.compile(r"^(?:[0-9a-f]{32}\.txt|google[0-9a-f]+\.html|BingSiteAuth\.xml|yandex_[0-9a-f]+\.html)$")
    private = sorted(n for n in os.listdir(OUTPUT_DIR)
                     if n not in PUBLIC_ENTRIES and not n.startswith((".", "_")) and not keep_pattern.match(n))
    lines = ["# Generated by build.py: GitHub Pages publishes only the site, not the tools and data behind it.",
             "exclude:"] + [f'  - "{n}"' for n in private]
    return "\n".join(lines) + "\n"


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
.page-shell button.page-back { cursor: pointer; line-height: inherit; }
.page-shell .share-post { font-weight: bold; }
.page-shell .post-tags { margin: 18px 0 6px; font-size: 13px; color: #444; }
.page-shell .post-tags a { color: #000080; margin-left: 4px; }
.page-shell .post-meta a { color: #000080; }
.page-shell .img-credit { font-size: 12px; color: #555; text-decoration: none; margin-left: 6px; }
.page-shell .img-credit:hover { text-decoration: underline; }
.page-shell .post-body figure, .page-shell .post-hero { margin: 16px auto; max-width: 560px; }
.page-shell .post-body figure img, .page-shell .post-hero img { max-width: 100%; height: auto; display: block; }
.page-shell .post-hero img { width: auto; max-height: 400px; margin: 0 auto; }
.page-shell .post-hero picture { display: block; }
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
.page-shell .page-list-thumb { width: 72px; min-height: 58px; flex-shrink: 0; background: #c0c0c0; border-right: 1px solid #a0a0a0;
  display: flex; align-items: center; justify-content: center; overflow: hidden; }
.page-shell .page-list-thumb img { width: 72px; height: 58px; object-fit: contain; display: block; }
.page-shell .page-list-text { flex: 1; min-width: 0; padding: 8px; display: block; }
.page-shell .page-list-title { display: block; font-size: 14px; font-weight: bold; color: #0000ff; }
.page-shell .page-list-meta { display: block; font-size: 12px; color: #555; margin-top: 2px; }
.page-shell .page-list-excerpt { display: block; font-size: 12px; color: #333; margin-top: 3px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.page-shell .page-copy p, .page-shell .page-copy h3 { margin-bottom: 8px; }
.page-shell .page-copy h3 { margin-top: 12px; }
.page-shell .authors-block { margin-top: 18px; padding-top: 12px; border-top: 1px solid #c0c0c0; }
.page-shell .author-card { background: #fff; border: 1px solid #c0c0c0; padding: 8px 10px; margin: 8px 0; }
.page-shell .author-name { font-weight: bold; color: #000080; text-decoration: none; font-size: 14px; }
.page-shell .author-card .author-beat { margin: 2px 0 4px; }
.page-shell .author-card p { font-size: 13px; margin: 0; }

/* Post header and in-page navigation */
.page-shell .post-breadcrumb { font-size: 13px; color: #555; margin-bottom: 8px; }
.page-shell .post-breadcrumb a { color: #000080; text-decoration: none; }
.page-shell .post-breadcrumb a:hover { text-decoration: underline; }
.page-shell .post-meta-sep { color: #999; margin: 0 2px; }
/* "Jump to" strip: the section list as one toolbar row instead of a tall box standing between the answer and the story */
.page-shell .post-toc { background: #f4f4f4; border: 1px solid #a0a0a0; padding: 7px 10px; margin: 12px 0 22px;
    font-size: 14px; line-height: 1.65; }
.page-shell .post-toc-title { display: inline; margin-right: 6px; font-weight: bold; color: #000080;
    font-family: "MS Sans Serif", Tahoma, Arial, sans-serif; }
.page-shell .post-toc ol { display: inline; margin: 0; padding: 0; list-style: none; }
.page-shell .post-toc li { display: inline; }
.page-shell .post-toc li + li::before { content: "\\00B7"; color: #808080; margin: 0 8px; }
.page-shell .post-toc a { color: #000080; text-decoration: none; }
.page-shell .post-toc a:hover, .page-shell .post-toc a:focus-visible { text-decoration: underline; }
/* The one line under the summary that points at the best part of the story still to come */
.page-shell .post-ahead { margin: 0 0 14px; font-size: 16px; line-height: 1.45; color: #444; }
.page-shell .post-ahead a { color: #000080; font-weight: bold; text-decoration: none; }
.page-shell .post-ahead a:hover, .page-shell .post-ahead a:focus-visible { text-decoration: underline; }
.page-shell .post-body h2 { scroll-margin-top: 52px; }

/* Dead brand index: a reference table people can sort and filter without leaving the page */
.page-shell .brand-index-tools { display: flex; align-items: center; gap: 8px; margin: 14px 0 8px; }
.page-shell .brand-index-tools label { font-size: 13px; font-weight: bold; }
.page-shell .brand-index-tools input { flex: 1; max-width: 340px; padding: 4px 6px; font-family: inherit; font-size: 13px;
    border: 2px inset #c0c0c0; background: #fff; }
.page-shell table.brand-index { width: 100%; border-collapse: collapse; font-size: 13px; background: #fff;
    border: 2px inset #c0c0c0; }
.page-shell table.brand-index th { position: sticky; top: 0; background: #c0c0c0; text-align: left; padding: 6px 8px;
    border: 1px solid #fff; border-right-color: #808080; border-bottom-color: #808080; cursor: pointer;
    font-family: "MS Sans Serif", Tahoma, Arial, sans-serif; white-space: nowrap; }
.page-shell table.brand-index th:hover { background: #d4d0c8; }
.page-shell table.brand-index th button { all: unset; cursor: pointer; display: block; width: 100%; }
.page-shell table.brand-index th button:focus-visible { outline: 1px dotted #000; outline-offset: 2px; }
.page-shell table.brand-index th.sorted::after { content: " \25be"; }
.page-shell table.brand-index th.sorted.asc::after { content: " \25b4"; }
.page-shell table.brand-index td { padding: 5px 8px; border-bottom: 1px solid #e0e0e0; vertical-align: top; }
.page-shell table.brand-index tr:nth-child(even) td { background: #f7f7f7; }
.page-shell table.brand-index a { color: #000080; font-weight: bold; }
.page-shell .brand-index-note { font-size: 12px; color: #444; margin-top: 10px; }
@media (max-width: 640px) {
    .page-shell table.brand-index thead { display: none; }
    .page-shell table.brand-index tr { display: block; border: 1px solid #c0c0c0; margin-bottom: 8px; background: #fff; }
    .page-shell table.brand-index td { display: flex; gap: 8px; border-bottom: 1px dotted #d0d0d0; }
    .page-shell table.brand-index td::before { content: attr(data-label); flex: 0 0 38%; font-weight: bold; color: #333; }
}

.page-shell .brand-index-reuse { margin-top: 18px; padding: 10px 12px; background: #ffffe1; border: 1px solid #c8c86a;
    border-left: 4px solid #000080; font-size: 13px; }
.page-shell .brand-index-reuse h2 { font-size: 15px; margin: 0 0 6px; }
.page-shell .brand-index-reuse p { margin: 0 0 6px; }
.page-shell .brand-index-downloads a { display: inline-block; margin-right: 8px; padding: 2px 10px; background: #c0c0c0;
    border: 2px outset #c0c0c0; color: #000; text-decoration: none; font-weight: bold; }
.page-shell .brand-index-downloads a:active { border-style: inset; }
.page-shell .brand-index-cite { font-family: "Courier New", monospace; font-size: 12px; background: #fff;
    border: 1px solid #c0c0c0; padding: 6px 8px; }
.page-shell .brand-index-snippet { margin: 0 0 6px; padding: 6px 8px; background: #fff; border: 1px inset #c0c0c0;
  font-family: "Courier New", monospace; font-size: 12px; white-space: pre-wrap; word-break: break-all; user-select: all; }

/* Reading flow: a mid-article "Keep reading" card and "Next in the archive" cards, styled as Win95 files */
.keep-reading { margin: 22px 0; border: 2px solid; border-color: #fff #808080 #808080 #fff; background: #c0c0c0; padding: 0 3px 3px; }
.keep-reading-bar { background: linear-gradient(90deg, #000080, #1084d0); color: #fff; font-weight: bold; font-size: 12px;
    padding: 3px 6px; margin: 0 -3px 3px; font-family: "MS Sans Serif", Tahoma, Arial, sans-serif; }
a.archive-card { display: flex; gap: 10px; align-items: center; padding: 8px; background: #fff; color: #000;
    text-decoration: none; border: 1px solid #a0a0a0; margin-bottom: 4px; line-height: 1.35; }
a.archive-card:hover, a.archive-card:focus { background: #000080; color: #fff; outline: 1px dotted #fff; outline-offset: -3px; }
a.archive-card img { width: 96px; height: 72px; object-fit: cover; flex: 0 0 96px; margin: 0; border: 1px solid #808080; }
.archive-card-icon { font-size: 34px; flex: 0 0 96px; text-align: center; }
.archive-card-text { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.archive-card-text strong { font-size: 15px; color: inherit; }
.archive-card-text span { font-size: 13px; color: inherit; opacity: .8; }
.related-posts { margin-top: 22px; }
.related-posts-title { font-weight: bold; font-size: 14px; margin-bottom: 6px; font-family: "MS Sans Serif", Tahoma, Arial, sans-serif; }
.post-body figure { margin: 18px 0; }
.post-body figcaption { font-size: 12px; color: #555; margin-top: 2px; }
.read-meter { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; color: #000; margin-right: 8px; }
.read-meter-track { width: 90px; height: 12px; background: #fff; border: 1px solid; border-color: #808080 #fff #fff #808080; padding: 1px; }
.read-meter-fill { display: block; height: 100%; width: 0; background: repeating-linear-gradient(90deg, #000080 0 7px, transparent 7px 9px); }
@media (max-width: 768px) {
    a.archive-card img { width: 72px; height: 54px; flex-basis: 72px; }
    .archive-card-icon { flex-basis: 72px; }
    .read-meter-track { width: 70px; }
}

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
.source-host { color: #555; font-size: 12px; margin-left: 4px; }
.affiliate-disclosure { font-size: 12px; color: #555; margin: 6px 0 10px 0; font-style: italic; }
.post-body .table-wrap, .post-body table { max-width: 100%; }
.post-body table { border-collapse: collapse; font-size: 13px; margin: 12px 0; width: 100%; font-variant-numeric: tabular-nums; }
.post-body th, .post-body td { border: 1px solid #a0a0a0; padding: 4px 6px; text-align: left; vertical-align: top; }
.post-body th { background: #dfdfdf; font-family: "MS Sans Serif", Tahoma, Arial, sans-serif; }
.post-body tr:nth-child(even) td { background: #f4f4f4; }
.post-body td a { color: #000080; }

/* Reading mode. The article used to sit in an 850x620 window with its own scrollbar, so readers
   scrolled a box inside the page and the browser's own scroll, find-in-page and reader view did not
   apply. Generated pages now open the window "maximized" into the document: the page scrolls like any
   site, the Win95 title bar sticks to the top and the taskbar to the bottom. */
/* Only the root scrolls. If body also gets overflow, it becomes the scroll container that sticky
   elements attach to, and since body itself never scrolls the title bar and taskbar stop sticking. */
html:has(body.page-shell) { height: auto; min-height: 100%; overflow-x: hidden; overflow-y: auto; }
body.page-shell { height: auto; min-height: 100%; overflow: visible; }
body.page-shell { user-select: text; }
.page-shell .post-body, .page-shell .page-card { user-select: text; }

@media (min-width: 769px) {
    .page-shell .page-back-mobile { display: none; }
    .page-shell .page-mobile-footer { display: none; }
    .page-shell .desktop-container { height: auto; min-height: 100vh; }
    .page-shell .desktop-area { flex: 1 0 auto; overflow: visible; padding: 18px 0 28px; }
    .page-shell #post-window { position: relative !important; left: auto !important; top: auto !important;
        width: min(920px, calc(100% - 250px)) !important; height: auto !important; margin: 0 auto !important;
        overflow: visible !important; }
    .page-shell #post-window .title-bar { position: sticky; top: 0; z-index: 30; }
    .page-shell #post-window .window-content { flex: none; overflow: visible !important; height: auto !important; padding: 10px; }
    .page-shell .resize-handle { display: none !important; }
    .page-shell .taskbar { position: sticky; bottom: 0; }
    .page-shell .start-menu { position: fixed; bottom: 38px; }
    .page-shell .page-card { max-width: 760px; margin: 0 auto; padding: 24px 36px 32px; background: #fff;
        border: 2px solid; border-top-color: #808080; border-left-color: #808080; border-right-color: #fff; border-bottom-color: #fff; }
    .page-shell .post-header h1 { font-size: 30px; line-height: 1.2; margin-bottom: 8px; }
    .page-shell .post-meta { font-size: 13px; }
    .page-shell .post-body { font-size: 18px; line-height: 1.7; color: #1a1a1a; }
    .page-shell .post-body h2 { font-size: 23px; line-height: 1.3; margin: 30px 0 10px; color: #000080; }
    .page-shell .post-body h3 { font-size: 19px; margin: 22px 0 8px; color: #000080; }
    .page-shell .post-body p { margin-bottom: 16px; }
    .page-shell .post-summary { font-size: 18px; }
}
@media (min-width: 769px) and (max-width: 1099px) {
    .page-shell .desktop-icons { display: none; }
    .page-shell #post-window { width: calc(100% - 40px) !important; }
}

@media (max-width: 768px) {
    .page-shell .desktop-container { display: block; height: auto; min-height: 100vh; }
    .page-shell .desktop-area { display: block; position: relative; overflow: visible; }
    .page-shell .desktop-icons, .page-shell .taskbar, .page-shell .footer, .page-shell .start-menu,
    .page-shell .resize-handle, .page-shell .window-button { display: none !important; }
    .page-shell #post-window { position: static !important; left: auto !important; top: auto !important;
        width: 100% !important; height: auto !important; display: block !important; overflow: visible !important; background: #008080; }
    .page-shell .title-bar { background: linear-gradient(90deg, #000080 0%, #1084d0 100%); color: #fff; padding: 8px 12px;
        display: flex; align-items: center; justify-content: space-between; flex-shrink: 0;
        font-family: "MS Sans Serif", Tahoma, Arial, sans-serif; border-bottom: 2px solid #000;
        position: sticky; top: 0; z-index: 30; }
    .page-shell .title-bar-title { font-size: 15px; font-weight: bold; display: flex; align-items: center; gap: 6px; overflow: hidden; min-width: 0; }
    .page-shell .title-bar-title span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .page-shell .window-content { overflow: visible; background: #c0c0c0; padding: 0 0 64px; }
    .page-shell .page-card { background: #fff; margin: 6px; padding: 12px; border: 2px solid;
        border-top-color: #fff; border-left-color: #fff; border-right-color: #808080; border-bottom-color: #808080; }
    .page-shell .post-header h1 { font-size: 25px; color: #000080; margin-bottom: 6px; line-height: 1.2; font-weight: bold; }
    .page-shell .post-meta { font-size: 12px; color: #666; margin-bottom: 14px; padding-bottom: 8px; border-bottom: 1px solid #c0c0c0; }
    .page-shell .post-body { font-size: 17px; line-height: 1.7; color: #1a1a1a; }
    .page-shell .post-body img, .page-shell .post-hero img { max-width: 100%; height: auto; margin: 10px 0; border: 2px solid;
        border-top-color: #808080; border-left-color: #808080; border-right-color: #fff; border-bottom-color: #fff; }
    .page-shell .post-body p { margin-bottom: 12px; }
    .page-shell .post-body h2, .page-shell .post-body h3 { margin-top: 18px; margin-bottom: 8px; color: #000080; }
    .page-shell .post-body a { color: #000080; text-decoration: underline; }
    .page-shell .page-back-desktop { display: none; }
    .page-shell .page-mobile-footer { display: flex; position: fixed; left: 0; right: 0; bottom: 0; z-index: 40; }
    .page-shell .mobile-footer-start { text-decoration: none; color: #000; }
    .page-shell .page-copy { font-size: 14px; line-height: 1.6; }
    .quick-facts dt { flex-basis: 40%; }
    /* The headline that tells a searcher "right page" must outrank the section headings below it */
    .page-shell .post-body h2 { font-size: 21px; line-height: 1.3; }
    .page-shell .post-body h3 { font-size: 18px; line-height: 1.35; }
    .page-shell .post-ahead { font-size: 15px; }
    /* A portrait photo used to fill a whole phone screen before the story; show it whole in a short viewer */
    .page-shell .post-hero img { width: 100%; max-height: 220px; object-fit: contain; background: #c0c0c0; }
    .page-shell .post-body a.archive-card img { width: 72px; height: 54px; }
}

/* CRT scanlines stay on the teal desktop. Over the article they cut the contrast of every line of text and every photo,
   so on generated pages they are painted into the desktop background, under the window, instead of over it. */
body.page-shell::before { display: none; }
body.page-shell { background: repeating-linear-gradient(0deg, rgba(0, 0, 0, .08) 0 2px, transparent 2px 4px),
    linear-gradient(135deg, #008080 0%, #106B6B 100%); }

/* Maximize is shown the way Win95 shows a control a fixed-size window cannot use: greyed and embossed */
.page-shell .window-button:disabled { cursor: default; }
.page-shell .window-button:disabled .btn-maximize { border-color: #808080; box-shadow: 1px 1px 0 #fff; }
.page-shell .window-button:disabled .btn-maximize::after { background: #808080; }

/* Next-story cards now sit inside the article body, where body link styles would otherwise restyle them */
.page-shell .post-body .related-posts { margin: 32px 0 28px; }
.page-shell .post-body a.archive-card { color: #000; text-decoration: none; }
.page-shell .post-body a.archive-card:hover, .page-shell .post-body a.archive-card:focus { color: #fff; }
.page-shell .post-body a.archive-card img { width: 96px; height: 72px; max-width: none; margin: 0; border: 1px solid #808080; }
@media (max-width: 768px) {
    .page-shell .post-body a.archive-card img { width: 72px; height: 54px; }
}

/* Wide screens: Quick facts becomes a Properties pane beside the article, so the story starts right after the answer.
   Narrower screens get the same box as a recap at the end of the story. */
@media (min-width: 1400px) {
    .page-shell.post-page #post-window { width: min(1100px, calc(100% - 250px)) !important; }
    .page-shell.post-page .page-card { margin: 0 300px 0 0; }
    .page-shell.post-page .quick-facts { position: absolute; top: 32px; right: 13px; width: 270px; margin: 0; padding: 0 3px 3px;
        background: #c0c0c0; border: 2px solid; border-color: #fff #808080 #808080 #fff; }
    .page-shell.post-page .quick-facts-title { background: linear-gradient(90deg, #000080, #1084d0); color: #fff; font-size: 12px;
        padding: 3px 6px; margin: 0 -3px 3px; }
    .page-shell.post-page .quick-facts dl { background: #fff; border: 1px solid; border-color: #808080 #fff #fff #808080; padding: 6px 10px; }
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
    inbound_related = build_related_map(posts)
    starved = [s for s, n in inbound_related.items() if n == 0]
    if starved:
        print(f"⚠️  {len(starved)} posts still receive no related link: {', '.join(starved[:5])}")
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
        "today": today,
        "today_label": datetime.strptime(today, "%Y-%m-%d").strftime("%d %B %Y").lstrip("0"),
        "desktop_icons": extract_div_by_marker(source, 'class="desktop-icons">'),
        "taskbar": extract_div_by_marker(source, 'class="taskbar">'),
        "footer": extract_div_by_marker(source, 'class="footer">'),
        "start_menu": extract_div_by_marker(source, 'class="start-menu" id="start-menu">').replace(
            "<!-- START_TOPICS -->", start_topics_html(tags)),
        "mobile_start_menu": mobile_start_menu_html(tags),
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
    write("posts/index.html", build_posts_index_page(ctx, posts))
    index_rows = brand_index_rows(posts)
    write("dead-brand-index.html", build_brand_index_page(ctx, posts))
    # A reference table only earns links when other people can take the data with them.
    write("dead-brand-index.json", json.dumps(
        {"name": "The dead brand index", "source": f"{BASE_URL}/dead-brand-index.html",
         "updated": today, "licence": "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/): free to reuse with credit and a link to the source page.",
         "count": len(index_rows),
         "brands": [{"name": r["name"], "started": r["started"], "status2026": r["status"],
                     "owner2026": r["owner"], "source": BASE_URL + r["url"]} for r in index_rows]},
        ensure_ascii=False, indent=1))
    csv_buf = io.StringIO()
    writer = csv.writer(csv_buf)
    writer.writerow(["name", "started", "status_2026", "owner_2026", "source"])
    for r in index_rows:
        writer.writerow([r["name"], r["started"], r["status"], r["owner"], BASE_URL + r["url"]])
    write("dead-brand-index.csv", csv_buf.getvalue())
    print(f"🗃️  dead-brand-index.html + .csv + .json ({len(index_rows)} brands)")

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

    # posts/<slug>.json fed the retired in-window reader; nothing reads them now, so the cleanup below removes them
    keep = {f"{s}.html" for s in by_slug} | {f"{o}.html" for o in redirects} | {"index.html"}
    for name in os.listdir(os.path.join(OUTPUT_DIR, "posts")):
        if name not in keep and (name.endswith(".html") or name.endswith(".json")):
            os.remove(os.path.join(OUTPUT_DIR, "posts", name))
            print(f"   🗑  removed stale posts/{name}")

    write("_config.yml", build_jekyll_config())

    print("🗺️  sitemap.xml, feed.xml, robots.txt, llms.txt, llms-full.txt, CNAME" + (", ads.txt" if config.get("ads_txt") else ""))
    write("sitemap.xml", build_sitemap(posts, tags, authors, today))
    write("feed.xml", build_feed(posts))
    write("robots.txt", build_robots())
    write("llms.txt", build_llms_txt(posts, tags, authors))
    write("llms-full.txt", build_llms_full(posts))
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
