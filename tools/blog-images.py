#!/usr/bin/env python3
"""
Generate the full image set for a Ring Mint Journal post in the house style.

    python3 tools/blog-images.py generate --slug are-tiktok-diamonds-real \
        --title "Are the diamonds|on TikTok Live|actually real?" \
        --og-title "Are TikTok|diamonds real?" \
        --answer "Yes. That's not the problem." \
        --sub "What $100 a carat actually buys,|from a jeweler who sorts these parcels."

writes to assets/blog/:
    SLUG-hero.jpg         1600x900   post hero (desktop)
    SLUG-hero-mobile.jpg  1080x1350  post hero (phones, via <picture>)
    SLUG-og.jpg           1200x630   social / OG card, title overlaid
    SLUG-card.jpg         800x500    /blog/ listing card
    SLUG-story.jpg        1080x1920  Instagram Story (not referenced by the site)
    SLUG-pin.jpg          1000x1500  Pinterest pin, 2:3 (not referenced by the site)

--og-title is a shorter, hand-broken headline for the social card and listing
card, which set type far larger than the hero does. It falls back to --title,
but a full post title is usually too long to render at full size.

For a post whose hero is a photograph, keep the photo as SLUG-hero.jpg and run
only the pieces that do not derive from it:

    python3 tools/blog-images.py crop-mobile --slug SLUG            # 4:5 centre crop of SLUG-hero.jpg
    python3 tools/blog-images.py crop-mobile --slug SLUG --source clean-photo.jpg   # if the hero has text on it
    python3 tools/blog-images.py og    --slug SLUG --og-title ...
    python3 tools/blog-images.py card  --slug SLUG --og-title ...
    python3 tools/blog-images.py story --slug SLUG --title ... --answer ... --sub ...
    python3 tools/blog-images.py pin   --slug SLUG --title ... --answer ... --sub ...

House style (do not drift): cream #fbf8f3 ground with a warm radial wash, gold
(174,143,69) line-art diamonds drawn as a faint watermark, ink #171717 Playfair
Display headlines, gold Playfair italic answer line, Inter 500 letter-spaced
small caps eyebrow, a hairline gold frame. This replaced an earlier charcoal and
Didot treatment: cream ground with dark type stays legible at the sizes these
images are actually viewed at, and matches the site the images link to. If the
style needs to change, change it here so every post changes with it.

Requires Pillow (pip3 install --user Pillow). Fonts are the site's own brand
faces, vendored under tools/fonts/ as .ttf because Pillow cannot read .woff2.
Inter ships as a variable font, so its static weights there are instances cut
with fontTools.varLib.instancer; regenerate them if the web fonts change.
"""
import argparse, hashlib, math, pathlib, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "blog"
FONTS = pathlib.Path(__file__).resolve().parent / "fonts"
PLAYFAIR = str(FONTS / "playfair-display-400-latin.ttf")
PLAYFAIR_I = str(FONTS / "playfair-display-400-italic-latin.ttf")
INTER = str(FONTS / "inter-500-latin.ttf")

# Palette, taken from :root in styles.css so the images match the site
BG = (251, 248, 243)         # --bg
BG_WARM = (246, 241, 231)    # --bg-warm
INK = (23, 23, 23)           # --ink
GOLD = (174, 143, 69)        # --gold
LINE = (215, 198, 156)       # --line-strong
MUTED = (98, 92, 82)         # --muted
S = 2  # supersample factor; every canvas is drawn at S and downsampled on save


class Sheet:
    """A cream page with gold line art and the brand faces.

    Everything is drawn at S times final size and downsampled in save(), which
    is what keeps the type crisp. Coordinates are given as fractions of the
    canvas so the same composition code works at any aspect ratio.
    """

    def __init__(self, w, h, wash_cx=0.72, wash_cy=0.45):
        self.W, self.H = w * S, h * S
        img = Image.new("RGB", (self.W, self.H), BG)
        # a warm radial wash, just enough to keep a large flat area from looking dead
        wash = Image.new("L", (self.W, self.H), 0)
        wd = ImageDraw.Draw(wash)
        cx, cy = self.W * wash_cx, self.H * wash_cy
        R0 = max(self.W, self.H) * 0.8
        for r in range(int(R0), 0, -8):
            wd.ellipse([cx - r * 1.15, cy - r * 0.9, cx + r * 1.15, cy + r * 0.9],
                       fill=int(150 * (1 - r / R0) ** 1.5))
        wash = wash.filter(ImageFilter.GaussianBlur(45 * S // 2))
        self.img = Image.composite(Image.new("RGB", (self.W, self.H), BG_WARM), img, wash)
        self.d = ImageDraw.Draw(self.img, "RGBA")

    # --- fonts ----------------------------------------------------------
    def play(self, px):   return ImageFont.truetype(PLAYFAIR, int(px * S))
    def play_i(self, px): return ImageFont.truetype(PLAYFAIR_I, int(px * S))
    def inter(self, px):  return ImageFont.truetype(INTER, int(px * S))

    # --- line art -------------------------------------------------------
    def diamond(self, fx, fy, w, alpha=120):
        """The crown-and-pavilion profile, as a faint watermark."""
        d, col = self.d, (*LINE, alpha)
        cx, cy, w = self.W * fx, self.H * fy, w * S
        lw = 2 * S
        tw, ch, ph = w * .55, w * .30, w * .95
        tl, tr = (cx - tw / 2, cy - ch), (cx + tw / 2, cy - ch)
        gl, gr, tip = (cx - w / 2, cy), (cx + w / 2, cy), (cx, cy + ph)
        d.polygon([tl, tr, gr, tip, gl], outline=col, width=lw)
        for i in range(5):
            d.line([(tl[0] + (tr[0] - tl[0]) * i / 4, tl[1]), (gl[0] + (gr[0] - gl[0]) * i / 4, cy)], fill=col, width=S)
        d.line([gl, gr], fill=col, width=lw)
        for i in range(1, 4):
            d.line([(gl[0] + (gr[0] - gl[0]) * i / 3, cy), tip], fill=col, width=S)

    def round_top(self, fx, fy, r, alpha=120):
        """A round brilliant seen from above."""
        d, col, n = self.d, (*LINE, alpha), 16
        cx, cy, r = self.W * fx, self.H * fy, r * S
        lw = 2 * S
        outer = [(cx + r * math.cos(2 * math.pi * i / n - math.pi / 2), cy + r * math.sin(2 * math.pi * i / n - math.pi / 2)) for i in range(n)]
        inner = [(cx + r * .52 * math.cos(2 * math.pi * (i + .5) / 8 - math.pi / 2), cy + r * .52 * math.sin(2 * math.pi * (i + .5) / 8 - math.pi / 2)) for i in range(8)]
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=lw)
        d.polygon(inner, outline=col, width=S)
        for i in range(8):
            for k in (0, 1, 2):
                d.line([outer[(i * 2 + k) % n], inner[i]], fill=col, width=S)

    def sparkles(self, pts):
        for fx, fy, r in pts:
            cx, cy, r = self.W * fx, self.H * fy, r * S
            col = (*GOLD, 130)
            self.d.line([(cx - r, cy), (cx + r, cy)], fill=col, width=S)
            self.d.line([(cx, cy - r), (cx, cy + r)], fill=col, width=S)
            self.d.line([(cx - r * .4, cy - r * .4), (cx + r * .4, cy + r * .4)], fill=col, width=S)
            self.d.line([(cx - r * .4, cy + r * .4), (cx + r * .4, cy - r * .4)], fill=col, width=S)

    def frame(self, inset=40):
        m = inset * S
        self.d.rectangle([m, m, self.W - m, self.H - m], outline=(*LINE, 150), width=S)

    # --- type -----------------------------------------------------------
    def tracked(self, text, fx, fy, font, fill, sp, anchor="lm"):
        """Letter-spaced small caps. Pillow has no tracking, so step per glyph."""
        widths = [self.d.textlength(c, font=font) for c in text]
        total = sum(widths) + sp * S * (len(text) - 1)
        x = self.W * fx
        if anchor == "mm":
            x -= total / 2
        for c, w in zip(text, widths):
            self.d.text((x, self.H * fy), c, font=font, fill=fill, anchor="lm")
            x += w + sp * S

    def fit(self, lines, start, minimum, maxw):
        """Largest Playfair size at which every line clears maxw (in device px)."""
        size = start
        while size > minimum:
            if max(self.d.textlength(l, font=self.play(size)) for l in lines) <= maxw:
                break
            size -= 2
        return size

    def headline(self, lines, fx, fy, size, anchor="lm", leading=1.18):
        gap = size * leading * S
        y0 = self.H * fy - (len(lines) - 1) * gap / 2
        for i, line in enumerate(lines):
            self.d.text((self.W * fx, y0 + i * gap), line, font=self.play(size), fill=INK, anchor=anchor)

    def hairline(self, fx, fy, w):
        x, y = self.W * fx, self.H * fy
        self.d.line([(x, y), (x + w * S, y)], fill=GOLD, width=3 * S)

    def pill(self, label, fy, w=420, h=76):
        pw, ph = w * S, h * S
        px, py = (self.W - pw) / 2, self.H * fy - ph / 2
        self.d.rounded_rectangle([px, py, px + pw, py + ph], radius=ph / 2, outline=GOLD, width=2 * S)
        self.tracked(label, 0.5, fy, self.inter(26), GOLD, 5, anchor="mm")

    def save(self, path, w, h, q=86):
        self.img.resize((w, h), Image.LANCZOS).save(path, quality=q, optimize=True, progressive=True)
        print("wrote", path.relative_to(ROOT), f"{path.stat().st_size // 1024} KB")
        return self.img.resize((w, h), Image.LANCZOS)


def _rng(slug):
    """Deterministic per-slug randomness. The same slug always produces the same
    artwork, so re-running the generator never silently changes a published image,
    but two different posts never come out byte-identical either."""
    return random.Random(hashlib.sha256(slug.encode()).hexdigest())


# --- compositions -------------------------------------------------------
def hero(slug):
    """Untyped line-art plate. The post's own <h1> sits above it in the page,
    so the hero carries no headline; it varies per slug so the index does not
    show eleven identical images."""
    r = _rng(slug)
    c = Sheet(1600, 900, wash_cx=r.uniform(0.55, 0.75), wash_cy=r.uniform(0.38, 0.52))
    focal_round = r.random() < 0.5
    fx, fy = r.uniform(0.30, 0.44), r.uniform(0.40, 0.50)
    (c.round_top if focal_round else c.diamond)(fx, fy, r.uniform(175, 215), 150)
    c.diamond(r.uniform(0.58, 0.66), r.uniform(0.34, 0.42), r.uniform(210, 250), 130)
    c.diamond(r.uniform(0.74, 0.82), r.uniform(0.38, 0.48), r.uniform(135, 165), 110)
    if r.random() < 0.7:
        c.diamond(r.uniform(0.48, 0.55), r.uniform(0.44, 0.52), r.uniform(90, 115), 95)
    # oversized faint shapes bleeding off opposite corners
    c.diamond(r.uniform(0.92, 1.00), r.uniform(0.24, 0.34), r.uniform(310, 360), 70)
    (c.round_top if r.random() < 0.5 else c.diamond)(r.uniform(0.04, 0.12), r.uniform(0.86, 0.96), r.uniform(200, 240), 70)
    c.sparkles([(r.uniform(0.08, 0.95), r.uniform(0.14, 0.88), r.randint(9, 18)) for _ in range(r.randint(6, 8))])
    c.frame()
    return c.save(OUT / f"{slug}-hero.jpg", 1600, 900, 84)


def hero_mobile(slug):
    r = _rng(slug + "-mobile")
    c = Sheet(1080, 1350, wash_cx=0.5, wash_cy=0.42)
    c.round_top(0.50, 0.36, 300, 150)
    c.diamond(0.22, 0.70, 170, 120)
    c.diamond(0.78, 0.70, 170, 120)
    c.diamond(0.50, 0.78, 120, 100)
    c.diamond(1.02, 0.12, 300, 70)
    c.round_top(-0.05, 1.0, 260, 70)
    c.sparkles([(.18, .18, 14), (.82, .22, 18), (.12, .50, 11), (.88, .48, 12), (.30, .92, 10), (.72, .95, 9), (.50, .08, 11)])
    c.frame()
    c.save(OUT / f"{slug}-hero-mobile.jpg", 1080, 1350, 84)


def og(slug, title):
    """The 1200x630 social card.

    Drawn from scratch rather than composited onto a downscaled hero: the
    original version drew 62-74px type at 1x over a busy crop, which rendered
    around 26px in a feed and was unreadable. The headline is auto-fit to the
    widest line and runs over the line art, which sits low enough in alpha that
    the overlap reads as a watermark."""
    c = Sheet(1200, 630, wash_cx=0.78, wash_cy=0.45)
    c.round_top(0.855, 0.44, 190, 120)
    c.diamond(0.95, 0.80, 110, 94)
    L = 88 / 1200
    c.tracked("THE RING MINT JOURNAL", L, 0.175, c.inter(23), GOLD, 6)
    c.hairline(L, 0.245, 120)
    lines = title[:3]
    size = c.fit(lines, 122 if len(lines) <= 2 else 100, 52, c.W * 0.86 - 88 * S)
    c.headline(lines, L, 0.535, size)
    c.tracked("RINGMINT.COM", L, 0.875, c.inter(22), MUTED, 5)
    c.save(OUT / f"{slug}-og.jpg", 1200, 630, 88)
    print("   headline", f"{size}px")


def card(slug, title):
    """The /blog/ listing card. Same construction as the OG card at 800x500, so
    the index and the social previews read as one set. The headline is burned in
    so the index is scannable and two posts are never interchangeable."""
    c = Sheet(800, 500, wash_cx=0.78, wash_cy=0.45)
    c.round_top(0.87, 0.42, 130, 120)
    c.diamond(0.96, 0.82, 78, 94)
    L = 60 / 800
    c.tracked("THE RING MINT JOURNAL", L, 0.16, c.inter(16), GOLD, 4)
    c.hairline(L, 0.235, 80)
    lines = title[:3]
    size = c.fit(lines, 78 if len(lines) <= 2 else 62, 32, c.W * 0.86 - 60 * S)
    c.headline(lines, L, 0.545, size)
    c.tracked("RINGMINT.COM", L, 0.89, c.inter(15), MUTED, 4)
    c.save(OUT / f"{slug}-card.jpg", 800, 500, 84)


def story(slug, title, answer, sub):
    c = Sheet(1080, 1920, wash_cx=0.5, wash_cy=0.30)
    c.round_top(0.12, 0.14, 300, 90)
    c.diamond(0.50, 0.26, 250, 140)
    c.diamond(0.24, 0.29, 130, 110)
    c.diamond(0.77, 0.28, 150, 120)
    c.diamond(0.96, 0.80, 360, 60)
    c.sparkles([(.30, .18, 14), (.68, .15, 18), (.86, .22, 11), (.12, .40, 12), (.62, .42, 10), (.14, .72, 12), (.86, .60, 9), (.40, .90, 11)])
    c.frame()
    c.tracked("THE RING MINT JOURNAL", 0.5, 0.505, c.inter(26), GOLD, 7, anchor="mm")
    lines = title[:3]
    size = c.fit(lines, 92, 46, c.W * 0.84)
    c.headline(lines, 0.5, 0.615, size, anchor="mm", leading=1.20)
    c.hairline(0.40, 0.715, 216)
    c.d.text((c.W / 2, c.H * 0.757), answer, font=c.play_i(52), fill=GOLD, anchor="mm")
    for i, line in enumerate(sub):
        c.d.text((c.W / 2, c.H * (0.815 + i * 0.03)), line, font=c.inter(29), fill=MUTED, anchor="mm")
    c.pill("READ THE POST", 0.895)
    c.tracked("RINGMINT.COM", 0.5, 0.94, c.inter(23), MUTED, 4, anchor="mm")
    c.save(OUT / f"{slug}-story.jpg", 1080, 1920, 86)


def pin(slug, title, answer, sub):
    # Pinterest's preferred 2:3. Same composition language as the Story, but no
    # Instagram UI safe zones, so the type sits higher and larger.
    c = Sheet(1000, 1500, wash_cx=0.5, wash_cy=0.28)
    c.round_top(0.50, 0.25, 250, 140)
    c.diamond(0.22, 0.29, 130, 110)
    c.diamond(0.78, 0.28, 150, 120)
    c.diamond(0.97, 0.84, 320, 60)
    c.round_top(0.04, 0.04, 220, 70)
    c.sparkles([(.30, .15, 14), (.68, .12, 18), (.88, .21, 11), (.10, .39, 12), (.62, .41, 10), (.14, .70, 12), (.88, .58, 9), (.40, .93, 11)])
    c.frame()
    c.tracked("THE RING MINT JOURNAL", 0.5, 0.475, c.inter(24), GOLD, 6, anchor="mm")
    lines = title[:3]
    size = c.fit(lines, 84, 42, c.W * 0.84)
    c.headline(lines, 0.5, 0.585, size, anchor="mm", leading=1.20)
    c.hairline(0.40, 0.695, 200)
    c.d.text((c.W / 2, c.H * 0.740), answer, font=c.play_i(48), fill=GOLD, anchor="mm")
    for i, line in enumerate(sub):
        c.d.text((c.W / 2, c.H * (0.800 + i * 0.032)), line, font=c.inter(27), fill=MUTED, anchor="mm")
    c.pill("READ THE POST", 0.885, w=380, h=70)
    c.tracked("RINGMINT.COM", 0.5, 0.935, c.inter(23), MUTED, 4, anchor="mm")
    c.save(OUT / f"{slug}-pin.jpg", 1000, 1500, 84)


def crop_mobile(slug, source=None):
    # A hero with a headline baked into it cannot be centre-cropped (the text gets
    # sliced), so pass --source with a clean photograph for those posts.
    src = Image.open(OUT / source if source else OUT / f"{slug}-hero.jpg")
    w, h = src.size
    tw = int(h * 4 / 5)
    if tw > w:
        th = int(w * 5 / 4); box = (0, (h - th) // 2, w, (h + th) // 2)
    else:
        box = ((w - tw) // 2, 0, (w + tw) // 2, h)
    out = src.crop(box)
    if out.width > 1080:
        out = out.resize((1080, 1350), Image.LANCZOS)
    out.save(OUT / f"{slug}-hero-mobile.jpg", quality=84, optimize=True, progressive=True)
    print("wrote", f"assets/blog/{slug}-hero-mobile.jpg", out.size)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["generate", "hero", "og", "card", "story", "pin", "crop-mobile"])
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", help="headline, lines separated by |, 2 or 3 lines")
    ap.add_argument("--og-title", help="shorter headline for the OG and listing cards, lines separated by |; defaults to --title")
    ap.add_argument("--answer", help="one short line, gold italic (story and pin)")
    ap.add_argument("--sub", default="", help="one or two supporting lines separated by | (story and pin)")
    ap.add_argument("--source", help="crop-mobile only: a clean photo in assets/blog/ to crop instead of SLUG-hero.jpg")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    title = a.title.split("|") if a.title else []
    og_title = a.og_title.split("|") if a.og_title else title
    sub = [s for s in a.sub.split("|") if s]

    if a.mode == "crop-mobile":
        return crop_mobile(a.slug, a.source)
    if a.mode == "hero":
        hero(a.slug)
        return hero_mobile(a.slug)
    if a.mode in ("og", "card"):
        if not og_title:
            sys.exit("--og-title (or --title) is required")
        return (og if a.mode == "og" else card)(a.slug, og_title)
    if not title:
        sys.exit("--title is required")
    if a.mode == "generate":
        hero(a.slug)
        hero_mobile(a.slug)
        og(a.slug, og_title)
        card(a.slug, og_title)
    if not a.answer:
        sys.exit("--answer is required for the story and pin images")
    if a.mode in ("generate", "story"):
        story(a.slug, title, a.answer, sub)
    if a.mode in ("generate", "pin"):
        pin(a.slug, title, a.answer, sub)


if __name__ == "__main__":
    main()
