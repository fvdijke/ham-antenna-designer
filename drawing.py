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


def _svg_from_scene(scene: Scene) -> svgwrite.Drawing:
    dwg = _new_drawing(scene.width, scene.height)
    _add_arrow_marker(dwg)

    for x1, y1, x2, y2, width, dashed in scene.lines:
        kwargs = dict(stroke="black", stroke_width=width)
        if dashed:
            kwargs["stroke_dasharray"] = "4,2" if width >= 1 else "2,2"
        dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), **kwargs))

    for points, width in scene.polygons:
        dwg.add(dwg.polygon(points=points, stroke="black", fill="none", stroke_width=width))

    for x, y, r in scene.dots:
        dwg.add(dwg.circle(center=(x, y), r=r, fill="black"))

    for x1, y1, x2, y2 in scene.dim_lines:
        dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), stroke="black", stroke_width=0.5,
                          marker_start="url(#arrow)", marker_end="url(#arrow)"))

    for x, y, text, size, bold in scene.texts:
        dwg.add(dwg.text(text, insert=(x, y), font_size=str(size), font_family="sans-serif",
                          font_weight="bold" if bold else "normal"))

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
    return parser


if __name__ == "__main__":
    import calculators  # noqa: F401
    from registry import design as design_fn

    args = _build_argparser().parse_args()
    out_path = args.out or f"{args.antenna_type}_{args.band}.svg"

    d = design_fn(args.antenna_type, args.band, lang=args.lang)
    dwg = draw_antenna(d, units=args.units, lang=args.lang)
    dwg.saveas(out_path)
    print(f"Saved drawing to {out_path}")
