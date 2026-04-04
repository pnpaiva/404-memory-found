#!/usr/bin/env python3
"""Add 2 new blog posts to posts.json for 404memoryfound.com"""

import json
from datetime import date

TODAY = date.today().isoformat()

# ============================================================
# POST 1: MARCUS - Creative Labs Sound Blaster
# ============================================================

marcus_post = {
    "id": "what-happened-to-creative-labs-sound-blaster",
    "title": "What Happened to Creative Labs and the Sound Blaster?",
    "date": TODAY,
    "excerpt": "The Sound Blaster didn't just give PCs a voice. It made them scream, sing, and explode. Then the world moved on.",
    "body": """<p>Picture this: 1994. You just got home from school, dropped your backpack by the door, and sat down at your family's Packard Bell. You double-click DOOM. And for the first time, instead of the tinny PC speaker going "beep boop" like a broken microwave, you hear actual sound. Shotgun blasts. Demon growls. A soundtrack that makes you feel like you're inside the game. That's the Sound Blaster. And if you were a PC gamer in the '90s, that little ISA card was the single most important upgrade you ever made.</p>

<p>Creative Technology started in the most unlikely place for a tech giant: a computer repair shop in Chinatown, Singapore. The year was 1981, and two childhood friends from Ngee Ann Polytechnic, Sim Wong Hoo and Ng Kai Wa, pooled together about $6,000 (USD) to open up shop in Pearl's Centre. They fixed Apple II computers, tinkered with add-on memory boards, and dreamed bigger than their tiny storefront suggested. Sim Wong Hoo, in particular, was obsessed with one thing: making computers sound better.</p>

<figure>
  <img src="https://upload.wikimedia.org/wikipedia/commons/4/4d/Sound_Blaster_16_CT2230.jpg" alt="A Creative Sound Blaster 16 ISA sound card, the card that dominated PC audio in the 1990s" loading="lazy" />
  <figcaption>The Sound Blaster 16: the card that turned every beige box into a multimedia machine.</figcaption>
</figure>

<h2>Before Sound Blaster: The Dark Ages of PC Audio</h2>

<p>To understand why the Sound Blaster mattered, you have to understand how bad PC audio was before it showed up. In the late 1980s, IBM-compatible PCs had exactly one audio output device: the internal PC speaker. It could beep. It could kind of make tones at different frequencies. Some very clever programmers figured out how to make it play crude approximations of music, but calling it "audio" was generous. Meanwhile, the Commodore Amiga and Atari ST had built-in sound chips that could actually play samples and synthesize music. PC owners were stuck in the stone age.</p>

<p>The first company to do something about it was Ad Lib, a Canadian outfit based in Quebec. Their Ad Lib Music Synthesizer Card, released in 1987, used a Yamaha YM3812 (OPL2) FM synthesis chip and sold for about $245. It was a revelation. Suddenly, PC games could have real background music with multiple channels and actual instruments. By 1990, Ad Lib had sold around 300,000 units and was the standard that game developers coded for. They owned the market.</p>

<p>But Ad Lib made a critical mistake. They focused exclusively on music synthesis and ignored something that would turn out to be far more important: digital audio playback. The ability to play actual recorded sound, sampled audio like voice clips, sound effects, and real instrument recordings. That gap was exactly what Sim Wong Hoo was waiting for.</p>

<h2>The Card That Changed Everything</h2>

<p>Creative had been building audio products since 1987, starting with the Creative Music System (also known as the C/MS or Game Blaster when Radio Shack sold it). It was decent but didn't set the world on fire. The breakthrough came in November 1989, at COMDEX in Las Vegas, the biggest computer trade show on the planet. Creative rolled up to the Singapore Trade Development Board's pavilion with a brand new product: the Sound Blaster 1.0, internally codenamed "Killer Kard."</p>

<p>The genius of the Sound Blaster was that it did everything the Ad Lib card could do (it was fully Ad Lib compatible, using the same Yamaha OPL2 chip) plus it added an 8-bit digital-to-analog converter for sampled audio playback, a joystick/MIDI port, and a microphone input. It was basically the Ad Lib card plus a tape recorder plus a game port, all on one ISA card. And it sold for around $130 to $200 depending on the bundle, roughly the same price as the Ad Lib card that could only do half as much.</p>

<p>At COMDEX '89, Creative sold 600 units in five days. One order every four minutes. Sim Wong Hoo knew he had something special.</p>

<h2>Destroying Ad Lib and Owning the Market</h2>

<p>What happened next was a masterclass in market domination. Creative aggressively courted game developers. They sent free Sound Blaster cards to every studio that would take one. They offered technical support. They made their development kit easy to use. And because the Sound Blaster was backwards-compatible with Ad Lib, developers had zero risk: code for Sound Blaster, and your game automatically works on Ad Lib too. But if you used Sound Blaster features like digital audio, suddenly your game had voice acting and realistic explosions that Ad Lib owners couldn't hear.</p>

<p>By 1991, "Sound Blaster compatible" had replaced "Ad Lib compatible" on game boxes everywhere. Ad Lib tried to catch up with the Ad Lib Gold in 1992, but it was too little, too late. On May 1, 1992, Ad Lib filed for bankruptcy. The market was Creative's, and it wasn't even close.</p>

<p>That same year, Creative dropped the bomb: the Sound Blaster 16. Launched in June 1992, it offered 16-bit audio at 44.1 kHz, CD-quality sound from a PC. It became the new standard practically overnight. Every game box now said "Sound Blaster 16 compatible." Creative went public on NASDAQ that same year, becoming the first Singapore-based company to list on the exchange. Revenue exploded from $5.4 million in 1989 to $658 million by 1994. By 1995, Creative had sold over 15 million Sound Blaster units worldwide, accounting for roughly seven out of every ten sound cards sold.</p>

<h2>The Golden Age: AWE32, AWE64, and Sound Blaster Live!</h2>

<p>The mid-to-late '90s were the absolute peak. In March 1994, Creative released the Sound Blaster AWE32, a beast of a card that packed wavetable synthesis, 512 KB of onboard RAM (expandable to 28 MB), and support for E-mu's SoundFont standard. It retailed for $399, which was serious money, but for musicians and audiophiles, it was worth every penny. MIDI music on the AWE32 sounded like an actual orchestra compared to the tinny FM synthesis of earlier cards.</p>

<p>The AWE64 followed in 1996, packing 64-voice polyphony into a more affordable package. And then in August 1998, Creative launched the Sound Blaster Live!, the card that brought 3D positional audio to PC gaming with Environmental Audio Extensions (EAX). If you played Half-Life or Unreal Tournament with a Sound Blaster Live! and a pair of decent headphones, you could hear enemies sneaking up behind you. Footsteps echoed differently in hallways versus open rooms. It was transformative for competitive gaming.</p>

<figure>
  <img src="https://upload.wikimedia.org/wikipedia/commons/f/f6/KL_Creative_Labs_Soundblaster_Live_Value_CT4670.jpg" alt="A Creative Sound Blaster Live! Value CT4670 PCI sound card from 1998" loading="lazy" />
  <figcaption>The Sound Blaster Live! brought EAX 3D audio to PC gamers and changed how we experienced games like Half-Life.</figcaption>
</figure>

<p>Creative's market cap hit $1.6 billion in 1994. They were a hardware juggernaut. Sim Wong Hoo was a national hero in Singapore. The Sound Blaster name was as synonymous with PC audio as Kleenex was with tissues.</p>

<h2>The Slow Fade: When Audio Became "Good Enough"</h2>

<p>So what went wrong? The short answer is: motherboards got better, and most people stopped caring. The longer answer involves Intel, Microsoft, and the relentless march of "good enough."</p>

<p>In 1997, Intel introduced the AC'97 audio codec specification, which allowed motherboard manufacturers to include basic audio right on the board. By the early 2000s, virtually every motherboard shipped with built-in audio that was, for most people, perfectly acceptable. Was it as good as a dedicated Sound Blaster card? No. But it was free. And for the average user watching YouTube videos or listening to MP3s, it did the job.</p>

<p>Then came the real knockout punch. With Windows Vista in 2007, Microsoft completely rewrote the Windows audio stack. They moved audio processing from hardware to software, effectively killing hardware audio acceleration. All those fancy EAX effects that Sound Blaster cards did in hardware? Vista handled them in software, or just dropped support entirely. Creative was furious. They released angry blog posts. They released compatibility patches. But the writing was on the wall: the era of the dedicated sound card as a must-have PC component was over.</p>

<h2>Creative After Sound Blaster</h2>

<p>Creative didn't go quietly. They tried to pivot. They launched the Zen line of MP3 players in 2002 to compete with the iPod, and while the Zen was actually a solid product with great sound quality, it got absolutely steamrolled by Apple's marketing and ecosystem. In 2006, Creative even sued Apple for patent infringement related to the hierarchical music menu interface and won a $100 million settlement. But winning a lawsuit and winning the market are very different things.</p>

<p>They kept making Sound Blaster cards, each generation getting more niche. The X-Fi in 2005, the Recon3D in 2011, the Sound Blaster AE-5 in 2017. Good cards, all of them. But each one sold to a smaller and smaller audience of audiophiles and competitive gamers who could tell the difference.</p>

<p>On January 4, 2023, Sim Wong Hoo passed away at the age of 67. The outpouring of tributes from the tech community was immediate and genuine. This was the man who gave PCs a voice. Over 400 million Sound Blaster units have been sold since that first COMDEX demo in 1989. Creative Technology still exists today, still headquartered in Singapore, still making audio products. But they're a fraction of the company they once were, with a market cap that would barely qualify as a rounding error by the standards of their 1990s peak.</p>

<h2>Why the Sound Blaster Still Matters</h2>

<p>Here's the thing about the Sound Blaster that doesn't show up in sales figures or market share reports. It was the product that turned the PC from a business machine into an entertainment platform. Before the Sound Blaster, a PC was something your parents used for spreadsheets and word processing. After the Sound Blaster, it was something you could play DOOM on with the lights off and the volume cranked. It was the card that made multimedia possible, that made CD-ROM games viable, that made the PC a legitimate gaming platform.</p>

<p>If you ever installed a Sound Blaster card, you remember it. You remember cracking open the case, finding the right ISA slot, pressing the card in until it clicked, running the DIAGNOSE.EXE program to set your IRQ and DMA channels, and then hearing that test sound play for the first time. You remember typing SET BLASTER=A220 I5 D1 into your AUTOEXEC.BAT because every single game needed to know where your Sound Blaster lived. You remember the first time you heard a game character actually speak. Not text on a screen. An actual human voice, coming out of your computer speakers.</p>

<p>That moment was magic. And it all started with two guys in a Singapore repair shop who thought computers should sound better than a broken microwave.</p>

<h2>Frequently Asked Questions</h2>

<p><strong>Does Creative Labs still make Sound Blaster cards?</strong><br>
Yes. Creative Technology still produces Sound Blaster branded audio products, including internal PCIe cards, external USB DACs, and gaming headsets. The Sound Blaster line continues to target audiophiles and gamers who want better-than-onboard audio quality.</p>

<p><strong>What killed the dedicated sound card market?</strong><br>
Two main factors. First, Intel's AC'97 and later HD Audio specifications put acceptable audio directly onto motherboards, eliminating the need for a separate card for most users. Second, Microsoft's decision to move audio processing to software in Windows Vista removed the hardware acceleration advantage that Sound Blaster cards relied on.</p>

<p><strong>What was the best-selling Sound Blaster card?</strong><br>
The Sound Blaster 16 family (including its many variants like the Vibra 16 and Value editions) was by far the best-selling line, becoming the de facto standard for PC audio throughout the mid-1990s. Over 400 million Sound Blaster units have been sold total across all models.</p>

<p><strong>Who was Sim Wong Hoo?</strong><br>
Sim Wong Hoo (1955 to 2023) was the co-founder and longtime CEO of Creative Technology. Born in Singapore, he co-founded the company in 1981 and led it to become one of the most influential PC hardware companies of the 1990s. He passed away on January 4, 2023, at the age of 67.</p>

<p><strong>What was the SET BLASTER command?</strong><br>
In the DOS era, the SET BLASTER environment variable (typically added to AUTOEXEC.BAT) told games where to find the Sound Blaster card. A typical setting looked like SET BLASTER=A220 I5 D1, where A220 was the I/O address, I5 was the IRQ, and D1 was the DMA channel. Getting these settings wrong meant no sound, and getting them right was a rite of passage for PC gamers.</p>

<!-- authored-by: marcus -->""",
    "tags": ["Hardware", "Gaming"],
    "image": "https://upload.wikimedia.org/wikipedia/commons/4/4d/Sound_Blaster_16_CT2230.jpg",
    "author": "404 Memory Found",
    "seo": {
        "title": "What Happened to Creative Labs and the Sound Blaster? | 404 Memory Found",
        "description": "The rise and fall of Creative Labs and the Sound Blaster sound card, from a Singapore repair shop to PC audio dominance and beyond.",
        "keywords": ["Sound Blaster", "Creative Labs", "Creative Technology", "sound card", "PC audio", "Sim Wong Hoo", "Sound Blaster 16", "retro PC gaming"],
        "canonical": "https://404memoryfound.com/posts/what-happened-to-creative-labs-sound-blaster"
    }
}

# ============================================================
# POST 2: DANA - Lycos Search Engine
# ============================================================

dana_post = {
    "id": "what-happened-to-lycos-search-engine",
    "title": "What Happened to Lycos, the Search Engine Worth $12 Billion?",
    "date": TODAY,
    "excerpt": "Lycos went from Carnegie Mellon research project to the most visited site on the internet. Then it was sold for $36 million.",
    "body": """<p>In April 1999, Lycos was the most visited destination on the entire internet. Not Google. Not Yahoo. Lycos. A search engine named after the Latin word for "wolf spider," born out of a Carnegie Mellon University research project, with a cartoon black Labrador retriever as its mascot. At its peak, the company had a global presence across more than 40 countries, owned nearly two dozen internet brands, and was valued at $12.5 billion. By 2010, it sold for $36 million. That's a 99.7% decline in value over the course of a single decade.</p>

<p>The story of Lycos is not a story about bad technology. The search engine worked fine. It's a story about what happens when a company built around one thing decides to become everything, right at the exact moment the market decides it only wants one thing done really, really well.</p>

<figure>
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/IBM_PC_XT_5160.jpg/960px-IBM_PC_XT_5160.jpg" alt="An IBM PC XT, representative of the early personal computing era that preceded the web portal wars" loading="lazy" />
  <figcaption>The personal computing revolution of the 1980s set the stage for the search engine wars that would define the late 1990s.</figcaption>
</figure>

<h2>The Wolf Spider from Pittsburgh</h2>

<p>Lycos started in July 1994 as a research project by Dr. Michael Loren Mauldin, a computer scientist at Carnegie Mellon University in Pittsburgh, Pennsylvania. Mauldin had been working on web crawling technology, building a system that could index the rapidly growing World Wide Web. The name came from Lycosidae, the scientific family name for wolf spiders, chosen because these spiders actively hunt their prey rather than waiting in webs. It was a fitting metaphor for a search crawler.</p>

<p>The technology was promising enough that venture capital firm CMGI invested approximately $2 million to spin the project out of CMU and into a proper company. Bob Davis, a former executive at Cambex Corporation, came on board as CEO and first employee in 1995. Davis had no background in search technology, but he understood something about the internet that many technologists missed: the real business wasn't in finding web pages. It was in keeping people on your site long enough to show them ads.</p>

<p>This insight would define Lycos's entire strategy. It would also, eventually, be its undoing.</p>

<h2>The Fastest IPO in History</h2>

<p>Lycos grew fast. Remarkably fast. In April 1996, roughly nine months after incorporation, the company completed what was then the fastest initial public offering from inception to offering in NASDAQ history. Three million shares went out at $16 each, and by the end of the first trading day, the stock had jumped to $29. The company's market value at close: $300 million. For a company that had existed for less than a year, with a product that was essentially a better index of web pages, that valuation was extraordinary.</p>

<p>But in 1996, the search engine landscape was crowded. AltaVista had launched in December 1995 with a massive index and advanced query syntax that power users loved. Excite was building a portal. Yahoo was curating its human-edited directory. HotBot, Infoseek, and WebCrawler were all competing for the same eyeballs. Google wouldn't arrive until 1998, but that didn't make things any easier. With so many options, user loyalty was almost nonexistent. People would switch search engines as casually as changing the radio station.</p>

<p>Bob Davis looked at this landscape and made a calculated decision. If you can't win on search alone, don't compete on search alone. Become a portal. Become a destination. Own so many services that users have a reason to stay.</p>

<h2>The Acquisition Spree</h2>

<p>Between 1997 and 1999, Lycos went on one of the most aggressive acquisition sprees of the dot-com era. The shopping list reads like an encyclopedia of late-'90s internet brands.</p>

<p>In 1998, Lycos acquired Tripod, the web hosting service, for $58 million. Then came WhoWhere, an internet white pages directory, for $133 million in stock. That deal also brought in Angelfire (free web hosting) and MailCity (free email). In October 1998, Lycos purchased Wired Digital from Conde Nast's Wired magazine empire. That one deal alone gave them HotBot (a search engine powered by Inktomi), Wired News, HotWired, Webmonkey (a web development tutorial site), and Suck.com (the snarky commentary site that was beloved by early web culture).</p>

<p>They also picked up Gamesville (online casual games), Quote.com (financial data), Matchmaker.com (dating), Raging Bull (stock message boards), and a string of international partnerships. By 1999, the Lycos Network included over 20 distinct brands and services. The idea was that a user could come to Lycos to search the web, then check their email on MailCity, build a personal homepage on Tripod, play games on Gamesville, look up stock quotes on Quote.com, read the news on Wired, and find a date on Matchmaker. All without ever leaving the Lycos ecosystem.</p>

<p>It was the exact same strategy that Yahoo, Excite, and every other portal was pursuing. The difference was that Lycos was doing it almost entirely through acquisitions rather than internal development. They were buying an empire rather than building one.</p>

<h2>The $12.5 Billion Peak</h2>

<p>By 1999, it looked like the strategy was working. Lycos was the most visited online destination in the world. Ad revenue was flowing. The stock was soaring. And on May 16, 2000, just weeks after the NASDAQ had begun its catastrophic collapse, Terra Networks announced it would acquire Lycos for $12.5 billion.</p>

<p>Terra Networks was the internet division of Telefonica, the Spanish telecommunications giant. The logic was straightforward: Terra had infrastructure and a massive presence in Spain and Latin America. Lycos had traffic and brands in the United States and Europe. Together, they would be a global internet powerhouse. The acquisition price represented a return of nearly 3,000 times Lycos's initial venture capital investment. Bob Davis walked away a very wealthy man.</p>

<p>The deal closed in October 2000. The merged entity was renamed Terra Lycos. And almost immediately, everything fell apart.</p>

<figure>
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/IBM_PC-5150.JPG/960px-IBM_PC-5150.JPG" alt="An early IBM Personal Computer, representing the computing era that laid groundwork for the internet revolution" loading="lazy" />
  <figcaption>From mainframes to search engines: the computing revolution moved fast, and Lycos couldn't keep up with the pace of change.</figcaption>
</figure>

<h2>The Collapse</h2>

<p>The dot-com bubble didn't just deflate. It detonated. The NASDAQ lost 78% of its value between March 2000 and October 2002. Advertising revenue, which was the lifeblood of every portal strategy, dried up almost overnight. Companies that had been spending millions on banner ads suddenly didn't exist anymore. The entire economic model that Lycos was built on evaporated.</p>

<p>But Lycos had a deeper problem than the market downturn. While it had been busy acquiring two dozen brands and trying to glue them together into a coherent portal experience, a small company in Mountain View, California had been quietly perfecting the one thing that actually mattered: search quality.</p>

<p>Google launched in September 1998 with a clean white page and a search algorithm called PageRank that returned dramatically better results than anything else available. While Lycos was adding features, Google was subtracting them. While Lycos was buying Gamesville and Matchmaker.com, Google was hiring PhDs to make their search results 1% more relevant. The irony is brutal: Lycos abandoned its core competency to become a portal, and Google won the entire internet by refusing to be anything other than a search engine (at least initially).</p>

<p>By late 2001, Terra Lycos abandoned its own search crawler entirely and started using FAST (later acquired by Microsoft) for search results. Think about that for a moment. A company that started as a search engine, that was named after a spider, gave up on building its own search technology. The wolf spider stopped hunting.</p>

<h2>Sold, Resold, and Sold Again</h2>

<p>What followed was a slow, painful series of fire sales. In August 2004, Terra Networks sold Lycos to Daum Communications Corporation, a South Korean internet company, for $95.4 million in cash. That's less than 2% of the $12.5 billion Terra had paid just four years earlier. Adjusted for what Terra spent integrating and operating Lycos during those years, the loss was even more staggering.</p>

<p>Under Daum, Lycos tried to reinvent itself around social media features and user-generated content. There were new features, new services, some modest innovations. None of it gained traction. The internet had moved on. Users had Google for search, Facebook for social networking, YouTube for video, and Gmail for email. Nobody needed a portal anymore.</p>

<p>In August 2010, Daum sold Lycos to Ybrant Digital, an internet marketing company based in Hyderabad, India, for $36 million. From $12.5 billion to $36 million in ten years. If you want to understand the dot-com era in a single statistic, that one is hard to beat.</p>

<h2>What Lycos Got Wrong (and What It Got Right)</h2>

<p>The conventional narrative is that Lycos simply lost to Google, and there's truth in that. But the more interesting question is why the portal strategy failed so completely, because it wasn't just Lycos. Excite, Infoseek, and AltaVista all pursued similar strategies and all met similar fates.</p>

<p>The portal model assumed that internet users wanted a single destination for everything. It assumed that bundling services created stickiness. And in 1998, when most people were still figuring out what the internet was for, that assumption seemed reasonable. But it turned out that users preferred best-in-class tools for each task over an okay-at-everything portal. They wanted Google for search, eBay for auctions, Amazon for shopping, and Hotmail (then Gmail) for email. The unbundling of the internet happened before the bundling had even finished.</p>

<p>Here's what Lycos actually got right, though. The acquisitions themselves were often smart. Tripod and Angelfire were genuinely popular services. HotBot was a respected search engine. Wired Digital had excellent content. The problem wasn't the individual pieces. It was the assumption that combining them under one brand would create something greater than the sum of its parts. In reality, each acquisition diluted focus and added operational complexity without adding proportional value.</p>

<p>This is essentially what Google learned from Lycos's mistakes. Google acquired YouTube, Android, Waze, and dozens of other companies, but it kept them largely independent. It never tried to merge Gmail and YouTube and Maps into a single "Google Portal." Each product stood on its own. That distinction matters more than it might seem.</p>

<h2>The Ghost That Still Howls</h2>

<p>Lycos.com is technically still alive. You can visit it today. It operates as a web portal with search (powered by Yahoo), email, news, and various other services. It receives a trickle of traffic, a rounding error compared to its 1999 peak. The black Lab mascot is gone. The Tripod and Angelfire services still technically exist, hosting millions of personal web pages from the late '90s like digital amber, preserving a version of the internet that feels almost impossibly quaint.</p>

<p>Michael Mauldin, the Carnegie Mellon researcher who created the original Lycos crawler, went on to co-found Conversive (later acquired) and continued working in artificial intelligence. Bob Davis, the CEO who rode the rocket from startup to $12.5 billion acquisition, became a venture capitalist. The technology they built wasn't bad. The business they built wasn't stupid. They just got caught in the same trap that ensnared an entire generation of internet companies: the belief that being big was the same as being good.</p>

<p>Google proved otherwise. And the wolf spider's hunting days were over.</p>

<h2>Frequently Asked Questions</h2>

<p><strong>Is Lycos still operating today?</strong><br>
Yes, Lycos.com is still active as a web portal offering search, email, and news services. However, its traffic is a tiny fraction of what it was during its peak in 1999 when it was the most visited site on the internet.</p>

<p><strong>How much was Lycos worth at its peak?</strong><br>
In May 2000, Terra Networks acquired Lycos for $12.5 billion. This represented a return of approximately 3,000 times the company's initial $2 million venture capital investment from CMGI.</p>

<p><strong>Why did Lycos fail against Google?</strong><br>
Lycos pivoted from being a search engine to being a portal, acquiring dozens of services to keep users on its platform. Meanwhile, Google focused exclusively on search quality. Users ultimately preferred best-in-class individual services over bundled portals. Lycos even abandoned its own search crawler in late 2001, conceding the core technology battle.</p>

<p><strong>What happened to Tripod and Angelfire?</strong><br>
Both services still technically exist and continue to host personal web pages created during the late 1990s and early 2000s. They operate under the Lycos umbrella but have not been actively developed or promoted in years.</p>

<p><strong>Who created Lycos?</strong><br>
Lycos was created in July 1994 by Dr. Michael Loren Mauldin as a research project at Carnegie Mellon University in Pittsburgh, Pennsylvania. The name comes from Lycosidae, the Latin family name for wolf spiders. Bob Davis joined as CEO in 1995 and led the company through its IPO and growth phase.</p>

<!-- authored-by: dana -->""",
    "tags": ["Internet Culture", "Business Blunders", "Money & Tech"],
    "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/IBM_PC_XT_5160.jpg/960px-IBM_PC_XT_5160.jpg",
    "author": "404 Memory Found",
    "seo": {
        "title": "What Happened to Lycos, the Search Engine Worth $12 Billion? | 404 Memory Found",
        "description": "From Carnegie Mellon research project to the most visited site on the internet to a $36 million fire sale. The complete history of Lycos.",
        "keywords": ["Lycos", "search engine", "dot-com bubble", "Terra Networks", "web portal", "1990s internet", "Bob Davis", "Carnegie Mellon"],
        "canonical": "https://404memoryfound.com/posts/what-happened-to-lycos-search-engine"
    }
}

# ============================================================
# Load, append, and save
# ============================================================

with open("posts.json", "r") as f:
    data = json.load(f)

# Check for duplicate IDs
existing_ids = {p["id"] for p in data["posts"]}
for post in [marcus_post, dana_post]:
    if post["id"] in existing_ids:
        print(f"ERROR: Duplicate ID '{post['id']}' already exists!")
        exit(1)

data["posts"].append(marcus_post)
data["posts"].append(dana_post)

with open("posts.json", "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Added 2 new posts. Total posts: {len(data['posts'])}")
print(f"  1. [{marcus_post['id']}] (Marcus)")
print(f"  2. [{dana_post['id']}] (Dana)")
