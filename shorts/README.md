---
name: 404mf-shorts
description: Make a vertical short video (YouTube Shorts, TikTok, Reels) from a 404memoryfound.com post with the Win95 house style, word-by-word captions and a voiceover. Use when Pedro asks for a short, a video, a Reel or a TikTok for 404 Memory Found.
---

# 404 Memory Found shorts

Project: `~/404-memory-found/shorts/` (Remotion 4, React 19, TypeScript). Committed to the repo; `node_modules`, `out/`, audio and `.env` are git-ignored.

## Pipeline (about 4 minutes per video)

Per-video files: authored scripts live in `scripts/<slug>.json`; `python3 make.py <slug>` fetches the images into `public/<slug>/`, voices it once (cached there), renders `out/<slug>.mp4` and `out/<slug>-small.mp4`; `--stills` renders one frame per scene, `--cover` renders the thumbnail `out/<slug>-cover.png` from the `cover` block (`text` 1 to 3 words, `sub`, optional `pos` for the photo focal point and `oneLine`). Scene components are parametrised: `found`, `chart`+`chartTitle`, `props`+`propsTitle`+`propsName`+`ticker`, `timeline`, `subject`, `heroPos`/`hero2Pos`. Portrait photos: lower `pos` percentages move the subject DOWN in the frame; landscape photos ignore vertical position.

1. **Scaffold** from a post slug: `python3 new_short.py <slug>` copies the hero image to `public/hero.jpg`, reads the post's title, summary, facts and sources, and writes a draft `script.json` with six scenes. Then WRITE the six `text` lines by hand (see rules) and fill `chart`, `props`, `timeline` from the post's facts and body. Never use a figure that is not in the post.
2. **Voice + word timings**: `python3 tts.py`. Uses ElevenLabs when `ELEVENLABS_API_KEY` is set (in the environment or in `shorts/.env`, one `KEY=value` per line; optional `ELEVENLABS_VOICE_ID`, default premade voice "Brian" `nPczCjzI2devNBz1zQrb`), which returns exact per-word timestamps. Falls back to macOS `say` (Samantha) with timings estimated from word length. Writes `scenes[].words`, `scenes[].audio`, `scenes[].frames`.
3. **Check frames** before a full render: `npx remotion still src/index.ts Short out/f.png --frame=N` and look at one frame per scene.
4. **Render**: `npx remotion render src/index.ts Short out/<slug>.mp4 --codec=h264 --image-format=jpeg --jpeg-quality=90 --concurrency=2` (JPEG frames keep temp disk small; the Mac has been at 100 percent disk before).
5. **Phone copy** (the chat upload limit is 30 MB): `ffmpeg -y -i out/<slug>.mp4 -c:v libx264 -crf 26 -preset medium -pix_fmt yuv420p -c:a aac -b:a 96k -movflags +faststart out/<slug>-small.mp4`, then SendUserFile with `display: render`.

## script.json shape

```json
{"fps":30,"width":1080,"height":1920,"hero":"hero.jpg","hero2":"hero2.jpg","title":"...","slug":"...",
 "scenes":[{"kind":"hook","text":"Is Blockbuster still open in 2026?","lines":["..."],"audio":"seg1.wav","frames":105,"words":[{"w":"Is","s":0.06,"e":0.3}]}],
 "chart":[{"label":"Peak","value":9000,"text":"9,000"}],
 "props":[["Owner","Dish Network"],["Bought","April 6, 2011"]],
 "timeline":[["2010","Bankruptcy"],["2019","Perth closes. Bend is last."]]}
```

`text` is what is spoken AND captioned (write numbers as they should display: `9,000`, `$320 million`). `say` is a legacy field; `text` wins when present.

## Scene kinds (src/Short.tsx)

| kind | visual | needs |
|---|---|---|
| `hook` | hero photo as a VHS tape (RGB jitter, tracking bar, PLAY OSD). Caption fully visible from frame 1 | hero |
| `found` | Win95 "Find" dialog, counter drops to the answer, cursor clicks, address line reveals | edit the counter range and address in `FoundScene` |
| `chart` | bar chart in a spreadsheet window, bars grow with counting labels | `chart` (2 to 4 bars) |
| `props` | file "Properties" dialog typed line by line, big number ticks up | `props` (4 rows) and the ticker target in `PropsScene` |
| `timeline` | dated events light up over `hero2` | `timeline` (4 to 6 rows) |
| `outro` | Start menu slides up, cursor clicks "Follow", CRT power-off | nothing |

Pick 4 to 6 kinds per video that match the post's data (a store chain gets `chart`, an ownership story gets `props`, a product gets a `timeline`). Vary the order between videos; only `hook` first and `outro` last are fixed. Add new kinds as components in `Short.tsx` and register them in `TITLES` and the `body` switch.

## Style rules (Pedro approved this look on 10 Sep 2026)

- Win95 desktop: teal `#008080`, grey bevel windows `#c0c0c0`, navy title bars `#000080`, yellow accent `#ffd400`, VT323 for chrome text, Inter 900 for captions. Top strip with logo and scene counter, bottom Win95 progress bar and the line "Sourced. Dated. No invented numbers."
- Captions are word-by-word, one continuous white bar per line (never one box per word), current word highlighted yellow, numbers and key words (`yes`, `one`, `only`, `last`, anything with a digit or `$`) navy with yellow text once spoken. The hook caption is fully visible from frame 1 so the viewer reads ahead of the voice; every other scene reveals word by word.
- Length 28 to 40 seconds, six scenes, 3 to 7 seconds each; scene length = trimmed audio + 0.06 s (tts.py cuts leading and trailing silence and shifts the word timings). Pedro wants sentences to run tight, no dead air.
- The main window stays open for the whole video; only its CONTENTS animate in (Pedro: no opening and closing the page). Content entrances never repeat within a video (the `entrance()` map in Short.tsx): hook = CRT power-on, found = slide from the right, chart = maximise from the bottom-left, props = drop from the top, timeline = wipe left to right, outro = zoom with a twist. Add a new entrance when adding a new scene kind.
- Music bed: `python3 gen_music.py 48` synthesises a royalty-free chiptune loop (A minor, 96 BPM) into `public/music.wav` (git-ignored, regenerate after a fresh clone); Short.tsx plays it looped at volume 0.04 (Pedro-approved level, do not raise it) with a 0.8 s fade-in and a 1.2 s fade-out. Change `--seed` for a different arpeggio pattern; keep it quiet and unmelodic so it never fights the voice.
- Every number, date and name comes from the post's `facts`, `summary` or body. No em dashes. US audience.
- One pen name is never shown; the brand is the byline.
- Second photo: `python3 -c "import fetch_images as f; print(f.commons_lookup('<query>'))"` from the repo root finds a free Commons image; download the 1280px thumb to `public/hero2.jpg`.


## Deliverable checklist (every time a video is handed over)

Always send, in the same message as the video:
1. **YouTube Shorts title**: under 60 characters, the status question or the surprise first, one number if the post has one, `#Shorts` not needed in the title. Example: "Is Blockbuster Still Open in 2026? One Store Left".
2. **Description**: 2 to 4 short lines answering the question with the key figures (all from the post), then the post URL on its own line, then 3 to 6 hashtags (#nostalgia #90s #2000s plus the subject). No em dashes. End with "Sources in the article."
3. Optional: 3 to 5 tag words for the YouTube tag field and a one-line TikTok/Reels caption (same text, shorter, hashtags first).


## Title, cover and description method (Pedro's rule from 10 Sep 2026: use the title and thumbnail analysis method, not ad-hoc copy)

Sources, all local: `reference/title-thumbnail-master-guide.pdf` (Colin & Samir + Creator Hooks: 3 click triggers, 8 title formulas, checklist, CCN test), `reference/guia-de-thumbnails.md` (ViewLab thumbnail method: question + emotion, top-third rule, 1 to 3 words, variations, contrast with the title) and the ViewLab title generator prompt in `~/ekkoa/lib/ai.ts` (`generateTitles`: one hook family per candidate, all CTR-optimised, ranked strongest first).

**Titles.** Generate 6 to 8 candidates, each from a DIFFERENT hook family and never two from the same: curiosity/open loop, number/specificity, contrast/comparison, fear/loss, desire/transformation, authority/proof, contrarian/pattern break, story/confession. Every candidate must still be optimised to perform: a real curiosity gap, specific (a number, a year, a place when the post has one), broad appeal, clear stakes, a promise the video keeps. Under 50 characters is the target (mobile), 60 is the ceiling. Emotional hook inside the first 3 words. No vague "this happened" without context. Run the CCN test (works for a fan of the channel, a casual nostalgia viewer, and someone with zero context). Every fact in a title must be in the post; never promise what the video does not show. No em dashes. Deliver: the recommended title, its hook family and one line of why, plus 2 alternates for an A/B test.

**Cover (the Shorts thumbnail).** YouTube shows a vertical frame from the video in the Shorts shelf and the channel grid, and only the top third reliably survives crops, so: pick the frame (usually the hook frame, whose caption is fully visible from frame 1) and describe 2 concepts, one safe and one bold, each with: scene/focus (one subject), 1 to 3 words of cover text with 2 variations to test, the question and emotion it triggers and how, composition (key element in the top third, one focus, contrast against the teal). The cover must add the question or emotion the title does not already say, not repeat it. Optional: render the frame with `npx remotion still ... --frame=N` and hand it over as the cover image.

**Description.** 2 to 4 lines that answer the question with the post's figures (answer-first, no tease, the same rule as the site's meta descriptions), then the post URL on its own line, then "Sources in the article.", then 3 to 6 hashtags. Tags for the YouTube tag field: 5 to 8 phrases people search. TikTok/Reels caption: one line, hashtags after.

Hand all of this over in the same message as the video file, every time.

## Known gaps / next upgrades

Word timings are estimated with the Mac voice (exact with ElevenLabs). Wanted next: a receipt scene for price-then-vs-now posts, a "loading" scene for websites, automatic upload (YouTube Data API once Pedro creates the channel and pastes credentials into GitHub secrets).
