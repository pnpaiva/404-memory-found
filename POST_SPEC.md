# 404 Memory Found: post specification

Every new post follows this spec. `generate_post.py` enforces it; write by hand to the same shape.

## Goal
One post answers one search query completely, so that Google can lift the answer into a snippet, a searcher has a reason to click (the title promises more than the answer), and a reader who clicks stays to the end and opens a second page. Real readers, not crawlers: success is measured in Search Console clicks and in engaged sessions from Organic Search and AI assistants, never in raw visit counts.

## Clicks and reading time (what the 2026-11 Search Console review taught)
- Status questions ("is X still open", "does X still exist") get impressions but few clicks, because Google answers them on the results page. Write them only for second-tier subjects, and always give the page something the results page cannot: where the last stores are, how to still use or play it, what one sells for, the story of the night it ended.
- Formats that need the click come first: price guides with a table, how to play, run, watch or digitize it today, every model or version ranked or listed, and stories with a real mystery.
- Every post carries 1 or 2 photos inside the body (see Images) in addition to the hero, placed after the second or third section. Walls of text lose readers; a photo of the real thing keeps them.
- Every section ends on a sentence that makes the next heading the obvious next question.
- The build adds a "Keep reading" card mid-article and "Next in the archive" cards where the story ends (before the FAQ), so a related post with a curiosity-driven title matters: link phrases and tags decide which posts surface there.
- The page headline is `seo.title` (the title Google shows), so the click lands on the promise it made. Keep `seo.title` a headline a person would want to read, not a keyword string.
- Under the summary the build prints "Still ahead in this story:" with one of the post's own section headings, picked automatically: a statement heading with a concrete detail (a date, a number, a scene) wins over a question, and headings that only restate the answer ("Who owns X today?", "Is X still open?") are never picked. So at least one heading after the first must be that kind of statement, the strangest moment in the story ("The day two soldiers carried the chairman out of his office", "The 30-hour auction that ended the American stores").
- The last section before the FAQ ends on a closing line that finishes the story, because the next-story cards come right after it.
- FAQ answers add something the summary does not already say (a second detail, a number, a how-to). An FAQ that repeats the summary word for word reads as filler at the moment readers decide whether to stay.

## Shape

| Part | Rule |
|---|---|
| Length | Set by the question, recorded in the post's `format` field. **quick**: 550 to 850 words, for one factual question ("Is X worth anything?", "Is X still open?") where the reader wants the answer and a price table, not a history. **standard**: 900 to 1,400 words, a status question with a real story behind it. **deep**: 1,600 to 2,400 words, only for a big multi-part subject people research at length. Count is the body before the FAQ. A mix across the archive is the point: identical lengths everywhere read as a template |
| Title | 45 to 60 characters. The searcher's own words first (the query as people type it), then a promise the page pays off that the results page cannot: the story, the twist, the price table, the how-to. **Never put the verdict in the title.** "Does Yahoo Answers Still Exist? It Closed in 2021" answers the question on Google's results page and nobody clicks; "What Happened to Yahoo Answers? Can You Still Read It?" earns the click. Good second halves: "and Who Owns It Now", "Where the Last Ones Are", "and What It's Worth Now", "How to Play It Today", "The Night It Vanished". At most one in three titles may start with "What Happened to" |
| Slug | lowercase, 3 to 7 words, keyword first, no stop words, no year unless it is the query |
| Meta title | `seo.title` is the title alone. The build appends " \| 404 Memory Found" only when the whole thing still fits in about 60 characters, because Google cuts longer titles and already shows the site name above the result |
| Meta description | `seo.description`, 130 to 158 characters. One concrete, surprising detail that proves the page knows the subject (a date, a price, a strange fact), then what else the reader gets by clicking (the price table, where the last stores are, how to run it today). It may hint at the answer but keeps the most wanted detail for the page. The `excerpt` can stay the plain answer: it is used for lists and feeds, not the results page |
| Summary | 2 to 3 sentences that answer the query directly. Rendered as the first paragraph. Contains the keyword. This is the featured-snippet candidate |
| Quick facts | 3 to 5 short label/value pairs: year launched, company, price then and inflation-adjusted, units sold, what replaced it, status today. A post with a "Status today" fact also carries a "Launched" (product, site, service) or "Founded" (company, store chain) fact with at least the year, verified against a source, and an "Owner today" fact when anyone holds the name: the Dead Brand Index builds its Started and Who owns it now columns from these, and a blank cell there reads as a gap |
| Sections | quick: 3 or 4 `<h2>`; standard: 4 to 6; deep: 6 to 9. Each section 100 to 250 words. Headings are specific and often question-shaped ("Why did the NSA ban Furby?"), never generic ("Background", "Conclusion") |
| Paragraphs | 1 to 4 sentences. No walls of text. Numbers, dates and prices in every section |
| Image | never write an `upload.wikimedia.org` URL from memory: those URLs live under a hash of the file name and a guessed one 404s forever. Give `imageSearch` keywords and let `fetch_images.py` resolve the real file. Only paste a URL you opened and saw load in this session |
| Internal links | 2 to 3 links to existing posts inside the prose, on the natural phrase, never "click here" |
| FAQ | `<h2>Frequently Asked Questions</h2>` then exactly 3 `<h3>` questions people actually search, most-asked first, each answered in 2 to 3 sentences that stand alone (restate the subject, carry their own dates) so the answer still makes sense lifted out of the page. Becomes FAQPage schema |
| Quotations | At least two short direct quotations (under 30 words each) in quotation marks, with the speaker and the outlet or document named and the year ("as CEO Sandi Harding told The Bulletin in 2023"). Only words that appear in a source you opened or in a search snippet you can cite; never reconstructed from memory. Quoted sentences are what answer engines lift verbatim |
| Entity naming | One canonical name per company, product or person, used in the title, summary, quick facts and FAQ ("Dish Network", not "DISH" in one place and "DISH Network Corporation" in another); short forms only after the first mention |
| Headings | No `<h2>` may restate the title. The first section starts on new ground |
| Sources | 3 to 5 links to primary or reputable sources (company filings, court records, contemporary news, museums, Wikipedia only as a fallback). Rendered as a Sources list. Every specific number in the post must trace to one of them |
| Affiliate hook | For products that still trade second-hand, one short "Where to find one today" paragraph with typical prices and exactly one plain link to the partner that fits, chosen from `AFFILIATES.md`: Etsy for toys, ephemera and artifacts; Stone Age Gamer or Anbernic for consoles and handhelds; GOG or Humble Bundle for PC games; Legacybox for tapes and camcorder formats; ScanMyPhotos for prints and negatives. Never eBay. Link the merchant's search or category page, not a listing that will vanish. `build.py` adds the tracking and the disclosure when an id is configured; never quote a commission rate in copy |
| Status questions | Every post about a company, product or service answers, explicitly and early, the questions Search Console shows people typing: is it still around in 2026, who owns it now, how many are left or what it costs today, and what replaced it. One of those belongs in the summary, one in a section heading, one in the quick facts ("Owner today", "Stores left", "Status"), one in the FAQ. **One status page per brand.** When the archive already has a post whose job is the brand's status ("Is X still around", "Who owns X now"), that post is the primary page: every other post about the same brand (a product, a story, a merger) leaves out the status heading, the status FAQ and the status keywords, and links to the primary page in one sentence instead. Two posts chasing the same status query split the clicks and Google ranks neither. Check posts.json for the brand before writing |
| Audience | Readers in the United States first, then the UK, Canada and Australia. Write for them: US spelling, prices in US dollars with the year, US retailers and the partner shops in `AFFILIATES.md` for 'where to find one today', US launch dates when they differ from Japan or Europe. Subjects must have had a real presence in those markets; a product or site that was big only in Brazil, India or continental Europe does not belong, however nostalgic it is |
| Buyer-intent posts | About one post in five answers a buying or doing question ("How to digitize VHS tapes in 2026", "Best way to play Genesis games today", "How to run 90s PC games on Windows 11"). Same shape, same sourcing rules, one link per partner named, the disclosure rendered by the build. The recommendation must be honest: name the DIY route and its cost before the paid service |
| Link phrases | `linkPhrases` holds 1 to 3 short names of this post's own subject (for example ["Sears", "Sears Holdings"]); the build links the first mention of those names in other posts back here. It is never the anchor text of the links you wrote to other posts. Each phrase must appear in your own title or slug |
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
  "imageSearch": ["exact subject", "subject logo", "wider fallback"],
  "imageAlt": "descriptive alt text",
  "imageCaption": "caption shown under the image",
  "body": "<h2>...</h2><p>...</p> ... <h2>Frequently Asked Questions</h2><h3>...?</h3><p>...</p>",
  "sources": [{"title": "Source name", "url": "https://..."}],
  "linkPhrases": ["Furby"],  // 1 to 3 names of THIS post's own subject, used to link OTHER posts here; never the anchor text of your outbound links
  "seo": {"title": "...", "description": "...", "keywords": ["..."]}
}
```

`body` holds the sections and the FAQ only. `build.py` renders summary, image, quick facts, sources and byline around it.

## Choosing a topic: only fight searches we can win

A domain this young, with no links pointing at it, cannot outrank newspapers and Wikipedia. "Is Kmart
still open" returns a full page of national news; "are old Nintendo Power magazines worth anything"
returns forum threads, an analysis from years ago and a scraped copy. The second kind is where this site
wins, and it is the only kind worth writing now.

Before writing, search the exact query and read the first page of results. Count how many results are
authoritative pages that already answer the question fully and recently: Wikipedia, national or major
trade press, the brand's own site, a dedicated price database. **Write only when that count is 3 or
fewer** and the rest are forum threads, Reddit, marketplace listings, thin or dated pages (nothing newer
than 2023), or copies. Otherwise skip the topic and record it as `skipped_competitive` so nobody tries
it again.

Where winnable demand lives:
- **What is it worth.** "Is X worth anything", "how much is X worth", "X value" for 1990s and 2000s
  toys, handhelds, games, magazines, cards, gadgets and media. Collectors type these constantly, the
  answers online are usually forum guesses, and money questions carry the best ad rates. Mainstream
  subjects with a big price database (Pokémon cards, Beanie Babies, Funko) are not winnable; second-tier
  ones usually are.
- **Second-tier brands.** "What happened to X" and "who owns X now" for companies, websites, toy lines
  and gadgets that were famous to one generation but are not national news anymore.
- **Dated moments.** Anniversaries and news, handled by the freshness desk on existing posts.

## Tables (the pages that outrank us have them; 229 of our first 232 posts did not)

Every new or upgraded post carries at least one `<table>` with real rows, because a table is what a reader
scans for first and what Google lifts into results. Pick the one the subject supports:
- a value post: sold prices by model and condition (see Price guides);
- a product: every version or model, with year, launch price and what changed;
- a company or store: a dated timeline (founded, peak, the deal, the closing) or a dated list of the
  stores that are left, with city and the date checked;
- a how-to-today post: what works where (platform, version, cost, catch).
Keep tables to 3 to 5 columns so they read on a phone. Every figure in a table needs a listed source and,
for anything that changes (prices, store counts), the month and year it describes.

## Price guides

A worth post carries a table of typical recent sold prices by model, variant and condition (loose,
complete, sealed or graded), using `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>`, each
range supported by a source you list (an auction archive, a price-guide page, a dated article quoting
sales). Then: how to tell the valuable version from the common one, what lowers the price, where to
sell or buy one (one partner shop link, never eBay or Amazon as a destination). Prices are always
ranges with the month and year they describe, never a single figure presented as exact.

## Images: the one rule that is never bent

Wikimedia keeps every file in a directory named after the md5 of its file name, so a URL written from
memory or composed by pattern returns 404 at every width, forever. It cannot be repaired later, because
nothing about the guessed path points at the real file.

- Never put an `upload.wikimedia.org` URL in a post unless a command in that same session printed it and
  a follow-up request returned 200. Copy it exactly: never retype a hash directory or a `NNNpx-` width.
- When Commons is unreachable, or the check did not return 200, set `image` to `null` and give
  `imageSearch`: three or four short queries naming the exact product or company, most specific first.
  `fetch_images.py` resolves them against the Commons API after the push. A post with good queries beats
  a post with an invented URL every time.
- The same applies to `<img>` inside the body. No verified URL means no figure.
- In-body photos go in as `<figure><img src="VERIFIED_UPLOAD_URL" alt="what the photo shows"><figcaption>honest caption</figcaption></figure>` between sections, never inside a paragraph. One or two per post, each showing something different from the hero (the box, the store, the screen, the people). The build self-hosts them, adds dimensions and the licence credit, and silently drops any figure whose URL it could not verify.
- Captions stay honest: say when the photo is a later model, a museum display, packaging, or a stand-in
  for the subject rather than the subject itself. A picture of something else is worse than no picture.

`fetch_images.py` now checks every hero URL against the Commons API and, when the file does not exist,
drops it and searches instead, and `build.py` ships no image that has no verified local copy. Those are
safety nets, not permission to guess.
