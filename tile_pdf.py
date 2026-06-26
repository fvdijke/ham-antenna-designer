"""Tile a scaled drawing of an antenna's primary radiator element across
printable pages, true to scale.

This is the "print-and-build" pipeline for the one part of any antenna design
that genuinely benefits from a 1:1 paper template: the radiator element(s) you
want to mark and cut precisely. Print every page at 100% scale (no "fit to
page"), trim to the overlap strip, and tape adjacent pages together using the
alignment marks -- then mark the cut length straight off the taped sheet.

Radials and counterpoises are NOT tiled: they're loose wire laid on the
ground/buried, normally cut with a tape measure rather than a paper template.
A full 1:1 template of e.g. a vertical mast plus 4 long ground radials would
be a 5m x 10m canvas -- 1000+ A4 pages -- which defeats the point of a
*practical* build aid. Those lengths are covered in build_notes.py instead.
"""

import math

from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from data_store import antenna_type_label
from i18n import TILE_PDF as TEXT
from models import AntennaDesign

PAGE_SIZES = {"a4": A4, "letter": LETTER}

OVERLAP_MM = 10.0  # shared strip between adjacent tiles, for taping alignment
PRINT_MARGIN_MM = 8.0  # unprintable margin most home printers need


def _length_label(length_m: float, length_ft: float, units: str) -> str:
    return f"{length_m:.2f} m" if units == "metric" else f"{length_ft:.2f} ft"


def tile_radiator(design: AntennaDesign, out_path: str, page: str = "a4", units: str = "metric", lang: str = "en") -> int:
    """Render the design's primary radiator element as a tiled, true-to-scale PDF.

    If the design has multiple equal-length radiator elements (e.g. dipole
    legs), one template is produced and the page notes say how many to cut.
    """
    if page not in PAGE_SIZES:
        raise ValueError(f"Unknown page size '{page}'. Choose from: {', '.join(PAGE_SIZES)}")
    if lang not in TEXT:
        raise ValueError(f"Unknown language '{lang}'. Choose from: {', '.join(TEXT)}")
    t = TEXT[lang]

    radiators = design.elements_with_role("radiator")
    if not radiators:
        raise ValueError("Design has no radiator element to tile")
    radiator = radiators[0]
    other_elements = [e for e in design.elements if e.role != "radiator"]

    page_w_pt, page_h_pt = PAGE_SIZES[page]
    page_w_mm = page_w_pt / mm
    page_h_mm = page_h_pt / mm
    usable_w_mm = page_w_mm - 2 * PRINT_MARGIN_MM
    usable_h_mm = page_h_mm - 2 * PRINT_MARGIN_MM
    tile_step_x = usable_w_mm - OVERLAP_MM
    tile_step_y = usable_h_mm - OVERLAP_MM

    element_mm = radiator.length_m * 1000.0
    drawing_margin_mm = 30.0
    canvas_w_mm = drawing_margin_mm * 2 + 40.0  # narrow strip -- a single straight element
    canvas_h_mm = element_mm + drawing_margin_mm * 2

    base_x = canvas_w_mm / 2
    base_y = canvas_h_mm - drawing_margin_mm
    top_y = base_y - element_mm

    cols = max(1, math.ceil(canvas_w_mm / tile_step_x))
    rows = max(1, math.ceil(canvas_h_mm / tile_step_y))

    c = canvas.Canvas(out_path, pagesize=(page_w_pt, page_h_pt))
    length_label = _length_label(radiator.length_m, radiator.length_ft, units)

    for row in range(rows):
        for col in range(cols):
            tile_origin_x = col * tile_step_x
            tile_origin_y = row * tile_step_y

            c.saveState()
            c.translate(PRINT_MARGIN_MM * mm - tile_origin_x * mm, PRINT_MARGIN_MM * mm - tile_origin_y * mm)

            y_top_flipped = (canvas_h_mm - top_y) * mm
            y_base_flipped = (canvas_h_mm - base_y) * mm

            c.setLineWidth(2)
            c.line(base_x * mm, y_base_flipped, base_x * mm, y_top_flipped)
            c.setLineWidth(0.5)
            c.circle(base_x * mm, y_base_flipped, 1.5 * mm, fill=1)  # feedpoint/end marker

            tick_m = 0
            while tick_m * 1000 <= element_mm:
                y_tick = (canvas_h_mm - (base_y - tick_m * 1000)) * mm
                c.line((base_x - 3) * mm, y_tick, (base_x + 3) * mm, y_tick)
                c.setFont("Helvetica", 5)
                c.drawString((base_x + 4) * mm, y_tick - 1.5 * mm, f"{tick_m:.1f}m")
                tick_m += 0.5

            c.setFont("Helvetica", 7)
            c.drawString((base_x + 12) * mm, (y_top_flipped + y_base_flipped) / 2, t["element_label"].format(length=length_label))

            c.restoreState()

            c.setFont("Helvetica", 6)
            c.drawString(2 * mm, (page_h_mm - 5) * mm, t["tile_label"].format(row=row + 1, rows=rows, col=col + 1, cols=cols))
            c.rect(0, 0, OVERLAP_MM * mm, page_h_pt, stroke=1, fill=0)
            c.rect(0, 0, page_w_pt, OVERLAP_MM * mm, stroke=1, fill=0)

            if row == 0 and col == 0:
                label = antenna_type_label(design.antenna_type, lang)
                c.setFont("Helvetica-Bold", 8)
                c.drawString(2 * mm, (page_h_mm - 12) * mm, t["title"].format(label=label, band=design.band))
                c.setFont("Helvetica", 6)
                y_note = page_h_mm - 16
                if len(radiators) > 1:
                    c.drawString(2 * mm, y_note * mm, t["cut_count_note"].format(count=len(radiators)))
                    y_note -= 4
                if other_elements:
                    detail = ", ".join(
                        f"{e.name} ({_length_label(e.length_m, e.length_ft, units)})" for e in other_elements
                    )
                    c.drawString(2 * mm, y_note * mm, t["other_elements_note"].format(detail=detail))

            c.showPage()

    c.save()
    return rows * cols


def _build_argparser():
    import argparse

    from data_store import BANDS_MHZ
    from registry import REGISTRY

    parser = argparse.ArgumentParser(description="Tile a true-to-scale print template of an antenna's radiator element")
    parser.add_argument("antenna_type", nargs="?", default="vertical_quarter_wave", help=f"One of: {', '.join(REGISTRY)}")
    parser.add_argument("band", nargs="?", default="20m", help=f"HAM band, one of: {', '.join(BANDS_MHZ)}")
    parser.add_argument("out", nargs="?", default=None, help="Output PDF path")
    parser.add_argument("--page", choices=list(PAGE_SIZES), default="a4", help="Page size (default: a4)")
    parser.add_argument("--units", choices=["metric", "imperial"], default="metric")
    parser.add_argument("--lang", choices=list(TEXT), default="en", help="Language for printed labels (default: en)")
    return parser


if __name__ == "__main__":
    import calculators  # noqa: F401
    from registry import design as design_fn

    args = _build_argparser().parse_args()
    out_path = args.out or f"{args.antenna_type}_{args.band}_template.pdf"

    d = design_fn(args.antenna_type, args.band, lang=args.lang)
    tile_count = tile_radiator(d, out_path, page=args.page, units=args.units, lang=args.lang)
    t = TEXT[args.lang]
    print(t["saved"].format(tiles=tile_count, path=out_path))
    print(t["print_hint"])
