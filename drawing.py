"""Scaled SVG drawing generator for antenna designs.

Build-template quality: the SVG embeds real-world units (mm) via width/height
and viewBox, so it prints true-to-scale at 1mm = 1 SVG user unit. Dispatches
on AntennaDesign.geometry so each antenna type's calculator doesn't need to
know anything about rendering.
"""

import math

import svgwrite

from i18n import DRAWING
from models import AntennaDesign

MM_PER_M = 1000.0


def _fmt_length(value_m: float, units: str) -> str:
    if units == "metric":
        return f"{value_m:.2f} m"
    feet = value_m / 0.3048
    return f"{feet:.2f} ft"


def _add_arrow_marker(dwg: svgwrite.Drawing):
    marker = dwg.marker(insert=(2, 2), size=(4, 4), orient="auto", id="arrow")
    marker.add(dwg.path(d="M0,0 L4,2 L0,4 Z", fill="black"))
    dwg.defs.add(marker)


def _draw_vertical(design: AntennaDesign, units: str, lang: str, margin_mm: float) -> svgwrite.Drawing:
    t = DRAWING[lang]
    radiator = design.elements_with_role("radiator")[0]
    radials = design.elements_with_role("radial")
    element_mm = radiator.length_m * MM_PER_M
    radial_mm = (radials[0].length_m if radials else 0) * MM_PER_M

    height_mm = element_mm + margin_mm * 2
    width_mm = radial_mm * 2 + margin_mm * 2 if radials else element_mm * 0.6 + margin_mm * 2

    dwg = svgwrite.Drawing(size=(f"{width_mm}mm", f"{height_mm}mm"), viewBox=f"0 0 {width_mm} {height_mm}")
    _add_arrow_marker(dwg)

    base_x = width_mm / 2
    base_y = height_mm - margin_mm
    top_y = base_y - element_mm

    dwg.add(dwg.line(start=(margin_mm / 2, base_y), end=(width_mm - margin_mm / 2, base_y),
                      stroke="black", stroke_width=1, stroke_dasharray="4,2"))
    dwg.add(dwg.line(start=(base_x, base_y), end=(base_x, top_y), stroke="black", stroke_width=2))
    dwg.add(dwg.circle(center=(base_x, base_y), r=4, fill="black"))

    dim_x = base_x + 15
    dwg.add(dwg.line(start=(dim_x, base_y), end=(dim_x, top_y), stroke="black", stroke_width=0.5,
                      marker_start="url(#arrow)", marker_end="url(#arrow)"))
    dwg.add(dwg.text(t["element_label"].format(length=_fmt_length(radiator.length_m, units)),
                      insert=(dim_x + 5, (base_y + top_y) / 2), font_size="8", font_family="sans-serif"))

    n = len(radials)
    for i, radial in enumerate(radials):
        angle_rad = math.radians((360.0 / n) * i)
        end_x = base_x + radial_mm * math.sin(angle_rad)
        end_y = base_y + radial_mm * math.cos(angle_rad) * 0.3
        dwg.add(dwg.line(start=(base_x, base_y), end=(end_x, end_y), stroke="black", stroke_width=1))
        if i == 0:
            dwg.add(dwg.text(t["radial_label"].format(count=n, length=_fmt_length(radial.length_m, units)),
                              insert=(end_x + 5, end_y), font_size="8", font_family="sans-serif"))

    dwg.add(dwg.text(
        t["feedpoint_label"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}",
                                     balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]),
        insert=(margin_mm / 2, base_y + 12), font_size="8", font_family="sans-serif"))
    dwg.add(dwg.text(t["band_label"].format(band=design.band, freq=design.design_freq_mhz),
                      insert=(margin_mm / 2, margin_mm / 2), font_size="9", font_family="sans-serif", font_weight="bold"))
    return dwg


def _draw_horizontal_center_fed(design: AntennaDesign, units: str, lang: str, margin_mm: float) -> svgwrite.Drawing:
    """Dipole: two legs running left/right from a center feedpoint."""
    t = DRAWING[lang]
    leg_a, leg_b = design.elements_with_role("radiator")[:2]
    leg_mm = leg_a.length_m * MM_PER_M

    width_mm = leg_mm * 2 + margin_mm * 2
    height_mm = margin_mm * 2 + 20

    dwg = svgwrite.Drawing(size=(f"{width_mm}mm", f"{height_mm}mm"), viewBox=f"0 0 {width_mm} {height_mm}")
    _add_arrow_marker(dwg)

    center_x = width_mm / 2
    y = height_mm / 2
    left_x = center_x - leg_mm
    right_x = center_x + leg_mm

    dwg.add(dwg.line(start=(left_x, y), end=(right_x, y), stroke="black", stroke_width=2))
    dwg.add(dwg.circle(center=(center_x, y), r=4, fill="black"))

    dim_y = y + 15
    for x0, x1 in [(left_x, center_x), (center_x, right_x)]:
        dwg.add(dwg.line(start=(x0, dim_y), end=(x1, dim_y), stroke="black", stroke_width=0.5,
                          marker_start="url(#arrow)", marker_end="url(#arrow)"))
    dwg.add(dwg.text(t["element_label"].format(length=_fmt_length(leg_a.length_m, units)),
                      insert=(center_x + 5, dim_y + 10), font_size="8", font_family="sans-serif"))

    dwg.add(dwg.text(
        t["feedpoint_label"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}",
                                     balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]),
        insert=(margin_mm / 2, height_mm - margin_mm / 2), font_size="8", font_family="sans-serif"))
    dwg.add(dwg.text(t["band_label"].format(band=design.band, freq=design.design_freq_mhz),
                      insert=(margin_mm / 2, margin_mm / 2), font_size="9", font_family="sans-serif", font_weight="bold"))
    return dwg


def _draw_horizontal_end_fed(design: AntennaDesign, units: str, lang: str, margin_mm: float) -> svgwrite.Drawing:
    """EFHW: a single long radiator run from the feedpoint, plus a short
    counterpoise drawn dropping away from the feedpoint at the other end."""
    t = DRAWING[lang]
    radiator = design.elements_with_role("radiator")[0]
    counterpoise = design.elements_with_role("counterpoise")[0]
    radiator_mm = radiator.length_m * MM_PER_M
    counterpoise_mm = counterpoise.length_m * MM_PER_M

    width_mm = radiator_mm + margin_mm * 2
    height_mm = counterpoise_mm + margin_mm * 2 + 20

    dwg = svgwrite.Drawing(size=(f"{width_mm}mm", f"{height_mm}mm"), viewBox=f"0 0 {width_mm} {height_mm}")
    _add_arrow_marker(dwg)

    feed_x = margin_mm
    feed_y = margin_mm + 20
    end_x = feed_x + radiator_mm

    dwg.add(dwg.line(start=(feed_x, feed_y), end=(end_x, feed_y), stroke="black", stroke_width=2))
    dwg.add(dwg.circle(center=(feed_x, feed_y), r=4, fill="black"))

    dim_y = feed_y - 12
    dwg.add(dwg.line(start=(feed_x, dim_y), end=(end_x, dim_y), stroke="black", stroke_width=0.5,
                      marker_start="url(#arrow)", marker_end="url(#arrow)"))
    dwg.add(dwg.text(t["element_label"].format(length=_fmt_length(radiator.length_m, units)),
                      insert=((feed_x + end_x) / 2, dim_y - 5), font_size="8", font_family="sans-serif"))

    # Counterpoise drops straight down from the feedpoint.
    cp_end_y = feed_y + counterpoise_mm
    dwg.add(dwg.line(start=(feed_x, feed_y), end=(feed_x, cp_end_y), stroke="black", stroke_width=1, stroke_dasharray="2,2"))
    dwg.add(dwg.text(t["counterpoise_label"].format(length=_fmt_length(counterpoise.length_m, units)),
                      insert=(feed_x + 5, cp_end_y), font_size="8", font_family="sans-serif"))

    dwg.add(dwg.text(
        t["feedpoint_label"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}",
                                     balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]),
        insert=(margin_mm / 2, height_mm - margin_mm / 2), font_size="8", font_family="sans-serif"))
    dwg.add(dwg.text(t["band_label"].format(band=design.band, freq=design.design_freq_mhz),
                      insert=(margin_mm / 2, margin_mm / 2), font_size="9", font_family="sans-serif", font_weight="bold"))
    return dwg


def _draw_horizontal_loop(design: AntennaDesign, units: str, lang: str, margin_mm: float) -> svgwrite.Drawing:
    """Full-wave loop drawn as a square, fed at the midpoint of one side."""
    t = DRAWING[lang]
    wire = design.elements_with_role("radiator")[0]
    side_m = wire.length_m / 4
    side_mm = side_m * MM_PER_M

    size_mm = side_mm + margin_mm * 2
    dwg = svgwrite.Drawing(size=(f"{size_mm}mm", f"{size_mm}mm"), viewBox=f"0 0 {size_mm} {size_mm}")
    _add_arrow_marker(dwg)

    x0, y0 = margin_mm, margin_mm
    x1, y1 = margin_mm + side_mm, margin_mm + side_mm

    dwg.add(dwg.polygon(points=[(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                         stroke="black", fill="none", stroke_width=2))

    feed_x = (x0 + x1) / 2
    feed_y = y1
    dwg.add(dwg.circle(center=(feed_x, feed_y), r=4, fill="black"))

    dwg.add(dwg.text(t["loop_side_label"].format(length=_fmt_length(side_m, units), count=4),
                      insert=(x0, y0 - 5), font_size="8", font_family="sans-serif"))
    dwg.add(dwg.text(
        t["feedpoint_label"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}",
                                     balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]),
        insert=(margin_mm / 2, size_mm - margin_mm / 4), font_size="8", font_family="sans-serif"))
    dwg.add(dwg.text(t["band_label"].format(band=design.band, freq=design.design_freq_mhz),
                      insert=(margin_mm / 2, margin_mm / 2), font_size="9", font_family="sans-serif", font_weight="bold"))
    return dwg


def _draw_vertical_loop(design: AntennaDesign, units: str, lang: str, margin_mm: float) -> svgwrite.Drawing:
    """Vertical delta loop drawn as an equilateral-ish triangle, fed at the
    midpoint of the bottom side."""
    t = DRAWING[lang]
    wire = design.elements_with_role("radiator")[0]
    side_m = wire.length_m / 3
    side_mm = side_m * MM_PER_M

    width_mm = side_mm + margin_mm * 2
    height_mm = side_mm * 0.87 + margin_mm * 2  # equilateral triangle height ~= side * sin(60)

    dwg = svgwrite.Drawing(size=(f"{width_mm}mm", f"{height_mm}mm"), viewBox=f"0 0 {width_mm} {height_mm}")
    _add_arrow_marker(dwg)

    bottom_y = height_mm - margin_mm
    left_x = margin_mm
    right_x = margin_mm + side_mm
    apex_x = (left_x + right_x) / 2
    apex_y = margin_mm

    dwg.add(dwg.polygon(points=[(left_x, bottom_y), (right_x, bottom_y), (apex_x, apex_y)],
                         stroke="black", fill="none", stroke_width=2))

    feed_x = (left_x + right_x) / 2
    dwg.add(dwg.circle(center=(feed_x, bottom_y), r=4, fill="black"))

    dwg.add(dwg.text(t["loop_side_label"].format(length=_fmt_length(side_m, units), count=3),
                      insert=(left_x, bottom_y + 10), font_size="8", font_family="sans-serif"))
    dwg.add(dwg.text(
        t["feedpoint_label"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}",
                                     balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]),
        insert=(margin_mm / 2, height_mm - margin_mm / 4), font_size="8", font_family="sans-serif"))
    dwg.add(dwg.text(t["band_label"].format(band=design.band, freq=design.design_freq_mhz),
                      insert=(margin_mm / 2, margin_mm / 2), font_size="9", font_family="sans-serif", font_weight="bold"))
    return dwg


def _draw_inverted_v(design: AntennaDesign, units: str, lang: str, margin_mm: float) -> svgwrite.Drawing:
    """Inverted-V dipole: apex at top center, legs sloping down on each side."""
    import math as _math

    t = DRAWING[lang]
    leg_a, leg_b = design.elements_with_role("radiator")[:2]
    leg_mm = leg_a.length_m * MM_PER_M
    droop_deg = 30  # legs droop 30 degrees below horizontal, a common practical angle

    dx = leg_mm * math.cos(_math.radians(droop_deg))
    dy = leg_mm * math.sin(_math.radians(droop_deg))

    width_mm = dx * 2 + margin_mm * 2
    height_mm = dy + margin_mm * 2

    dwg = svgwrite.Drawing(size=(f"{width_mm}mm", f"{height_mm}mm"), viewBox=f"0 0 {width_mm} {height_mm}")
    _add_arrow_marker(dwg)

    apex_x = width_mm / 2
    apex_y = margin_mm
    left_x, left_y = apex_x - dx, apex_y + dy
    right_x, right_y = apex_x + dx, apex_y + dy

    dwg.add(dwg.line(start=(apex_x, apex_y), end=(left_x, left_y), stroke="black", stroke_width=2))
    dwg.add(dwg.line(start=(apex_x, apex_y), end=(right_x, right_y), stroke="black", stroke_width=2))
    dwg.add(dwg.circle(center=(apex_x, apex_y), r=4, fill="black"))

    dwg.add(dwg.text(t["element_label"].format(length=_fmt_length(leg_a.length_m, units)),
                      insert=(apex_x + 5, apex_y + dy / 2), font_size="8", font_family="sans-serif"))
    dwg.add(dwg.text(
        t["feedpoint_label"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}",
                                     balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]),
        insert=(margin_mm / 2, height_mm - margin_mm / 4), font_size="8", font_family="sans-serif"))
    dwg.add(dwg.text(t["band_label"].format(band=design.band, freq=design.design_freq_mhz),
                      insert=(margin_mm / 2, margin_mm / 2), font_size="9", font_family="sans-serif", font_weight="bold"))
    return dwg


def _draw_horizontal_off_center_fed(design: AntennaDesign, units: str, lang: str, margin_mm: float) -> svgwrite.Drawing:
    """OCF dipole: asymmetric legs running left/right from an off-center feedpoint."""
    t = DRAWING[lang]
    short_leg = design.elements_with_role("leg_short")[0]
    long_leg = design.elements_with_role("leg_long")[0]
    short_mm = short_leg.length_m * MM_PER_M
    long_mm = long_leg.length_m * MM_PER_M

    width_mm = short_mm + long_mm + margin_mm * 2
    height_mm = margin_mm * 2 + 20

    dwg = svgwrite.Drawing(size=(f"{width_mm}mm", f"{height_mm}mm"), viewBox=f"0 0 {width_mm} {height_mm}")
    _add_arrow_marker(dwg)

    feed_x = margin_mm + short_mm
    y = height_mm / 2
    left_x = margin_mm
    right_x = margin_mm + short_mm + long_mm

    dwg.add(dwg.line(start=(left_x, y), end=(right_x, y), stroke="black", stroke_width=2))
    dwg.add(dwg.circle(center=(feed_x, y), r=4, fill="black"))

    dim_y = y + 15
    dwg.add(dwg.text(t["element_label"].format(length=_fmt_length(short_leg.length_m, units)),
                      insert=((left_x + feed_x) / 2 - 10, dim_y), font_size="8", font_family="sans-serif"))
    dwg.add(dwg.text(t["element_label"].format(length=_fmt_length(long_leg.length_m, units)),
                      insert=((feed_x + right_x) / 2 - 10, dim_y), font_size="8", font_family="sans-serif"))

    dwg.add(dwg.text(
        t["feedpoint_label"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}",
                                     balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]),
        insert=(margin_mm / 2, height_mm - margin_mm / 4), font_size="8", font_family="sans-serif"))
    dwg.add(dwg.text(t["band_label"].format(band=design.band, freq=design.design_freq_mhz),
                      insert=(margin_mm / 2, margin_mm / 2), font_size="9", font_family="sans-serif", font_weight="bold"))
    return dwg


def _draw_j_pole(design: AntennaDesign, units: str, lang: str, margin_mm: float) -> svgwrite.Drawing:
    """J-pole: long radiator and short stub, parallel, joined at the bottom,
    with the coax feed tap marked on the stub."""
    t = DRAWING[lang]
    radiator = design.elements_with_role("radiator")[0]
    stub = design.elements_with_role("matching_stub")[0]
    radiator_mm = radiator.length_m * MM_PER_M
    stub_mm = stub.length_m * MM_PER_M
    gap_mm = 25.0

    width_mm = gap_mm + margin_mm * 2
    height_mm = radiator_mm + margin_mm * 2

    dwg = svgwrite.Drawing(size=(f"{width_mm}mm", f"{height_mm}mm"), viewBox=f"0 0 {width_mm} {height_mm}")
    _add_arrow_marker(dwg)

    base_y = height_mm - margin_mm
    radiator_x = margin_mm
    stub_x = margin_mm + gap_mm
    radiator_top_y = base_y - radiator_mm
    stub_top_y = base_y - stub_mm

    dwg.add(dwg.line(start=(radiator_x, base_y), end=(radiator_x, radiator_top_y), stroke="black", stroke_width=2))
    dwg.add(dwg.line(start=(stub_x, base_y), end=(stub_x, stub_top_y), stroke="black", stroke_width=2))
    dwg.add(dwg.line(start=(radiator_x, base_y), end=(stub_x, base_y), stroke="black", stroke_width=2))  # shorted bottom bridge

    tap_fraction = design.extra.get("feed_tap_fraction", 0.2)
    tap_y = base_y - stub_mm * tap_fraction
    dwg.add(dwg.circle(center=(stub_x, tap_y), r=4, fill="black"))

    dwg.add(dwg.text(t["element_label"].format(length=_fmt_length(radiator.length_m, units)),
                      insert=(radiator_x - 22, (base_y + radiator_top_y) / 2), font_size="8", font_family="sans-serif"))
    dwg.add(dwg.text(t["element_label"].format(length=_fmt_length(stub.length_m, units)),
                      insert=(stub_x + 5, (base_y + stub_top_y) / 2), font_size="8", font_family="sans-serif"))
    dwg.add(dwg.text(
        t["feedpoint_label"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}",
                                     balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]),
        insert=(margin_mm / 2, base_y + 12), font_size="8", font_family="sans-serif"))
    dwg.add(dwg.text(t["band_label"].format(band=design.band, freq=design.design_freq_mhz),
                      insert=(margin_mm / 2, margin_mm / 2), font_size="9", font_family="sans-serif", font_weight="bold"))
    return dwg


_RENDERERS = {
    "vertical": _draw_vertical,
    "horizontal_center_fed": _draw_horizontal_center_fed,
    "horizontal_end_fed": _draw_horizontal_end_fed,
    "horizontal_loop": _draw_horizontal_loop,
    "vertical_loop": _draw_vertical_loop,
    "inverted_v": _draw_inverted_v,
    "horizontal_off_center_fed": _draw_horizontal_off_center_fed,
    "j_pole": _draw_j_pole,
}


def draw_antenna(design: AntennaDesign, units: str = "metric", lang: str = "en", margin_mm: float = 50.0) -> svgwrite.Drawing:
    if design.geometry not in _RENDERERS:
        raise ValueError(f"No renderer for geometry '{design.geometry}'")
    return _RENDERERS[design.geometry](design, units, lang, margin_mm)


def _build_argparser():
    import argparse

    from data_store import BANDS_MHZ
    from registry import REGISTRY

    parser = argparse.ArgumentParser(description="Generate a scaled SVG drawing of an antenna design")
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
    print(f"Saved scaled drawing to {out_path}")
