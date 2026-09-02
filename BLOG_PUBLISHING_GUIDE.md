# Ring Mint Journal Publishing Guide

How to publish a blog post that is perfectly optimized for Google, Bing, and AI search
(ChatGPT, Claude, Perplexity, Google AI Overviews). Follow this top to bottom for **every** post.

The blog lives at `/blog/`. There is **one template**: hero image + text
([blog/_post-template.html](blog/_post-template.html)). Categories:

| Category | Anchor on /blog/ | `articleSection` value |
|---|---|---|
| Jewelry News | `#jewelry-news` | `Jewelry News` |
| Diamonds & Gemstones | `#diamonds-and-gemstones` | `Diamonds & Gemstones` |

---

## 1. Before you write

- [ ] **Pick one primary keyword/question** the post answers (e.g. "do lab diamonds test as real diamonds"). One post = one search intent. If you have two intents, write two posts.
- [ ] **Check it isn't cannibalizing an existing page.** The pillar pages (custom rings, lab diamonds, concierge, FAQ) already rank for their topics, so a post should support them, not compete. If it overlaps, link to the pillar, don't restate it.
- [ ] **Phrase the title the way people actually ask.** AI assistants surface pages that literally match the question. "How much does a custom engagement ring cost?" beats "Custom ring pricing explained."
- [ ] **List 3-5 secondary keywords/phrasings** to work in naturally (synonyms, "vs" variants, misspellings people use like "moissanite vs diamond").
- [ ] **Decide the "short answer."** If you can't write a 2-3 sentence answer to the post's central question, the post isn't ready.

## 2. Slug and files

- [ ] Slug: lowercase, hyphens, 3-6 words, contains the primary keyword, **no dates, no stop words** (`/blog/lab-diamond-resale-value/`, not `/blog/2026/09/what-you-should-know-about-the-resale-value-of-lab-diamonds/`). Slugs are permanent. Never change one after publishing.
- [ ] `cp blog/_post-template.html blog/YOUR-SLUG/index.html`
- [ ] **Every post ships five images**, all in `/assets/blog/`, all in the same house style (see below). None are optional.
  - `YOUR-SLUG-hero.jpg`: 1600×900, the post hero on desktop and tablet.
  - `YOUR-SLUG-hero-mobile.jpg`: 1080×1350 (4:5), the post hero on phones. The template serves it through `<picture>` below 620px. A 16:9 image cropped to a phone screen is either a tiny strip or a sliver of the middle; this file is a separate composition, not a resize.
  - `YOUR-SLUG-og.jpg`: 1200×630, the social/OG image, title overlaid.
  - `YOUR-SLUG-card.jpg`: 800×500, the card image for the /blog/ listing.
  - `YOUR-SLUG-story.jpg`: 1080×1920, the Instagram Story for the post. Not referenced by the site; it exists so the post is announced on Stories the day it publishes, in the same look as everything else. Text stays out of the top and bottom 250px (Instagram's own UI covers those), and the "read the post" pill sits at roughly 89% height so the link sticker can go on top of it.
  - Compress everything (target < 200 KB each; the generator does this for you, otherwise Squoosh.app, quality ~75 JPEG).
  - Filenames are descriptive and keyworded: `oval-lab-diamond-ring-hero.jpg`, never `IMG_4021.jpg`.
- [ ] **Generate them with the script, do not freehand them.** [tools/blog-images.py](tools/blog-images.py) produces all five from a slug and a headline, in the house style, at the right sizes and weights:
  ```bash
  python3 tools/blog-images.py generate --slug YOUR-SLUG --title "Line one|line two|line three" --answer "One short answer line." --sub "Supporting line,|second supporting line."
  ```
  If the post has a real photograph for its hero (a stone on the bench, a client's ring), keep the photo as `YOUR-SLUG-hero.jpg`, make the OG and card from it, and run only the two commands the script cannot replace with line art:
  ```bash
  python3 tools/blog-images.py crop-mobile --slug YOUR-SLUG
  ```
  ```bash
  python3 tools/blog-images.py story --slug YOUR-SLUG --title "..." --answer "..." --sub "..."
  ```
- [ ] **House style for all five images.** Charcoal `#171717` ground with a warm radial glow, gold `rgb(212,183,134)` line-art diamonds (round brilliant seen from above, and the classic crown-and-pavilion profile), small four-point sparkles, a hairline gold frame inset 40px, Didot for headlines in cream `rgb(244,239,230)`, Didot italic in gold for the one-line answer, Georgia letter-spaced small caps for the "THE RING MINT JOURNAL" eyebrow. A photographic hero is fine, but the OG, card, and Story built from it still carry the same type, eyebrow, hairline, and pill. Do not introduce new colours, fonts, or icon styles for one post. If the style needs to change, change it in the script so every future post changes with it.

## 3. Fill in the template

Replace **every ALL-CAPS token**. Then verify:

### Head / metadata
- [ ] `<title>`: 50-60 characters, primary keyword at the front, ends `| Ring Mint`. Unique across the site.
- [ ] Meta description: 140-160 characters, contains the primary keyword, states the answer or promise. Unique across the site.
- [ ] **Delete the `noindex` line and uncomment the `index, follow` robots line.** (The template ships noindexed so an unfinished copy can't leak into Google.)
- [ ] Canonical URL matches the final URL exactly, with trailing slash: `https://ringmint.com/blog/YOUR-SLUG/`.
- [ ] All OG/Twitter fields filled; OG image URL is absolute (`https://ringmint.com/...`).
- [ ] `article:published_time` and `article:modified_time` set (ISO dates, `2026-09-02`).

### Structured data (JSON-LD)
- [ ] `BlogPosting` block: headline, description, image, dates, `articleSection`, `keywords`, `wordCount` (rough count is fine) all filled.
- [ ] Breadcrumb item 3 name/URL updated.
- [ ] If the post contains a real Q&A section (3+ questions with self-contained answers), add a second `<script type="application/ld+json">` with `FAQPage` markup; copy the pattern from [faq/index.html](faq/index.html). Only mark up questions that visibly appear on the page.
- [ ] If the post is a step-by-step process, consider `HowTo` markup instead of FAQ.
- [ ] Validate at https://validator.schema.org and https://search.google.com/test/rich-results. **Zero errors** before publishing.

### Body
- [ ] Exactly **one `<h1>`**, matching (or close to) the title tag.
- [ ] Byline present and linked to `/press/` (`rel="author"`), date in a `<time datetime="...">` element, read time filled in.
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
- [ ] **No em dashes or en dashes, anywhere.** Not the long dash, not the short one, not in body copy, the takeaway box, the JSON-LD, the meta description, or the llms.txt line. They are the single most recognizable AI-writing tell. Rewrite the sentence with a period, comma, or colon, and write ranges with "to" ("$100 to $200", "2 to 3 sentences"). Plain hyphens in compound words ("lab-grown", "30-second") are fine. Before publishing, this must return nothing:
  ```bash
  grep -n $'\xe2\x80\x94\\|\xe2\x80\x93' blog/YOUR-SLUG/index.html
  ```

### Linking
- [ ] **≥ 2 internal links** in body copy to Ring Mint pages, with descriptive anchor text ("lab created diamond engagement rings", never "click here").
- [ ] **≥ 1 external link** to a genuine authority (GIA, IGI, Gem-A, Reuters/JCK for news). Citing sources makes the page itself more citable.
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
- [ ] **Internal link from an existing page:** add at least one contextual link to the new post from a relevant pillar page or older post. A post only the blog index links to is an orphan.

## 6. Pre-publish technical checklist

- [ ] Open the page locally; check console for errors, click every link.
- [ ] View source: no remaining ALL-CAPS tokens (`grep -n '[A-Z]\{4,\}' blog/YOUR-SLUG/index.html` and eyeball the hits).
- [ ] `noindex` removed (this is the #1 way to silently publish an invisible post).
- [ ] Mobile check: narrow the window to ~375px: no horizontal scroll, and the hero is the 4:5 `-hero-mobile.jpg` (right-click, open image in new tab, check the filename). If it is the 16:9 file, the `<picture>` source is wrong.
- [ ] Run https://pagespeed.web.dev on the URL after deploy: LCP < 2.5s, CLS < 0.1. The hero image is the LCP element; if it fails, compress harder.
- [ ] Rich results test passes; social preview checked at https://www.opengraph.xyz (or the LinkedIn Post Inspector).

## 7. After publishing

- [ ] **Google Search Console:** URL Inspection → Request Indexing for the new URL.
- [ ] **Bing Webmaster Tools:** submit the URL (Bing feeds ChatGPT search and Copilot, so do not skip this).
- [ ] Share to the channels (Instagram, LinkedIn, Pinterest); social links are discovery signals and Pinterest jewelry content has long tail.
- [ ] Post `YOUR-SLUG-story.jpg` to Instagram Stories the same day, with a link sticker to the post URL placed over the "READ THE POST" pill. Write the LinkedIn post as a hook plus the first idea, never the whole article, with the URL as the last line.
- [ ] Note the publish in GA4 annotations if you use them (per the analytics setup, leads come via AI assistants and Direct, so watch `Direct` and referral from chat domains, not just organic).

## 8. Maintenance (quarterly)

- [ ] Re-read old posts; update anything stale (prices, news). When you materially update: change `dateModified` in the JSON-LD, `article:modified_time`, and `lastmod` in the sitemap. Don't fake-update dates without real changes.
- [ ] Check Search Console → Pages for posts Google dropped; check queries each post gets impressions for and add missing phrasings as H2s.
- [ ] Fix broken external links.
- [ ] Merge posts that ended up competing for the same query (301 the weaker one via a meta refresh + canonical, since this is a static host).

---

## Quick-reference: the 12 things that matter most

1. One post = one question, phrased how people ask it.
2. Answer in the first 100 words *and* in the takeaway box.
3. Question-shaped H2s, answer in each section's first sentence.
4. Concrete numbers and named sources in every quotable claim.
5. One thing only a real jeweler would know.
6. Unique 50-60 char title, 140-160 char description.
7. Valid `BlogPosting` JSON-LD (+ `FAQPage` when there's real Q&A).
8. All five images (hero, hero-mobile, og, card, story) from `tools/blog-images.py`, same house style, honest alt text.
9. `noindex` removed. Canonical correct.
10. Card added to /blog/, entry added to sitemap.xml **and** llms.txt.
11. At least one link *to* the post from an existing page.
12. Request indexing in Google Search Console **and** Bing.
