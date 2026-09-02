#!/usr/bin/env python3
"""
Build /feed.xml (RSS 2.0, full text) from every published post in /blog/.

    python3 tools/build-feed.py

Run it after a post is final and again after any material update, because the
feed embeds the full article body. It reads each blog/*/index.html (skipping the
template and anything still marked noindex), sorts by article:published_time,
newest first, and rewrites feed.xml at the repo root. No dependencies.
"""
import html, pathlib, re, sys
from datetime import datetime, timezone
from email.utils import format_datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://ringmint.com"
FEED_URL = f"{SITE}/feed.xml"


def meta(src, attr, name):
    m = re.search(rf'<meta\s+{attr}="{re.escape(name)}"\s+content="([^"]*)"', src)
    return html.unescape(m.group(1)) if m else ""


def extract_div(src, cls):
    """Return the inner HTML of the first <div class="cls"> ... </div>, depth-aware."""
    start = re.search(rf'<div\s+class="{re.escape(cls)}"[^>]*>', src)
    if not start:
        return ""
    i, depth = start.end(), 1
    for m in re.finditer(r'<div\b[^>]*>|</div>', src[start.end():]):
        depth += 1 if m.group(0).startswith('<div') else -1
        if depth == 0:
            return src[i:start.end() + m.start()]
    return ""


def absolutise(body):
    body = re.sub(r'(href|src|srcset)="/', rf'\1="{SITE}/', body)
    body = re.sub(r'\s(?:loading|fetchpriority)="[^"]*"', '', body)
    return body.strip()


def post_entry(path):
    src = path.read_text(encoding="utf-8")
    robots = meta(src, "name", "robots")
    if "noindex" in robots:
        return None
    link = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', src).group(1)
    h1 = re.search(r'<h1>(.*?)</h1>', src, re.S)
    title = html.unescape(re.sub(r'<[^>]+>', '', h1.group(1))).strip() if h1 else meta(src, "property", "og:title")
    desc = meta(src, "name", "description")
    pub = meta(src, "property", "article:published_time")
    mod = meta(src, "property", "article:modified_time") or pub
    section = meta(src, "property", "article:section")
    tags = [html.unescape(t) for t in re.findall(r'<meta\s+property="article:tag"\s+content="([^"]*)"', src)]
    og_image = meta(src, "property", "og:image")
    body = absolutise(extract_div(src, "prose"))
    if not body:
        sys.exit(f"{path}: could not find <div class=\"prose\">")
    img_path = ROOT / og_image.replace(SITE + "/", "")
    img_len = img_path.stat().st_size if img_path.exists() else 0
    return dict(link=link, title=title, desc=desc, pub=pub, mod=mod, section=section,
                tags=tags, og_image=og_image, img_len=img_len, body=body)


def rfc822(iso):
    d = datetime.strptime(iso, "%Y-%m-%d").replace(hour=12, tzinfo=timezone.utc)
    return format_datetime(d)


def main():
    posts = []
    for p in sorted((ROOT / "blog").glob("*/index.html")):
        if p.parent.name.startswith("_"):
            continue
        e = post_entry(p)
        if e:
            posts.append(e)
    posts.sort(key=lambda e: (e["pub"], e["link"]), reverse=True)
    if not posts:
        sys.exit("no published posts found")

    now = format_datetime(datetime.now(timezone.utc))
    items = []
    for e in posts:
        cats = "".join(f"\n      <category>{html.escape(c)}</category>" for c in [e["section"]] + e["tags"] if c)
        enclosure = f'\n      <enclosure url="{e["og_image"]}" length="{e["img_len"]}" type="image/jpeg" />' if e["og_image"] else ""
        items.append(f"""    <item>
      <title>{html.escape(e["title"])}</title>
      <link>{e["link"]}</link>
      <guid isPermaLink="true">{e["link"]}</guid>
      <pubDate>{rfc822(e["pub"])}</pubDate>
      <atom:updated>{e["mod"]}T12:00:00Z</atom:updated>
      <dc:creator>Chloe Alpert</dc:creator>{cats}
      <description>{html.escape(e["desc"])}</description>{enclosure}
      <content:encoded><![CDATA[
{e["body"]}
      ]]></content:encoded>
    </item>""")

    out = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:atom="http://www.w3.org/2005/Atom"
     xmlns:content="http://purl.org/rss/1.0/modules/content/"
     xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>The Ring Mint Journal</title>
    <link>{SITE}/blog/</link>
    <atom:link href="{FEED_URL}" rel="self" type="application/rss+xml" />
    <description>Jewelry news, diamond and gemstone guides, and buying guides, written by Chloe Alpert, a second-generation jeweler. Plain answers, no sales pitch.</description>
    <language>en-us</language>
    <copyright>Ring Mint</copyright>
    <managingEditor>chloe@ringmint.com (Chloe Alpert)</managingEditor>
    <webMaster>chloe@ringmint.com (Chloe Alpert)</webMaster>
    <lastBuildDate>{now}</lastBuildDate>
    <ttl>1440</ttl>
    <image>
      <url>{SITE}/assets/fav.png</url>
      <title>The Ring Mint Journal</title>
      <link>{SITE}/blog/</link>
    </image>
{chr(10).join(items)}
  </channel>
</rss>
"""
    (ROOT / "feed.xml").write_text(out, encoding="utf-8")
    print(f"wrote feed.xml with {len(posts)} post(s):")
    for e in posts:
        print(f"  {e['pub']}  {e['link']}")


if __name__ == "__main__":
    main()
