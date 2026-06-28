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
    # x1,y1,x2,y2,width,dashed,kind -- kind picks the render color:
    # "element" (the main radiating wire, bright) vs "radial" (radials /
    # counterpoise, drawn darker so the main element stands out) vs
    # "reference" (ground line etc., dim, not a real wire).
    lines: List[Tuple[float, float, float, float, float, bool, str]] = field(default_factory=list)
    polygons: List[Tuple[list, float]] = field(default_factory=list)  # points, width
    dim_lines: List[Tuple[float, float, float, float]] = field(default_factory=list)  # x1,y1,x2,y2
    texts: List[Tuple[float, float, str, int, bool, str]] = field(default_factory=list)  # x,y,text,size,bold,align
    # Feedpoint: a dot plus a ring around it (donut shape), visually distinct
    # from plain element/junction dots so it reads as "this is the feed".
    feed_points: List[Tuple[float, float, float]] = field(default_factory=list)  # x,y,r
    # Balun/unun/choke marker: a small component-box symbol connected to the
    # feedpoint by a short leader line, with its label -- instead of bare
    # floating text, so it reads as "this box is inserted in the feedline".
    balun_boxes: List[Tuple[float, float, float, float, str]] = field(default_factory=list)  # feed_x,feed_y,box_x,box_y,text
    # Core/shield identification tags, boxed the same way as the balun --
    # filled with that wire's own color ("core" = bright element color,
    # "shield" = dim radial color), connected to the point it's labeling by
    # a dashed leader line -- same idea as the balun box, so the box can sit
    # well clear of the feedpoint/other labels without losing its meaning.
    tag_boxes: List[Tuple[float, float, float, float, str, str]] = field(default_factory=list)  # anchor_x,anchor_y,box_x,box_y,text,kind

    def line(self, x1, y1, x2, y2, width=2.0, dashed=False, kind="element"):
        self.lines.append((x1, y1, x2, y2, width, dashed, kind))

    def polygon(self, points, width=2.0):
        self.polygons.append((points, width))

    def dim_line(self, x1, y1, x2, y2):
        self.dim_lines.append((x1, y1, x2, y2))

    def text(self, x, y, text, size=8, bold=False, align="left"):
        self.texts.append((x, y, text, size, bold, align))

    def feed_point(self, x, y, r=5.0):
        self.feed_points.append((x, y, r))

    def balun_box(self, feed_x, feed_y, box_x, box_y, text):
        self.balun_boxes.append((feed_x, feed_y, box_x, box_y, text))

    def tag_box(self, anchor_x, anchor_y, box_x, box_y, text, kind="core"):
        self.tag_boxes.append((anchor_x, anchor_y, box_x, box_y, text, kind))


INFO_BLOCK_H = 40.0  # reserved height at the bottom for the combined caption


def _place_info_block(s: Scene, t: dict, design: AntennaDesign, margin: float) -> None:
    """Design band/frequency + feedpoint impedance/balun, always together at
    the top-right of the drawing -- one caption block, right-aligned in the
    top margin strip (above where any geometry starts), so it never collides
    with the schematic itself regardless of that antenna's shape."""
    x = s.width - margin / 2
    s.text(x, margin / 2, t["band_label"].format(band=design.band, freq=design.design_freq_mhz),
           size=10, bold=True, align="right")
    s.text(x, margin / 2 + 18, t["feedpoint_label"].format(
        ohms=f"{design.feedpoint_impedance_ohms:.0f}", balun_type=design.balun["type"], balun_ratio=design.balun["ratio"]),
        align="right")


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

    # Fan radials across a downward-facing arc (not a full 360 circle) so
    # none of them point back up into the vertical element -- matches how
    # a real radial system is usually drawn/photographed from the side.
    n = len(radials)
    spread_deg = 150.0
    angle_step = spread_deg / (n - 1) if n > 1 else 0.0
    start_deg = -spread_deg / 2 if n > 1 else 0.0
    angles_deg = [start_deg + angle_step * i for i in range(n)]
    drop_factor = 0.6  # vertical flatten for a side-view perspective
    max_drop = max((radial_u * math.cos(math.radians(a)) * drop_factor for a in angles_deg), default=0.0)
    label_room = 24.0  # space below the radial tips for their length labels

    height = element_u + margin * 2 + max_drop + label_room + INFO_BLOCK_H
    width = (radial_u * 2 + margin * 2 if radials else element_u * 0.6 + margin * 2) + 75
    s = Scene(width, height)

    base_x = width / 2
    base_y = margin + element_u
    top_y = margin

    s.line(margin / 2, base_y, width - margin / 2, base_y, width=1, dashed=True, kind="reference")
    s.line(base_x, base_y, base_x, top_y, width=2)
    s.feed_point(base_x, base_y)
    s.tag_box(base_x, base_y, base_x + 12.8, base_y - 54.4, t["core_tag"], "core")
    s.tag_box(base_x, base_y, base_x + 12.8, base_y + 28.8, t["shield_tag"], "shield")

    dim_x = base_x + 15
    s.dim_line(dim_x, base_y, dim_x, top_y)
    s.text(dim_x + 5, (base_y + top_y) / 2, t["element_label"].format(length=_fmt_length(radiator.length_m, units)))

    for i, (angle_deg, radial) in enumerate(zip(angles_deg, radials)):
        angle_rad = math.radians(angle_deg)
        end_x = base_x + radial_u * math.sin(angle_rad)
        end_y = base_y + radial_u * math.cos(angle_rad) * drop_factor
        s.line(base_x, base_y, end_x, end_y, width=1, kind="radial")
        s.text(end_x + 4, end_y, t["radial_each_label"].format(index=i + 1, length=_fmt_length(radial.length_m, units)), size=8)

    if radials:
        spacing_angle = 360.0 / n
        s.text(margin / 2, margin + 6,
               t["radial_label"].format(count=n, length=_fmt_length(radials[0].length_m, units), angle=spacing_angle))

    # The balun box has a fixed pixel footprint regardless of render scale,
    # while this antenna's wide radial fan often pushes the render scale
    # quite small -- push the box far enough left that it can never reach
    # the core/shield tags next to the feedpoint, at any scale.
    s.balun_box(base_x, base_y, base_x - 190, base_y - 50, design.balun["type"])

    _place_info_block(s, t, design, margin)
    return s


def _scene_horizontal_center_fed(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    """Dipole/EDZ: two legs running left/right from a center feedpoint."""
    t = DRAWING[lang]
    leg_a, leg_b = design.elements_with_role("radiator")[:2]
    scale = _scale_for(leg_a.length_m * 2)
    leg_u = leg_a.length_m * scale

    width = leg_u * 2 + margin * 2
    height = margin * 2 + 75 + INFO_BLOCK_H
    s = Scene(width, height)

    center_x = width / 2
    y = margin + 20
    left_x = center_x - leg_u
    right_x = center_x + leg_u

    # Right leg = core side, left leg = shield side -- colored to match,
    # not just labeled, same convention as the vertical's mast/radials.
    s.line(center_x, y, right_x, y, width=2, kind="element")
    s.line(left_x, y, center_x, y, width=2, kind="radial")
    s.feed_point(center_x, y)
    s.balun_box(center_x, y, center_x + 70, y - 25, design.balun["type"])
    s.tag_box(center_x, y, center_x + 12.8, y + 9.6, t["core_tag"], "core")
    s.tag_box(center_x, y, center_x - 112, y + 9.6, t["shield_tag"], "shield")

    dim_y = y + 18
    for x0, x1 in [(left_x, center_x), (center_x, right_x)]:
        s.dim_line(x0, dim_y, x1, dim_y)
    s.text(center_x + 5, dim_y + 6, t["element_label"].format(length=_fmt_length(leg_a.length_m, units)))

    total_y = dim_y + 28
    s.dim_line(left_x, total_y, right_x, total_y)
    s.text(center_x - 35, total_y + 6, t["total_label"].format(length=_fmt_length(leg_a.length_m + leg_b.length_m, units)), size=9, bold=True)

    _place_info_block(s, t, design, margin)
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
    height = counterpoise_u + margin * 2 + 20 + INFO_BLOCK_H
    s = Scene(width, height)

    feed_x = margin
    feed_y = margin + 20
    end_x = feed_x + radiator_u

    s.line(feed_x, feed_y, end_x, feed_y, width=2)
    s.feed_point(feed_x, feed_y)
    s.balun_box(feed_x, feed_y, feed_x + 50, feed_y + 28, design.balun["type"])
    s.tag_box(feed_x, feed_y, feed_x + 12.8, feed_y - 38.4, t["core_tag"], "core")

    dim_y = feed_y - 12
    s.dim_line(feed_x, dim_y, end_x, dim_y)
    s.text((feed_x + end_x) / 2, dim_y - 5, t["element_label"].format(length=_fmt_length(radiator.length_m, units)))

    cp_end_y = feed_y + counterpoise_u
    s.line(feed_x, feed_y, feed_x, cp_end_y, width=1, dashed=True, kind="radial")
    s.tag_box(feed_x, feed_y, feed_x + 8, feed_y + 19.2, t["shield_tag"], "shield")
    s.text(feed_x + 5, cp_end_y, t["counterpoise_label"].format(count=1, length=_fmt_length(counterpoise.length_m, units)))

    _place_info_block(s, t, design, margin)
    return s


def _scene_horizontal_loop(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    """Full-wave loop / loop-on-ground: a square, fed at the midpoint of one side."""
    t = DRAWING[lang]
    wire = design.elements_with_role("radiator")[0]
    side_m = wire.length_m / 4
    scale = _scale_for(side_m)
    side_u = side_m * scale

    side_size = side_u + margin * 2
    height = side_size + INFO_BLOCK_H
    s = Scene(side_size, height)

    x0, y0 = margin, margin
    x1, y1 = margin + side_u, margin + side_u

    feed_x = (x0 + x1) / 2
    feed_y = y1
    top_mid_x = (x0 + x1) / 2

    # Single continuous loop wire, split into its two halves at the
    # feedpoint gap (bottom) and the antipodal point (top-mid) -- core
    # side (right-going) colored like the element, shield side (left-going)
    # colored like a radial, instead of one uniform polygon color.
    s.line(feed_x, feed_y, x1, y1, width=2, kind="element")
    s.line(x1, y1, x1, y0, width=2, kind="element")
    s.line(x1, y0, top_mid_x, y0, width=2, kind="element")
    s.line(feed_x, feed_y, x0, y1, width=2, kind="radial")
    s.line(x0, y1, x0, y0, width=2, kind="radial")
    s.line(x0, y0, top_mid_x, y0, width=2, kind="radial")
    s.feed_point(feed_x, feed_y)
    s.balun_box(feed_x, feed_y, feed_x + 55, feed_y - 20, design.balun["type"])
    s.tag_box(feed_x, feed_y, feed_x + 9.6, feed_y + 16, t["core_tag"], "core")
    s.tag_box(feed_x, feed_y, feed_x - 112, feed_y + 16, t["shield_tag"], "shield")

    s.text(x0, y0 - 5, t["loop_side_label"].format(length=_fmt_length(side_m, units), count=4))
    s.text(x0, y0 + 10, t["total_label"].format(length=_fmt_length(side_m * 4, units)), bold=True)
    _place_info_block(s, t, design, margin)
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
    height = side_u * 0.87 + margin * 2 + INFO_BLOCK_H
    s = Scene(width, height)

    bottom_y = margin + side_u * 0.87
    left_x = margin
    right_x = margin + side_u
    apex_x = (left_x + right_x) / 2
    apex_y = margin

    feed_x = (left_x + right_x) / 2

    # Single loop wire, split at the feedpoint gap and the apex (its
    # natural antipodal point) -- core side (right) vs shield side (left).
    s.line(feed_x, bottom_y, right_x, bottom_y, width=2, kind="element")
    s.line(right_x, bottom_y, apex_x, apex_y, width=2, kind="element")
    s.line(feed_x, bottom_y, left_x, bottom_y, width=2, kind="radial")
    s.line(left_x, bottom_y, apex_x, apex_y, width=2, kind="radial")

    s.feed_point(feed_x, bottom_y)
    s.balun_box(feed_x, bottom_y, feed_x + 55, bottom_y - 20, design.balun["type"])
    s.tag_box(feed_x, bottom_y, feed_x + 9.6, bottom_y + 16, t["core_tag"], "core")
    s.tag_box(feed_x, bottom_y, feed_x - 112, bottom_y + 16, t["shield_tag"], "shield")

    s.text(left_x, bottom_y + 10, t["loop_side_label"].format(length=_fmt_length(side_m, units), count=3))
    s.text(left_x, margin / 2, t["total_label"].format(length=_fmt_length(side_m * 3, units)), bold=True)
    _place_info_block(s, t, design, margin)
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

    # Extra width for the apex-height dimension line/label on the right.
    width = dx * 2 + margin * 2 + 150
    height = dy + margin * 2 + INFO_BLOCK_H
    s = Scene(width, height)

    apex_x = dx + margin
    apex_y = margin
    left_x, left_y = apex_x - dx, apex_y + dy
    right_x, right_y = apex_x + dx, apex_y + dy

    s.line(apex_x, apex_y, right_x, right_y, width=2, kind="element")
    s.line(apex_x, apex_y, left_x, left_y, width=2, kind="radial")
    s.feed_point(apex_x, apex_y)
    s.balun_box(apex_x, apex_y, apex_x + 65, apex_y + 16, design.balun["type"])
    s.tag_box(apex_x, apex_y, apex_x + 9.6, apex_y + 48, t["core_tag"], "core")
    s.tag_box(apex_x, apex_y, apex_x - 112, apex_y + 48, t["shield_tag"], "shield")

    s.text(apex_x + 5, apex_y + dy / 2, t["element_label"].format(length=_fmt_length(leg_a.length_m, units)))
    s.text(margin / 2, margin / 2 + 14, t["total_label"].format(length=_fmt_length(leg_a.length_m + leg_b.length_m, units)), bold=True)

    # Apex height above the (level) leg ends -- the one non-obvious
    # geometric dimension for this shape, derived from the droop angle.
    height_m = leg_a.length_m * math.sin(math.radians(droop_deg))
    dim_x2 = right_x + 20
    s.dim_line(dim_x2, apex_y, dim_x2, right_y)
    s.text(dim_x2 + 5, apex_y + dy / 2, t["height_label"].format(length=_fmt_length(height_m, units)), size=8)

    _place_info_block(s, t, design, margin)
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
    height = margin * 2 + 75 + INFO_BLOCK_H
    s = Scene(width, height)

    feed_x = margin + short_u
    y = margin + 20
    left_x = margin
    right_x = margin + short_u + long_u

    s.line(left_x, y, right_x, y, width=2)
    s.feed_point(feed_x, y)
    s.balun_box(feed_x, y, feed_x + 55, y - 25, design.balun["type"])

    dim_y = y + 18
    s.text((left_x + feed_x) / 2 - 10, dim_y, t["element_label"].format(length=_fmt_length(short_leg.length_m, units)))
    s.text((feed_x + right_x) / 2 - 10, dim_y, t["element_label"].format(length=_fmt_length(long_leg.length_m, units)))

    total_y = dim_y + 28
    s.dim_line(left_x, total_y, right_x, total_y)
    s.text((left_x + right_x) / 2 - 30, total_y + 6, t["total_label"].format(length=_fmt_length(short_leg.length_m + long_leg.length_m, units)), bold=True)

    _place_info_block(s, t, design, margin)
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

    # Extra width -- this shape is naturally just two close vertical lines,
    # far too narrow on its own to fit the top-right info block's text.
    width = gap + margin * 2 + 300
    height = radiator_u + margin * 2 + INFO_BLOCK_H
    s = Scene(width, height)

    base_y = margin + radiator_u
    radiator_x = margin
    stub_x = margin + gap
    radiator_top_y = base_y - radiator_u
    stub_top_y = base_y - stub_u

    s.line(radiator_x, base_y, radiator_x, radiator_top_y, width=2)
    s.line(stub_x, base_y, stub_x, stub_top_y, width=2)
    s.line(radiator_x, base_y, stub_x, base_y, width=2)

    tap_fraction = design.extra.get("feed_tap_fraction", 0.2)
    tap_y = base_y - stub_u * tap_fraction
    s.feed_point(stub_x, tap_y)
    s.balun_box(stub_x, tap_y, stub_x + 45, tap_y - 18, design.balun["type"])

    s.text(radiator_x - 22, (base_y + radiator_top_y) / 2, t["element_label"].format(length=_fmt_length(radiator.length_m, units)))
    s.text(stub_x + 5, (base_y + stub_top_y) / 2, t["element_label"].format(length=_fmt_length(stub.length_m, units)))
    _place_info_block(s, t, design, margin)
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

    # Extra width so the director's label (the rightmost element) has room
    # to the right of the boom instead of running off the canvas edge.
    # Extra top margin so the balun box (drawn above the driven element)
    # has room clear of the top-right info block.
    extra_top = 50.0
    width = boom_u + margin * 2 + 90
    height = max_element_u + margin * 2 + INFO_BLOCK_H + extra_top
    s = Scene(width, height)

    boom_y = margin + extra_top + max_element_u / 2
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
        if label_key == "element_label":
            # Driven element is fed at its center -- split into core
            # (upper half) and shield (lower half). Reflector/director are
            # unfed parasitic elements, stay one uniform color.
            s.line(x, boom_y, x, boom_y - half, width=2, kind="element")
            s.line(x, boom_y, x, boom_y + half, width=2, kind="radial")
        else:
            s.line(x, boom_y - half, x, boom_y + half, width=2)
        s.text(x + 3, boom_y - half - 3, t[label_key].format(length=_fmt_length(element.length_m, units)), size=8)

    s.feed_point(driven_x, boom_y)
    s.balun_box(driven_x, boom_y, driven_x + 50, boom_y - max_element_u / 2 - 20, design.balun["type"])
    s.tag_box(driven_x, boom_y, driven_x + 9.6, boom_y + 9.6, t["core_tag"], "core")
    s.tag_box(driven_x, boom_y, driven_x - 112, boom_y + 9.6, t["shield_tag"], "shield")
    s.text(reflector_x, boom_y + max_element_u / 2 + 12, t["boom_label"].format(length=_fmt_length(boom_m, units)))
    _place_info_block(s, t, design, margin)
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
    height = max_side_u + margin * 2 + INFO_BLOCK_H
    s = Scene(width, height)

    base_y = margin + max_side_u

    def square(x0, side_u):
        y0 = base_y - side_u
        return [(x0, y0), (x0 + side_u, y0), (x0 + side_u, base_y), (x0, base_y)]

    reflector_x0 = margin
    driven_x0 = margin + spacing_u

    # Reflector loop is unfed/parasitic -- one uniform color, no core/shield
    # meaning. Driven loop IS fed -- split into its core/shield halves.
    s.polygon(square(reflector_x0, reflector_side_u), width=2)

    feed_x = driven_x0 + driven_side_u / 2
    driven_y0 = base_y - driven_side_u
    driven_x1 = driven_x0 + driven_side_u
    s.line(feed_x, base_y, driven_x1, base_y, width=2, kind="element")
    s.line(driven_x1, base_y, driven_x1, driven_y0, width=2, kind="element")
    s.line(driven_x1, driven_y0, feed_x, driven_y0, width=2, kind="element")
    s.line(feed_x, base_y, driven_x0, base_y, width=2, kind="radial")
    s.line(driven_x0, base_y, driven_x0, driven_y0, width=2, kind="radial")
    s.line(driven_x0, driven_y0, feed_x, driven_y0, width=2, kind="radial")

    s.feed_point(feed_x, base_y)
    s.balun_box(feed_x, base_y, feed_x + 50, base_y - 24, design.balun["type"])
    s.tag_box(feed_x, base_y, feed_x + 9.6, base_y + 19.2, t["core_tag"], "core")
    s.tag_box(feed_x, base_y, feed_x - 112, base_y + 19.2, t["shield_tag"], "shield")

    s.text(driven_x0, base_y - driven_side_u - 5, t["loop_side_label"].format(length=_fmt_length(driven_side_m, units), count=4), size=8)
    s.text(reflector_x0, base_y - reflector_side_u - 5, t["reflector_label"].format(length=_fmt_length(reflector.length_m, units)), size=8)
    s.text(reflector_x0, base_y + 12, t["spacing_label"].format(length=_fmt_length(spacing_m, units)))
    _place_info_block(s, t, design, margin)
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
    height = depth_u + margin * 2 + INFO_BLOCK_H
    s = Scene(width, height)
    t = DRAWING[lang]

    left_x = margin
    right_x = margin + a_u
    driven_y = margin + depth_u
    driven_tail_y = driven_y - b_u
    reflector_y = margin
    reflector_tail_y = reflector_y + d_u

    feed_x = (left_x + right_x) / 2

    # Driven bracket is fed at the center of its top wire -- split into
    # core (right) and shield (left) halves. Reflector bracket is unfed
    # parasitic, stays one uniform color.
    s.line(feed_x, driven_y, right_x, driven_y, width=2, kind="element")
    s.line(right_x, driven_y, right_x, driven_tail_y, width=2, kind="element")
    s.line(feed_x, driven_y, left_x, driven_y, width=2, kind="radial")
    s.line(left_x, driven_y, left_x, driven_tail_y, width=2, kind="radial")

    s.line(left_x, reflector_y, right_x, reflector_y, width=2)
    s.line(left_x, reflector_y, left_x, reflector_tail_y, width=2)
    s.line(right_x, reflector_y, right_x, reflector_tail_y, width=2)
    s.feed_point(feed_x, driven_y)
    s.balun_box(feed_x, driven_y, feed_x + 50, driven_y - 22, design.balun["type"])
    s.tag_box(feed_x, driven_y, feed_x + 9.6, driven_y + 19.2, t["core_tag"], "core")
    s.tag_box(feed_x, driven_y, feed_x - 112, driven_y + 19.2, t["shield_tag"], "shield")

    s.text(left_x, driven_y + 10, f"A: {_fmt_length(a_m, units)}", size=8)
    s.text(left_x, (driven_tail_y + reflector_tail_y) / 2,
           f"B: {_fmt_length(b_m, units)}  C: {_fmt_length(c_m, units)}  D: {_fmt_length(d_m, units)}", size=8)
    _place_info_block(s, t, design, margin)
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
    height = apex_gap + cone_u + margin * 2 + INFO_BLOCK_H
    s = Scene(width, height)

    center_x = width / 2
    disc_y = margin
    apex_y = disc_y + apex_gap
    rim_y = apex_y + cone_u
    rim_half = cone_u * math.tan(math.radians(design.extra.get("cone_angle_deg", 30)))

    # Disc = core side, cone skirt = shield side -- matches a real discone's
    # wiring (center conductor to disc, shield/ground to the cone).
    s.line(center_x - disc_u / 2, disc_y, center_x + disc_u / 2, disc_y, width=2, kind="element")
    s.feed_point(center_x, apex_y)
    s.balun_box(center_x, apex_y, center_x + 60, apex_y + 14, design.balun["type"])
    s.tag_box(center_x, apex_y, center_x + 9.6, apex_y - 28.8, t["core_tag"], "core")
    s.tag_box(center_x, apex_y, center_x + 9.6, apex_y + 41.6, t["shield_tag"], "shield")
    s.line(center_x, apex_y, center_x - rim_half, rim_y, width=2, kind="radial")
    s.line(center_x, apex_y, center_x + rim_half, rim_y, width=2, kind="radial")
    s.line(center_x - rim_half, rim_y, center_x + rim_half, rim_y, width=1, kind="radial")

    s.text(center_x + disc_u / 2 + 5, disc_y + 3, t["disc_label"].format(length=_fmt_length(disc.length_m, units)))
    s.text(center_x + rim_half / 2 + 5, (apex_y + rim_y) / 2, t["cone_label"].format(length=_fmt_length(cone.length_m, units)))
    _place_info_block(s, t, design, margin)
    return s


def _scene_vertical_end_fed(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    """Half-/full-wave vertical: radiator runs straight up from the base
    feedpoint, with a short counterpoise running along the ground."""
    t = DRAWING[lang]
    radiator = design.elements_with_role("radiator")[0]
    counterpoise = design.elements_with_role("counterpoise")[0]
    scale = _scale_for(radiator.length_m)
    radiator_u = radiator.length_m * scale
    counterpoise_u = counterpoise.length_m * scale

    width = counterpoise_u + margin * 2 + 40
    height = radiator_u + margin * 2 + INFO_BLOCK_H
    s = Scene(width, height)

    base_x = margin + 40
    feed_y = margin + radiator_u
    top_y = margin

    s.line(margin / 2, feed_y, width - margin / 2, feed_y, width=1, dashed=True, kind="reference")
    s.line(base_x, feed_y, base_x, top_y, width=2)
    s.feed_point(base_x, feed_y)
    s.balun_box(base_x, feed_y, base_x - 60, feed_y - 25, design.balun["type"])
    s.tag_box(base_x, feed_y, base_x + 9.6, feed_y - 51.2, t["core_tag"], "core")

    dim_x = base_x + 15
    s.dim_line(dim_x, feed_y, dim_x, top_y)
    s.text(dim_x + 5, (feed_y + top_y) / 2, t["element_label"].format(length=_fmt_length(radiator.length_m, units)))

    cp_end_x = base_x + counterpoise_u
    s.line(base_x, feed_y, cp_end_x, feed_y, width=1, dashed=False, kind="radial")
    s.tag_box(base_x, feed_y, base_x + 8, feed_y + 22.4, t["shield_tag"], "shield")
    s.text(base_x + 5, feed_y + 26, t["counterpoise_label"].format(count=1, length=_fmt_length(counterpoise.length_m, units)))

    _place_info_block(s, t, design, margin)
    return s


_SCENE_BUILDERS = {
    "vertical": _scene_vertical,
    "vertical_end_fed": _scene_vertical_end_fed,
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
