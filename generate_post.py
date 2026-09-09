#!/usr/bin/env python3
"""
Write one or more new posts for 404 Memory Found with Claude and append them to posts.json.

Flow per post
  1. Pick a topic: the first unpublished entry in topic-backlog.json, or a --topic override.
     If the backlog is empty, research ten new topics first (web search) and add them to the backlog.
  2. Research: Claude searches the web for facts, dates, prices and primary sources.
  3. Write: Claude turns the research into a post that follows POST_SPEC.md (structured JSON output).
  4. Validate against the spec (length, title, FAQ, sources, tags). One rewrite on failure.
  5. Find a Wikimedia Commons image (free licence) for the hero.
  6. Append to posts.json and mark the backlog entry published.

Then run: python fetch_images.py && python make_og_cards.py && python build.py
(the daily-post workflow does all of this on a schedule).

Requires ANTHROPIC_API_KEY (or an `ant auth login` profile) and `pip install anthropic`.
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import date
from urllib.parse import quote
from urllib.request import Request, urlopen

import anthropic

MODEL = "claude-opus-5"
ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_TAGS = ["Business Blunders", "Hardware", "Internet Culture", "Gaming", "Software & Apps",
             "Then vs Now", "Money & Tech", "Music & Entertainment"]
USER_AGENT = "404MemoryFound-build/1.0 (https://404memoryfound.com; hello@404memoryfound.com)"
FREE_LICENCES = ("cc0", "cc by", "cc-by", "public domain", "pd", "gfdl", "attribution")

client = anthropic.Anthropic()


def path(name):
    return os.path.join(ROOT, name)


def load(name, default):
    p = path(name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def save(name, data):
    with open(path(name), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def text_of(message):
    return "".join(b.text for b in message.content if b.type == "text")


def word_count(html_body):
    return len(re.sub(r"<[^>]+>", " ", html_body).split())


# --------------------------------------------------------------------------- topics

def pending_topics(backlog):
    out = []
    for key, items in backlog.items():
        if key.startswith("_"):
            continue
        for t in items:
            if t.get("status") != "published":
                out.append((key, t))
    return out


def research_topics(posts, backlog, spec):
    """Ask Claude for ten new, searchable topics that the site has not covered."""
    existing = "\n".join(f"- {p['id']}: {p['title']}" for p in posts)
    schema = {
        "type": "object",
        "properties": {"topics": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "slug": {"type": "string"},
                "primary_keyword": {"type": "string"},
                "why_now": {"type": "string"},
                "angle": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string", "enum": SITE_TAGS}},
                "persona": {"type": "string", "enum": ["marcus", "dana", "theo"]},
                "target_keywords": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "slug", "primary_keyword", "why_now", "angle", "tags", "persona", "target_keywords"],
            "additionalProperties": False,
        }}},
        "required": ["topics"],
        "additionalProperties": False,
    }
    prompt = f"""You plan content for 404 Memory Found, a nostalgia site about the technology, games, websites and companies
of the 1990s and 2000s. Readers are 25 to 45, mostly in the US, arriving from Google.

Propose 10 new post topics with real search demand that the site has NOT covered. Use web search to check what
people ask about (People Also Ask, forum threads, "what happened to" queries) and to avoid subjects with a strong
existing answer from a major publisher. Prefer: products people still own or buy second-hand, companies with a
clear rise-and-fall, "X vs today" comparisons with real prices, and questions with a surprising factual answer.
Spread the topics across the site's beats: marcus = consoles/handhelds/hardware, dana = dot-com companies and
internet culture, theo = software, formats, everyday gadgets and then-vs-now money.

Titles must follow the spec below (45 to 60 characters, at most 3 of 10 starting with "What Happened to").
Slugs: lowercase, 3 to 7 words, keyword first.

Already covered (do not repeat these subjects; a different angle on the same subject is only acceptable if
the keyword is clearly different):
{existing}

Post spec for reference:
{spec}"""
    with client.messages.stream(
        model=MODEL, max_tokens=32000,
        tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 12}],
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        notes = stream.get_final_message()
    # Second pass: structure the answer (structured outputs cannot run alongside server tools)
    structured = client.messages.create(
        model=MODEL, max_tokens=16000,
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": "Return the 10 topics from this research as JSON:\n\n" + text_of(notes)}],
    )
    topics = json.loads(text_of(structured))["topics"]
    slugs = {p["id"] for p in posts} | {t["slug"] for _, t in pending_topics(backlog)}
    fresh = [dict(t, status="pending", added=str(date.today())) for t in topics if t["slug"] not in slugs]
    backlog.setdefault("priority_2_medium_high", []).extend(fresh)
    backlog["_last_updated"] = str(date.today())
    save("topic-backlog.json", backlog)
    print(f"  researched {len(fresh)} new topics")
    return fresh


# --------------------------------------------------------------------------- research + write

def research(topic, spec):
    prompt = f"""Research this subject for a short, sourced article. Use web search generously (at least 6 searches).

Subject: {topic['title']}
Angle: {topic.get('angle', '')}
Keywords readers use: {', '.join(topic.get('target_keywords', []))}

Collect, with a URL for each: launch date and company; original price and (if known) units sold; the key
turning points with dates; who made the decisions; what replaced it; current status (is it still sold, what do
originals sell for second-hand, any relaunch); the three questions people most often ask about it; two or three
surprising, verifiable details. Prefer primary sources: company statements, SEC filings, court records,
contemporary newspaper reports, museum collections. Use Wikipedia only as a last resort and say so.

Output plain research notes, each fact followed by its source URL. Flag anything you could not confirm."""
    with client.messages.stream(
        model=MODEL, max_tokens=32000,
        tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 15}],
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        msg = stream.get_final_message()
    return text_of(msg)


POST_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "slug": {"type": "string"},
        "excerpt": {"type": "string"},
        "summary": {"type": "string"},
        "facts": {"type": "array", "items": {"type": "object", "properties": {
            "label": {"type": "string"}, "value": {"type": "string"}},
            "required": ["label", "value"], "additionalProperties": False}},
        "body": {"type": "string"},
        "sources": {"type": "array", "items": {"type": "object", "properties": {
            "title": {"type": "string"}, "url": {"type": "string"}},
            "required": ["title", "url"], "additionalProperties": False}},
        "tags": {"type": "array", "items": {"type": "string", "enum": SITE_TAGS}},
        "author": {"type": "string", "enum": ["marcus", "dana", "theo"]},
        "linkPhrases": {"type": "array", "items": {"type": "string"}},
        "imageSearch": {"type": "array", "items": {"type": "string"}},
        "imageAlt": {"type": "string"},
        "imageCaption": {"type": "string"},
        "seo": {"type": "object", "properties": {
            "title": {"type": "string"}, "description": {"type": "string"},
            "keywords": {"type": "array", "items": {"type": "string"}}},
            "required": ["title", "description", "keywords"], "additionalProperties": False},
    },
    "required": ["title", "slug", "excerpt", "summary", "facts", "body", "sources", "tags", "author",
                 "linkPhrases", "imageSearch", "imageAlt", "imageCaption", "seo"],
    "additionalProperties": False,
}


def write_post(topic, notes, posts, authors, spec, feedback=""):
    link_targets = "\n".join(f"- /posts/{p['id']}.html : {p['title']}" for p in posts[:200])
    author_lines = "\n".join(f"- {k}: {a['name']}, {a['beat']}" for k, a in authors.items() if not k.startswith("_"))
    prompt = f"""Write a post for 404 Memory Found following the spec exactly.

SPEC
{spec}

SUBJECT: {topic['title']}
ANGLE: {topic.get('angle', '')}
KEYWORDS: {', '.join(topic.get('target_keywords', []))}
SUGGESTED AUTHOR: {topic.get('persona', 'theo')}

AUTHORS (pick by beat)
{author_lines}

RESEARCH NOTES (use only facts that appear here, with their sources; do not add unsourced numbers)
{notes}

EXISTING POSTS you may link to inside the prose (2 or 3 links, on natural phrases, only where relevant):
{link_targets}

BODY RULES: `body` is HTML containing only <h2>, <h3>, <p>, <ul>/<li>, <a> and <strong>. It starts with the first
<h2> (the summary is a separate field and is rendered above it). It ends with <h2>Frequently Asked Questions</h2>
followed by exactly three <h3> questions each answered in one <p>. No image tags. No "Sources" section in the body
(sources is a separate field). Use straight quotes, no em dashes, no markdown.
{('REVIEWER FEEDBACK ON YOUR PREVIOUS DRAFT, FIX ALL OF IT: ' + feedback) if feedback else ''}"""
    with client.messages.stream(
        model=MODEL, max_tokens=24000,
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": POST_SCHEMA}},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        msg = stream.get_final_message()
    return json.loads(text_of(msg))


def validate(post, existing_slugs):
    problems = []
    body = post["body"]
    n = word_count(re.split(r"<h2>\s*Frequently Asked Questions\s*</h2>", body, flags=re.I)[0])
    if not 800 <= n <= 1450:
        problems.append(f"body is {n} words before the FAQ; the spec asks for 900 to 1300")
    if not 40 <= len(post["title"]) <= 65:
        problems.append(f"title is {len(post['title'])} characters; needs 45 to 60")
    if not 110 <= len(post["excerpt"]) <= 160:
        problems.append(f"excerpt (meta description) is {len(post['excerpt'])} characters; needs 120 to 155")
    if not re.search(r"<h2>\s*Frequently Asked Questions\s*</h2>", body, re.I):
        problems.append("missing the <h2>Frequently Asked Questions</h2> section")
    faq = re.split(r"<h2>\s*Frequently Asked Questions\s*</h2>", body, flags=re.I)[-1]
    if len(re.findall(r"<h3>.*?\?.*?</h3>", faq)) != 3:
        problems.append("FAQ must contain exactly three <h3> questions")
    if len(re.findall(r"<h2>", body)) < 5:
        problems.append("fewer than 4 section headings plus the FAQ")
    if len(post["sources"]) < 3:
        problems.append("fewer than 3 sources")
    if not all(s["url"].startswith("http") for s in post["sources"]):
        problems.append("a source URL is not an http(s) link")
    if not post["tags"] or not set(post["tags"]) <= set(SITE_TAGS):
        problems.append("tags must be 1 to 3 of the site tags")
    if "<img" in body or "—" in body or "—" in post["summary"]:
        problems.append("body contains an image tag or an em dash")
    if post["slug"] in existing_slugs:
        problems.append(f"slug {post['slug']} already exists")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+){2,7}", post["slug"]):
        problems.append("slug must be lowercase words joined by hyphens, 3 to 8 words")
    return problems


# --------------------------------------------------------------------------- image

def commons_candidates(query):
    """Free-licence JPEG/PNG hits for a Commons search, with title, description and licence for Claude to judge."""
    url = ("https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrlimit=12"
           f"&gsrsearch={quote(query)}&prop=imageinfo&iiprop=url%7Cextmetadata%7Csize%7Cmime&iiurlwidth=960&format=json")
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as r:
        data = json.load(r)
    out = []
    for page in sorted(data.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99)):
        ii = page["imageinfo"][0]
        meta = ii.get("extmetadata", {})
        licence = (meta.get("LicenseShortName", {}).get("value") or "").lower()
        if ii.get("mime") not in ("image/jpeg", "image/png"):
            continue
        if ii.get("width", 0) < 640 or not any(k in licence for k in FREE_LICENCES):
            continue
        desc = re.sub(r"<[^>]+>", "", meta.get("ImageDescription", {}).get("value") or "")[:200]
        out.append({"title": page["title"], "description": desc, "licence": licence,
                    "url": normalize_commons_url(ii.get("thumburl") or ii.get("url"))})
    return out


def pick_image(post, candidates):
    """Commons search matches on file names, so 'Furby' returns church ruins in Sweden. Let Claude choose or reject."""
    listing = "\n".join(f"{i}. {c['title']} | {c['licence']} | {c['description']}" for i, c in enumerate(candidates))
    schema = {"type": "object", "properties": {"index": {"type": "integer"}, "caption": {"type": "string"},
                                               "alt": {"type": "string"}},
              "required": ["index", "caption", "alt"], "additionalProperties": False}
    msg = client.messages.create(
        model=MODEL, max_tokens=2000,
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": (
            f"Post title: {post['title']}\nSummary: {post['summary']}\n\nCandidate images from Wikimedia Commons:\n"
            f"{listing}\n\nReturn the index of the image that actually shows the subject of the post (the product, "
            "company, website or person), or -1 if none does. Never pick a place, building or unrelated object that "
            "merely shares the name. Also return a one-sentence caption that is accurate for that exact image "
            "(say if it is a later model or a museum display) and descriptive alt text.")}],
    )
    return json.loads(text_of(msg))


def commons_search(query, post=None):
    candidates = commons_candidates(query)
    if not candidates:
        return None
    if post is None:
        return candidates[0]["url"]
    choice = pick_image(post, candidates)
    if 0 <= choice["index"] < len(candidates):
        post["imageCaption"] = choice["caption"] or post.get("imageCaption", "")
        post["imageAlt"] = choice["alt"] or post.get("imageAlt", "")
        return candidates[choice["index"]]["url"]
    return None


def normalize_commons_url(url):
    """The API returns thumb.wikimedia.org URLs with tracking params; store the canonical upload.wikimedia.org form."""
    url = url.split("?")[0]
    return re.sub(r"^https://thumb\.wikimedia\.org/", "https://upload.wikimedia.org/", url)


def find_image(post):
    for q in post.get("imageSearch", [])[:4]:
        try:
            hit = commons_search(q, post)
        except Exception as e:  # noqa: BLE001
            print(f"  commons search failed for {q!r}: {e}")
            hit = None
        if hit:
            print(f"  image: {hit[-60:]}  (query: {q})")
            return hit
        time.sleep(1)
    print("  no free image found; post will publish without a hero")
    return None


# --------------------------------------------------------------------------- main

def make_post(topic, posts, authors, spec):
    print(f"• {topic['title']}")
    notes = research(topic, spec)
    print(f"  research: {len(notes.split())} words of notes")
    existing = {p["id"] for p in posts}
    draft = write_post(topic, notes, posts, authors, spec)
    problems = validate(draft, existing)
    if problems:
        print("  rewrite needed: " + "; ".join(problems))
        draft = write_post(topic, notes, posts, authors, spec, feedback="; ".join(problems))
        problems = validate(draft, existing)
        if problems:
            raise SystemExit("  still failing the spec after one rewrite: " + "; ".join(problems))
    image = find_image(draft)
    post = {
        "id": draft["slug"],
        "title": draft["title"],
        "date": str(date.today()),
        "author": draft["author"],
        "tags": draft["tags"][:3],
        "excerpt": draft["excerpt"],
        "summary": draft["summary"],
        "facts": draft["facts"][:5],
        "image": image,
        "imageAlt": draft["imageAlt"],
        "imageCaption": draft["imageCaption"],
        "body": draft["body"],
        "sources": draft["sources"][:6],
        "linkPhrases": draft["linkPhrases"][:3],
        "seo": {"title": draft["seo"]["title"][:70], "description": draft["seo"]["description"][:160],
                "keywords": draft["seo"]["keywords"][:8]},
    }
    print(f"  written: {word_count(post['body'])} words, {len(post['sources'])} sources, author {post['author']}")
    return post


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--topic", default="", help="force a subject instead of using the backlog")
    args = ap.parse_args()

    spec = open(path("POST_SPEC.md"), encoding="utf-8").read()
    data = load("posts.json", {"posts": []})
    posts = sorted(data["posts"], key=lambda p: p["date"], reverse=True)
    authors = load("authors.json", {})
    backlog = load("topic-backlog.json", {})

    written = 0
    for _ in range(max(1, args.count)):
        if args.topic and written == 0:
            topic = {"title": args.topic, "angle": "", "target_keywords": [args.topic.lower()], "persona": "theo"}
            key = None
        else:
            pending = pending_topics(backlog)
            if not pending:
                research_topics(posts, backlog, spec)
                pending = pending_topics(backlog)
            if not pending:
                raise SystemExit("no topics available")
            key, topic = pending[0]
        post = make_post(topic, posts, authors, spec)
        data["posts"].insert(0, post)
        posts.insert(0, post)
        save("posts.json", data)
        if key:
            topic["status"] = "published"
            topic["published_slug"] = post["id"]
            backlog["_last_updated"] = str(date.today())
            save("topic-backlog.json", backlog)
        written += 1
    print(f"\n{written} post(s) added to posts.json")


if __name__ == "__main__":
    sys.exit(main())
