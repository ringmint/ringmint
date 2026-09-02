#!/usr/bin/env python3
"""
Generate the full image set for a Ring Mint Journal post in the house style.

    python3 tools/blog-images.py generate --slug are-tiktok-diamonds-real \
        --title "Are the diamonds|on TikTok Live|actually real?" \
        --answer "Yes. That's not the problem." \
        --sub "What $100 a carat actually buys,|from a jeweler who sorts these parcels."

writes to assets/blog/:
    SLUG-hero.jpg         1600x900   post hero (desktop)
    SLUG-hero-mobile.jpg  1080x1350  post hero (phones, via <picture>)
    SLUG-og.jpg           1200x630   social / OG card, title overlaid
    SLUG-card.jpg         800x500    /blog/ listing card
    SLUG-story.jpg        1080x1920  Instagram Story (not referenced by the site)
    SLUG-pin.jpg          1000x1500  Pinterest pin, 2:3 (not referenced by the site)

For a post whose hero is a photograph, keep the photo as SLUG-hero.jpg and run
only the mobile crop, the story, and the pin:

    python3 tools/blog-images.py crop-mobile --slug SLUG            # 4:5 centre crop of SLUG-hero.jpg
    python3 tools/blog-images.py crop-mobile --slug SLUG --source clean-photo.jpg   # if the hero has text on it
    python3 tools/blog-images.py story --slug SLUG --title ... --answer ... --sub ...
    python3 tools/blog-images.py pin   --slug SLUG --title ... --answer ... --sub ...

House style (do not drift): charcoal #171717 ground with a warm glow, gold
(212,183,134) line-art diamonds, cream (244,239,230) Didot headline, gold Didot
italic answer line, Georgia small caps eyebrow, a hairline frame inset 40px.
Requires Pillow (pip3 install --user Pillow). Uses macOS system Didot and Georgia.
"""
import argparse, math, pathlib, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "blog"
DIDOT = "/System/Library/Fonts/Supplemental/Didot.ttc"
GEORGIA = "/System/Library/Fonts/Supplemental/Georgia.ttf"

GOLD = (212, 183, 134)
CREAM = (244, 239, 230)
INK = (23, 23, 23)
WARM = (64, 54, 42)
S = 2  # supersample factor for clean line-art


class Canvas:
    def __init__(self, w, h, glow_cx=0.5, glow_cy=0.42):
        self.W, self.H = w * S, h * S
        self.img = Image.new("RGB", (self.W, self.H), INK)
        glow = Image.new("L", (self.W, self.H), 0)
        gd = ImageDraw.Draw(glow)
        cx, cy = self.W * glow_cx, self.H * glow_cy
        R0 = max(self.W, self.H) * 0.7
        for r in range(int(R0), 0, -8):
            a = int(72 * (1 - r / R0) ** 1.6)
            gd.ellipse([cx - r * 1.2, cy - r * 0.8, cx + r * 1.2, cy + r * 0.8], fill=a)
        glow = glow.filter(ImageFilter.GaussianBlur(45))
        self.img = Image.composite(Image.new("RGB", (self.W, self.H), WARM), self.img, glow)
        self.d = ImageDraw.Draw(self.img, "RGBA")
        self.lw = 3 * S

    # --- line art -------------------------------------------------------
    def diamond(self, fx, fy, w, alpha=255):
        d, lw = self.d, self.lw
        cx, cy, w = self.W * fx, self.H * fy, w * S
        col, dim = (*GOLD, alpha), (*GOLD, int(alpha * 0.55))
        tw, ch, ph = w * 0.55, w * 0.30, w * 0.95
        tl, tr = (cx - tw / 2, cy - ch), (cx + tw / 2, cy - ch)
        gl, gr, tip = (cx - w / 2, cy), (cx + w / 2, cy), (cx, cy + ph)
        d.polygon([tl, tr, gr, tip, gl], outline=col, width=lw)
        for i in range(5):
            d.line([(tl[0] + (tr[0] - tl[0]) * i / 4, tl[1]), (gl[0] + (gr[0] - gl[0]) * i / 4, cy)], fill=dim, width=lw - S)
        d.line([gl, gr], fill=col, width=lw)
        for i in range(1, 4):
            d.line([(gl[0] + (gr[0] - gl[0]) * i / 3, cy), tip], fill=dim, width=lw - S)

    def round_top(self, fx, fy, r, alpha=255):
        d, lw = self.d, self.lw
        cx, cy, r = self.W * fx, self.H * fy, r * S
        col, dim, n = (*GOLD, alpha), (*GOLD, int(alpha * 0.55)), 16
        outer = [(cx + r * math.cos(2 * math.pi * i / n - math.pi / 2), cy + r * math.sin(2 * math.pi * i / n - math.pi / 2)) for i in range(n)]
        inner = [(cx + r * .52 * math.cos(2 * math.pi * (i + .5) / 8 - math.pi / 2), cy + r * .52 * math.sin(2 * math.pi * (i + .5) / 8 - math.pi / 2)) for i in range(8)]
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=lw)
        d.polygon(inner, outline=col, width=lw - S)
        for i in range(8):
            for k in (0, 1, 2):
                d.line([outer[(i * 2 + k) % n], inner[i]], fill=dim, width=lw - S)

    def sparkles(self, pts):
        for fx, fy, r in pts:
            cx, cy, r = self.W * fx, self.H * fy, r * S
            col = (240, 228, 205, 200)
            self.d.line([(cx - r, cy), (cx + r, cy)], fill=col, width=S)
            self.d.line([(cx, cy - r), (cx, cy + r)], fill=col, width=S)
            self.d.line([(cx - r * .4, cy - r * .4), (cx + r * .4, cy + r * .4)], fill=col, width=S)
            self.d.line([(cx - r * .4, cy + r * .4), (cx + r * .4, cy - r * .4)], fill=col, width=S)

    def frame(self):
        m = 40 * S
        self.d.rectangle([m, m, self.W - m, self.H - m], outline=(*GOLD, 60), width=S)

    # --- type -----------------------------------------------------------
    def font(self, which, px):
        if which == "didot":   return ImageFont.truetype(DIDOT, px * S, index=0)
        if which == "didot_i": return ImageFont.truetype(DIDOT, px * S, index=1)
        return ImageFont.truetype(GEORGIA, px * S)

    def center(self, text, fy, font, fill):
        self.d.text((self.W / 2, self.H * fy), text, font=font, fill=fill, anchor="mm")

    def spaced(self, text, fy, font, fill, spacing):
        widths = [self.d.textlength(ch, font=font) for ch in text]
        x = (self.W - (sum(widths) + spacing * S * (len(text) - 1))) / 2
        for ch, w in zip(text, widths):
            self.d.text((x, self.H * fy), ch, font=font, fill=fill, anchor="lm")
            x += w + spacing * S

    def hairline(self, fy, half=0.10):
        self.d.line([(self.W * (.5 - half), self.H * fy), (self.W * (.5 + half), self.H * fy)], fill=(*GOLD, 255), width=S)

    def pill(self, label, fy, w=420, h=76):
        pw, ph = w * S, h * S
        px, py = (self.W - pw) / 2, self.H * fy - ph / 2
        self.d.rounded_rectangle([px, py, px + pw, py + ph], radius=ph / 2, outline=(*GOLD, 255), width=2 * S)
        self.spaced(label, fy, self.font("georgia", 26), CREAM, 5)

    def dim(self, alpha=150):
        ov = Image.new("RGBA", self.img.size, (15, 15, 15, alpha))
        self.img = Image.alpha_composite(self.img.convert("RGBA"), ov).convert("RGB")
        self.d = ImageDraw.Draw(self.img, "RGBA")

    def save(self, path, w, h, q=80):
        self.img.resize((w, h), Image.LANCZOS).save(path, quality=q, optimize=True, progressive=True)
        print("wrote", path.relative_to(ROOT), f"{path.stat().st_size // 1024} KB")


def title_lines(c, lines, fy0, size, gap):
    for i, line in enumerate(lines):
        c.center(line, fy0 + i * gap, c.font("didot", size), CREAM)


# --- compositions -------------------------------------------------------
def hero(slug):
    c = Canvas(1600, 900)
    c.round_top(0.32, 0.44, 190)
    c.diamond(0.62, 0.38, 230)
    c.diamond(0.78, 0.42, 150, 190)
    c.diamond(0.52, 0.47, 100, 150)
    c.diamond(0.96, 0.30, 340, 45)
    c.round_top(0.08, 0.92, 220, 45)
    c.sparkles([(.24, .22, 14), (.44, .62, 10), (.70, .18, 16), (.86, .62, 11), (.57, .24, 9), (.12, .55, 12), (.92, .80, 9)])
    c.frame()
    c.save(OUT / f"{slug}-hero.jpg", 1600, 900, 78)
    return c.img.resize((1600, 900), Image.LANCZOS)


def hero_mobile(slug):
    c = Canvas(1080, 1350, glow_cy=0.45)
    c.round_top(0.50, 0.36, 300)
    c.diamond(0.22, 0.70, 170, 200)
    c.diamond(0.78, 0.70, 170, 200)
    c.diamond(0.50, 0.78, 120, 150)
    c.diamond(1.02, 0.12, 300, 40)
    c.round_top(-0.05, 1.0, 260, 40)
    c.sparkles([(.18, .18, 14), (.82, .22, 18), (.12, .50, 11), (.88, .48, 12), (.30, .92, 10), (.72, .95, 9), (.50, .08, 11)])
    c.frame()
    c.save(OUT / f"{slug}-hero-mobile.jpg", 1080, 1350, 78)


def og(slug, title, hero_img):
    src = hero_img.crop((100, 60, 1540, 816)).resize((1200, 630), Image.LANCZOS)
    c = Canvas(1200, 630)
    c.img = src; c.d = ImageDraw.Draw(c.img, "RGBA")
    c.W, c.H = 1200, 630
    global S; S_prev = S
    # the OG canvas is composed at 1x on top of the rendered hero, so scale text helpers accordingly
    S = 1
    c.dim(170)
    c.spaced("THE RING MINT JOURNAL", 0.20, ImageFont.truetype(GEORGIA, 24), GOLD, 4)
    n = len(title)
    size = 74 if n <= 2 else 62
    gap = 0.15 if n <= 2 else 0.125
    fy0 = 0.49 - (n - 1) * gap / 2
    for i, line in enumerate(title):
        c.d.text((600, 630 * (fy0 + i * gap)), line, font=ImageFont.truetype(DIDOT, size, index=0), fill=CREAM, anchor="mm")
    c.d.line([(510, 630 * 0.80), (690, 630 * 0.80)], fill=GOLD, width=2)
    c.d.text((600, 630 * 0.88), "ringmint.com", font=ImageFont.truetype(GEORGIA, 24), fill=(190, 180, 165), anchor="mm")
    S = S_prev
    c.img.save(OUT / f"{slug}-og.jpg", quality=80, optimize=True, progressive=True)
    print("wrote", f"assets/blog/{slug}-og.jpg")


def card(slug, hero_img):
    hero_img.crop((160, 75, 1440, 875)).resize((800, 500), Image.LANCZOS).save(OUT / f"{slug}-card.jpg", quality=78, optimize=True, progressive=True)
    print("wrote", f"assets/blog/{slug}-card.jpg")


def story(slug, title, answer, sub):
    c = Canvas(1080, 1920, glow_cy=0.40)
    c.round_top(0.12, 0.16, 300, 50)
    c.diamond(0.50, 0.29, 250)
    c.diamond(0.24, 0.32, 130, 170)
    c.diamond(0.77, 0.31, 150, 190)
    c.diamond(0.96, 0.80, 360, 30)
    c.sparkles([(.30, .20, 14), (.68, .17, 18), (.86, .24, 11), (.12, .42, 12), (.62, .44, 10), (.14, .72, 12), (.86, .60, 9), (.40, .90, 11)])
    c.frame()
    c.spaced("THE RING MINT JOURNAL", 0.505, c.font("georgia", 26), GOLD, 7)
    n = len(title)
    title_lines(c, title, 0.615 - (n - 1) * 0.05 / 2, 84, 0.05)
    c.hairline(0.715)
    c.center(answer, 0.757, c.font("didot_i", 52), GOLD)
    for i, line in enumerate(sub):
        c.center(line, 0.815 + i * 0.03, c.font("georgia", 30), (200, 190, 175))
    c.pill("READ THE POST", 0.895)
    c.center("ringmint.com", 0.94, c.font("georgia", 24), (150, 140, 125))
    c.save(OUT / f"{slug}-story.jpg", 1080, 1920, 85)


def pin(slug, title, answer, sub):
    # Pinterest's preferred 2:3. Same composition language as the Story, but no
    # Instagram UI safe zones, so the type sits higher and larger.
    c = Canvas(1000, 1500, glow_cy=0.36)
    c.round_top(0.50, 0.27, 250)
    c.diamond(0.22, 0.31, 130, 170)
    c.diamond(0.78, 0.30, 150, 190)
    c.diamond(0.97, 0.84, 320, 30)
    c.round_top(0.04, 0.04, 220, 40)
    c.sparkles([(.30, .16, 14), (.68, .13, 18), (.88, .22, 11), (.10, .40, 12), (.62, .42, 10), (.14, .70, 12), (.88, .58, 9), (.40, .93, 11)])
    c.frame()
    c.spaced("THE RING MINT JOURNAL", 0.475, c.font("georgia", 24), GOLD, 6)
    n = len(title)
    title_lines(c, title, 0.585 - (n - 1) * 0.055 / 2, 76, 0.055)
    c.hairline(0.695)
    c.center(answer, 0.740, c.font("didot_i", 48), GOLD)
    for i, line in enumerate(sub):
        c.center(line, 0.800 + i * 0.032, c.font("georgia", 28), (200, 190, 175))
    c.pill("READ THE POST", 0.885, w=380, h=70)
    c.center("ringmint.com", 0.935, c.font("georgia", 24), (150, 140, 125))
    c.save(OUT / f"{slug}-pin.jpg", 1000, 1500, 82)


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
    out.save(OUT / f"{slug}-hero-mobile.jpg", quality=80, optimize=True, progressive=True)
    print("wrote", f"assets/blog/{slug}-hero-mobile.jpg", out.size)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["generate", "story", "pin", "crop-mobile"])
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", help="headline, lines separated by |, 2 or 3 lines")
    ap.add_argument("--answer", help="one short line, gold italic (story and pin)")
    ap.add_argument("--sub", default="", help="one or two supporting lines separated by | (story and pin)")
    ap.add_argument("--source", help="crop-mobile only: a clean photo in assets/blog/ to crop instead of SLUG-hero.jpg")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    title = a.title.split("|") if a.title else []
    sub = [s for s in a.sub.split("|") if s]
    if a.mode == "crop-mobile":
        return crop_mobile(a.slug, a.source)
    if not title:
        sys.exit("--title is required")
    if a.mode == "generate":
        h = hero(a.slug)
        hero_mobile(a.slug)
        og(a.slug, title, h)
        card(a.slug, h)
    if not a.answer:
        sys.exit("--answer is required for the story and pin images")
    if a.mode in ("generate", "story"):
        story(a.slug, title, a.answer, sub)
    if a.mode in ("generate", "pin"):
        pin(a.slug, title, a.answer, sub)


if __name__ == "__main__":
    main()
