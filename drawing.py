"""SVG export of an antenna schematic, for saving and printing.

Uses the same model and label layout as the in-app viewer (schematic.py),
painted in the light "print" theme (a situation sketch: lawn, masts, copper
wire, blue counterpoise, black coax to the shack). NOT true to scale -- the
labels carry the calculated dimensions.
"""

from models import AntennaDesign
from schematic import build_model, layout
from schematic_render import THEMES, MeasureOnly, SvgPainter


class SvgDrawing:
    def __init__(self, svg: str):
        self.svg = svg

    def tostring(self) -> str:
        return self.svg

    def saveas(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + self.svg)


def draw_antenna(design: AntennaDesign, units: str = "metric", lang: str = "en", cable: str = None,
                 theme: str = "print", view: str = "2d") -> SvgDrawing:
    th = THEMES[theme]
    metrics = MeasureOnly(th)
    model = build_model(design, units=units, lang=lang, cable=cable)
    L = layout(design, model, view, metrics.measure, metrics.line_h, lang)
    painter = SvgPainter(th, L.width, L.height)
    th.paint(L, painter)
    return SvgDrawing(painter.svg())


def _build_argparser():
    import argparse

    from data_store import BANDS_MHZ
    from registry import REGISTRY

    parser = argparse.ArgumentParser(description="Save an antenna schematic as SVG (not true to scale)")
    parser.add_argument("antenna_type", nargs="?", default="vertical_quarter_wave", help=f"One of: {', '.join(REGISTRY)}")
    parser.add_argument("band", nargs="?", default="20m", help=f"Band, one of: {', '.join(BANDS_MHZ)}")
    parser.add_argument("out", nargs="?", default=None, help="Output SVG path")
    parser.add_argument("--units", choices=["metric", "imperial"], default="metric")
    parser.add_argument("--lang", choices=["en", "nl"], default="en")
    parser.add_argument("--theme", choices=list(THEMES), default="print")
    parser.add_argument("--view", choices=["2d", "3d"], default="2d")
    parser.add_argument("--freq", type=float, default=None, dest="freq_mhz",
                        help="Custom design frequency in MHz, overriding the band's default")
    return parser


if __name__ == "__main__":
    import calculators  # noqa: F401
    from registry import design as design_fn

    args = _build_argparser().parse_args()
    out_path = args.out or f"{args.antenna_type}_{args.band}.svg"
    d = design_fn(args.antenna_type, args.band, lang=args.lang, freq_mhz=args.freq_mhz)
    draw_antenna(d, units=args.units, lang=args.lang, theme=args.theme, view=args.view).saveas(out_path)
    print(f"Saved drawing to {out_path}")
