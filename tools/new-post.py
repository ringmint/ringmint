#!/usr/bin/env python3
"""
Build a Ring Mint Journal post from a spec file and wire it into the site.

    python3 tools/new-post.py content/drafts/YOUR-SLUG.txt [--publish] [--no-images]

The spec is a header block between --- lines, the body HTML, and an optional
FAQ block. See content/drafts/_example.txt. What this does, in order:

  1. blog/SLUG/index.html from blog/_post-template.html (tokens replaced,
     wordCount and read time computed, FAQPage JSON-LD built from the FAQ block,
     capture form / sticky bar / outro wired with the slug)
  2. assets/blog/SLUG-*.jpg via tools/blog-images.py generate (skipped if the
     hero already exists, or with --no-images)
  3. a card at the top of the right category grid on /blog/ (removing the
     .blog-empty placeholder), unless the card is already there
  4. sitemap.xml entry, llms.txt line under the Journal entry, feed.xml rebuild
  5. content/calendar.csv row: status drafted (or published with --publish)

Without --publish the post is written with robots noindex, so it can sit on the
live site as a draft until Chloe's first-hand detail lands. Run again with
--publish to flip it (safe to re-run; it rewrites the post from the spec).
"""
import csv, html, json, pathlib, re, subprocess, sys, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://ringmint.com"
CATEGORIES = {
    "Jewelry News": "jewelry-news",
    "Diamonds & Gemstones": "diamonds-and-gemstones",
    "Buying Guides": "buying-guides",
    "Custom Ring Guides": "custom-ring-guides",
    "Pricing & Budgets": "pricing-and-budgets",
    "Ring Styles": "ring-styles",
}
MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]

def parse(spec_path):
    text = pathlib.Path(spec_path).read_text(encoding="utf-8")
    m = re.match(r'---\n(.*?)\n---\n(.*)', text, re.S)
    if not m: sys.exit("spec needs a --- header block")
    meta = {}
    for line in m.group(1).split("\n"):
        if not line.strip() or line.startswith("#"): continue
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    rest = m.group(2)
    body, faq = rest, []
    if "\n---faq---\n" in rest:
        body, faq_text = rest.split("\n---faq---\n", 1)
        q = None
        for line in faq_text.strip().split("\n"):
            if line.startswith("Q:"): q = line[2:].strip()
            elif line.startswith("A:") and q:
                faq.append((q, line[2:].strip())); q = None
    return meta, body.strip(), faq

def strip_tags(s):
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    return html.unescape(re.sub(r'<[^>]+>', ' ', s))

def esc(s): return html.escape(s, quote=True)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if not args: sys.exit(__doc__)
    meta, body, faq = parse(args[0])
    slug = meta["slug"]
    publish = "--publish" in flags
    cat = meta["category"]
    if cat not in CATEGORIES: sys.exit(f"category must be one of {list(CATEGORIES)}")
    anchor = CATEGORIES[cat]
    date = meta["date"]
    modified = meta.get("modified", date)
    y, mo, d = date.split("-")
    date_h = f"{MONTHS[int(mo)-1]} {int(d)}, {y}"
    tags = [t.strip() for t in meta["tags"].split(",") if t.strip()]
    url = f"{SITE}/blog/{slug}/"
    title = meta["title"].strip()
    h1 = meta.get("h1", title)
    headline = meta.get("headline", h1)[:110]
    desc = meta["description"].strip()
    og_desc = meta.get("og_description", desc)
    crumb = meta.get("crumb", h1[:40])
    short = meta["short"]
    outro_eyebrow = meta.get("outro_eyebrow", "Thinking about a custom piece?")
    cta = f'<a href="/contact/?ref={slug}" class="text-link" data-cta="article-outro">Email Chloe</a>'
    outro = meta.get("outro", "Ring Mint designs every piece from scratch, sources stones only after you describe what you want, and charges below jewelry store prices because there is no store. {cta}. Real questions welcome, no pressure.").replace("{cta}", cta)

    # FAQ html + json-ld
    faq_html = ""
    faq_ld = ""
    if faq:
        faq_html = '\n            <h2>Quick answers</h2>\n' + "".join(
            f'            <h3>{esc(q)}</h3>\n            <p>{a}</p>\n' for q, a in faq)
        faq_ld = '\n  <script type="application/ld+json">\n' + json.dumps({
            "@context": "https://schema.org", "@type": "FAQPage", "@id": f"{url}#faq",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a).strip()}} for q, a in faq]
        }, indent=2, ensure_ascii=False) + '\n  </script>'

    prose = f'''<div class="takeaway">
              <span class="eyebrow">The short answer</span>
              {short}
            </div>

{body}
{faq_html}
            <div class="takeaway">
              <span class="eyebrow">{esc(outro_eyebrow)}</span>
              <p>{outro}</p>
            </div>'''
    words = len(strip_tags(prose).split())
    read_min = max(1, round(words / 230))

    tpl = (ROOT / "blog" / "_post-template.html").read_text(encoding="utf-8")
    out = tpl
    # head tokens
    out = out.replace("<title>POST TITLE (50-60 CHARS, KEYWORD FIRST) | Ring Mint</title>", f"<title>{esc(title)} | Ring Mint</title>")
    out = out.replace('content="META DESCRIPTION: 140-160 characters, contains the primary keyword, states the answer or promise of the post, no clickbait."', f'content="{esc(desc)}"')
    if publish:
        out = out.replace('  <!-- TEMPLATE SAFETY: noindex until this is a real post. DELETE the next line and\n       uncomment the index,follow line when publishing. -->\n  <meta name="robots" content="noindex, nofollow" />\n  <!-- <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1" /> -->',
                          '  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1" />')
    else:
        out = out.replace('  <!-- TEMPLATE SAFETY: noindex until this is a real post. DELETE the next line and\n       uncomment the index,follow line when publishing. -->\n  <meta name="robots" content="noindex, nofollow" />\n  <!-- <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1" /> -->',
                          '  <!-- DRAFT: waiting on first-hand detail. Rebuild with --publish to index. -->\n  <meta name="robots" content="noindex, follow" />')
    out = out.replace('content="POST TITLE | Ring Mint"', f'content="{esc(title)} | Ring Mint"')
    out = out.replace('content="SAME OR SLIGHTLY WARMER VERSION OF THE META DESCRIPTION."', f'content="{esc(og_desc)}"')
    out = out.replace('content="META DESCRIPTION AGAIN."', f'content="{esc(desc)}"')
    out = out.replace('content="DESCRIBE THE OG IMAGE IN ONE SENTENCE."', f'content="{esc(meta.get("og_alt", h1))}"')
    out = out.replace('<meta property="article:published_time" content="YYYY-MM-DD" />', f'<meta property="article:published_time" content="{date}" />')
    out = out.replace('<meta property="article:modified_time" content="YYYY-MM-DD" />', f'<meta property="article:modified_time" content="{modified}" />')
    out = re.sub(r'<meta property="article:section" content="CATEGORY NAME[^"]*" />', f'<meta property="article:section" content="{esc(cat)}" />', out)
    tag_lines = "\n".join(f'  <meta property="article:tag" content="{esc(t)}" />' for t in tags)
    out = re.sub(r'  <meta property="article:tag" content="PRIMARY KEYWORD" />\n  <meta property="article:tag" content="SECONDARY KEYWORD" />\n  <meta property="article:tag" content="THIRD KEYWORD" />', tag_lines, out)
    # json-ld
    out = out.replace('"headline": "POST TITLE (MAX 110 CHARS)"', f'"headline": {json.dumps(headline, ensure_ascii=False)}')
    out = out.replace('"description": "META DESCRIPTION AGAIN."', f'"description": {json.dumps(desc, ensure_ascii=False)}')
    out = out.replace('"datePublished": "YYYY-MM-DD"', f'"datePublished": "{date}"').replace('"dateModified": "YYYY-MM-DD"', f'"dateModified": "{modified}"')
    out = out.replace('"articleSection": "CATEGORY NAME"', f'"articleSection": {json.dumps(cat)}')
    out = out.replace('"keywords": "PRIMARY KEYWORD, SECONDARY KEYWORD, THIRD KEYWORD"', f'"keywords": {json.dumps(", ".join(tags), ensure_ascii=False)}')
    out = out.replace('"wordCount": 1234', f'"wordCount": {words}')
    out = out.replace('"name": "POST TITLE | Ring Mint"', f'"name": {json.dumps(title + " | Ring Mint", ensure_ascii=False)}')
    out = out.replace('"name": "POST TITLE SHORT FORM"', f'"name": {json.dumps(crumb, ensure_ascii=False)}')
    out = out.replace('  <!-- OPTIONAL: if the post has a genuine Q&A section, add a second JSON-LD\n       script with FAQPage markup. See BLOG_PUBLISHING_GUIDE.md §Structured data. -->', faq_ld)
    # body tokens
    out = out.replace('<span aria-current="page">POST TITLE SHORT FORM</span>', f'<span aria-current="page">{esc(crumb)}</span>')
    out = out.replace('<a href="/blog/#CATEGORY-ANCHOR">CATEGORY NAME</a>', f'<a href="/blog/#{anchor}">{esc(cat)}</a>')
    out = out.replace('<h1>POST TITLE AS THE READER SEES IT (H1: exactly one on the page)</h1>', f'<h1>{h1}</h1>')
    out = out.replace('<time datetime="YYYY-MM-DD">Month D, YYYY</time>', f'<time datetime="{date}">{date_h}</time>')
    out = out.replace('<span>N min read</span>', f'<span>{read_min} min read</span>')
    out = out.replace('alt="DESCRIBE WHAT IS IN THE IMAGE, naturally including the keyword if honest"', f'alt="{esc(meta.get("hero_alt", h1))}"')
    if meta.get("figcaption"):
        out = out.replace('<figcaption class="container">OPTIONAL CAPTION: credit or context. Delete the figcaption element if unused.</figcaption>', f'<figcaption class="container">{meta["figcaption"]}</figcaption>')
    else:
        out = out.replace('        <figcaption class="container">OPTIONAL CAPTION: credit or context. Delete the figcaption element if unused.</figcaption>\n', '')
    # replace the whole example prose
    out = re.sub(r'(<div class="prose">\n)(.*?)(\n            <form class="capture")', lambda m: m.group(1) + "            " + prose + m.group(3), out, flags=re.S)
    out = out.replace("POST-SLUG", slug)
    out = out.replace("SLUGREF", slug)
    dest = ROOT / "blog" / slug / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"wrote {dest.relative_to(ROOT)} ({words} words, {read_min} min, {'index' if publish else 'NOINDEX draft'})")

    # images
    # No hero: a post gets in-body imagery only when there is a real image worth
    # showing, added deliberately. What is generated here is the social card, the
    # /blog/ listing card, and the Story and pin, none of which appear in the post.
    card = ROOT / "assets" / "blog" / f"{slug}-og.jpg"
    if "--no-images" not in flags and not card.exists():
        cmd = [sys.executable, str(ROOT / "tools" / "blog-images.py"), "social", "--slug", slug,
               "--title", meta.get("image_title", h1),
               "--answer", meta.get("image_answer", ""), "--sub", meta.get("image_sub", "")]
        if meta.get("image_og_title"):
            cmd += ["--og-title", meta["image_og_title"]]
        subprocess.run(cmd, check=True)

    # blog index card
    idx = ROOT / "blog" / "index.html"; s = idx.read_text(encoding="utf-8")
    if f'href="/blog/{slug}/"' not in s:
        excerpt = meta.get("excerpt", desc)[:160]
        card = f'''          <a class="blog-card" href="/blog/{slug}/">
            <div class="blog-card-media">
              <img src="/assets/blog/{slug}-card.jpg" alt="{esc(meta.get("card_alt", "Gold line drawings of cut diamonds on a dark background"))}" width="800" height="500" loading="lazy" />
            </div>
            <div class="blog-card-body">
              <p class="blog-card-meta"><span class="blog-card-category">{esc(cat)}</span> · <time datetime="{date}">{date_h}</time></p>
              <h3>{h1}</h3>
              <p class="blog-card-excerpt">{esc(excerpt)}</p>
              <span class="blog-card-more">Read the post</span>
            </div>
          </a>
'''
        head, sec = s.split(f'id="{anchor}"', 1)
        sec_body, rest = sec.split("</section>", 1)
        sec_body = sec_body.replace('<div class="blog-grid">\n', '<div class="blog-grid">\n' + card, 1)
        sec_body = re.sub(r'\n        <p class="blog-empty">.*?</p>', '', sec_body, flags=re.S)
        s = head + f'id="{anchor}"' + sec_body + "</section>" + rest
        idx.write_text(s, encoding="utf-8"); print("card added to /blog/")

    # sitemap
    sm = ROOT / "sitemap.xml"; s = sm.read_text()
    entry = f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{modified}</lastmod>\n    <changefreq>yearly</changefreq>\n    <priority>0.6</priority>\n  </url>\n"
    if url not in s:
        if publish:
            s = s.replace("</urlset>", entry + "</urlset>"); sm.write_text(s); print("sitemap entry added")
    elif publish:
        s = re.sub(rf'(<loc>{re.escape(url)}</loc>\s*<lastmod>)[^<]+', rf'\g<1>{modified}', s); sm.write_text(s)
    else:
        # Demoted back to a draft. A noindex page must not sit in the sitemap,
        # so drop the entry; re-running with --publish puts it back.
        s = re.sub(rf'  <url>\s*<loc>{re.escape(url)}</loc>.*?</url>\n', '', s, flags=re.S)
        sm.write_text(s); print("sitemap entry removed (draft)")
    # blog index lastmod
    s = sm.read_text(); s = re.sub(r'(<loc>https://ringmint.com/blog/</loc>\s*<lastmod>)[^<]+', rf'\g<1>{modified}', s); sm.write_text(s)

    # llms.txt
    ll = ROOT / "llms.txt"; s = ll.read_text()
    if url not in s and meta.get("llms"):
        line = f"- [{h1}]({url}): {meta['llms']}\n"
        s = re.sub(r'(- \[The Ring Mint Journal\]\([^\n]*\n)', lambda m: m.group(1) + line, s, count=1)
        ll.write_text(s); print("llms.txt line added")

    # feed
    subprocess.run([sys.executable, str(ROOT / "tools" / "build-feed.py")], check=True)

    # calendar
    cal = ROOT / "content" / "calendar.csv"
    rows = list(csv.DictReader(cal.open(newline="")))
    found = False
    for r in rows:
        if r["slug"] == slug:
            r["status"] = "published" if publish else "drafted"
            r["publish_date"] = date if publish else r["publish_date"]
            found = True
    if not found:
        rows.append({"slug": slug, "path": f"/blog/{slug}/", "cluster": meta.get("cluster", ""), "priority": meta.get("priority", ""),
                     "title": h1, "primary_keyword": tags[0] if tags else "", "status": "published" if publish else "drafted",
                     "publish_date": date if publish else "", "refresh_due": meta.get("refresh_due", ""), "gsc_clicks_30d": "", "gsc_clicks_90d": "", "notes": ""})
    with cal.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("calendar updated")

if __name__ == "__main__":
    main()
