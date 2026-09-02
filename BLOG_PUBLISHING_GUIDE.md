# Ring Mint Journal Publishing Guide

How to publish a blog post that is perfectly optimized for Google, Bing, and AI search
(ChatGPT, Claude, Perplexity, Google AI Overviews). Follow this top to bottom for **every** post.

The blog lives at `/blog/`. There is **one template**: hero image + text
([blog/_post-template.html](blog/_post-template.html)). Categories:

| Category | Anchor on /blog/ | `articleSection` value | What goes here |
|---|---|---|---|
| Jewelry News | `#jewelry-news` | `Jewelry News` | Trade news and what it means for a buyer |
| Diamonds & Gemstones | `#diamonds-and-gemstones` | `Diamonds & Gemstones` | Grading, sourcing, lab vs natural, colored stones |
| Buying Guides | `#buying-guides` | `Buying Guides` | Cost, timelines, what to ask, how to compare options |

Three tools do the mechanical work. Learn these three commands and the rest of this guide is context:

| Tool | What it does |
|---|---|
| `python3 tools/blog-images.py generate ...` | Makes all six images for a post in the house style |
| `python3 tools/build-feed.py` | Rebuilds `/feed.xml` (full-text RSS) from every published post |
| `python3 tools/blog-check.py YOUR-SLUG` | Runs every mechanical check in sections 3, 5, and 6 and exits non-zero on any miss |

---

## 1. Before you write

- [ ] **Pick one primary keyword/question** the post answers (e.g. "do lab diamonds test as real diamonds"). One post = one search intent. If you have two intents, write two posts.
- [ ] **Check it isn't cannibalizing an existing page.** The pillar pages (custom rings, lab diamonds, concierge, FAQ) already rank for their topics, so a post should support them, not compete. If it overlaps, link to the pillar, don't restate it.
- [ ] **Pick the category.** News about the trade is Jewelry News. Anything about the stone itself is Diamonds & Gemstones. Anything about the decision to buy (cost, timing, process, comparing options) is Buying Guides. If a post could sit in two, the reader's intent wins: a person asking "how much" wants a buying guide even if the answer is mostly about stones.
- [ ] **Phrase the title the way people actually ask.** AI assistants surface pages that literally match the question. "How much does a custom engagement ring cost?" beats "Custom ring pricing explained."
- [ ] **List 3-5 secondary keywords/phrasings** to work in naturally (synonyms, "vs" variants, misspellings people use like "moissanite vs diamond"). These become the JSON-LD `keywords` and the `article:tag` entries, so pick real search phrasings, not internal labels.
- [ ] **Decide the "short answer."** If you can't write a 2-3 sentence answer to the post's central question, the post isn't ready.

## 2. Slug and files

- [ ] Slug: lowercase, hyphens, 3-6 words, contains the primary keyword, **no dates, no stop words** (`/blog/lab-diamond-resale-value/`, not `/blog/2026/09/what-you-should-know-about-the-resale-value-of-lab-diamonds/`). Slugs are permanent. Never change one after publishing.
- [ ] `cp blog/_post-template.html blog/YOUR-SLUG/index.html`
- [ ] **Every post ships six images**, all in `/assets/blog/`, all in the same house style (see below). None are optional.
  - `YOUR-SLUG-hero.jpg`: 1600×900, the post hero on desktop and tablet.
  - `YOUR-SLUG-hero-mobile.jpg`: 1080×1350 (4:5), the post hero on phones. The template serves it through `<picture>` below 620px. A 16:9 image cropped to a phone screen is either a tiny strip or a sliver of the middle; this file is a separate composition, not a resize.
  - `YOUR-SLUG-og.jpg`: 1200×630, the social/OG image, title overlaid. This is what Facebook, LinkedIn, iMessage, Slack, and X show when the URL is pasted.
  - `YOUR-SLUG-card.jpg`: 800×500, the card image for the /blog/ listing.
  - `YOUR-SLUG-story.jpg`: 1080×1920, the Instagram Story for the post. Not referenced by the site; it exists so the post is announced on Stories the day it publishes, in the same look as everything else. Text stays out of the top and bottom 250px (Instagram's own UI covers those), and the "read the post" pill sits at roughly 89% height so the link sticker can go on top of it.
  - `YOUR-SLUG-pin.jpg`: 1000×1500 (2:3), the Pinterest pin. Not referenced by the site. Pinterest crops anything that isn't 2:3, so the Story and OG images both lose their headline there; this file is the one you pin.
  - Compress everything (target < 200 KB each; the generator does this for you, otherwise Squoosh.app, quality ~75 JPEG).
  - Filenames are descriptive and keyworded: `oval-lab-diamond-ring-hero.jpg`, never `IMG_4021.jpg`.
- [ ] **Generate them with the script, do not freehand them.** [tools/blog-images.py](tools/blog-images.py) produces all six from a slug and a headline, in the house style, at the right sizes and weights:
  ```bash
  python3 tools/blog-images.py generate --slug YOUR-SLUG --title "Line one|line two|line three" --answer "One short answer line." --sub "Supporting line,|second supporting line."
  ```
  If the post has a real photograph for its hero (a stone on the bench, a client's ring), keep the photo as `YOUR-SLUG-hero.jpg`, make the OG and card from it, and run only the three commands the script cannot replace with line art:
  ```bash
  python3 tools/blog-images.py crop-mobile --slug YOUR-SLUG
  ```
  ```bash
  python3 tools/blog-images.py story --slug YOUR-SLUG --title "..." --answer "..." --sub "..."
  ```
  ```bash
  python3 tools/blog-images.py pin --slug YOUR-SLUG --title "..." --answer "..." --sub "..."
  ```
- [ ] **House style for all six images.** Charcoal `#171717` ground with a warm radial glow, gold `rgb(212,183,134)` line-art diamonds (round brilliant seen from above, and the classic crown-and-pavilion profile), small four-point sparkles, a hairline gold frame inset 40px, Didot for headlines in cream `rgb(244,239,230)`, Didot italic in gold for the one-line answer, Georgia letter-spaced small caps for the "THE RING MINT JOURNAL" eyebrow. A photographic hero is fine, but the OG, card, Story, and pin built from it still carry the same type, eyebrow, hairline, and pill. Do not introduce new colours, fonts, or icon styles for one post. If the style needs to change, change it in the script so every future post changes with it.

## 3. Fill in the template

Replace **every ALL-CAPS token**. Then verify (`tools/blog-check.py` checks all of this, but know what it is checking):

### Head / metadata
- [ ] `<title>`: 50-60 characters, primary keyword at the front, ends `| Ring Mint`. Unique across the site.
- [ ] Meta description: 140-160 characters, contains the primary keyword, states the answer or promise. Unique across the site.
- [ ] **Delete the `noindex` line and uncomment the `index, follow` robots line.** (The template ships noindexed so an unfinished copy can't leak into Google.)
- [ ] Canonical URL matches the final URL exactly, with trailing slash: `https://ringmint.com/blog/YOUR-SLUG/`.
- [ ] The `<link rel="alternate" type="application/rss+xml">` line is already correct in the template. Leave it.
- [ ] **Open Graph, all filled:** `og:title`, `og:description` (same as the meta description or slightly warmer), `og:url` (identical to the canonical), `og:image` **and** `og:image:secure_url` (both the absolute `https://ringmint.com/assets/blog/YOUR-SLUG-og.jpg`), `og:image:type` stays `image/jpeg`, width 1200, height 630, and `og:image:alt` describing the OG image in one sentence.
- [ ] **Article tags:** `article:published_time` and `article:modified_time` (ISO dates, `2026-09-02`), `article:section` matching the category table exactly, and **3 to 6 `article:tag` lines**, one per keyword, mirroring the JSON-LD `keywords` list. Pinterest Rich Pins and Facebook read these.
- [ ] **Twitter/X:** `twitter:card` stays `summary_large_image`; `twitter:site` and `twitter:creator` are preset to `@theringmint`; fill `twitter:title`, `twitter:description`, and `twitter:image` (same OG image).

### Structured data (JSON-LD)
- [ ] `BlogPosting` block: headline (max 110 chars), description, image, dates, `articleSection`, `keywords`, `wordCount` (rough count is fine, the check script warns past 20% drift) all filled. Dates must equal the `article:` meta dates.
- [ ] Breadcrumb item 3 name/URL updated.
- [ ] The `Person` block already carries `sameAs` links to Instagram, LinkedIn, Pinterest, and Trustpilot so Google ties the byline to the same author entity as the homepage. Leave it.
- [ ] If the post contains a real Q&A section (3+ questions with self-contained answers), add a second `<script type="application/ld+json">` with `FAQPage` markup; copy the pattern from [faq/index.html](faq/index.html). Only mark up questions that visibly appear on the page (the check script fails any FAQ question it cannot find in the body).
- [ ] If the post is a step-by-step process, consider `HowTo` markup instead of FAQ.
- [ ] Validate at https://validator.schema.org and https://search.google.com/test/rich-results. **Zero errors** before publishing.

### Body
- [ ] Exactly **one `<h1>`**, matching (or close to) the title tag.
- [ ] Byline present and linked to `/press/` (`rel="author"`), date in a `<time datetime="...">` element equal to `article:published_time`, read time filled in (about 230 words a minute).
- [ ] Hero image: keep the `<picture>` element from the template. The `<source>` points at `-hero-mobile.jpg` (1080×1350) for `(max-width: 620px)`, the `<img>` at `-hero.jpg` (1600×900) with real `width`/`height` attributes and `fetchpriority="high"`. **Descriptive alt text** (describe the image honestly; include the keyword only if it truly belongs). The two `<link rel="preload" as="image">` tags in the head carry matching `media` attributes so a phone only downloads the mobile file; update both hrefs.
- [ ] Category eyebrow links to the right anchor on `/blog/`.

## 4. Writing rules (SEO + AI-search / GEO)

This is what gets a page quoted by ChatGPT, Perplexity, and AI Overviews:

- [ ] **Answer first.** The "short answer" takeaway box at the top answers the central question in 2-3 self-contained sentences. Then the opening paragraph answers it again in ~100 words. LLMs and featured snippets lift these blocks verbatim, so write them to be quotable out of context.
- [ ] **Question-shaped H2s.** Each `<h2>` is a question people actually ask, or a plain-noun subtopic. Each section's **first sentence answers its heading**. Never bury the answer at the end of the section.
- [ ] **Self-contained sections.** Assume any single section may be extracted alone. Don't rely on "as mentioned above"; repeat the key noun instead of "it."
- [ ] **Facts, numbers, and specifics.** LLMs prefer citing pages with concrete data ("lab diamonds typically cost 60-80% less", "Mohs hardness 10") over vague prose. Every claim you'd want quoted should have a number, a named authority (GIA, IGI, Gem-A), or a first-hand observation attached.
- [ ] **First-hand experience (E-E-A-T).** Include at least one thing only a working jeweler would know: something from the bench, a real client scenario (anonymized), what you actually see under a loupe. This is the moat against AI-generated competitor content.
- [ ] **Honesty is the brand and the ranking strategy.** State downsides plainly (resale value, treatments, trade-offs), exactly like the site's existing lab-diamond page does. Hedged sales copy doesn't get cited; blunt expert answers do.
- [ ] **Plain language.** Short sentences, short paragraphs (2-4 sentences), one idea per paragraph. Define trade terms on first use.
- [ ] **Use structure LLMs parse well:** bulleted/numbered lists for steps and criteria, a comparison `<table>` for any "X vs Y" topic, `<strong>` on the key claim of a section. **Every `<table>` goes inside `<div class="table-wrap">`**; tables have a 560px minimum width and the wrapper is what lets them scroll sideways on a phone instead of breaking the page.
- [ ] **Length:** as long as the question deserves, no longer. 800-1,500 words is the usual sweet spot; a news item can be 400. Never pad.
- [ ] **No AI-content tells:** no "In today's fast-paced world," no "It's important to note," no conclusion that restates everything. Read it aloud once.
- [ ] **No em dashes or en dashes, anywhere.** Not the long dash, not the short one, not in body copy, the takeaway box, the JSON-LD, the meta description, or the llms.txt line. They are the single most recognizable AI-writing tell. Rewrite the sentence with a period, comma, or colon, and write ranges with "to" ("$100 to $200", "2 to 3 sentences"). Plain hyphens in compound words ("lab-grown", "30-second") are fine. The check script fails on any dash and prints the line numbers.

### Linking
- [ ] **≥ 2 internal links** in body copy to Ring Mint pages, with descriptive anchor text ("lab created diamond engagement rings", never "click here"). The closing CTA link does not count.
- [ ] **≥ 1 external link** to a genuine authority (GIA, IGI, Gem-A, Reuters/JCK for news), with `rel="noopener"`. Citing sources makes the page itself more citable.
- [ ] Link related Journal posts to each other once they exist (add a link in the older post too; every post should have at least one internal link *pointing at it*).
- [ ] End with the soft CTA takeaway box (already in the template): one CTA, not three.

### Images
- [ ] Every image: descriptive `alt`, real `width`/`height` (prevents layout shift), `loading="lazy"` on everything **except** the hero.
- [ ] Captions where they add information (credit, what stone/setting is shown).
- [ ] **How each image is displayed, so you size the file for it, not larger:**
  - Hero on desktop: an 880px band at 2:1 (16:9 on tablets). The 1600×900 file is the right size; do not upload a 4000px original.
  - Hero on phones: the 1080×1350 `-hero-mobile.jpg`, full width at 4:5.
  - In-body figures: the 760px reading column. Export landscape figures at 1200px wide and portrait ones at 800px wide, under 200 KB each. Add `class="portrait"` to any portrait image (screenshots, phone photos) so it is capped at 440px wide and centred instead of filling the screen.
  - Listing card and featured card: 800×500 and the 1600×900 hero respectively; both are cropped by CSS to their boxes.
- [ ] Weight check before publishing: `ls -la assets/blog/YOUR-SLUG-*` and nothing over 200 KB. A JPEG at quality 75 to 80 is invisible from quality 95 at these sizes and a third of the weight.

## 5. Wire the post into the site

- [ ] **Listing card:** add a `.blog-card` at the **top** of the correct category grid in [blog/index.html](blog/index.html) (the commented example shows the exact markup). Remove the `.blog-empty` placeholder if it's the category's first post. Excerpt ≤ 160 chars.
- [ ] **Featured slot (optional):** the `#featured` section at the top of [blog/index.html](blog/index.html) holds exactly one `.blog-card.blog-featured`. To feature a post, replace that card's href, image (use the 1600×900 `-hero.jpg`), title, and excerpt. The post keeps its normal card in its category grid too.
- [ ] **Sitemap:** add to [sitemap.xml](sitemap.xml):
  ```xml
  <url>
    <loc>https://ringmint.com/blog/YOUR-SLUG/</loc>
    <lastmod>2026-09-02</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.6</priority>
  </url>
  ```
  Also bump `<lastmod>` on the `/blog/` entry.
- [ ] **llms.txt:** add a one-line entry under the Journal line in [llms.txt](llms.txt): `- [Post title](https://ringmint.com/blog/YOUR-SLUG/): one-sentence summary with the key facts.` AI crawlers read this file, and the summary line itself gets used in answers, so put the actual answer in it, not a teaser.
- [ ] **Feed:** once the post is final (the feed embeds the full body), rebuild `/feed.xml`:
  ```bash
  python3 tools/build-feed.py
  ```
  It reads every published post, skips anything still `noindex`, and sorts newest first. Bing, Feedly, Flipboard, and several AI crawlers watch this file, so a post that is not in it is invisible to them until they happen to recrawl.
- [ ] **Internal link from an existing page:** add at least one contextual link to the new post from a relevant pillar page or older post. A post only the blog index links to is an orphan; the check script warns about it.

## 6. Pre-publish technical checklist

- [ ] **Run the check script.** It covers everything mechanical in sections 3, 5, and 6 and exits non-zero on a miss. Fix every `FAIL`; read every `WARN`:
  ```bash
  python3 tools/blog-check.py YOUR-SLUG
  ```
  What it checks: leftover template tokens, `noindex` gone, no dashes, canonical and `og:url` match the folder, title and description lengths and site-wide uniqueness, every OG/Twitter/article meta present with the right image, `article:tag` count, hero preloads, JSON-LD parses with matching dates and IDs, FAQ questions visible on the page, one `<h1>`, byline and `<time>`, category anchor, `<picture>` wiring, tables wrapped, in-body images with alt/size/lazy, link counts, word count and read-time drift, all six images present at the right pixel size and under 200 KB, and the post present in `sitemap.xml`, `llms.txt`, `blog/index.html` (in the right category, placeholder removed), and `feed.xml`, plus at least one inbound link.
- [ ] Open the page locally; check console for errors, click every link.
- [ ] Mobile check: narrow the window to ~375px: no horizontal scroll, and the hero is the 4:5 `-hero-mobile.jpg` (right-click, open image in new tab, check the filename). If it is the 16:9 file, the `<picture>` source is wrong.
- [ ] Rich results test passes: https://search.google.com/test/rich-results.
- [ ] Social preview checked at https://www.opengraph.xyz (or the LinkedIn Post Inspector). If you have shared the URL before and the card is stale, use the Facebook Sharing Debugger's "Scrape Again" and the LinkedIn Post Inspector to refresh their caches.
- [ ] Run https://pagespeed.web.dev on the URL after deploy: LCP < 2.5s, CLS < 0.1. The hero image is the LCP element; if it fails, compress harder.

## 7. After publishing

- [ ] **Push, then ping IndexNow** (Bing, Yandex, Naver, Seznam in one call; Bing feeds ChatGPT search and Copilot, so do not skip this). Pass the new post, the blog index, and the feed, all of which changed:
  ```bash
  ./scripts/indexnow.sh https://ringmint.com/blog/YOUR-SLUG/ https://ringmint.com/blog/ https://ringmint.com/feed.xml
  ```
  With no arguments it submits every URL in the sitemap, which is the right call after a site-wide change. IndexNow fetches the pages, so run it only after the deploy is live.
- [ ] **Google Search Console:** URL Inspection → Request Indexing for the new URL. Google ignores IndexNow.
- [ ] **Bing Webmaster Tools:** confirm the URL shows up under IndexNow submissions; submit it by hand only if it does not.
- [ ] **Instagram Stories:** post `YOUR-SLUG-story.jpg` the same day, with a link sticker to the post URL placed over the "READ THE POST" pill.
- [ ] **Pinterest:** pin `YOUR-SLUG-pin.jpg` to the relevant board with the post URL as the destination, the title as the pin title, and the meta description as the pin description (Pinterest indexes both; jewelry content has a long tail there). Rich Pins pull the rest from the `article:` meta tags.
- [ ] **LinkedIn:** write the post as a hook plus the first idea, never the whole article, with the URL as the last line. Social links are discovery signals.
- [ ] Note the publish in GA4 annotations if you use them (per the analytics setup, leads come via AI assistants and Direct, so watch `Direct` and referral from chat domains, not just organic).

## 8. Maintenance (quarterly)

- [ ] Re-read old posts; update anything stale (prices, news). When you materially update: change `dateModified` in the JSON-LD, `article:modified_time`, and `lastmod` in the sitemap, then rebuild the feed and ping IndexNow for that URL. Don't fake-update dates without real changes.
- [ ] Check Search Console → Pages for posts Google dropped; check queries each post gets impressions for and add missing phrasings as H2s (and as `article:tag` / `keywords` entries).
- [ ] Fix broken external links.
- [ ] Merge posts that ended up competing for the same query (301 the weaker one via a meta refresh + canonical, since this is a static host). Remove the merged post from the sitemap, llms.txt, and the blog index, and rebuild the feed.
- [ ] Re-run `python3 tools/blog-check.py` on every post after any template or site-wide change; the checks are cheap and drift is silent.

---

## Quick-reference: the 12 things that matter most

1. One post = one question, phrased how people ask it, in the right one of three categories.
2. Answer in the first 100 words *and* in the takeaway box.
3. Question-shaped H2s, answer in each section's first sentence.
4. Concrete numbers and named sources in every quotable claim.
5. One thing only a real jeweler would know.
6. Unique 50-60 char title, 140-160 char description, full OG set, 3 to 6 `article:tag` lines.
7. Valid `BlogPosting` JSON-LD (+ `FAQPage` when there's real Q&A).
8. All six images (hero, hero-mobile, og, card, story, pin) from `tools/blog-images.py`, same house style, honest alt text.
9. `noindex` removed. Canonical correct.
10. Card added to /blog/, entry added to sitemap.xml **and** llms.txt, `tools/build-feed.py` run.
11. At least one link *to* the post from an existing page.
12. `tools/blog-check.py` passes, then IndexNow, Google Search Console, Stories, and a Pinterest pin.
