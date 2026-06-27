"""Renderer-agnostic drawing primitives for an antenna schematic.

Each antenna geometry has ONE function here that computes positions/labels
(`_scene_*`, dispatched by AntennaDesign.geometry, same pattern as the old
drawing.py). The result is a Scene: a flat list of abstract drawing ops
(lines, polygons, dimension lines, dots, text) in a single set of drawing
units. Two renderers consume the same Scene:
  - drawing.py    -> SVG, black-on-white, for file export/printing
  - canvas_view.py -> tk.Canvas, dark/amber glow theme, for in-app viewing

This keeps the geometry math (which is the part that has to stay correct)
in exactly one place, instead of duplicated per renderer.
"""

import math
from dataclasses import dataclass, field
from typing import List, Tuple

from i18n import DRAWING
from models import AntennaDesign

TARGET_SIZE = 700.0  # fixed target size (drawing units) for a design's largest natural dimension


@dataclass
class Scene:
    width: float
    height: float
    lines: List[Tuple[float, float, float, float, float, bool]] = field(default_factory=list)  # x1,y1,x2,y2,width,dashed
    polygons: List[Tuple[list, float]] = field(default_factory=list)  # points, width
    dots: List[Tuple[float, float, float]] = field(default_factory=list)  # x,y,r (feedpoint markers)
    dim_lines: List[Tuple[float, float, float, float]] = field(default_factory=list)  # x1,y1,x2,y2
    texts: List[Tuple[float, float, str, int, bool]] = field(default_factory=list)  # x,y,text,size,bold

    def line(self, x1, y1, x2, y2, width=2.0, dashed=False):
        self.lines.append((x1, y1, x2, y2, width, dashed))

    def polygon(self, points, width=2.0):
        self.polygons.append((points, width))

    def dot(self, x, y, r=4.0):
        self.dots.append((x, y, r))

    def dim_line(self, x1, y1, x2, y2):
        self.dim_lines.append((x1, y1, x2, y2))

    def text(self, x, y, text, size=8, bold=False):
        self.texts.append((x, y, text, size, bold))


def _scale_for(natural_extent_m: float) -> float:
    """Units-per-meter so that natural_extent_m maps to TARGET_SIZE."""
    if natural_extent_m <= 0:
        return 1.0
    return TARGET_SIZE / natural_extent_m


def _fmt_length(value_m: float, units: str) -> str:
    if units == "metric":
        return f"{value_m:.2f} m"
    feet = value_m / 0.3048
    return f"{feet:.2f} ft"


def _scene_vertical(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    t = DRAWING[lang]
    radiator = design.elements_with_role("radiator")[0]
    radials = design.elements_with_role("radial")
    scale = _scale_for(radiator.length_m)
    element_u = radiator.length_m * scale
    radial_u = (radials[0].length_m if radials else 0) * scale

    height = element_u + margin * 2
    width = radial_u * 2 + margin * 2 if radials else element_u * 0.6 + margin * 2
    s = Scene(width, height)

    base_x = width / 2
    base_y = height - margin
    top_y = base_y - element_u

    s.line(margin / 2, base_y, width - margin / 2, base_y, width=1, dashed=True)
    s.line(base_x, base_y, base_x, top_y, width=2)
    s.dot(base_x, base_y)

    dim_x = base_x + 15
    s.dim_line(dim_x, base_y, dim_x, top_y)
    s.text(dim_x + 5, (base_y + top_y) / 2, t["element_label"].format(length=_fmt_length(radiator.length_m, units)))

    n = len(radials)
    for i, radial in enumerate(radials):
        angle_rad = math.radians((360.0 / n) * i)
        end_x = base_x + radial_u * math.sin(angle_rad)
        end_y = base_y + radial_u * math.cos(angle_rad) * 0.3
        s.line(base_x, base_y, end_x, end_y, width=1)
        if i == 0:
            s.text(end_x + 5, end_y, t["radial_label"].format(count=n, length=_fmt_length(radial.length_m, units)))

    s.text(margin / 2, base_y + 12, t["feedpoint_label"].format(
        ohms=f"{design.feedpoint_impedance_ohms:.0f}", balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]))
    s.text(margin / 2, margin / 2, t["band_label"].format(band=design.band, freq=design.design_freq_mhz), size=9, bold=True)
    return s


def _scene_horizontal_center_fed(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    """Dipole/EDZ: two legs running left/right from a center feedpoint."""
    t = DRAWING[lang]
    leg_a, leg_b = design.elements_with_role("radiator")[:2]
    scale = _scale_for(leg_a.length_m * 2)
    leg_u = leg_a.length_m * scale

    width = leg_u * 2 + margin * 2
    height = margin * 2 + 20
    s = Scene(width, height)

    center_x = width / 2
    y = height / 2
    left_x = center_x - leg_u
    right_x = center_x + leg_u

    s.line(left_x, y, right_x, y, width=2)
    s.dot(center_x, y)

    dim_y = y + 15
    for x0, x1 in [(left_x, center_x), (center_x, right_x)]:
        s.dim_line(x0, dim_y, x1, dim_y)
    s.text(center_x + 5, dim_y + 10, t["element_label"].format(length=_fmt_length(leg_a.length_m, units)))

    s.text(margin / 2, height - margin / 2, t["feedpoint_label"].format(
        ohms=f"{design.feedpoint_impedance_ohms:.0f}", balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]))
    s.text(margin / 2, margin / 2, t["band_label"].format(band=design.band, freq=design.design_freq_mhz), size=9, bold=True)
    return s


def _scene_horizontal_end_fed(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    """EFHW/longwire: a single long radiator run from the feedpoint, plus a
    short counterpoise drawn dropping away from the feedpoint."""
    t = DRAWING[lang]
    radiator = design.elements_with_role("radiator")[0]
    counterpoise = design.elements_with_role("counterpoise")[0]
    scale = _scale_for(max(radiator.length_m, counterpoise.length_m))
    radiator_u = radiator.length_m * scale
    counterpoise_u = counterpoise.length_m * scale

    width = radiator_u + margin * 2
    height = counterpoise_u + margin * 2 + 20
    s = Scene(width, height)

    feed_x = margin
    feed_y = margin + 20
    end_x = feed_x + radiator_u

    s.line(feed_x, feed_y, end_x, feed_y, width=2)
    s.dot(feed_x, feed_y)

    dim_y = feed_y - 12
    s.dim_line(feed_x, dim_y, end_x, dim_y)
    s.text((feed_x + end_x) / 2, dim_y - 5, t["element_label"].format(length=_fmt_length(radiator.length_m, units)))

    cp_end_y = feed_y + counterpoise_u
    s.line(feed_x, feed_y, feed_x, cp_end_y, width=1, dashed=True)
    s.text(feed_x + 5, cp_end_y, t["counterpoise_label"].format(length=_fmt_length(counterpoise.length_m, units)))

    s.text(margin / 2, height - margin / 2, t["feedpoint_label"].format(
        ohms=f"{design.feedpoint_impedance_ohms:.0f}", balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]))
    s.text(margin / 2, margin / 2, t["band_label"].format(band=design.band, freq=design.design_freq_mhz), size=9, bold=True)
    return s


def _scene_horizontal_loop(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    """Full-wave loop / loop-on-ground: a square, fed at the midpoint of one side."""
    t = DRAWING[lang]
    wire = design.elements_with_role("radiator")[0]
    side_m = wire.length_m / 4
    scale = _scale_for(side_m)
    side_u = side_m * scale

    size = side_u + margin * 2
    s = Scene(size, size)

    x0, y0 = margin, margin
    x1, y1 = margin + side_u, margin + side_u

    s.polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], width=2)

    feed_x = (x0 + x1) / 2
    feed_y = y1
    s.dot(feed_x, feed_y)

    s.text(x0, y0 - 5, t["loop_side_label"].format(length=_fmt_length(side_m, units), count=4))
    s.text(margin / 2, size - margin / 4, t["feedpoint_label"].format(
        ohms=f"{design.feedpoint_impedance_ohms:.0f}", balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]))
    s.text(margin / 2, margin / 2, t["band_label"].format(band=design.band, freq=design.design_freq_mhz), size=9, bold=True)
    return s


def _scene_vertical_loop(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    """Vertical delta loop: an equilateral-ish triangle, fed at the midpoint
    of the bottom side."""
    t = DRAWING[lang]
    wire = design.elements_with_role("radiator")[0]
    side_m = wire.length_m / 3
    scale = _scale_for(side_m)
    side_u = side_m * scale

    width = side_u + margin * 2
    height = side_u * 0.87 + margin * 2
    s = Scene(width, height)

    bottom_y = height - margin
    left_x = margin
    right_x = margin + side_u
    apex_x = (left_x + right_x) / 2
    apex_y = margin

    s.polygon([(left_x, bottom_y), (right_x, bottom_y), (apex_x, apex_y)], width=2)

    feed_x = (left_x + right_x) / 2
    s.dot(feed_x, bottom_y)

    s.text(left_x, bottom_y + 10, t["loop_side_label"].format(length=_fmt_length(side_m, units), count=3))
    s.text(margin / 2, height - margin / 4, t["feedpoint_label"].format(
        ohms=f"{design.feedpoint_impedance_ohms:.0f}", balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]))
    s.text(margin / 2, margin / 2, t["band_label"].format(band=design.band, freq=design.design_freq_mhz), size=9, bold=True)
    return s


def _scene_inverted_v(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    """Inverted-V dipole: apex at top center, legs sloping down on each side."""
    t = DRAWING[lang]
    leg_a, leg_b = design.elements_with_role("radiator")[:2]
    scale = _scale_for(leg_a.length_m)
    leg_u = leg_a.length_m * scale
    droop_deg = 30

    dx = leg_u * math.cos(math.radians(droop_deg))
    dy = leg_u * math.sin(math.radians(droop_deg))

    width = dx * 2 + margin * 2
    height = dy + margin * 2
    s = Scene(width, height)

    apex_x = width / 2
    apex_y = margin
    left_x, left_y = apex_x - dx, apex_y + dy
    right_x, right_y = apex_x + dx, apex_y + dy

    s.line(apex_x, apex_y, left_x, left_y, width=2)
    s.line(apex_x, apex_y, right_x, right_y, width=2)
    s.dot(apex_x, apex_y)

    s.text(apex_x + 5, apex_y + dy / 2, t["element_label"].format(length=_fmt_length(leg_a.length_m, units)))
    s.text(margin / 2, height - margin / 4, t["feedpoint_label"].format(
        ohms=f"{design.feedpoint_impedance_ohms:.0f}", balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]))
    s.text(margin / 2, margin / 2, t["band_label"].format(band=design.band, freq=design.design_freq_mhz), size=9, bold=True)
    return s


def _scene_horizontal_off_center_fed(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    """OCF dipole: asymmetric legs running left/right from an off-center feedpoint."""
    t = DRAWING[lang]
    short_leg = design.elements_with_role("leg_short")[0]
    long_leg = design.elements_with_role("leg_long")[0]
    scale = _scale_for(short_leg.length_m + long_leg.length_m)
    short_u = short_leg.length_m * scale
    long_u = long_leg.length_m * scale

    width = short_u + long_u + margin * 2
    height = margin * 2 + 20
    s = Scene(width, height)

    feed_x = margin + short_u
    y = height / 2
    left_x = margin
    right_x = margin + short_u + long_u

    s.line(left_x, y, right_x, y, width=2)
    s.dot(feed_x, y)

    dim_y = y + 15
    s.text((left_x + feed_x) / 2 - 10, dim_y, t["element_label"].format(length=_fmt_length(short_leg.length_m, units)))
    s.text((feed_x + right_x) / 2 - 10, dim_y, t["element_label"].format(length=_fmt_length(long_leg.length_m, units)))

    s.text(margin / 2, height - margin / 4, t["feedpoint_label"].format(
        ohms=f"{design.feedpoint_impedance_ohms:.0f}", balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]))
    s.text(margin / 2, margin / 2, t["band_label"].format(band=design.band, freq=design.design_freq_mhz), size=9, bold=True)
    return s


def _scene_j_pole(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    """J-pole: long radiator and short stub, parallel, joined at the bottom,
    with the coax feed tap marked on the stub."""
    t = DRAWING[lang]
    radiator = design.elements_with_role("radiator")[0]
    stub = design.elements_with_role("matching_stub")[0]
    scale = _scale_for(radiator.length_m)
    radiator_u = radiator.length_m * scale
    stub_u = stub.length_m * scale
    gap = 25.0

    width = gap + margin * 2
    height = radiator_u + margin * 2
    s = Scene(width, height)

    base_y = height - margin
    radiator_x = margin
    stub_x = margin + gap
    radiator_top_y = base_y - radiator_u
    stub_top_y = base_y - stub_u

    s.line(radiator_x, base_y, radiator_x, radiator_top_y, width=2)
    s.line(stub_x, base_y, stub_x, stub_top_y, width=2)
    s.line(radiator_x, base_y, stub_x, base_y, width=2)

    tap_fraction = design.extra.get("feed_tap_fraction", 0.2)
    tap_y = base_y - stub_u * tap_fraction
    s.dot(stub_x, tap_y)

    s.text(radiator_x - 22, (base_y + radiator_top_y) / 2, t["element_label"].format(length=_fmt_length(radiator.length_m, units)))
    s.text(stub_x + 5, (base_y + stub_top_y) / 2, t["element_label"].format(length=_fmt_length(stub.length_m, units)))
    s.text(margin / 2, base_y + 12, t["feedpoint_label"].format(
        ohms=f"{design.feedpoint_impedance_ohms:.0f}", balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]))
    s.text(margin / 2, margin / 2, t["band_label"].format(band=design.band, freq=design.design_freq_mhz), size=9, bold=True)
    return s


def _scene_yagi(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    """3-element Yagi: a horizontal boom with reflector, driven, and director
    drawn as perpendicular elements at their correct spacing along it."""
    t = DRAWING[lang]
    reflector = design.elements_with_role("reflector")[0]
    driven = design.elements_with_role("radiator")[0]
    director = design.elements_with_role("director")[0]

    boom_m = design.extra["boom_m"]
    max_element_m = max(reflector.length_m, driven.length_m, director.length_m)
    scale = _scale_for(max(boom_m, max_element_m))

    reflector_spacing_u = design.extra["reflector_spacing_m"] * scale
    director_spacing_u = design.extra["director_spacing_m"] * scale
    boom_u = boom_m * scale
    max_element_u = max_element_m * scale

    width = boom_u + margin * 2
    height = max_element_u + margin * 2
    s = Scene(width, height)

    boom_y = height / 2
    reflector_x = margin
    driven_x = margin + reflector_spacing_u
    director_x = driven_x + director_spacing_u

    s.line(reflector_x, boom_y, director_x, boom_y, width=1)

    for x, element, label_key in [
        (reflector_x, reflector, "reflector_label"),
        (driven_x, driven, "element_label"),
        (director_x, director, "director_label"),
    ]:
        half = element.length_m * scale / 2
        s.line(x, boom_y - half, x, boom_y + half, width=2)
        s.text(x + 3, boom_y - half - 3, t[label_key].format(length=_fmt_length(element.length_m, units)), size=7)

    s.dot(driven_x, boom_y)
    s.text(reflector_x, boom_y + max_element_u / 2 + 12, t["boom_label"].format(length=_fmt_length(boom_m, units)))
    s.text(margin / 2, height - margin / 4, t["feedpoint_label"].format(
        ohms=f"{design.feedpoint_impedance_ohms:.0f}", balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]))
    s.text(margin / 2, margin / 2, t["band_label"].format(band=design.band, freq=design.design_freq_mhz), size=9, bold=True)
    return s


def _scene_quad(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    """2-element quad: two squares (driven, reflector) separated by the boom spacing."""
    t = DRAWING[lang]
    driven = design.elements_with_role("driven_loop")[0]
    reflector = design.elements_with_role("reflector_loop")[0]
    driven_side_m = driven.length_m / 4
    reflector_side_m = reflector.length_m / 4
    spacing_m = design.extra["spacing_m"]

    max_side_m = max(driven_side_m, reflector_side_m)
    scale = _scale_for(spacing_m + max_side_m)

    driven_side_u = driven_side_m * scale
    reflector_side_u = reflector_side_m * scale
    spacing_u = spacing_m * scale
    max_side_u = max_side_m * scale

    width = spacing_u + max_side_u + margin * 2
    height = max_side_u + margin * 2
    s = Scene(width, height)

    base_y = height - margin

    def square(x0, side_u):
        y0 = base_y - side_u
        return [(x0, y0), (x0 + side_u, y0), (x0 + side_u, base_y), (x0, base_y)]

    reflector_x0 = margin
    driven_x0 = margin + spacing_u

    s.polygon(square(reflector_x0, reflector_side_u), width=2)
    s.polygon(square(driven_x0, driven_side_u), width=2)

    feed_x = driven_x0 + driven_side_u / 2
    s.dot(feed_x, base_y)

    s.text(driven_x0, base_y - driven_side_u - 5, t["loop_side_label"].format(length=_fmt_length(driven_side_m, units), count=4), size=7)
    s.text(reflector_x0, base_y - reflector_side_u - 5, t["reflector_label"].format(length=_fmt_length(reflector.length_m, units)), size=7)
    s.text(reflector_x0, base_y + 12, t["spacing_label"].format(length=_fmt_length(spacing_m, units)))
    s.text(margin / 2, height - margin / 4 + 12, t["feedpoint_label"].format(
        ohms=f"{design.feedpoint_impedance_ohms:.0f}", balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]))
    s.text(margin / 2, margin / 2, t["band_label"].format(band=design.band, freq=design.design_freq_mhz), size=9, bold=True)
    return s


def _scene_moxon(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    """Moxon rectangle: driven element bracket facing reflector bracket, with
    the A/B/C/D dimensions from the Cebik regression equations."""
    a_m, b_m, c_m, d_m = design.extra["a_m"], design.extra["b_m"], design.extra["c_m"], design.extra["d_m"]
    depth_m = b_m + c_m + d_m
    scale = _scale_for(max(a_m, depth_m))

    a_u, b_u, c_u, d_u = a_m * scale, b_m * scale, c_m * scale, d_m * scale
    depth_u = b_u + c_u + d_u

    width = a_u + margin * 2
    height = depth_u + margin * 2
    s = Scene(width, height)
    t = DRAWING[lang]

    left_x = margin
    right_x = margin + a_u
    driven_y = margin + depth_u
    driven_tail_y = driven_y - b_u
    reflector_y = margin
    reflector_tail_y = reflector_y + d_u

    s.line(left_x, driven_y, right_x, driven_y, width=2)
    s.line(left_x, driven_y, left_x, driven_tail_y, width=2)
    s.line(right_x, driven_y, right_x, driven_tail_y, width=2)

    s.line(left_x, reflector_y, right_x, reflector_y, width=2)
    s.line(left_x, reflector_y, left_x, reflector_tail_y, width=2)
    s.line(right_x, reflector_y, right_x, reflector_tail_y, width=2)

    feed_x = (left_x + right_x) / 2
    s.dot(feed_x, driven_y)

    s.text(left_x, driven_y + 10, f"A: {_fmt_length(a_m, units)}", size=7)
    s.text(left_x, (driven_tail_y + reflector_tail_y) / 2,
           f"B: {_fmt_length(b_m, units)}  C: {_fmt_length(c_m, units)}  D: {_fmt_length(d_m, units)}", size=7)
    s.text(margin / 2, height - margin / 4, t["feedpoint_label"].format(
        ohms=f"{design.feedpoint_impedance_ohms:.0f}", balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]))
    s.text(margin / 2, margin / 2, t["band_label"].format(band=design.band, freq=design.design_freq_mhz), size=9, bold=True)
    return s


def _scene_discone(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    """Discone: disc at top, cone skirt flaring down and outward from the
    apex just below it -- drawn as a side-view silhouette."""
    t = DRAWING[lang]
    cone = design.elements_with_role("radiator")[0]
    disc = design.elements_with_role("disc")[0]
    scale = _scale_for(cone.length_m)
    cone_u = cone.length_m * scale
    disc_u = disc.length_m * scale

    apex_gap = 10.0
    width = max(disc_u, cone_u * 1.3) + margin * 2
    height = apex_gap + cone_u + margin * 2
    s = Scene(width, height)

    center_x = width / 2
    disc_y = margin
    apex_y = disc_y + apex_gap
    rim_y = apex_y + cone_u
    rim_half = cone_u * math.tan(math.radians(design.extra.get("cone_angle_deg", 30)))

    s.line(center_x - disc_u / 2, disc_y, center_x + disc_u / 2, disc_y, width=2)
    s.dot(center_x, apex_y)
    s.line(center_x, apex_y, center_x - rim_half, rim_y, width=2)
    s.line(center_x, apex_y, center_x + rim_half, rim_y, width=2)
    s.line(center_x - rim_half, rim_y, center_x + rim_half, rim_y, width=1)

    s.text(center_x + disc_u / 2 + 5, disc_y + 3, t["disc_label"].format(length=_fmt_length(disc.length_m, units)))
    s.text(center_x + rim_half / 2 + 5, (apex_y + rim_y) / 2, t["cone_label"].format(length=_fmt_length(cone.length_m, units)))
    s.text(margin / 2, height - margin / 4, t["feedpoint_label"].format(
        ohms=f"{design.feedpoint_impedance_ohms:.0f}", balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]))
    s.text(margin / 2, margin / 2, t["band_label"].format(band=design.band, freq=design.design_freq_mhz), size=9, bold=True)
    return s


_SCENE_BUILDERS = {
    "vertical": _scene_vertical,
    "horizontal_center_fed": _scene_horizontal_center_fed,
    "horizontal_end_fed": _scene_horizontal_end_fed,
    "horizontal_loop": _scene_horizontal_loop,
    "vertical_loop": _scene_vertical_loop,
    "inverted_v": _scene_inverted_v,
    "horizontal_off_center_fed": _scene_horizontal_off_center_fed,
    "j_pole": _scene_j_pole,
    "yagi": _scene_yagi,
    "quad": _scene_quad,
    "moxon": _scene_moxon,
    "discone": _scene_discone,
}


def build_scene(design: AntennaDesign, units: str = "metric", lang: str = "en", margin: float = 50.0) -> Scene:
    if design.geometry not in _SCENE_BUILDERS:
        raise ValueError(f"No scene builder for geometry '{design.geometry}'")
    return _SCENE_BUILDERS[design.geometry](design, units, lang, margin)
