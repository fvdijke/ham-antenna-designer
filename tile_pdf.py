"""Tile a scaled drawing of the vertical mast element across printable pages,
true to scale.

This is the "print-and-build" pipeline for the one part of this antenna that
genuinely benefits from a 1:1 paper template: the vertical mast element, which
you want to mark and cut precisely. Print every page at 100% scale (no "fit to
page"), trim to the overlap strip, and tape adjacent pages together using the
alignment marks to line them up -- then mark the element length straight off
the taped sheet.

Radials are NOT tiled here: they are loose wire laid on the ground or buried,
normally cut with a tape measure rather than a paper template. A full 1:1
template of a vertical mast plus 4 long ground radials would be a 5m x 10m
canvas -- 1000+ A4 pages -- which defeats the point of a *practical* build aid.
Radial lengths are covered in build_notes.py instead.
"""

import math

from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from i18n import TILE_PDF as TEXT

PAGE_SIZES = {"a4": A4, "letter": LETTER}

OVERLAP_MM = 10.0  # shared strip between adjacent tiles, for taping alignment
PRINT_MARGIN_MM = 8.0  # unprintable margin most home printers need


def _length_label(value_m: float, value_ft: float, units: str) -> str:
    return f"{value_m:.2f} m" if units == "metric" else f"{value_ft:.2f} ft"


def tile_mast(design, out_path: str, page: str = "a4", units: str = "metric", lang: str = "en") -> int:
    """Render the vertical mast element ONLY as a tiled, true-to-scale PDF.

    design: a VerticalDesign from antenna_calc.design_vertical()
    page: "a4" or "letter"
    lang: "en" or "nl" -- controls printed text, not the geometry/scale
    """
    if page not in PAGE_SIZES:
        raise ValueError(f"Unknown page size '{page}'. Choose from: {', '.join(PAGE_SIZES)}")
    if lang not in TEXT:
        raise ValueError(f"Unknown language '{lang}'. Choose from: {', '.join(TEXT)}")
    t = TEXT[lang]

    page_w_pt, page_h_pt = PAGE_SIZES[page]
    page_w_mm = page_w_pt / mm
    page_h_mm = page_h_pt / mm
    usable_w_mm = page_w_mm - 2 * PRINT_MARGIN_MM
    usable_h_mm = page_h_mm - 2 * PRINT_MARGIN_MM
    tile_step_x = usable_w_mm - OVERLAP_MM
    tile_step_y = usable_h_mm - OVERLAP_MM

    element_mm = design.element_length_m * 1000.0
    drawing_margin_mm = 30.0
    canvas_w_mm = drawing_margin_mm * 2 + 40.0  # narrow strip -- the mast is a single vertical line
    canvas_h_mm = element_mm + drawing_margin_mm * 2

    base_x = canvas_w_mm / 2
    base_y = canvas_h_mm - drawing_margin_mm
    top_y = base_y - element_mm

    cols = max(1, math.ceil(canvas_w_mm / tile_step_x))
    rows = max(1, math.ceil(canvas_h_mm / tile_step_y))

    c = canvas.Canvas(out_path, pagesize=(page_w_pt, page_h_pt))
    length_label = _length_label(design.element_length_m, design.element_length_ft, units)

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
            c.circle(base_x * mm, y_base_flipped, 1.5 * mm, fill=1)  # base/feedpoint marker

            # Tick marks every 500mm along the mast for easy mid-length reference.
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
                c.setFont("Helvetica-Bold", 8)
                c.drawString(2 * mm, (page_h_mm - 12) * mm, t["title"].format(band=design.band))
                c.setFont("Helvetica", 6)
                radial_label = _length_label(design.radial_length_m, design.radial_length_ft, units)
                c.drawString(2 * mm, (page_h_mm - 16) * mm, t["radial_note"].format(count=design.radial_count, length=radial_label))

            c.showPage()

    c.save()
    return rows * cols


def _build_argparser():
    import argparse
    from antenna_calc import BANDS_MHZ

    parser = argparse.ArgumentParser(description="Tile a true-to-scale print template of the vertical mast element")
    parser.add_argument("band", nargs="?", default="20m", help=f"HAM band, one of: {', '.join(BANDS_MHZ)}")
    parser.add_argument("out", nargs="?", default=None, help="Output PDF path (default: vertical_<band>_mast_template.pdf)")
    parser.add_argument("--page", choices=list(PAGE_SIZES), default="a4", help="Page size (default: a4)")
    parser.add_argument("--units", choices=["metric", "imperial"], default="metric")
    parser.add_argument("--lang", choices=list(TEXT), default="en", help="Language for printed labels (default: en)")
    return parser


if __name__ == "__main__":
    from antenna_calc import design_vertical

    args = _build_argparser().parse_args()
    out_path = args.out or f"vertical_{args.band}_mast_template.pdf"

    d = design_vertical(args.band)
    tile_count = tile_mast(d, out_path, page=args.page, units=args.units, lang=args.lang)
    t = TEXT[args.lang]
    print(t["saved"].format(tiles=tile_count, path=out_path))
    print(t["print_hint"])
