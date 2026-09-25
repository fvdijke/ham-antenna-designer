"""Render the HAM Antenna Designer logo (a Smith chart with the match point
in the centre) to PNG sizes, a Windows .ico and an SVG, into assets/.

Run once after changing the logo (needs Pillow): python tools/make_logo.py
The app itself only loads the generated files -- no Pillow at runtime.
"""

import os

from PIL import Image, ImageDraw

AMBER = (232, 150, 12, 255)   # #E8960C, as in the HAMIOS logo
NODE = (252, 231, 125, 255)   # #FCE77D
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets")

# geometry on a 120 x 120 grid: (kind, args, stroke width)
SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
<circle cx="60" cy="60" r="46" fill="none" stroke="#E8960C" stroke-width="4"/>
<path d="M14 60 L106 60" fill="none" stroke="#E8960C" stroke-width="3" stroke-linecap="round"/>
<circle cx="83" cy="60" r="23" fill="none" stroke="#E8960C" stroke-width="3"/>
<circle cx="95" cy="60" r="11" fill="none" stroke="#E8960C" stroke-width="2.4"/>
<path d="M106 60 A46 46 0 0 0 60 14" fill="none" stroke="#E8960C" stroke-width="3" stroke-linecap="round"/>
<path d="M106 60 A46 46 0 0 1 60 106" fill="none" stroke="#E8960C" stroke-width="3" stroke-linecap="round"/>
<circle cx="60" cy="60" r="5.5" fill="#FCE77D" stroke="#E8960C" stroke-width="3"/>
</svg>
"""


def render(size: int, boost: float = 1.0) -> Image.Image:
    """Draw at 8x and scale down (anti-aliasing). `boost` thickens the
    strokes for the tiny icon sizes so they stay visible."""
    k = size * 8 / 120
    img = Image.new("RGBA", (size * 8, size * 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def circle(cx, cy, r, w):
        d.ellipse([(cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k], outline=AMBER, width=round(w * k * boost))

    def arc(cx, cy, r, a0, a1, w):
        d.arc([(cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k], a0, a1, fill=AMBER, width=round(w * k * boost))

    circle(60, 60, 46, 4)
    d.line([14 * k, 60 * k, 106 * k, 60 * k], fill=AMBER, width=round(3 * k * boost))
    circle(83, 60, 23, 3)
    circle(95, 60, 11, 2.4)
    arc(106, 14, 46, 90, 180, 3)
    arc(106, 106, 46, 180, 270, 3)
    r = 5.5 * (1 + (boost - 1) * 0.5)
    d.ellipse([(60 - r) * k, (60 - r) * k, (60 + r) * k, (60 + r) * k], fill=NODE, outline=AMBER,
              width=round(3 * k * boost))
    return img.resize((size, size), Image.LANCZOS)


def main():
    os.makedirs(OUT, exist_ok=True)
    for s in (20, 32, 40, 64, 128, 256):
        render(s, boost=1.6 if s <= 32 else 1.25 if s <= 64 else 1.0).save(os.path.join(OUT, f"logo_{s}.png"))
    icon_sizes = [16, 20, 24, 32, 40, 48, 64, 128, 256]
    frames = [render(s, boost=1.8 if s <= 24 else 1.5 if s <= 48 else 1.0) for s in icon_sizes]
    frames[-1].save(os.path.join(OUT, "icon.ico"), sizes=[(s, s) for s in icon_sizes], append_images=frames[:-1])
    with open(os.path.join(OUT, "logo.svg"), "w", encoding="utf-8") as f:
        f.write(SVG)
    print("written to", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
