#!/usr/bin/env python3
"""
Pre-publish lint for a Ring Mint Journal post. Runs every mechanical check in
BLOG_PUBLISHING_GUIDE.md sections 3, 5, and 6 against one slug:

    python3 tools/blog-check.py YOUR-SLUG

Prints FAIL / WARN / ok lines and exits 1 on any FAIL. What it cannot do:
PageSpeed, the rich-results test, the social preview, and reading the prose.
Needs Pillow for image dimensions (pip3 install --user Pillow); without it the
pixel-size checks are skipped with a warning.
"""
import html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://ringmint.com"
CATEGORIES = {
    "Jewelry News": "jewelry-news",
    "Diamonds & Gemstones": "diamonds-and-gemstones",
    "Buying Guides": "buying-guides",
}
IMAGES = {  # suffix: (width, height)
    "hero": (1600, 900), "hero-mobile": (1080, 1350), "og": (1200, 630),
    "card": (800, 500), "story": (1080, 1920), "pin": (1000, 1500),
}
MAX_KB = 200
WORDS_PER_MIN = 230
TEMPLATE_TOKENS = [
    "POST-SLUG", "POST TITLE", "YYYY-MM-DD", "META DESCRIPTION", "CATEGORY NAME",
    "CATEGORY-ANCHOR", "DESCRIBE WHAT", "DESCRIBE THE", "DESCRIBE IT", "OPTIONAL CAPTION",
    "OPTIONAL ASIDE", "ANSWER THE POST", "OPENING PARAGRAPH", "SUBHEAD", "Body copy.",
    "N min read", "Month D, YYYY", "List item one", "PRIMARY KEYWORD", "SECONDARY KEYWORD",
    "THIRD KEYWORD", "SAME OR SLIGHTLY WARMER", "MAX 110 CHARS", "SHORT FORM",
]
CAPS_ALLOW = {"HPHT", "GIA", "IGI", "GCAL", "AGS", "HRD", "JSON", "HTML", "TIKTOK", "FAQ",
              "DOCTYPE", "UTF", "LLM", "LLMS", "FTC", "JCK", "CVD", "AAA", "SI", "VS", "VVS",
              "CDATA", "CTA", "UV", "LED", "GTAG", "USA", "UK", "NYC", "READ", "RING", "MINT",
              "JOURNAL", "THE", "POST", "MOHS", "EBAY", "CAD"}

fails, warns = [], []
def fail(msg): fails.append(msg); print(f"FAIL  {msg}")
def warn(msg): warns.append(msg); print(f"WARN  {msg}")
def ok(msg): print(f"ok    {msg}")

def meta(src, attr, name, all_=False):
    pat = rf'<meta\s+{attr}="{re.escape(name)}"\s+content="([^"]*)"'
    if all_:
        return [html.unescape(x) for x in re.findall(pat, src)]
    m = re.search(pat, src)
    return html.unescape(m.group(1)) if m else None

def extract_div(src, cls):
    start = re.search(rf'<div\s+class="{re.escape(cls)}"[^>]*>', src)
    if not start:
        return ""
    depth = 1
    for m in re.finditer(r'<div\b[^>]*>|</div>', src[start.end():]):
        depth += 1 if m.group(0).startswith('<div') else -1
        if depth == 0:
            return src[start.end():start.end() + m.start()]
    return ""

def strip_tags(s):
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    return html.unescape(re.sub(r'<[^>]+>', ' ', s))

def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    slug = sys.argv[1].strip("/").split("/")[-1]
    path = ROOT / "blog" / slug / "index.html"
    if not path.exists():
        sys.exit(f"no such post: {path}")
    src = path.read_text(encoding="utf-8")
    lines = src.split("\n")
    url = f"{SITE}/blog/{slug}/"
    print(f"Checking {path.relative_to(ROOT)}\n")

    # --- slug -------------------------------------------------------------
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', slug):
        fail(f"slug '{slug}' is not lowercase-hyphenated")
    elif re.search(r'\d{4}', slug):
        warn(f"slug '{slug}' contains a 4-digit number; the guide says no dates in slugs")
    n_words = len(slug.split("-"))
    if not 3 <= n_words <= 6:
        warn(f"slug has {n_words} words; the guide says 3 to 6")

    # --- leftover template tokens ----------------------------------------
    hits = [t for t in TEMPLATE_TOKENS if t in src]
    if hits:
        fail(f"template tokens still present: {', '.join(hits)}")
    else:
        ok("no template tokens left")
    body_text = strip_tags(re.sub(r'<script.*?</script>', '', src, flags=re.S))
    caps = sorted({w for w in re.findall(r'\b[A-Z]{4,}\b', body_text) if w not in CAPS_ALLOW})
    if caps:
        warn(f"ALL-CAPS words to eyeball (real acronyms are fine): {', '.join(caps)}")

    # --- robots / canonical ----------------------------------------------
    robots = meta(src, "name", "robots") or ""
    if "noindex" in robots:
        fail("robots meta still says noindex; delete it and uncomment the index,follow line")
    elif "index" not in robots:
        fail("no index,follow robots meta")
    else:
        ok(f"robots: {robots}")
    canon = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', src)
    if not canon or canon.group(1) != url:
        fail(f"canonical is {canon.group(1) if canon else 'missing'}, expected {url}")
    else:
        ok("canonical matches slug")
    if meta(src, "property", "og:url") != url:
        fail("og:url does not match the canonical URL")
    if 'application/rss+xml' not in src:
        fail("missing <link rel=\"alternate\" type=\"application/rss+xml\"> (copy from the template)")

    # --- dashes -----------------------------------------------------------
    dash_lines = [i + 1 for i, l in enumerate(lines) if "—" in l or "–" in l]
    if dash_lines:
        fail(f"em/en dashes on lines {dash_lines}; rewrite with a period, comma, colon, or 'to'")
    else:
        ok("no em or en dashes")

    # --- title / description ---------------------------------------------
    t = re.search(r'<title>(.*?)</title>', src, re.S)
    title = html.unescape(t.group(1).strip()) if t else ""
    if not title:
        fail("no <title>")
    else:
        if not title.endswith("| Ring Mint"):
            fail("title does not end with '| Ring Mint'")
        if not 50 <= len(title) <= 60:
            (fail if len(title) > 70 or len(title) < 30 else warn)(f"title is {len(title)} chars (target 50 to 60): {title}")
        else:
            ok(f"title {len(title)} chars")
    desc = meta(src, "name", "description") or ""
    if not desc:
        fail("no meta description")
    elif not 140 <= len(desc) <= 160:
        (fail if len(desc) > 200 or len(desc) < 80 else warn)(f"description is {len(desc)} chars (target 140 to 160)")
    else:
        ok(f"description {len(desc)} chars")
    # uniqueness across the site
    for other in ROOT.rglob("*.html"):
        if other == path or ".git" in other.parts or other.name.startswith("_") or other.name.startswith("pinterest-"):
            continue
        o = other.read_text(encoding="utf-8", errors="ignore")
        ot = re.search(r'<title>(.*?)</title>', o, re.S)
        if ot and html.unescape(ot.group(1).strip()) == title:
            fail(f"title duplicates {other.relative_to(ROOT)}")
        if desc and (meta(o, "name", "description") == desc):
            fail(f"description duplicates {other.relative_to(ROOT)}")

    # --- OG / Twitter / article meta -------------------------------------
    for prop in ["og:type", "og:site_name", "og:title", "og:description", "og:url", "og:image",
                 "og:image:secure_url", "og:image:type", "og:image:width", "og:image:height",
                 "og:image:alt", "article:published_time", "article:modified_time",
                 "article:author", "article:section"]:
        if meta(src, "property", prop) is None:
            fail(f"missing <meta property=\"{prop}\">")
    for name in ["twitter:card", "twitter:site", "twitter:creator", "twitter:title",
                 "twitter:description", "twitter:image"]:
        if meta(src, "name", name) is None:
            fail(f"missing <meta name=\"{name}\">")
    og_img = meta(src, "property", "og:image") or ""
    if og_img != f"{SITE}/assets/blog/{slug}-og.jpg":
        fail(f"og:image should be {SITE}/assets/blog/{slug}-og.jpg, got {og_img or 'nothing'}")
    if meta(src, "property", "og:image:secure_url") not in (None, og_img):
        fail("og:image:secure_url differs from og:image")
    if meta(src, "name", "twitter:image") != og_img:
        fail("twitter:image differs from og:image")
    tags = meta(src, "property", "article:tag", all_=True)
    if not tags:
        fail("no article:tag entries (mirror the JSON-LD keywords)")
    elif len(tags) < 3:
        warn(f"only {len(tags)} article:tag entries; 3 to 6 is typical")
    else:
        ok(f"{len(tags)} article:tag entries")
    pub, mod = meta(src, "property", "article:published_time"), meta(src, "property", "article:modified_time")
    for label, d in (("published", pub), ("modified", mod)):
        if d and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', d):
            fail(f"article:{label}_time '{d}' is not YYYY-MM-DD")
    if pub and mod and mod < pub:
        fail("article:modified_time is earlier than article:published_time")
    section = meta(src, "property", "article:section") or ""
    if section not in CATEGORIES:
        fail(f"article:section '{section}' is not one of: {', '.join(CATEGORIES)}")

    # --- preloads ---------------------------------------------------------
    for fname, media in ((f"{slug}-hero-mobile.jpg", "(max-width: 620px)"), (f"{slug}-hero.jpg", "(min-width: 621px)")):
        if not re.search(rf'<link\s+rel="preload"\s+as="image"\s+href="/assets/blog/{re.escape(fname)}"\s+media="{re.escape(media)}"', src):
            fail(f"hero preload for {fname} with media=\"{media}\" missing or wrong")

    # --- JSON-LD ----------------------------------------------------------
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', src, re.S)
    if not blocks:
        fail("no JSON-LD")
    posting = None
    for i, blk in enumerate(blocks):
        try:
            data = json.loads(blk)
        except json.JSONDecodeError as e:
            fail(f"JSON-LD block {i + 1} does not parse: {e}")
            continue
        nodes = data.get("@graph", [data]) if isinstance(data, dict) else data
        for node in nodes:
            if node.get("@type") == "BlogPosting":
                posting = node
            if node.get("@type") == "FAQPage":
                qs = [q.get("name", "") for q in node.get("mainEntity", [])]
                missing = [q for q in qs if q and html.escape(q, quote=False) not in src and q not in body_text]
                if missing:
                    fail(f"FAQPage questions not visible on the page: {missing[:3]}")
                else:
                    ok(f"FAQPage with {len(qs)} questions, all visible")
            if node.get("@type") == "BreadcrumbList":
                last = node.get("itemListElement", [])[-1] if node.get("itemListElement") else {}
                if last.get("item") != url:
                    fail(f"breadcrumb item 3 is {last.get('item')}, expected {url}")
            if node.get("@type") == "Person" and "sameAs" not in node:
                warn("Person node has no sameAs (copy the block from the template)")
    if posting is None:
        fail("no BlogPosting node")
    else:
        for key in ["headline", "description", "image", "datePublished", "dateModified",
                    "articleSection", "keywords", "wordCount", "author", "publisher", "mainEntityOfPage"]:
            if key not in posting:
                fail(f"BlogPosting missing {key}")
        if len(posting.get("headline", "")) > 110:
            fail("BlogPosting headline over 110 chars")
        if posting.get("datePublished") != pub or posting.get("dateModified") != mod:
            fail("BlogPosting dates differ from article:published_time / article:modified_time")
        if posting.get("articleSection") != section:
            fail("BlogPosting articleSection differs from article:section")
        if posting.get("@id") != f"{url}#article":
            fail(f"BlogPosting @id should be {url}#article")
        img = posting.get("image", {})
        if isinstance(img, dict) and img.get("url") != f"{SITE}/assets/blog/{slug}-hero.jpg":
            fail("BlogPosting image.url should be the -hero.jpg")
        ok("BlogPosting node present")

    # --- body -------------------------------------------------------------
    h1s = re.findall(r'<h1[\s>]', src)
    (ok if len(h1s) == 1 else fail)(f"{len(h1s)} <h1> element(s)")
    if 'rel="author"' not in src:
        fail("byline link needs rel=\"author\"")
    tm = re.search(r'<time\s+datetime="([^"]+)"', src)
    if not tm:
        fail("no <time datetime> in the byline")
    elif pub and tm.group(1) != pub:
        fail(f"<time datetime=\"{tm.group(1)}\"> differs from article:published_time {pub}")
    if section and f'href="/blog/#{CATEGORIES[section]}"' not in src:
        fail(f"category eyebrow should link to /blog/#{CATEGORIES.get(section)}")
    pic = re.search(r'<picture>(.*?)</picture>', src, re.S)
    if not pic:
        fail("hero <picture> element missing")
    else:
        p = pic.group(1)
        if f"/assets/blog/{slug}-hero-mobile.jpg" not in p or 'media="(max-width: 620px)"' not in p:
            fail("<picture> <source> must point at -hero-mobile.jpg for (max-width: 620px)")
        if f'src="/assets/blog/{slug}-hero.jpg"' not in p:
            fail("<picture> <img> must point at -hero.jpg")
        if 'fetchpriority="high"' not in p:
            fail("hero <img> needs fetchpriority=\"high\"")
        if not re.search(r'<img[^>]*\swidth="1600"[^>]*\sheight="900"', p):
            fail("hero <img> needs width=\"1600\" height=\"900\"")
    if not extract_div(src, "takeaway"):
        fail("no .takeaway 'short answer' box")
    prose = extract_div(src, "prose")
    if not prose:
        fail("no <div class=\"prose\">")
    else:
        # tables
        n_tables = len(re.findall(r'<table\b', prose))
        n_wraps = len(re.findall(r'<div class="table-wrap">\s*<table\b', prose))
        if n_tables != n_wraps:
            fail(f"{n_tables} table(s) but {n_wraps} wrapped in <div class=\"table-wrap\">")
        elif n_tables:
            ok(f"{n_tables} table(s), all wrapped")
        # images
        for m in re.finditer(r'<img\b[^>]*>', prose):
            tag = m.group(0)
            if 'alt="' not in tag or 'alt=""' in tag:
                fail(f"image without alt: {tag[:80]}")
            if 'width="' not in tag or 'height="' not in tag:
                fail(f"image without width/height: {tag[:80]}")
            if 'loading="lazy"' not in tag:
                fail(f"in-body image without loading=\"lazy\": {tag[:80]}")
            srcm = re.search(r'src="([^"]+)"', tag)
            if srcm and srcm.group(1).startswith("/") and not (ROOT / srcm.group(1).lstrip("/")).exists():
                fail(f"image file missing: {srcm.group(1)}")
        # links
        hrefs = re.findall(r'<a\s[^>]*href="([^"]+)"', prose)
        internal = [h for h in hrefs if (h.startswith("/") or h.startswith(SITE)) and "#inquire" not in h and f"/blog/{slug}/" not in h]
        external = [h for h in hrefs if h.startswith("http") and SITE not in h]
        (ok if len(internal) >= 2 else fail)(f"{len(internal)} internal link(s) in body (need 2+)")
        (ok if len(external) >= 1 else fail)(f"{len(external)} external authority link(s) in body (need 1+)")
        if re.search(r'>\s*(click|read) here\s*<', prose, re.I):
            fail("'click here' anchor text found")
        for h in external:
            if not re.search(rf'href="{re.escape(h)}"[^>]*rel="[^"]*noopener', prose) and not re.search(rf'rel="[^"]*noopener[^"]*"[^>]*href="{re.escape(h)}"', prose):
                warn(f"external link without rel=\"noopener\": {h}")
        # word count and read time
        words = len(strip_tags(prose).split())
        if posting and isinstance(posting.get("wordCount"), int):
            wc = posting["wordCount"]
            drift = abs(words - wc) / max(words, 1)
            (warn if drift > 0.2 else ok)(f"body has {words} words; JSON-LD wordCount {wc} ({drift:.0%} drift)")
        rt = re.search(r'(\d+)\s*min read', src)
        if rt:
            n = int(rt.group(1)); est = max(1, round(words / WORDS_PER_MIN))
            (warn if abs(n - est) > max(1, 0.2 * n) else ok)(f"read time says {n} min; {words} words is about {est} min")
        else:
            fail("no 'N min read' in the byline")
        if words < 350:
            warn(f"only {words} words; the guide's floor for a news item is about 400")

    # --- images on disk ---------------------------------------------------
    try:
        from PIL import Image
    except ImportError:
        Image = None
        warn("Pillow not installed; skipping pixel-size checks")
    for suffix, (w, h) in IMAGES.items():
        f = ROOT / "assets" / "blog" / f"{slug}-{suffix}.jpg"
        if not f.exists():
            fail(f"missing image {f.relative_to(ROOT)}")
            continue
        kb = f.stat().st_size // 1024
        if kb > MAX_KB:
            warn(f"{f.name} is {kb} KB (target under {MAX_KB} KB)")
        if Image:
            with Image.open(f) as im:
                if im.size != (w, h):
                    fail(f"{f.name} is {im.size[0]}x{im.size[1]}, expected {w}x{h}")
    ok("image set checked")

    # --- wiring -----------------------------------------------------------
    sitemap = (ROOT / "sitemap.xml").read_text()
    if f"<loc>{url}</loc>" not in sitemap:
        fail("not in sitemap.xml")
    else:
        m = re.search(rf'<loc>{re.escape(url)}</loc>\s*<lastmod>([^<]+)</lastmod>', sitemap)
        if m and mod and m.group(1) != mod:
            warn(f"sitemap lastmod {m.group(1)} differs from article:modified_time {mod}")
        else:
            ok("in sitemap.xml")
    llms = (ROOT / "llms.txt").read_text()
    (ok if url in llms else fail)("in llms.txt" if url in llms else "not in llms.txt")
    index = (ROOT / "blog" / "index.html").read_text()
    if f'href="/blog/{slug}/"' not in index:
        fail("no card on /blog/ (blog/index.html)")
    else:
        ok("card on /blog/")
        if section and f'id="{CATEGORIES[section]}"' in index:
            sec_html = index.split(f'id="{CATEGORIES[section]}"', 1)[1].split("</section>", 1)[0]
            if f'href="/blog/{slug}/"' not in sec_html:
                fail(f"card is not inside the #{CATEGORIES[section]} section")
            if 'class="blog-empty"' in sec_html:
                fail(f"the .blog-empty placeholder is still in #{CATEGORIES[section]}")
    feed = ROOT / "feed.xml"
    if not feed.exists() or url not in feed.read_text():
        fail("not in feed.xml; run python3 tools/build-feed.py")
    else:
        ok("in feed.xml")
    inbound = []
    for other in ROOT.rglob("*.html"):
        if other in (path, ROOT / "blog" / "index.html") or ".git" in other.parts or other.name.startswith("_"):
            continue
        if f"/blog/{slug}/" in other.read_text(encoding="utf-8", errors="ignore"):
            inbound.append(str(other.relative_to(ROOT)))
    (ok if inbound else warn)(f"inbound links from: {', '.join(inbound)}" if inbound else "no page other than /blog/ links to this post (orphan); add one contextual link from a pillar page or older post")

    print(f"\n{len(fails)} FAIL, {len(warns)} WARN")
    if fails:
        print("Fix every FAIL before publishing.")
        sys.exit(1)
    print("Mechanical checks pass. Still to do by hand: PageSpeed, rich-results test, social preview, and read it aloud once.")


if __name__ == "__main__":
    main()
