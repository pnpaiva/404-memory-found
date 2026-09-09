# Affiliate partners: what to apply to and where to paste the ids

Chosen in the study of 9 September 2026 (full text with 77 sources in `docs/affiliate-study-2026-09.md`). eBay Partner Network is excluded on purpose. Every rate below is what the merchant or network published on that date; verify inside the dashboard before relying on it, and never quote a rate in a post.

## Apply this week (no traffic minimum)

| Order | Program | Network | Published terms | Sign up | Paste into `site-config.json` |
|---|---|---|---|---|---|
| 1 | Legacybox, Southtree, Kodak Digitizing | ShareASale (Awin) | up to 10%, 30-day cookie, orders in the hundreds of dollars | https://www.shareasale.com/info/affiliates/ then search the three merchants | `Legacybox` entry: `id` = ShareASale user id, `merchant_id` = merchant number from each merchant page |
| 2 | ScanMyPhotos | Awin | 10% rising to 30% per merchant | https://www.awin.com/us/publishers (1 USD refundable deposit) | `ScanMyPhotos` entry: `id` = Awin publisher id, `merchant_id` from the Awin advertiser page |
| 3 | Etsy | Awin | 4%, 30-day web cookie | same Awin account, join the Etsy program | `Etsy` entry: `id` = Awin publisher id (merchant id 6220 is already filled in) |
| 4 | Stone Age Gamer | direct | 2.5% open tier, 3% after the site is 3 months old, 10% Premier | https://stoneagegamer.com/affiliate-program/ | `Stone Age Gamer` entry: `id`, and correct `param` to whatever the approval email names |
| 5 | Anbernic | UpPromote | 2% base, 6% after review, 30-day cookie, 10 USD payout | https://anbernic.com/pages/affiliate-program | `Anbernic` entry: `id` = the sca_ref value |
| 6 | GOG | direct | 6% flat, 7-day cookie, open to everyone | https://www.gog.com/affiliate | `GOG` entry: `id` |
| 7 | Humble Bundle | Impact | 15% bundles, 5% store, 7-day cookie, 25 USD payout | https://www.humblebundle.com/affiliates | `Humble Bundle` entry: paste Impact's tracking link as `template`, with `{url_encoded}` where the deep link goes |
| 8 | Green Man Gaming | Impact | up to 5%, 10% on bundles | https://www.greenmangaming.com/affiliates/ | `Green Man Gaming` entry: Impact `template` |
| 9 | Displate | direct | reported 25%, unverified | https://displate.com/affiliate | `Displate` entry: `template` |
| 10 | Walmart Affiliates | Impact | Walmart fee schedule, no follower gate on this track | https://affiliates.walmart.com/ | `Walmart` entry: Impact `template` |

Google AdSense is already live (ca-pub-2779742602426192).

## Wait for a trigger

| Program | Apply when | Why wait |
|---|---|---|
| Journey by Mediavine | 1,000 Tier 1 sessions in 30 days | 2 to 4 times AdSense; applying early wastes the application |
| Amazon Associates | 20+ posts and enough traffic for 3 orders in 180 days | an account with no 3 orders in 180 days is closed permanently |
| Raptive | 25,000 monthly pageviews | the step up from Journey |
| Stone Age Gamer level 3 | 10,000 unique monthly visitors | higher tier |

## Skip

Ezoic (250,000 users minimum since February 2026), Monumetric (99 USD fee), Best Buy, Target, Redbubble, BoxLunch, Elgato (rates near 1%), and every retro independent with no program (DKOldies, Lukie, JJGames, Castlemania, Limited Run, Analogue, Hyperkin, Evercade, Antstream, Nintendo, Discogs, Steam).

## How links work in this repo

- Writers put one plain link to the matching partner in the "Where to find one today" paragraph (see `POST_SPEC.md`).
- `build.py` reads `site-config.json` → `affiliates`. Partners with an id get tracking and `rel="sponsored nofollow"`; partners without one stay `nofollow`.
- The FTC disclosure (`affiliate_disclosure` in the config) renders above the article body whenever a page carries a sponsored link, which satisfies the "same page, before the link" rule in 16 CFR Part 255.
- Never hard-code a commission rate in copy. Rates change without notice.

## Revenue model from the study (planning figures, not forecasts)

| Monthly visits | Ads | Affiliate | Total |
|---|---|---|---|
| 10,000 | about 120 USD (Journey) | about 60 USD | about 180 USD |
| 30,000 | about 360 USD | about 175 USD | about 535 USD |
| 50,000 | about 900 USD (Raptive) | about 430 USD | about 1,330 USD |

On that mix, 5,000 USD a month needs roughly 170,000 to 200,000 visits, or a heavier digitizing cluster (Legacybox and ScanMyPhotos pay ten times Amazon per order), or a third line such as a newsletter sponsorship.
