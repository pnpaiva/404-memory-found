# 404 Memory Found: post specification

Every new post follows this spec. `generate_post.py` enforces it; write by hand to the same shape.

## Goal
One post answers one search query completely in under five minutes of reading, so that Google can lift the answer into a snippet and a reader who clicks stays to the end. Shorter than the 2026 archive (median 2,800 words), denser, and sourced.

## Shape

| Part | Rule |
|---|---|
| Length | 900 to 1,300 words in the body (FAQ and sources excluded) |
| Title | 45 to 60 characters, primary keyword in the first half. Rotate patterns; at most one in three titles may start with "What Happened to". Other patterns: "Is X Still Around in 2026?", "Who Owns X Now?", "How Many X Are Left?", "Why X Failed", "X Explained", "How X Lost to Y", "X in 1998 vs Today", "The Real Story of X". Status patterns get priority: they match what people actually type |
| Slug | lowercase, 3 to 7 words, keyword first, no stop words, no year unless it is the query |
| Meta title | same as title plus " \| 404 Memory Found", max 70 characters total |
| Meta description | 120 to 155 characters, contains the keyword, ends with a concrete hook (a number, a date, a surprise) |
| Summary | 2 to 3 sentences that answer the query directly. Rendered as the first paragraph. Contains the keyword. This is the featured-snippet candidate |
| Quick facts | 3 to 5 short label/value pairs: year launched, company, price then and inflation-adjusted, units sold, what replaced it, status today |
| Sections | 4 to 6 `<h2>` headings, 120 to 220 words each. Headings are specific and often question-shaped ("Why did the NSA ban Furby?"), never generic ("Background", "Conclusion") |
| Paragraphs | 1 to 4 sentences. No walls of text. Numbers, dates and prices in every section |
| Image | one image after the summary, from Wikimedia Commons (CC or public domain), with descriptive alt text and a caption |
| Internal links | 2 to 3 links to existing posts inside the prose, on the natural phrase, never "click here" |
| FAQ | `<h2>Frequently Asked Questions</h2>` then exactly 3 `<h3>` questions people actually search, most-asked first, each answered in 2 to 3 sentences that stand alone (restate the subject, carry their own dates) so the answer still makes sense lifted out of the page. Becomes FAQPage schema |
| Quotations | At least two short direct quotations (under 30 words each) in quotation marks, with the speaker and the outlet or document named and the year ("as CEO Sandi Harding told The Bulletin in 2023"). Only words that appear in a source you opened or in a search snippet you can cite; never reconstructed from memory. Quoted sentences are what answer engines lift verbatim |
| Entity naming | One canonical name per company, product or person, used in the title, summary, quick facts and FAQ ("Dish Network", not "DISH" in one place and "DISH Network Corporation" in another); short forms only after the first mention |
| Headings | No `<h2>` may restate the title. The first section starts on new ground |
| Sources | 3 to 5 links to primary or reputable sources (company filings, court records, contemporary news, museums, Wikipedia only as a fallback). Rendered as a Sources list. Every specific number in the post must trace to one of them |
| Affiliate hook | For products that still trade second-hand, one short "Where to find one today" paragraph with typical prices and exactly one plain link to the partner that fits, chosen from `AFFILIATES.md`: Etsy for toys, ephemera and artifacts; Stone Age Gamer or Anbernic for consoles and handhelds; GOG or Humble Bundle for PC games; Legacybox for tapes and camcorder formats; ScanMyPhotos for prints and negatives. Never eBay. Link the merchant's search or category page, not a listing that will vanish. `build.py` adds the tracking and the disclosure when an id is configured; never quote a commission rate in copy |
| Status questions | Every post about a company, product or service answers, explicitly and early, the questions Search Console shows people typing: is it still around in 2026, who owns it now, how many are left or what it costs today, and what replaced it. One of those belongs in the summary, one in a section heading, one in the quick facts ("Owner today", "Stores left", "Status"), one in the FAQ |
| Audience | Readers in the United States first, then the UK, Canada and Australia. Write for them: US spelling, prices in US dollars with the year, US retailers and the partner shops in `AFFILIATES.md` for 'where to find one today', US launch dates when they differ from Japan or Europe. Subjects must have had a real presence in those markets; a product or site that was big only in Brazil, India or continental Europe does not belong, however nostalgic it is |
| Buyer-intent posts | About one post in five answers a buying or doing question ("How to digitize VHS tapes in 2026", "Best way to play Genesis games today", "How to run 90s PC games on Windows 11"). Same shape, same sourcing rules, one link per partner named, the disclosure rendered by the build. The recommendation must be honest: name the DIY route and its cost before the paid service |
| Author | one of the pen names in `authors.json`, chosen by beat |
| Tags | 1 to 3 from the eight site tags only |

## Voice
Plain, confident, specific. Third person. Contractions are fine. No em dashes. No "Picture this", "Let's dive in", "In conclusion", "game-changer", "iconic", "beloved", "fast forward". No rhetorical questions in a row. Every claim with a number carries a year. When a fact is disputed, say who says what.

## Don'ts
Never invent a quote, a price or a sales figure. If a number cannot be sourced, leave it out. Never claim a writer did or owned something. Never write a second post on a subject that already has one (check the slug list); write a different angle with a different keyword instead.

## JSON shape (what the generator emits and posts.json stores)

```json
{
  "id": "furby-nsa-ban-1999",
  "title": "Why the NSA Banned Furby in 1999",
  "date": "2026-09-10",
  "author": "marcus",
  "tags": ["Hardware", "Internet Culture"],
  "excerpt": "meta description, 120 to 155 characters",
  "summary": "2 to 3 sentence direct answer",
  "facts": [{"label": "Launched", "value": "October 1998, Tiger Electronics"}],
  "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/.../960px-....jpg",
  "imageAlt": "descriptive alt text",
  "imageCaption": "caption shown under the image",
  "body": "<h2>...</h2><p>...</p> ... <h2>Frequently Asked Questions</h2><h3>...?</h3><p>...</p>",
  "sources": [{"title": "Source name", "url": "https://..."}],
  "linkPhrases": ["Furby"],
  "seo": {"title": "...", "description": "...", "keywords": ["..."]}
}
```

`body` holds the sections and the FAQ only. `build.py` renders summary, image, quick facts, sources and byline around it.
