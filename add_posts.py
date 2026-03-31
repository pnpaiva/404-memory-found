#!/usr/bin/env python3
"""Add 2 new blog posts to posts.json."""
import json

# Read existing posts
with open('posts.json') as f:
    data = json.load(f)
posts = data['posts']

# ============================================================
# POST 1: MARCUS - The Original Xbox
# ============================================================
marcus_post = {
    "id": "what-happened-to-original-xbox-microsoft-gaming",
    "title": "What Happened to the Original Xbox? Microsoft's $4 Billion Bet on Gaming",
    "date": "2026-03-31",
    "excerpt": "Four engineers, a gutted Dell laptop, and a plan to trick Bill Gates into building a gaming console. The original Xbox was never supposed to exist.",
    "body": """<p>Picture this: it's late 1998, and four guys at Microsoft are sitting around after work, tearing apart Dell laptops. Not because they're bored. Because they're terrified. Sony's PlayStation 2 is coming, and everyone at Microsoft knows it's going to be more than a game console. It's going to be a living room computer. And if Sony pulls that off, Windows could lose the one room in the house it hasn't conquered yet.</p>

<p>The four engineers were Kevin Bachus, Seamus Blackley, Ted Hase, and Otto Berkes. All of them from Microsoft's DirectX team, the group responsible for making Windows not terrible at running games. They weren't executives. They weren't in the console business. They were just a handful of guys who loved games and saw something their bosses didn't: that the future of the living room was about to be decided, and Microsoft wasn't even in the conversation.</p>

<p>What they built from those gutted laptops would become the original Xbox. A machine that lost Microsoft over $4 billion, nearly got canceled a dozen times, and somehow changed the entire gaming industry forever.</p>

<figure>
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Xbox-Console-wDuke-L.jpg/960px-Xbox-Console-wDuke-L.jpg" alt="The original Microsoft Xbox console with its distinctive Duke controller" loading="lazy" />
  <figcaption>The original Xbox console and its massive Duke controller, which became one of gaming's most iconic (and divisive) peripherals.</figcaption>
</figure>

<h2>The Pitch That Almost Didn't Happen</h2>

<p>Here's the thing about the Xbox: the people who made it happen had to essentially trick their own company into building it. Microsoft in the late '90s was a Windows company. Everything revolved around Windows. So when Blackley and his team first pitched the idea of a dedicated gaming console, the immediate response from upper management was predictable. Why not just make it run Windows?</p>

<p>There was actually a competing team at Microsoft, the WebTV group, that wanted to do exactly that. Build a cheap set-top box that ran a stripped-down version of Windows. It would be cheaper to produce and, more importantly, it would keep the Windows ecosystem front and center. On paper, it made total sense for a company like Microsoft.</p>

<p>The DirectX team wanted something completely different. They wanted a real gaming machine. Custom hardware, built-in hard drive, broadband-ready out of the box. Things no console had ever shipped with before. And they knew that if they pitched it honestly, as a non-Windows device, they'd get shut down immediately.</p>

<p>So Seamus Blackley did something bold. He told Bill Gates exactly what Gates wanted to hear: that the console would run a modified version of Windows. Later, Blackley openly admitted that this was intentional misdirection. He has said publicly that he "hoodwinked" Gates into approving the project by framing it as a Windows device, knowing full well that the final product would barely resemble Windows at all.</p>

<p>The two teams made their competing pitches to Gates on May 5, 1999, in a meeting with over twenty people. The WebTV team argued for the cheap appliance approach. The DirectX team, backed by Microsoft VP Ed Fries, argued that a built-in hard drive would enable online gaming in a way no other console could match. Gates sided with the DirectX team. The Xbox was officially a go.</p>

<h2>Building the Beast</h2>

<p>What made the Xbox so unusual for 2001 was that it was basically a PC in a black and green box. While Sony and Nintendo designed custom chips from scratch, Microsoft went to Intel for a 733 MHz Pentium III processor and Nvidia for a custom GPU based on the GeForce 3 architecture. It had 64 MB of RAM, which was four times what the PS2 offered. It had an 8 or 10 GB hard drive built in. And it had an Ethernet port, which in 2001 was practically science fiction for a game console.</p>

<p>The philosophy was straightforward: make it powerful enough that developers used to working on PCs could transition easily, and make it connected enough that online gaming could become a real thing. No memory cards, no dial-up adapters sold separately. Just plug it in and go.</p>

<p>The controller, though. We need to talk about the controller. The original Xbox controller, nicknamed "The Duke," was enormous. It was designed primarily for American hands, which is a polite way of saying it was comically oversized for anyone who wasn't a linebacker. It was 6.5 inches wide. The original PlayStation controller was about 5.5 inches. Japanese gamers in particular found it nearly unusable. Microsoft eventually released the smaller Controller S, which had originally been designed for the Japanese market, and it became the default controller bundled with the system worldwide by 2002.</p>

<h2>The Secret Weapon Nobody Saw Coming</h2>

<p>In June 2000, Microsoft announced that it had acquired a small game studio called Bungie for approximately $30 million. At the time, Bungie was best known for the Marathon series on Mac and was working on a game called Halo, which was being developed as a Mac and PC title. The gaming press noticed, but nobody understood just how important this acquisition would be.</p>

<p>Halo was retooled from the ground up as an Xbox exclusive and launch title. When the Xbox hit shelves on November 15, 2001, priced at $299, Halo: Combat Evolved was right there next to it. And it changed everything.</p>

<p>The launch was massive. Microsoft sold over 1.5 million consoles before the end of 2001, just six weeks of sales. Halo had a roughly 50% attach rate at launch, meaning about half of everyone who bought an Xbox also bought Halo. By the time the dust settled, Halo sold over 6.4 million copies, meaning roughly one in four Xbox owners had a copy. For a brand-new franchise on a brand-new console from a company with zero credibility in gaming, those numbers were staggering.</p>

<figure>
  <img src="https://upload.wikimedia.org/wikipedia/commons/f/f2/Bill_Gates_unveiling_Xbox.jpg" alt="Bill Gates presenting the original Xbox console at its official unveiling" loading="lazy" />
  <figcaption>Bill Gates unveiling the Xbox to the world. For a company that had never made a gaming console, the stakes were enormous.</figcaption>
</figure>

<h2>Losing Money on Every Single Console</h2>

<p>Here's where the math gets painful. The Xbox retailed for $299, but estimates put the manufacturing cost somewhere between $375 and $425 per unit. Let that sink in. Microsoft was losing somewhere around $100 to $125 on every single console it sold. The plan, the same plan Sony and others had used before, was to make it up on game licensing fees. Every third-party game sold on Xbox meant money flowing back to Microsoft.</p>

<p>But the PS2 had launched a year earlier, in October 2000, and it already had a massive head start. By the time the Xbox arrived, the PS2 was the dominant force in gaming with a library that was growing by the week. Nintendo's GameCube launched just three days after the Xbox, on November 18, 2001, splitting the "alternative to PS2" market even further.</p>

<p>The Xbox ultimately sold around 24 million units worldwide. Not bad for a first attempt, but nowhere near the PS2's 155 million. Microsoft's gaming division reported cumulative losses of over $4 billion on the original Xbox. Four billion dollars. That's not a rounding error. That's a bet so large that only a company with Microsoft's cash reserves could survive it.</p>

<h2>Xbox Live Changed the Game</h2>

<p>If Halo proved the Xbox could compete, Xbox Live proved it could innovate. Launched on November 15, 2002, exactly one year after the console itself, Xbox Live was the first truly integrated online gaming service for consoles. Sony had online capabilities for the PS2, but they were fragmented, game-by-game, requiring separate setups. Xbox Live was unified: one account, one friends list, one voice chat system across every game.</p>

<p>The launch titles included MechAssault, Ghost Recon, and MotoGP Online, but it was Halo 2 in November 2004 that turned Xbox Live into a phenomenon. Within 24 hours of its release, Halo 2 generated $125 million in sales, making it the biggest entertainment launch in history at the time, bigger than any movie, any album, anything.</p>

<p>Xbox Live introduced concepts that we now take completely for granted: friend lists, achievements, voice chat built into the system, downloadable content. Every online gaming service that exists today, PlayStation Network, Nintendo Switch Online, Steam's friends system, owes something to what Xbox Live pioneered in 2002.</p>

<h2>Japan Was a Disaster</h2>

<p>For all its success in North America and moderate success in Europe, the Xbox was a spectacular failure in Japan. It launched there on February 22, 2002, and the reception was brutal. Japanese gamers found the console too large, the controller too bulky, and the game library too Western-focused. Microsoft sold roughly 450,000 to 500,000 Xboxes in Japan over the console's entire lifespan. For context, the PS2 sold over 21 million units in Japan alone.</p>

<p>Part of the problem was cultural. Microsoft was an American software company trying to sell hardware in a market dominated by Sony and Nintendo, two companies that Japanese consumers had grown up with. Part of it was practical. The Duke controller really was too big for many Japanese gamers' hands. And part of it was the game library. Microsoft invested heavily in securing Japanese game developers, but the results never matched the investment.</p>

<p>This Japan problem would haunt Xbox for decades. Even now, the Xbox brand has never found significant footing in the Japanese market, though the situation has improved slightly with Game Pass.</p>

<h2>The Legacy Nobody Expected</h2>

<p>Microsoft discontinued the original Xbox in 2006, but by then, the Xbox 360 was already a year old and well on its way to becoming one of the most successful consoles of its generation. The original Xbox was never profitable. It was never the market leader. It never cracked Japan. By most traditional business metrics, it was a failure.</p>

<p>But that misses the point entirely. The Xbox proved that Microsoft could compete in gaming. It established Xbox Live as the gold standard for online console gaming. It launched the Halo franchise, which has generated billions in revenue across games, merchandise, a TV series, and novels. It forced Sony and Nintendo to take online gaming seriously, which ultimately made gaming better for everyone.</p>

<p>And it created a gaming brand worth tens of billions of dollars. Microsoft's acquisition of Activision Blizzard in 2023 for $68.7 billion was only possible because four engineers tore apart some laptops in 1998 and convinced Bill Gates to bet on gaming.</p>

<p>Sometimes the best business decisions look terrible on the spreadsheet. The original Xbox lost $4 billion and changed an industry. Not a bad trade.</p>

<h2>Frequently Asked Questions</h2>

<h2>How much did the original Xbox cost at launch?</h2>
<p>The original Xbox launched on November 15, 2001, at a retail price of $299 in North America. This was competitive with the Nintendo GameCube ($199) and PlayStation 2 ($299 at the time of Xbox's launch, having dropped from its original $299 price). The price was eventually reduced to $179 in 2003 and $149 in 2004.</p>

<h2>How many original Xbox consoles were sold?</h2>
<p>Microsoft sold approximately 24 million Xbox consoles worldwide during its production run from 2001 to 2006. While respectable for a first-time console maker, this was far behind the PlayStation 2's approximately 155 million units and ahead of the GameCube's roughly 21.7 million units.</p>

<h2>Why was the original Xbox controller so big?</h2>
<p>The original Xbox controller, nicknamed "The Duke," was designed primarily with the North American market in mind. At about 6.5 inches wide, it was significantly larger than competing controllers. Microsoft eventually released the smaller Controller S, originally designed for the Japanese market, which became the standard controller bundled with the console from mid-2002 onward.</p>

<h2>What was the best-selling original Xbox game?</h2>
<p>Halo 2 was the best-selling original Xbox game, with over 8 million copies sold. It was followed by the original Halo: Combat Evolved at approximately 6.4 million copies. Together, the two Halo games represented a significant portion of the Xbox's total software sales.</p>

<h2>Did Microsoft lose money on the original Xbox?</h2>
<p>Yes, Microsoft lost over $4 billion on the original Xbox. The company sold each console at a substantial loss, with manufacturing costs estimated between $375 and $425 per unit against a $299 retail price. The strategy was to recoup losses through game licensing fees, but the console never reached the install base needed to turn a profit.</p>

<!-- authored-by: marcus -->""",
    "tags": ["Gaming", "Hardware", "Business Blunders"],
    "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Xbox-Console-wDuke-L.jpg/960px-Xbox-Console-wDuke-L.jpg",
    "author": "404 Memory Found",
    "seo": {
        "title": "What Happened to the Original Xbox? Microsoft's $4 Billion Bet | 404 Memory Found",
        "description": "How four Microsoft engineers tricked Bill Gates into building a gaming console, lost $4 billion, and created one of the biggest brands in gaming history.",
        "keywords": ["original xbox", "xbox history", "microsoft xbox", "halo combat evolved", "xbox live", "seamus blackley", "bill gates xbox", "xbox launch 2001"],
        "canonical": "https://404memoryfound.com/posts/what-happened-to-original-xbox-microsoft-gaming"
    }
}

# ============================================================
# POST 2: DANA - The AOL-Time Warner Merger
# ============================================================
dana_post = {
    "id": "aol-time-warner-merger-worst-deal-in-history",
    "title": "The AOL-Time Warner Merger: The Worst Deal in Corporate History",
    "date": "2026-03-31",
    "excerpt": "In January 2000, AOL bought Time Warner for $182 billion. Within three years, the combined company posted the largest annual loss ever recorded. Here is how it fell apart.",
    "body": """<p>On January 10, 2000, Steve Case and Gerald Levin stood side by side at a press conference in New York and announced the largest merger in corporate history. AOL, a company that delivered the internet through phone lines and free trial CDs, was acquiring Time Warner, the media conglomerate behind CNN, HBO, Warner Bros., and Time magazine. The deal was valued at $182 billion.</p>

<p>The logic seemed obvious. Time Warner had the content. AOL had the audience. Combine them, and you'd have a vertically integrated media empire that could deliver movies, news, and music directly to 30 million American living rooms through AOL's dial-up service. It was the kind of deal that made Wall Street analysts use words like "transformative" and "paradigm shift" without a trace of irony.</p>

<p>Three years later, the combined company posted a loss of $98.7 billion, the largest annual loss in corporate history. By 2003, they had quietly dropped "AOL" from the company name. By 2009, they had formally split apart. Over $200 billion in shareholder value had evaporated. Ted Turner, who had merged his Turner Broadcasting into Time Warner in 1995, estimated he lost roughly 80% of his wealth, approximately $8 billion.</p>

<p>The AOL-Time Warner merger is routinely called the worst deal in business history. The interesting question is not whether it failed. It's why anyone thought it would work.</p>

<figure>
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/AOL_promotional_CDs_in_Canada.jpg/960px-AOL_promotional_CDs_in_Canada.jpg" alt="A collection of AOL free trial CDs, the ubiquitous marketing tool that helped AOL reach 30 million subscribers" loading="lazy" />
  <figcaption>AOL's promotional free trial CDs became one of the most aggressive marketing campaigns in tech history, helping the company reach 30 million subscribers before the merger.</figcaption>
</figure>

<h2>The Numbers That Made It Look Brilliant</h2>

<p>To understand why this deal happened, you need to understand what AOL looked like in January 2000. The company had roughly 30 million subscribers paying around $21.95 per month. Its market capitalization was approximately $163 billion. For context, Time Warner, a company that owned HBO, CNN, Warner Bros. film studio, Time magazine, and the second-largest cable system in the United States, was valued at roughly $83 billion. AOL, a company that mailed people plastic CDs, was worth nearly twice as much as all of that combined.</p>

<p>This was the dot-com bubble at its most inflated. The NASDAQ had peaked at 5,048 on March 10, 2000, just two months after the merger announcement. Internet companies were being valued not on earnings but on "eyeballs," unique visitors, and subscriber growth curves. By those metrics, AOL was a rocket ship.</p>

<p>Steve Case, AOL's CEO, understood something that many people have since given him credit for: the stock was overvalued, and it wouldn't stay that way forever. The merger was, in a very real sense, AOL using its inflated stock to buy real assets before the music stopped. Case has never quite put it that way publicly, but the structure of the deal tells the story. AOL shareholders received 55% of the new company despite AOL contributing less than 30% of the combined revenue. It was a stock swap, and AOL's stock was the currency.</p>

<p>Gerald Levin, Time Warner's CEO, believed the internet was going to transform media and that Time Warner needed a digital distribution partner. He pushed the deal through despite significant resistance from within his own company. Levin reportedly didn't even consult Time Warner's board before entering into serious negotiations.</p>

<h2>The Broadband Problem Nobody Wanted to Talk About</h2>

<p>Here is the fact that should have killed the deal before it started: at the time of the merger, only about 3% of American households had broadband internet. The other 97% were on dial-up or not online at all. AOL's entire business model was built on dial-up subscriptions.</p>

<p>Broadband was already arriving. Cable companies were rolling out high-speed internet service. DSL was expanding through phone companies. The trajectory was obvious to anyone paying attention. Within a few years, dial-up would begin its decline, and with it, the primary reason 30 million people paid AOL every month.</p>

<p>The merger was supposed to solve this problem. Time Warner owned Road Runner, one of the largest cable broadband providers in the country. The idea was that AOL would transition its subscribers from dial-up to broadband over Time Warner's cable lines. AOL would become the internet service people accessed through their cable modems instead of through their phone lines.</p>

<p>It never happened. Time Warner's cable division had its own priorities and its own revenue targets. Road Runner was already a functioning broadband service. The cable operators had no interest in making AOL the default interface for their broadband customers. Why would they? They were already selling internet access directly. Adding AOL as a middleman only complicated things and cut into their margins.</p>

<p>This was the central failure of the merger's thesis. The "synergies" that justified the $182 billion price tag depended on different divisions of the combined company cooperating in ways that went against their individual business interests. That almost never works in large mergers, and it certainly didn't work here.</p>

<h2>A Culture Clash for the History Books</h2>

<p>Even if the business logic had held up, the execution was doomed by something more fundamental: the two companies genuinely despised each other.</p>

<p>AOL's culture was fast, aggressive, and deal-oriented. Time Warner's culture was deliberate, creative, and fiefdom-based. HBO operated like a separate country. CNN operated like a separate country. Warner Bros. operated like a separate country. These divisions had spent decades building walls around their operations, and they had no intention of tearing them down because some dial-up company had bought their parent corporation.</p>

<p>Time Warner executives reportedly referred to their AOL counterparts as "Assholes Online." The contempt was not subtle. AOL people were seen as overpaid internet cowboys who didn't understand the media business. Time Warner people were seen by AOL as dinosaurs who didn't understand the internet. Both characterizations contained some truth, which made the resentment worse.</p>

<p>The promised integration never materialized. AOL was supposed to sell advertising across Time Warner's properties. Time Warner's content was supposed to flow through AOL's platform. Instead, each division continued operating exactly as it had before the merger, only now with an extra layer of corporate bureaucracy and a shared sense of mutual resentment.</p>

<figure>
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Time_Warner_Center_May_2010.JPG/960px-Time_Warner_Center_May_2010.JPG" alt="The Time Warner Center building at Columbus Circle in New York City" loading="lazy" />
  <figcaption>The Time Warner Center at Columbus Circle in Manhattan. By the time this building opened in 2004, the AOL name had already been scrubbed from the corporate identity.</figcaption>
</figure>

<h2>The Collapse in Numbers</h2>

<p>The merger officially closed on January 11, 2001. Within weeks, the dot-com bubble burst in earnest. The NASDAQ, which had peaked near 5,048 in March 2000, fell below 2,000 by early 2001 and would eventually bottom out around 1,114 in October 2002.</p>

<p>AOL's advertising revenue, which had been growing aggressively through the late '90s, collapsed. The company had been booking revenue from advertising deals in ways that regulators later questioned. In October 2002, the SEC and Department of Justice began investigating AOL's accounting practices, particularly around "round-trip" advertising deals where AOL would buy services from a company and that company would simultaneously buy advertising from AOL, inflating revenue figures on both sides.</p>

<p>Meanwhile, AOL's subscriber base, the crown jewel of the merger, started shrinking. Subscribers peaked at approximately 26.7 million in 2002, then began a decline that would never reverse. As broadband adoption accelerated, fewer people needed AOL's dial-up service. And unlike the merger thesis predicted, those departing subscribers weren't switching to AOL-branded broadband over Time Warner's cables. They were just leaving.</p>

<p>In 2002, the combined company took a goodwill write-down of $99 billion. That single accounting entry remains one of the largest in corporate history. It was the company formally acknowledging that the assets it had acquired in the merger were worth roughly $99 billion less than what it had paid for them.</p>

<p>The total loss for 2002 was $98.7 billion. To put that in perspective, that was more than the GDP of most countries at the time. It remains the largest annual corporate loss ever recorded.</p>

<h2>The Leadership Exodus</h2>

<p>Gerald Levin stepped down as CEO in May 2002, just sixteen months after the merger closed. He was replaced by Richard Parsons, a Time Warner veteran who had quietly opposed the merger from the beginning. Steve Case resigned as chairman in January 2003, under pressure from the board and from Time Warner executives who blamed AOL for the catastrophe.</p>

<p>Ted Turner, who had been vice chairman and the company's largest individual shareholder, saw his stake decline from roughly $10 billion to approximately $2 billion. He has called the merger "the biggest mistake of my life" and estimated his personal loss at about $8 billion. Turner largely stepped away from the company's operations after the merger, losing the influence he had spent decades building.</p>

<p>The company quietly dropped "AOL" from its name in October 2003, becoming simply Time Warner again. It was a small but telling admission. The AOL brand, which had been worth enough to justify 55% ownership of the combined entity just three years earlier, was now toxic enough that the company wanted it off the letterhead.</p>

<h2>What Actually Went Wrong</h2>

<p>The standard explanation for the AOL-Time Warner failure is that the dot-com bubble burst and took AOL's value with it. That is true but incomplete. The merger would have struggled even in a healthy market, because its core assumptions were flawed.</p>

<p>First, the idea that dial-up subscribers would seamlessly transition to broadband through Time Warner's cable systems assumed a level of corporate cooperation that never existed and was never incentivized. Second, the idea that AOL's platform would become the default interface for consuming Time Warner's content assumed that AOL's platform was good enough to justify that role. It wasn't. AOL's software was designed for dial-up. It was slow, cluttered, and increasingly irrelevant in a broadband world.</p>

<p>Third, and most fundamentally, the merger assumed that bundling content and distribution under one roof would create value. This is essentially what TikTok's algorithm does today, matching content to audience through a single platform. But AOL wasn't an algorithm. It was a gated community built on a 56k modem connection. The concept was right. The execution was two technology generations too early.</p>

<p>The final separation came in 2009, when Time Warner formally spun off AOL as an independent company. AOL was subsequently acquired by Verizon in 2015 for $4.4 billion, a fraction of the $163 billion market cap it had held in 2000. Verizon merged AOL with Yahoo into a subsidiary called Oath, which was later renamed Verizon Media, and then sold to Apollo Global Management in 2021 for roughly $5 billion.</p>

<h2>The Lesson That Keeps Repeating</h2>

<p>The AOL-Time Warner merger is often treated as a cautionary tale about dot-com excess, and it is. But it is also a cautionary tale about something more specific: the danger of using inflated currency to buy real assets and then failing to integrate them. The deal made Steve Case's shareholders temporarily rich and Gerald Levin's shareholders permanently poorer. The "synergies" were a story told to justify a price that only made sense if you believed AOL's stock price reflected actual value.</p>

<p>Every few years, a version of this story repeats itself. A high-flying company with an inflated valuation acquires a mature business with real assets, promises transformative synergies, and watches as the cultures clash, the integration stalls, and the market corrects. The names change. The pattern doesn't.</p>

<p>Which is probably the most useful thing the AOL-Time Warner merger ever produced: a case study that business schools will teach for the next hundred years, about what happens when you mistake momentum for gravity.</p>

<h2>Frequently Asked Questions</h2>

<h2>How much was the AOL-Time Warner merger worth?</h2>
<p>The merger was valued at approximately $182 billion when announced in January 2000, making it the largest corporate merger in history at that time. Adjusted for inflation, that would be over $330 billion in 2026 dollars. AOL shareholders received 55% of the combined company, despite AOL contributing less than 30% of combined revenue.</p>

<h2>How much money did the AOL-Time Warner merger lose?</h2>
<p>The combined company posted a loss of $98.7 billion in 2002, still the largest annual corporate loss ever recorded. Over $200 billion in shareholder value was destroyed between the merger's completion in January 2001 and the company's eventual separation. The company took a goodwill write-down of approximately $99 billion in 2002 alone.</p>

<h2>Why did the AOL-Time Warner merger fail?</h2>
<p>The merger failed for multiple overlapping reasons: the dot-com bubble burst shortly after the deal closed, AOL's dial-up subscriber base began declining as broadband adoption accelerated, the promised "synergies" between AOL's internet platform and Time Warner's content never materialized, and a severe culture clash between the two companies prevented meaningful integration.</p>

<h2>What happened to AOL after the merger?</h2>
<p>Time Warner dropped "AOL" from its corporate name in 2003 and formally spun off AOL as an independent company in 2009. Verizon acquired AOL in 2015 for $4.4 billion and merged it with Yahoo into a subsidiary. That unit was sold to Apollo Global Management in 2021 for approximately $5 billion. The AOL dial-up service was finally discontinued in 2024.</p>

<h2>How many subscribers did AOL have at its peak?</h2>
<p>AOL's subscriber base peaked at approximately 26.7 million in 2002. At that point, roughly half of all internet-connected American households were accessing the internet through AOL's dial-up service. Subscribers declined steadily after 2002 as broadband adoption accelerated, dropping to about 2 million by the time Verizon acquired AOL in 2015.</p>

<!-- authored-by: dana -->""",
    "tags": ["Business Blunders", "Internet Culture", "Money & Tech"],
    "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/AOL_promotional_CDs_in_Canada.jpg/960px-AOL_promotional_CDs_in_Canada.jpg",
    "author": "404 Memory Found",
    "seo": {
        "title": "The AOL-Time Warner Merger: The Worst Deal in Corporate History | 404 Memory Found",
        "description": "How AOL used $182 billion in inflated stock to buy Time Warner, lost $99 billion in a single year, and created the biggest corporate disaster in history.",
        "keywords": ["aol time warner merger", "worst merger in history", "aol time warner failure", "steve case gerald levin", "dot-com bubble", "time warner aol", "corporate mergers gone wrong"],
        "canonical": "https://404memoryfound.com/posts/aol-time-warner-merger-worst-deal-in-history"
    }
}

# Add new posts
posts.append(marcus_post)
posts.append(dana_post)

# Write back
data['posts'] = posts
with open('posts.json', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Added 2 new posts. Total posts: {len(posts)}")
print(f"  Marcus: {marcus_post['title']}")
print(f"  Dana: {dana_post['title']}")
