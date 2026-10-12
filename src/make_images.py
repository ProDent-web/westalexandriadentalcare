#!/usr/bin/env python3
"""Generate favicon.svg, favicon PNGs, apple-touch-icon and the Open Graph image from the brand mark.
Run:  python3 src/make_images.py   (writes into src/assets/img/)
"""
import os, glob
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(ROOT, "assets", "img")
NAVY = (23, 52, 62); BLUE = (103, 171, 196); CREAM = (247, 242, 234); WHITE = (255, 255, 255); GOLD = (213, 173, 100)

MARK_PATHS = [
    ("M30 119 72 224l56-73 56 73 42-105", None, NAVY, 27, "round"),
    ("M118 79 78 183M138 79l40 104M102 136h52", None, BLUE, 21, "round"),
    ("M104 28c8-11 19-7 24 1 5-8 16-12 24-1 11 14 4 32-3 44-6 10-7 24-14 28-7 4-3-22-7-22s0 26-7 22c-7-4-8-18-14-28-7-12-14-30-3-44Z", WHITE, NAVY, 4, "round"),
    ("M63 87c-15-1-25-10-26-23 15-4 27 2 32 14 1 4-1 7-6 9ZM193 87c15-1 25-10 26-23-15-4-27 2-32 14-1 4 1 7 6 9Z", BLUE, None, 0, "round"),
]

def svg_mark(bg=None, pad=0):
    body = "".join(
        f'<path d="{d}" fill="{("#%02x%02x%02x" % f) if f else "none"}"' +
        (f' stroke="#{s[0]:02x}{s[1]:02x}{s[2]:02x}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"' if s else "") + "/>"
        for d, f, s, w, _ in MARK_PATHS)
    rect = f'<rect width="256" height="256" rx="56" fill="#{bg[0]:02x}{bg[1]:02x}{bg[2]:02x}"/>' if bg else ""
    inner = f'<g transform="translate({pad} {pad}) scale({(256-2*pad)/256})">{body}</g>' if pad else body
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">{rect}{inner}</svg>'

def find_font(names, size):
    dirs = ["/System/Library/Fonts", "/System/Library/Fonts/Supplemental", "/Library/Fonts", os.path.expanduser("~/Library/Fonts")]
    for n in names:
        for d in dirs:
            for p in glob.glob(os.path.join(d, n)):
                try: return ImageFont.truetype(p, size)
                except Exception: pass
    return ImageFont.load_default()

def render_mark_png(size, bg=None, scale=0.74):
    """Rasterize the mark with PIL (no cairo): draw simplified shapes at high res and downsample."""
    S = 1024
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    if bg:
        dr.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.22), fill=bg + (255,))
    k = S / 256 * scale; ox = (S - 256 * k) / 2; oy = (S - 256 * k) / 2 + S * 0.02
    P = lambda x, y: (ox + x * k, oy + y * k)
    # W stroke
    w = int(27 * k)
    pts = [P(30, 119), P(72, 224), P(128, 151), P(184, 224), P(226, 119)]
    dr.line(pts, fill=NAVY + (255,), width=w, joint="curve")
    for p in pts: dr.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=NAVY + (255,))
    # A strokes
    w2 = int(21 * k)
    for a, b in [((118, 79), (78, 183)), ((138, 79), (178, 183)), ((102, 136), (154, 136))]:
        pa, pb = P(*a), P(*b)
        dr.line([pa, pb], fill=BLUE + (255,), width=w2)
        for p in (pa, pb): dr.ellipse([p[0] - w2 / 2, p[1] - w2 / 2, p[0] + w2 / 2, p[1] + w2 / 2], fill=BLUE + (255,))
    # tooth (approximate with a polygon of the bezier outline)
    tooth = [(104, 28), (112, 20), (122, 22), (128, 29), (134, 22), (144, 20), (152, 28), (158, 40), (156, 55), (149, 72), (143, 85), (140, 97), (135, 100), (131, 90), (128, 78), (125, 90), (121, 100), (116, 97), (113, 85), (107, 72), (100, 55), (98, 40)]
    dr.polygon([P(*t) for t in tooth], fill=WHITE + (255,), outline=NAVY + (255,), width=int(4 * k))
    # leaves
    for pts_ in ([(63, 87), (50, 85), (40, 74), (37, 64), (50, 62), (62, 68), (69, 78)], [(193, 87), (206, 85), (216, 74), (219, 64), (206, 62), (194, 68), (187, 78)]):
        dr.polygon([P(*t) for t in pts_], fill=BLUE + (255,))
    return im.resize((size, size), Image.LANCZOS)

def main():
    os.makedirs(IMG, exist_ok=True)
    open(os.path.join(IMG, "favicon.svg"), "w").write(svg_mark())
    open(os.path.join(IMG, "logo-mark.svg"), "w").write(svg_mark())
    render_mark_png(512, bg=CREAM).save(os.path.join(IMG, "icon-512.png"))
    render_mark_png(192, bg=CREAM).save(os.path.join(IMG, "icon-192.png"))
    render_mark_png(180, bg=CREAM).save(os.path.join(IMG, "apple-touch-icon.png"))
    render_mark_png(32).save(os.path.join(IMG, "favicon-32.png"))
    # OG image 1200x630
    og = Image.new("RGB", (1200, 630), CREAM)
    dr = ImageDraw.Draw(og)
    # soft blobs
    blob = Image.new("RGBA", (1200, 630), (0, 0, 0, 0)); bd = ImageDraw.Draw(blob)
    bd.ellipse([760, -120, 1320, 420], fill=BLUE + (46,)); bd.ellipse([-160, 380, 360, 820], fill=GOLD + (40,))
    og.paste(Image.alpha_composite(og.convert("RGBA"), blob).convert("RGB"))
    dr = ImageDraw.Draw(og)
    mark = render_mark_png(300, scale=0.95)
    og.paste(mark, (96, 150), mark)
    serif = find_font(["Iowan Old Style*.ttc", "Georgia.ttf", "Palatino.ttc", "Times New Roman.ttf"], 74)
    sans = find_font(["Helvetica.ttc", "Arial.ttf", "SFNS.ttf"], 26)
    sans_b = find_font(["Helvetica.ttc", "Arial Bold.ttf", "Arial.ttf"], 24)
    dr.text((430, 170), "West Alexandria", font=serif, fill=NAVY)
    dr.text((430, 258), "Dental Care", font=serif, fill=NAVY)
    dr.line([(430, 352), (1080, 352)], fill=GOLD, width=2)
    dr.text((430, 372), "Complete care. One dental home.", font=sans, fill=(43, 125, 156))
    dr.text((430, 420), "Mon–Fri 7 AM–8 PM  ·  Sat–Sun 8 AM–1 PM  ·  703-560-7200", font=sans_b, fill=(86, 106, 113))
    dr.text((430, 456), "3543 W. Braddock Road, Suite E1, Alexandria, VA 22302", font=sans_b, fill=(86, 106, 113))
    og.save(os.path.join(IMG, "og.jpg"), quality=88)
    print("wrote favicon.svg, logo-mark.svg, icon-512.png, icon-192.png, apple-touch-icon.png, favicon-32.png, og.jpg")

if __name__ == "__main__":
    main()
