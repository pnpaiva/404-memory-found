# 404 Memory Found

Nostalgia blog about the technology, games, websites and companies of the 90s and 2000s, served as a
Windows 95 desktop. Static site on GitHub Pages at https://404memoryfound.com.

## How publishing works

```
topic-backlog.json ──► generate_post.py ──► posts.json ──► fetch_images.py ──► make_og_cards.py ──► build.py ──► GitHub Pages
      (topics)          (Claude writes)     (source of truth)   (/img)            (/og)           (html, json, sitemap, feed)
```

- **Daily post** (`.github/workflows/daily-post.yml`) runs at 11:00 UTC: writes one post with Claude, fetches its image,
  makes its share card, rebuilds and pushes. Run it by hand from the Actions tab with a `count` (posts per run) and an
  optional `topic`.
- **Build** (`.github/workflows/build.yml`) rebuilds whenever `posts.json`, `build.py` or `src/` change on `main`.
- Writers are pen names defined in `authors.json`. No photos, no personal details. Bylines link to `/authors/<key>.html`.
- Every new post follows `POST_SPEC.md`: 900 to 1,300 words, direct answer first, quick facts, three FAQ questions,
  a sources list, one free-licence image. The generator rejects drafts that miss the spec and rewrites once.

## One-time setup (owner only)

1. **API key for the writer.** Repository → Settings → Secrets and variables → Actions → New repository secret
   `ANTHROPIC_API_KEY`. Without it the daily workflow fails at the "Write new post(s)" step and nothing is published.
   Cost is roughly $0.50 to $1.50 per post at Opus 5 rates (research with web search plus one structured write).
2. **AdSense.** Apply at https://adsense.google.com with the site URL. Once approved, put the publisher id in
   `site-config.json` → `adsense_client` (`ca-pub-…`) and the `ads.txt` line in `ads_txt`, commit, and the next build
   injects Auto ads on every page and writes `/ads.txt`. The privacy page already carries the required disclosure.
3. **Affiliate links (optional).** eBay Partner Network campaign id → `ebay_campaign_id`; Amazon Associates tag →
   `amazon_tag`. The build then tags every eBay/Amazon link in post bodies as `rel="sponsored"` with tracking and
   shows the disclosure under the post. Posts about products carry a "Where to find one today" paragraph for this.
4. **Search Console.** Submit `https://404memoryfound.com/sitemap.xml` and request indexing for `/`, `/posts/` and the
   eight `/tags/` pages.

## Local commands

```bash
python3 build.py                 # regenerate everything from posts.json + src/index.html
python3 fetch_images.py          # download/resize any new Wikimedia images referenced in posts.json
python3 make_og_cards.py         # generate missing share cards in /og
python3 generate_post.py --count 1          # needs ANTHROPIC_API_KEY and Python 3.10+
python3 -m http.server 8404      # preview at http://localhost:8404
```

## Files

| Path | What it is |
|---|---|
| `src/index.html` | The desktop SPA (CSS + JS inline). Edit here, never in the generated `index.html`. |
| `posts.json` | Every post. `body` is HTML. New-format posts also carry `summary`, `facts`, `sources`, `linkPhrases`. |
| `authors.json` | Pen names, beats and bios. |
| `site-config.json` | AdSense id, ads.txt line, affiliate ids, disclosure text. |
| `redirects.json` | Old slug → new slug. The build writes canonical + meta-refresh stubs for old URLs. |
| `images-manifest.json` | Wikimedia URL → local file, written by `fetch_images.py`. |
| `topic-backlog.json` | Topics to write. The generator refills it with ten researched topics when it runs dry. |
| `POST_SPEC.md` | The editorial spec the generator enforces. |
| `CONTENT_CALENDAR.md` | Original 50-topic research from March 2026, still a useful idea list. |
