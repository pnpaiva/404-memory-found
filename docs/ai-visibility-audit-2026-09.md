# AI Answer Engine Visibility Audit: 404memoryfound.com

Date of audit: 2026-09-09. Site: 144 posts, static HTML on GitHub Pages, US nostalgia-tech audience.

Method: 20+ live pages read (official crawler docs from OpenAI, Anthropic, Perplexity, Google Search Central, Bing Webmaster blog, llmstxt.org, plus the Princeton GEO paper and independent citation studies), then a scripted crawl of all 144 post URLs from the sitemap to measure which on-page blocks actually exist.

**Headline: the build is already better than most sites on the technical basics, and the single biggest problem is not a missing feature. It is that the good format only exists on 19 of 144 posts.**

---

## 1. How each engine sources citations in 2026

### OpenAI / ChatGPT search

Three separate user agents, each with a different job. Blocking the wrong one has very different consequences.

| Agent | Purpose | robots.txt |
|---|---|---|
| `GPTBot` | Crawls candidate **training** data for foundation models | Respected |
| `OAI-SearchBot` | Builds the index that **ChatGPT search** answers from | Respected |
| `ChatGPT-User` | Fetches a page because a **user** asked for that URL | Not applied |

OpenAI states directly that sites blocking `OAI-SearchBot` "will not be shown in ChatGPT search answers, though can still appear as navigational links," and that `ChatGPT-User` visits are user-initiated so "robots.txt rules may not apply." Robots.txt changes take about 24 hours to propagate.

Source: https://developers.openai.com/api/docs/bots

On whether ChatGPT uses Bing: OpenAI's own documentation describes `OAI-SearchBot` as building its own index, and does not name Bing. Multiple SEO sources describe Bing as a retrieval layer behind ChatGPT search, but I could not verify that from a first-party OpenAI or Microsoft document. **Treat "ChatGPT runs on Bing" as unverified.** The safe reading is that OpenAI crawls first-party and may supplement with third-party search APIs, so being in Bing is a cheap hedge rather than a proven requirement.

### Anthropic / Claude

Also three agents, and the split matters the same way.

| Agent | Purpose | robots.txt |
|---|---|---|
| `ClaudeBot` | Model development / training | Respected |
| `Claude-SearchBot` | Indexes content **to improve search results** | Respected |
| `Claude-User` | Fetches pages when a user asks Claude something | Respected per Anthropic's guidance |

Anthropic says blocking `Claude-User` "prevents our system from retrieving your content in response to a user query" and blocking `Claude-SearchBot` reduces "visibility and accuracy in user search results." IP verification list at https://claude.com/crawling/bots.json.

Source: https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler

### Perplexity

Runs its **own index**, not Bing's or Google's.

| Agent | Purpose | robots.txt |
|---|---|---|
| `PerplexityBot` | Builds the index that surfaces and links sites in Perplexity results. Not used for training | Respected; Perplexity explicitly recommends allowing it |
| `Perplexity-User` | User-initiated page visits | "Generally ignores robots.txt" |

Perplexity retrieves from its index at query time, extracts passages, and synthesises with citations. IP ranges at https://www.perplexity.com/perplexitybot.json.

Source: https://docs.perplexity.ai/guides/bots

### Google AI Overviews and AI Mode

Uses the **normal Google index and Googlebot**. There is no separate AI crawler for the linking surface. `Google-Extended` is a training/grounding control, not an index control.

Google is unusually blunt here, and it contradicts a lot of GEO marketing:

> "There are no additional requirements to appear in AI Overviews or AI Mode, nor other special optimizations necessary."

and

> "You don't need to create new machine readable files, AI text files, or markup to appear in these features. There's also no special schema.org structured data that you need to add."

Google describes a **query fan-out** technique: AI Mode issues multiple related sub-searches across subtopics, which is why it surfaces a wider and more diverse set of links than the classic ten blue links. Practical implication: one page that cleanly answers one narrow sub-question can get pulled in even when the site does not rank for the broad head term.

Source: https://developers.google.com/search/docs/appearance/ai-features

### Bing / Microsoft Copilot

Copilot retrieves candidates from the **Bing index**, then the model writes a cited answer. Bing's own guidance stresses IndexNow for AI surfaces:

> "IndexNow helps ensure your most important updates are reflected in search results fast, especially critical in AI-driven environments."

Bing also frames visibility as depending on "relevance, content structure, freshness, and how well your pages align with user intent" rather than on schema specifically.

Source: https://blogs.bing.com/webmaster/June-2025/Start-Using-Bing-Webmaster-Tools-to-Improve-Your-Site-Visibility

Secondary reporting says Bing Webmaster Tools shipped an **AI Performance report** around 11 Feb 2026, which would be the only first-party AI citation dashboard from any major engine. I could not confirm this from the Bing blog directly, so **treat the exact date and feature name as unverified**, but it is worth logging into BWT to check, because if it exists it is the single best free measurement tool available.

### Is llms.txt actually used by anyone?

Short answer: **no engine has confirmed using it, and the log evidence says almost nobody fetches it.**

- Google's John Mueller, 17 June 2025 on Bluesky: "no AI system currently uses llms.txt," pointing at server logs as the evidence. He compared it to the keywords meta tag. Source: https://www.seroundtable.com/google-ai-llms-txt-39607.html
- Gary Illyes (Google) separately confirmed Google does not support it and is not planning to.
- Crawler monitoring cited in secondary coverage found that of 500M+ AI bot visits over 90 days, only ~408 targeted llms.txt. Adoption sits near 10% of domains. **These specific figures are from SEO vendor blogs and are unverified**, but they point the same direction as Mueller's log claim.
- The spec itself (v2, updated 10 Aug 2026) is real and OpenAI, Anthropic and Gemini publish llms.txt for their own docs. Source: https://llmstxt.org/

Verdict for this site: keep it, do not invest more in it. It costs nothing at build time, it is already spec-correct, and it may pay off later. It is not a lever.

---

## 2. What actually makes a page get cited, and what the site does

### The strongest evidence

The best peer-reviewed source is the Princeton GEO paper (Aggarwal et al., KDD 2024, https://arxiv.org/abs/2311.09735). GEO-bench tested ~10,000 queries across nine datasets. The tactics that raised citation visibility by roughly 22-41%:

1. **Cite Sources** (add named citations)
2. **Quotation Addition** (add direct quotes)
3. **Statistics Addition** (add concrete numbers)
4. Fluency Optimization
5. Authoritative Voice

And critically: **keyword stuffing produced zero benefit and slightly degraded performance in Perplexity.**

The second-best source is Orbit Media's tracking study: 13,184 citations across 1,765 answers from ChatGPT, Claude, Gemini and Perplexity over ~3 months (https://www.orbitmedia.com/blog/ai-citation-sources/). Findings that matter here:

- Sources per answer: Perplexity 19.2, Gemini 8.1, ChatGPT 4.5, Claude 3.6. Perplexity is by far the easiest to get into.
- The four models agreed on the same domain for the same question only **1.7%** of the time. There is no single "AI ranking" to optimise for.
- Only **10-30%** of cited domains ranked in Google's top 10; at exact-URL level, **1-5%**. Google rank is a weak proxy for citation.
- ChatGPT skews toward primary sources (documentation, arXiv, vendor pages). This favours a site that links SEC filings and contemporary reporting.
- Study caveat, stated by the author: 12-40 questions per brand, directional not definitive.

Surfer's AI Overviews analysis reports 67.82% of AI Overview citations do not rank in Google's top 10 for the same query, consistent with Orbit. Source: https://surferseo.com/blog/llm-citations/

### The weaker evidence, flagged

Claims circulating that "FAQ schema gives a 3.2x citation rate" and that a "Princeton and Moz study of 500,000 URLs" found this are **unverified**. I could not trace them to a primary study, and the phrasing recurs across low-quality SEO content-marketing blogs that appear to be citing each other. Do not build a plan on that number. The GEO16 arXiv preprint (https://arxiv.org/pdf/2509.10762) reports metadata/freshness (r=0.68), semantic HTML (r=0.65) and structured data (r=0.63) as correlating with citation, but it is a preprint and correlational, not causal.

One notable negative finding, reported in that same cluster: **page load speed showed no measurable effect on citation rate.** The site's TTFB is 0.176s on a 29KB static page, so this is moot regardless.

### Scorecard: what the site does versus misses

I fetched all 144 post URLs and tested for each block.

| Factor | Evidence | Status on this site |
|---|---|---|
| Direct answer near the top | GEO fluency/authority; extraction needs a liftable sentence | **Partial. 19/144.** Blockbuster opens with a complete 4-sentence answer before any heading. RadioShack has no such block |
| Question-form headings | Query fan-out matches sub-questions to H2s | **Partial.** Blockbuster H2s are literal questions ("Is Blockbuster still open in 2026?"). RadioShack H2s are narrative ("The Peak: 7,000 Stores and Counting") |
| Facts with dates and numbers | GEO **Statistics Addition**, 30-40% lift | **Strong where present.** Blockbuster carries $320M, 9,000 stores, April 6 2011, Dec 31 2023, 0.350877 conversion ratio, 26,000 movies |
| Named sources | GEO **Cite Sources**, 30-40% lift | **19/144 (13%).** Visible Sources block with host labels (sec.gov, nbcnews.com) plus a `citation` array in JSON-LD. Excellent where it exists |
| Direct quotations | GEO **Quotation Addition**, 30-40% lift | **Missing sitewide.** Blockbuster paraphrases Sandi Harding ("Her line to visitors is straightforward...") but never quotes her in quotation marks. This is a named GEO tactic left on the table |
| dateModified freshness | GEO16 r=0.68; Bing names freshness | **Weak.** 125/144 posts have `dateModified` frozen at Mar-May 2026. Only 19 read Sept 2026. On the 19 good posts, `datePublished` == `dateModified`, so the field carries no freshness signal at all |
| BlogPosting / Article schema | Standard; Google says not required but harmless | **144/144.** Complete: headline, description, wordCount, keywords, articleSection, author, publisher, mainEntityOfPage, image |
| FAQPage schema | Matches question-shaped prompts | **68/144 (47%)** |
| `citation` property | Machine-readable provenance | **19/144 (13%)** |
| Quick-facts block | Liftable key-value pairs | **19/144 (13%)** |
| BreadcrumbList | Site structure | Present on posts |
| Author entity | Authoritative Voice; entity grounding | **Weak.** Named authors with bios, jobTitle, worksFor and dedicated author pages, which is good. But **`sameAs` appears nowhere on the site**, and the About page states authors are pen names. An ungrounded pen name is a weak entity |
| Organization entity | Publisher trust | **Weak.** Homepage has WebSite + Blog. `about.html` carries only `{"@type":"WebPage"}`. No Organization, no AboutPage, no sameAs |
| robots.txt allows AI crawlers | Required gate for OAI-SearchBot, PerplexityBot, Claude-SearchBot | **Excellent.** 21 agents explicitly allowed including all three OpenAI, three Anthropic-adjacent, both Perplexity, Google-Extended, Applebot-Extended, plus both sitemaps |
| llms.txt | Not used by any engine (Mueller) | **Present and spec-correct.** 337 lines, H1, blockquote summary, H2 sections, annotated links, plus llms-full.txt |
| Page speed | No measured effect on citation | TTFB 0.176s, 29KB, server-rendered HTML. Non-issue |
| In Bing's index | Gate for Copilot, possibly ChatGPT | **Could not verify. See below** |
| Renders without JS | Crawlers need HTML | Full content in raw HTML |

### Bing and DuckDuckGo index checks: blocked, not negative

Both requested checks failed to produce trustworthy data. I am reporting this as inconclusive rather than as evidence of a problem.

- **Bing** (`site:404memoryfound.com`): HTTP 200, but zero `404memoryfound.com` URLs in the returned HTML. I ran a **control query** (`site:en.wikipedia.org`) which also returned zero Wikipedia URLs, proving Bing serves a JavaScript shell to non-browser clients and that the raw HTML simply does not contain results. A second attempt through a rendering fetcher returned ten results from unrelated domains (google.com, obsproject.com), which is a scrambled or bot-mitigated SERP, not a real answer.
- **DuckDuckGo** (`duckduckgo.com/html/?q=site:...`): HTTP 202 with an `anomaly.js` challenge. Explicitly bot-blocked.

**Conclusion: Bing index status is unverified.** Given that Copilot retrieves from Bing, and given the plausible-but-unconfirmed Bing-behind-ChatGPT claim, confirming this manually is high value and takes two minutes. Check it in a real browser, and register the site in Bing Webmaster Tools to see indexed-page counts directly.

---

## 3. Prioritised changes for the build

Ordered by expected citation impact per unit of work.

### P0. Backfill the Tier 3 format to the other 125 posts

The site already has a proven-good post format. It exists on 13% of the library. Nothing else in this list comes close to the value of applying it to the rest. Each backfilled post needs: the one-paragraph direct answer, the Quick facts table, question-form H2s, the Sources block, the `citation` array, and FAQPage.

Concretely, in build order: 125 posts need Quick facts + Sources + `citation`, and 76 of those also need FAQPage. Do it in batches, oldest and highest-traffic first. Supported by GEO Cite Sources and Statistics Addition (30-40% lift each) and by the fact that Perplexity averages 19.2 sources per answer, so there is a lot of citation supply to win.

### P1. Make `dateModified` mean something, and add a visible "Last verified" line

Right now `datePublished` == `dateModified` on every post, and 125 posts are frozen at Mar-May 2026. The field is currently decorative.

Change the build so `dateModified` updates only when content actually changes, and add a visible line under the byline: `Last verified: 9 September 2026`. Then run a quarterly verification pass on the ~30 posts whose facts move (store counts, ownership, "is X still open", prices, anything with a number that decays) and let the rest sit. Freshness is the highest-correlating factor in the GEO16 preprint (r=0.68) and Bing names it directly. A "Last verified" line is also the single most liftable trust sentence for a nostalgia site whose whole value proposition is "we checked."

Do **not** fake-bump dates on unchanged posts. That is the failure mode this guards against.

### P2. Add direct quotations

This is the one named Princeton GEO tactic (30-40% lift) the site does not use at all. The research is already being done: the Blockbuster post has Sandi Harding, The Bulletin, Retail Dive and an SEC filing, and paraphrases all of them. Change the post spec to require **at least two direct quotations in quotation marks with the speaker and outlet named** per post. Quoted sentences are also disproportionately liftable into an AI answer verbatim.

### P3. Ground the entities with `sameAs`

`sameAs` appears nowhere on the site. Add:

- **Organization** on `about.html` (currently bare `WebPage`), with `sameAs` pointing to whatever real profiles exist for the publication.
- **Person** `sameAs` on author pages, or, if the pen names have no external presence, drop the pretence of individual `sameAs` and instead make the Organization the authority. An ungrounded pen name may be worse than an honest editorial byline.
- **WebSite** with `publisher` referencing the Organization by `@id`, and use `@id` cross-references so the graph is connected rather than three disconnected islands.

Note honestly: Google says no special schema is needed for AI features. This is an entity-grounding play for the non-Google engines and for general trust, and the evidence is correlational (GEO16 r=0.63).

### P4. Verify and secure Bing indexing, then add IndexNow

Register in Bing Webmaster Tools, submit the sitemap, confirm the indexed page count, and check whether the AI Performance report is available on the account. Then wire **IndexNow** into the build: on deploy, ping the IndexNow endpoint with changed URLs. Bing names this specifically as "critical in AI-driven environments." This is the only recommendation in this list that Microsoft asks for by name, and it is a small build step for a static site.

### P5. Fix heading discipline on the legacy posts

RadioShack has an `<h1>` and a near-duplicate `<h2>` saying almost the same thing ("What Happened to RadioShack? The Store on Every Corner" then "What Happened to RadioShack? The Store That Was on Every Corner in America"). Remove the duplicate. Then convert narrative H2s into question form where a real question exists, because query fan-out matches sub-questions. "The Peak: 7,000 Stores and Counting" becomes "How many RadioShack stores were there at its peak?"

Also: this violates the no-colon-intro rule anyway, so it is a double win.

### P6. Add comparison tables where the post is a comparison

The "Then vs Now" category (~20 posts) is inherently tabular and is currently prose. A table is the most reliably extractable structure in an HTML document. Add an HTML `<table>` with a real `<thead>`, and wrap it in `overflow-x: auto` so mobile does not break. Where a post compares priced items over time, state the year for every figure.

### P7. Enforce consistent entity naming

Pick one canonical string per entity and use it on first mention in every post, then allow the short form. "Dish Network" versus "DISH" versus "DISH Network Corporation" appears inconsistently even within the Blockbuster post. Retrieval systems match on strings; picking one and using it in the H1, the answer paragraph, the Quick facts and the FAQ raises the chance the passage is judged relevant. Cheap to enforce in the post spec.

### P8. Standardise FAQ ordering and length

Where FAQPage exists, order questions by search demand, most-asked first, and keep answers self-contained: each answer should make sense lifted out of the page with no surrounding context. Blockbuster does this well already (each answer restates the subject and carries its own dates). Make it a spec rule rather than an accident. Aim for 3-6 questions; note that the widely repeated "3-7 questions, 100-200 words, 3.2x" figure is **unverified**, so treat the range as a sensible default, not a target.

### P9. Add the answer to the meta description and the first 160 characters

Already done well on Blockbuster ("Yes, but only one store, in Bend, Oregon"). Make it a spec rule for the backfill: the meta description must contain the actual answer, not a tease. Curiosity-first is the right call for slides and video; for an AI-extracted answer page it is the wrong call, because the extractor may only see the top.

### P10. Keep llms.txt, but stop investing in it

It is spec-correct and costs one build step. Regenerate it as part of the build so it never goes stale. Do not expand it, do not build a second variant, and do not count it as a visibility lever. Mueller's server-log claim and the near-zero fetch counts are the reason.

### What I would skip as unproven

- **`speakable` schema.** Zero posts have it, and I would leave it that way. It is scoped to news voice results on Google Assistant, is limited to a small set of publishers, and there is no evidence linking it to AI answer-engine citation. Pure ceremony here.
- **Page speed work.** TTFB is 0.176s on 29KB of static HTML. The one study that measured it found no effect on citation rate. Nothing to gain.
- **A separate "AI-optimised" content endpoint** beyond llms-full.txt. No engine has committed to consuming one.
- **Chasing the "3.2x FAQ schema" number.** Untraceable to a primary source. Add FAQ because it structures question-shaped content well, not because of that figure.
- **Keyword density work.** Princeton measured this directly: zero benefit, slight degradation in Perplexity.

---

## 4. How to measure

### Monthly citation-share protocol

Fix a prompt set, run it the same way every month, record verbatim. The point is trend, not absolute numbers, because these systems are non-deterministic and the four major models agree with each other only 1.7% of the time.

**Rules.** Run in a logged-out or temporary chat so personalisation and memory do not contaminate results. Same day each month. Same prompt wording. Record the answer's cited URLs, not just whether the brand was named.

**The 12 prompts.** Mixed across the site's strongest categories, phrased the way a real person types.

1. Is Blockbuster still open?
2. Who owns Blockbuster now?
3. What happened to RadioShack?
4. Who owns Sears now and how many stores are left?
5. Who owns Atari now?
6. Is Toys R Us still in business?
7. Why did Circuit City go out of business?
8. How much did a computer cost in 1995?
9. What happened to Napster?
10. Why did Blockbuster not buy Netflix?
11. What was the Windows 95 startup sound and who made it?
12. What happened to Kodak and why did it miss digital cameras?

Add or swap prompts to match whichever 20 posts you backfill first, so the measurement tracks the work.

**Engines.** ChatGPT (search mode on), Perplexity, Claude (web search on), Google AI Mode, and Bing Copilot. Expect Perplexity to be the earliest and easiest win at 19.2 sources per answer, and Claude the hardest at 3.6.

**Recording.** One row per prompt per engine per month, in a plain spreadsheet or CSV in the repo:

`date, engine, prompt, cited_404mf (y/n), cited_url, position_in_source_list, total_sources, competing_domains, answer_snippet`

Two numbers to watch: **citation rate** (share of the 12x5 = 60 runs where the site is cited) and **share of sources** (site citations divided by total citations across all runs). Because the top-cited domain on any platform rarely exceeds 5% of total citations, do not expect or chase a big share. Movement from 0/60 to 6/60 is the win condition.

**Free tools.** Bing Webmaster Tools is the only first-party option worth the setup: register the site, submit the sitemap, and check for the AI Performance report on the account (reported to exist since Feb 2026, unverified). Google Search Console shows AI Overview impressions folded into normal Search performance, not broken out. Commercial trackers (Profound, Peec, Otterly, Semrush AI toolkit) exist but are paid; the manual 60-run protocol above costs an hour a month and is honestly more trustworthy for a site this size.

### Seeing AI referrals in GA4

**Fix this first, or none of the rest works.** The site currently ships:

```html
<meta name="referrer" content="no-referrer">
```

on its post pages. That directive tells the browser to strip the `Referer` header on outbound navigation **from** these pages. It does not block inbound referrers, so AI referrals should still land. But it is a fragile, unusual setting to have on a content site, it breaks outbound attribution for anyone you link to, and it is worth confirming it was deliberate. Recommendation: change it to `strict-origin-when-cross-origin`, which is the safe modern default and preserves attribution in both directions.

**Referrer patterns to segment on.** In GA4, build an exploration or a comparison filtered on `Session source` / `Page referrer` containing any of:

- `chatgpt.com`, `chat.openai.com`
- `perplexity.ai`
- `claude.ai`
- `copilot.microsoft.com`, `bing.com/chat`
- `gemini.google.com`, `bard.google.com`
- `you.com`, `poe.com`, `phind.com`

**Practical setup.** Admin > Data display > Channel groups > create a custom channel group named "AI Assistants" with a rule matching `Source` regex:

```
chatgpt|openai|perplexity|claude\.ai|copilot|gemini\.google|bard\.google|you\.com|poe\.com|phind
```

Then AI traffic shows as its own channel in every standard report instead of being buried in Referral or, worse, Direct.

**Two caveats to keep the numbers honest.** First, Google AI Overviews and AI Mode referrals arrive as ordinary `google.com` organic and cannot be separated in GA4, so Google AI traffic is structurally invisible. Second, a large share of AI answers are read without any click at all, so referral volume systematically understates citation share. That is exactly why the manual prompt protocol above exists alongside GA4 rather than instead of it.

---

## Sources

- https://developers.openai.com/api/docs/bots
- https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler
- https://docs.perplexity.ai/guides/bots
- https://developers.google.com/search/docs/appearance/ai-features
- https://blogs.bing.com/webmaster/June-2025/Start-Using-Bing-Webmaster-Tools-to-Improve-Your-Site-Visibility
- https://llmstxt.org/
- https://www.seroundtable.com/google-ai-llms-txt-39607.html
- https://arxiv.org/abs/2311.09735 (Princeton GEO, KDD 2024)
- https://www.orbitmedia.com/blog/ai-citation-sources/
- https://surferseo.com/blog/llm-citations/
- https://arxiv.org/pdf/2509.10762 (GEO16 preprint, correlational)
- https://contently.com/2026/04/29/top-sources-llms-cite/
- Live site: robots.txt, llms.txt, sitemap.xml, and a scripted crawl of all 144 post URLs
