#!/usr/bin/env python3
"""
Sync the latest Instagram posts into the static site.

Fetches recent media via the Instagram Graph API, downloads each photo,
centre-crops it to a square, writes AVIF + JPEG into assets/instagram/,
and rewrites the tile markup in index.html between the
`ig:feed:start` / `ig:feed:end` markers.

The result is plain static HTML with locally hosted, optimised images --
crawlable, fast, and with no third-party script on the page.

Env:
  IG_ACCESS_TOKEN   long-lived Instagram access token (required)
  IG_POST_COUNT     how many tiles to show (default 6)

Run locally:
  IG_ACCESS_TOKEN=xxx python3 scripts/sync_instagram.py
"""

from __future__ import annotations

import html
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://graph.instagram.com/v21.0"
ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets" / "instagram"
INDEX = ROOT / "index.html"
PROFILE = "https://www.instagram.com/theringmint"

START = "<!-- ig:feed:start"
END = "<!-- ig:feed:end -->"
TILE_SIZE = 700

IG_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">'
    '<rect x="3" y="3" width="18" height="18" rx="5"/>'
    '<circle cx="12" cy="12" r="4"/>'
    '<circle cx="17.2" cy="6.8" r="1.1" fill="currentColor" stroke="none"/></svg>'
)


def fail(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode())


def fetch_media(token: str, count: int) -> list[dict]:
    fields = (
        "id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,"
        "children{media_url,media_type,thumbnail_url}"
    )
    qs = urllib.parse.urlencode({"fields": fields, "limit": max(count * 2, count), "access_token": token})
    data = get_json(f"{API}/me/media?{qs}")
    if "error" in data:
        fail(f"Instagram API: {data['error'].get('message', data['error'])}")
    return data.get("data", [])


def image_url(item: dict) -> str | None:
    """Best still image for a post, whatever its media type."""
    t = item.get("media_type")
    if t == "IMAGE":
        return item.get("media_url")
    if t == "VIDEO":
        return item.get("thumbnail_url")
    if t == "CAROUSEL_ALBUM":
        for child in (item.get("children") or {}).get("data", []):
            if child.get("media_type") == "VIDEO":
                if child.get("thumbnail_url"):
                    return child["thumbnail_url"]
            elif child.get("media_url"):
                return child["media_url"]
    return item.get("media_url") or item.get("thumbnail_url")


def clean_caption(caption: str | None) -> str:
    """Turn a caption into something usable as alt text."""
    if not caption:
        return ""
    text = caption.split("\n")[0]
    text = re.sub(r"#\w+", "", text)               # drop hashtags
    text = re.sub(r"@[\w.]+", "", text)            # drop @mentions
    text = "".join(c for c in text if c.isprintable() and ord(c) < 0x2190)  # drop emoji
    text = re.sub(r"\s+", " ", text).strip(" -–—·|")
    if len(text) > 120:
        text = text[:117].rsplit(" ", 1)[0] + "…"
    return text.strip()


def square(img, size: int):
    """Centre-crop to a square, then resize."""
    from PIL import Image

    w, h = img.size
    side = min(w, h)
    img = img.crop(((w - side) // 2, (h - side) // 2, (w + side) // 2, (h + side) // 2))
    return img.convert("RGB").resize((size, size), Image.LANCZOS)


def save_variants(img, stem: str) -> bool:
    """Write JPEG (always) and AVIF (if the encoder is available). Returns avif_ok."""
    img.save(OUT_DIR / f"{stem}.jpg", "JPEG", quality=80, optimize=True, progressive=True)
    try:
        img.save(OUT_DIR / f"{stem}.avif", "AVIF", quality=58)
        return True
    except Exception as e:  # encoder missing -> JPEG-only, page still works
        print(f"  note: AVIF unavailable ({e}); JPEG only for {stem}")
        return False


def build_tiles(posts: list[dict]) -> str:
    rows = []
    for p in posts:
        alt = p["alt"] or "Custom engagement ring by Ring Mint"
        src = f'/assets/instagram/{p["stem"]}'
        source = f'\n              <source srcset="{src}.avif" type="image/avif" />' if p["avif"] else ""
        rows.append(
            f'          <a class="ig-tile" href="{html.escape(p["permalink"])}" '
            f'target="_blank" rel="noopener noreferrer">\n'
            f"            <picture>{source}\n"
            f'              <img src="{src}.jpg" width="{TILE_SIZE}" height="{TILE_SIZE}" '
            f'loading="lazy" decoding="async" alt="{html.escape(alt, quote=True)}" />\n'
            f"            </picture>\n"
            f'            <span class="ig-mark" aria-hidden="true">{IG_SVG}</span>\n'
            f"          </a>"
        )
    return (
        '        <div class="ig-grid" id="igGrid">\n'
        + "\n".join(rows)
        + "\n        </div>"
    )


def main() -> None:
    token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    if not token:
        fail("IG_ACCESS_TOKEN is not set")
    count = int(os.environ.get("IG_POST_COUNT", "6"))

    try:
        from PIL import Image
    except ImportError:
        fail("Pillow is required: pip install Pillow pillow-avif-plugin")
    try:
        import pillow_avif  # noqa: F401  (registers the AVIF encoder)
    except ImportError:
        pass

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    items = fetch_media(token, count)
    if not items:
        fail("the API returned no media (is the account a Business/Creator account?)")

    posts, used = [], set()
    for item in items:
        if len(posts) >= count:
            break
        url = image_url(item)
        if not url:
            continue
        stem = f"ig-{item['id']}"
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                img = Image.open(io.BytesIO(r.read()))
            avif_ok = save_variants(square(img, TILE_SIZE), stem)
        except Exception as e:
            print(f"  skipped {item.get('id')}: {e}")
            continue
        used.update({f"{stem}.jpg", f"{stem}.avif"})
        posts.append({
            "stem": stem,
            "permalink": item.get("permalink") or PROFILE,
            "alt": clean_caption(item.get("caption")),
            "avif": avif_ok,
        })
        print(f"  ok {stem}  {posts[-1]['alt'][:60] or '(no caption)'}")

    if not posts:
        fail("no downloadable images found")

    # rewrite the tiles in place
    page = INDEX.read_text()
    i, j = page.find(START), page.find(END)
    if i == -1 or j == -1:
        fail("could not find the ig:feed markers in index.html")
    head_end = page.find("-->", i) + 3
    page = page[:head_end] + "\n" + build_tiles(posts) + "\n        " + page[j:]
    INDEX.write_text(page)

    # drop tiles that are no longer in the feed
    for f in OUT_DIR.iterdir():
        if f.name.startswith("ig-") and f.name not in used:
            f.unlink()
            print(f"  removed stale {f.name}")

    print(f"synced {len(posts)} post(s)")


if __name__ == "__main__":
    main()
