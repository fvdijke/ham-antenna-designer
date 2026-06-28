"""SVG drawing generator for antenna designs (black-on-white, for file export
and printing).

NOT true-to-scale: each drawing is scaled (uniformly, so relative proportions
between elements within one drawing stay correct) to fit a fixed target
canvas size, so a 5m vertical and a 22m loop both render at a similar,
reasonable on-screen size instead of wildly different physical dimensions.
There is no print-template feature in this tool -- these are diagrams for
understanding the layout, not 1:1 build templates.

The actual geometry (where every line/label goes) lives in scene.py, shared
with canvas_view.py's in-app dark/amber viewer -- this module just renders
that geometry to SVG.
"""

import svgwrite

from models import AntennaDesign
from scene import Scene, build_scene


def _new_drawing(width: float, height: float) -> svgwrite.Drawing:
    return svgwrite.Drawing(size=(width, height), viewBox=f"0 0 {width} {height}")


def _add_arrow_marker(dwg: svgwrite.Drawing):
    marker = dwg.marker(insert=(2, 2), size=(4, 4), orient="auto", id="arrow")
    marker.add(dwg.path(d="M0,0 L4,2 L0,4 Z", fill="black"))
    dwg.defs.add(marker)


_LINE_STROKE_BY_KIND = {
    "element": "black",     # the main radiating wire -- drawn darkest/boldest
    "radial": "#777777",    # radials/counterpoise -- lighter gray, secondary to the element
    "reference": "#bbbbbb",  # ground line etc. -- faint, not a real wire
}


def _svg_from_scene(scene: Scene) -> svgwrite.Drawing:
    dwg = _new_drawing(scene.width, scene.height)
    _add_arrow_marker(dwg)

    for x1, y1, x2, y2, width, dashed, kind in scene.lines:
        kwargs = dict(stroke=_LINE_STROKE_BY_KIND.get(kind, "black"), stroke_width=width)
        if dashed:
            kwargs["stroke_dasharray"] = "4,2" if width >= 1 else "2,2"
        dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), **kwargs))

    for points, width in scene.polygons:
        dwg.add(dwg.polygon(points=points, stroke="black", fill="none", stroke_width=width))

    for x1, y1, x2, y2 in scene.dim_lines:
        dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), stroke="black", stroke_width=0.5,
                          marker_start="url(#arrow)", marker_end="url(#arrow)"))

    for x, y, text, size, bold, align in scene.texts:
        kwargs = {"text_anchor": "end"} if align == "right" else {}
        dwg.add(dwg.text(text, insert=(x, y), font_size=str(size), font_family="sans-serif",
                          font_weight="bold" if bold else "normal", **kwargs))

    # Feedpoint: filled dot + an outline ring, so it reads as "the feed"
    # rather than a generic junction point.
    for x, y, r in scene.feed_points:
        dwg.add(dwg.circle(center=(x, y), r=r, fill="black"))
        dwg.add(dwg.circle(center=(x, y), r=r + 3, fill="none", stroke="black", stroke_width=0.75))

    # Balun/unun/choke: a leader line from the feedpoint to a small
    # component-box symbol carrying the label, like a real schematic.
    for feed_x, feed_y, box_x, box_y, text in scene.balun_boxes:
        dwg.add(dwg.line(start=(feed_x, feed_y), end=(box_x, box_y), stroke="black", stroke_width=0.75, stroke_dasharray="2,2"))
        box_w = len(text) * 7.0 * 0.62 + 10
        box_h = 7.0 * 1.8
        dwg.add(dwg.rect(insert=(box_x - 4, box_y - box_h / 2), size=(box_w, box_h),
                          fill="white", stroke="black", stroke_width=0.75))
        dwg.add(dwg.text(text, insert=(box_x, box_y + 2.5), font_size="7", font_family="sans-serif", font_weight="bold"))

    # Core/shield tags, boxed like the balun -- bordered in that wire's own
    # stroke color (black for core/"element", gray for shield/"radial"),
    # with the same dashed leader line back to the point being labeled.
    for anchor_x, anchor_y, box_x, box_y, text, kind in scene.tag_boxes:
        stroke = _LINE_STROKE_BY_KIND.get("element" if kind == "core" else "radial", "black")
        dwg.add(dwg.line(start=(anchor_x, anchor_y), end=(box_x, box_y), stroke=stroke, stroke_width=0.75, stroke_dasharray="2,2"))
        box_w = len(text) * 7.0 * 0.62 + 10
        box_h = 7.0 * 1.8
        dwg.add(dwg.rect(insert=(box_x - 4, box_y - box_h / 2), size=(box_w, box_h),
                          fill="white", stroke=stroke, stroke_width=1.0))
        dwg.add(dwg.text(text, insert=(box_x, box_y + 2.5), font_size="7", font_family="sans-serif", font_weight="bold"))

    return dwg


def draw_antenna(design: AntennaDesign, units: str = "metric", lang: str = "en", margin_mm: float = 50.0) -> svgwrite.Drawing:
    scene = build_scene(design, units=units, lang=lang, margin=margin_mm)
    return _svg_from_scene(scene)


def _build_argparser():
    import argparse

    from data_store import BANDS_MHZ
    from registry import REGISTRY

    parser = argparse.ArgumentParser(description="Generate an SVG diagram of an antenna design (not true-to-scale)")
    parser.add_argument("antenna_type", nargs="?", default="vertical_quarter_wave", help=f"One of: {', '.join(REGISTRY)}")
    parser.add_argument("band", nargs="?", default="20m", help=f"HAM band, one of: {', '.join(BANDS_MHZ)}")
    parser.add_argument("out", nargs="?", default=None, help="Output SVG path")
    parser.add_argument("--units", choices=["metric", "imperial"], default="metric")
    parser.add_argument("--lang", choices=["en", "nl"], default="en")
    parser.add_argument("--freq", type=float, default=None, dest="freq_mhz",
                         help="Custom design frequency in MHz, overriding the band's default")
    return parser


if __name__ == "__main__":
    import calculators  # noqa: F401
    from registry import design as design_fn

    args = _build_argparser().parse_args()
    out_path = args.out or f"{args.antenna_type}_{args.band}.svg"

    d = design_fn(args.antenna_type, args.band, lang=args.lang, freq_mhz=args.freq_mhz)
    dwg = draw_antenna(d, units=args.units, lang=args.lang)
    dwg.saveas(out_path)
    print(f"Saved drawing to {out_path}")
