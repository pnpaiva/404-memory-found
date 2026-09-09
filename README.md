# 404 Memory Found

Nostalgia blog about the technology, games, websites and companies of the 90s and 2000s, served as a
Windows 95 desktop. Static site on GitHub Pages at https://404memoryfound.com.

## How publishing works

```
topic-backlog.json ──► generate_post.py ──► posts.json ──► fetch_images.py ──► make_og_cards.py ──► build.py ──► GitHub Pages
      (topics)          (Claude writes)     (source of truth)   (/img)            (/og)           (html, json, sitemap, feed)
```

- **Publishing routine.** A Claude cloud routine ("404 Memory Found: write and publish one post", managed at
  https://claude.ai/code/routines) runs four times a day at 06:00, 11:00, 16:00 and 21:00 UTC. Each run clones the
  repo, picks or researches a topic, writes one post to `POST_SPEC.md`, validates it, fetches the image, makes the
  share card, builds, pushes to `main` and pings IndexNow. No API key needed; it runs on the Claude subscription.
- **Fallback writer** (`.github/workflows/daily-post.yml`, manual trigger only) does the same with the Anthropic API
  (`generate_post.py`) if the routine is ever paused. It needs the `ANTHROPIC_API_KEY` secret.
- **Build** (`.github/workflows/build.yml`) rebuilds whenever `posts.json`, `build.py` or `src/` change on `main`.
- Writers are pen names defined in `authors.json`. No photos, no personal details. Bylines link to `/authors/<key>.html`.
- Every new post follows `POST_SPEC.md`: 900 to 1,300 words, direct answer first, quick facts, three FAQ questions,
  a sources list, one free-licence image. The generator rejects drafts that miss the spec and rewrites once.

## One-time setup (owner only)

1. **API key for the fallback writer (optional).** Repository → Settings → Secrets and variables → Actions → New
   repository secret `ANTHROPIC_API_KEY`. Only needed to run the manual `Daily post` workflow; the Claude routine
   publishes without it.
2. **AdSense.** Apply at https://adsense.google.com with the site URL. Once approved, put the publisher id in
   `site-config.json` → `adsense_client` (`ca-pub-…`) and the `ads.txt` line in `ads_txt`, commit, and the next build
   injects Auto ads on every page and writes `/ads.txt`. The privacy page already carries the required disclosure.
3. **Affiliate links (optional).** The partner table lives in `site-config.json` under `affiliates` and the sign-up checklist in `AFFILIATES.md`. Paste each network's id into the matching entry; the build then rewrites links to that partner's domains with tracking, marks them `rel="sponsored nofollow"` and renders the FTC disclosure above the article. No eBay.
4. **Search Console.** Submit `https://404memoryfound.com/sitemap.xml` (and `/feed.xml` as a second sitemap) and request
   indexing for `/`, `/posts/` and the eight `/tags/` pages. Paste the HTML-tag verification code into
   `site-config.json` → `google_verification` if you verify that way.
5. **Bing Webmaster Tools.** https://www.bing.com/webmasters → Import from Google Search Console (one click), or add
   the site and paste the `msvalidate.01` code into `site-config.json` → `bing_verification`. IndexNow pings
   (`indexnow_ping.py`, key file at the repo root) already run after every build, so Bing learns about new posts
   within minutes once the site is added.
6. **Pinterest.** Create a business account for the site (not linked to you), claim the website by pasting the
   `p:domain_verify` code into `site-config.json` → `pinterest_verification`, create a board, then either
   (a) turn on Pinterest's own *Auto-publish from RSS* with `https://404memoryfound.com/feed.xml` (every item carries
   its share card as media), or (b) create an app at https://developers.pinterest.com, generate a token with
   `pins:write` and `boards:read`, and add the secrets `PINTEREST_ACCESS_TOKEN` and `PINTEREST_BOARD_ID`. With (b)
   the daily workflow pins each new post plus two older ones per day (`pinterest_publish.py`).

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
| `indexnow.json`, `8e27a526d67545f5b42848dda0062e6a.txt` | IndexNow key (Bing/Yandex instant indexing). |
| `pinterest-state.json` | What has been pinned, written by the workflow. |
| `topic-backlog.json` | Topics to write. The generator refills it with ten researched topics when it runs dry. |
| `POST_SPEC.md` | The editorial spec the generator enforces. |
| `CONTENT_CALENDAR.md` | Original 50-topic research from March 2026, still a useful idea list. |
