"""Scaled SVG drawing generator for antenna designs.

Build-template quality: the SVG embeds real-world units (mm) via width/height
and viewBox, so it prints true-to-scale at 1mm = 1 SVG user unit. Dimension
callouts use leader lines + arrowheads with inline length labels, per the
design doc's documented convention.
"""

import math

import svgwrite

MM_PER_M = 1000.0
MM_PER_FT = 304.8


def _fmt_length(value_m: float, units: str) -> str:
    if units == "metric":
        return f"{value_m:.2f} m"
    feet = value_m / 0.3048
    return f"{feet:.2f} ft"


def draw_vertical(design, units: str = "metric", margin_mm: float = 50.0) -> svgwrite.Drawing:
    """Draw a ground-mounted quarter-wave vertical with N radials, to true scale.

    design: a VerticalDesign from antenna_calc.design_vertical()
    units: "metric" or "imperial" -- controls the printed labels only;
           the underlying drawing is always scaled in mm.
    """
    element_mm = design.element_length_m * MM_PER_M
    radial_mm = design.radial_length_m * MM_PER_M

    # Canvas: tall enough for the vertical element plus margin, wide enough
    # for radials laid out left/right of the base plus margin.
    height_mm = element_mm + margin_mm * 2
    width_mm = radial_mm * 2 + margin_mm * 2

    dwg = svgwrite.Drawing(
        size=(f"{width_mm}mm", f"{height_mm}mm"),
        viewBox=f"0 0 {width_mm} {height_mm}",
    )

    # Define an arrowhead marker for dimension leader lines.
    marker = dwg.marker(insert=(2, 2), size=(4, 4), orient="auto", id="arrow")
    marker.add(dwg.path(d="M0,0 L4,2 L0,4 Z", fill="black"))
    dwg.defs.add(marker)

    base_x = width_mm / 2
    base_y = height_mm - margin_mm
    top_y = base_y - element_mm

    # Ground line.
    dwg.add(dwg.line(
        start=(margin_mm / 2, base_y), end=(width_mm - margin_mm / 2, base_y),
        stroke="black", stroke_width=1, stroke_dasharray="4,2",
    ))

    # Vertical element.
    dwg.add(dwg.line(
        start=(base_x, base_y), end=(base_x, top_y),
        stroke="black", stroke_width=2,
    ))
    dwg.add(dwg.circle(center=(base_x, base_y), r=4, fill="black"))  # feedpoint marker

    # Vertical element dimension callout (offset to the right of the element).
    dim_x = base_x + 15
    dwg.add(dwg.line(
        start=(dim_x, base_y), end=(dim_x, top_y),
        stroke="black", stroke_width=0.5,
        marker_start="url(#arrow)",
        marker_end="url(#arrow)",
    ))
    dwg.add(dwg.text(
        f"Element: {_fmt_length(design.element_length_m, units)}",
        insert=(dim_x + 5, (base_y + top_y) / 2),
        font_size="8", font_family="sans-serif",
    ))

    # Radials, evenly spaced around the base (drawn flattened/fan-out for a 2D template).
    n = design.radial_count
    for i in range(n):
        angle_deg = (360.0 / n) * i
        angle_rad = math.radians(angle_deg)
        end_x = base_x + radial_mm * math.sin(angle_rad)
        end_y = base_y + radial_mm * math.cos(angle_rad) * 0.3  # flatten for page fit
        dwg.add(dwg.line(
            start=(base_x, base_y), end=(end_x, end_y),
            stroke="black", stroke_width=1,
        ))
        if i == 0:
            dwg.add(dwg.text(
                f"Radial x{n}: {_fmt_length(design.radial_length_m, units)} each",
                insert=(end_x + 5, end_y),
                font_size="8", font_family="sans-serif",
            ))

    # Feedpoint / balun label.
    dwg.add(dwg.text(
        f"Feedpoint: ~{design.feedpoint_impedance_ohms:.0f} ohms, {design.balun['type']} ({design.balun['ratio']})",
        insert=(margin_mm / 2, base_y + 12),
        font_size="8", font_family="sans-serif",
    ))
    dwg.add(dwg.text(
        f"{design.band} band -- design freq {design.design_freq_mhz} MHz",
        insert=(margin_mm / 2, margin_mm / 2),
        font_size="9", font_family="sans-serif", font_weight="bold",
    ))

    return dwg


def _build_argparser():
    import argparse
    from antenna_calc import BANDS_MHZ

    parser = argparse.ArgumentParser(description="Generate a scaled SVG drawing of a vertical antenna")
    parser.add_argument("band", nargs="?", default="20m", help=f"HAM band, one of: {', '.join(BANDS_MHZ)}")
    parser.add_argument("out", nargs="?", default=None, help="Output SVG path (default: vertical_<band>.svg)")
    parser.add_argument(
        "--units", choices=["metric", "imperial"], default="metric",
        help="Units for the printed dimension labels (default: metric)",
    )
    return parser


if __name__ == "__main__":
    from antenna_calc import design_vertical

    args = _build_argparser().parse_args()
    out_path = args.out or f"vertical_{args.band}.svg"

    d = design_vertical(args.band)
    dwg = draw_vertical(d, units=args.units)
    dwg.saveas(out_path)
    print(f"Saved scaled drawing to {out_path}")
