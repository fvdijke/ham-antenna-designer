"""Isometric 3D antenna schematics -- a second visual mode alongside the
flat 2D side-view in scene.py. Same idea, same Scene output (so canvas_view.py
and drawing.py render it with zero changes), but the geometry is computed in
real 3D world coordinates (meters) and projected through a fixed 30-degree
isometric transform before any drawing op is emitted.

Antennas that are inherently 3D structures (a mast with radials spread in a
circle, a Yagi's boom-and-elements, a discone's cone) look genuinely
different -- and more informative -- in this view than in the flat 2D one.
Antennas that are basically planar (a dipole, a delta loop) still benefit:
the isometric tilt reads as "this is a 3D object" even for a flat shape.

Dimension-line arrows from the 2D view are dropped here -- the precise
technical measurements are scene.py's job. This view is the visual/spatial
companion, carrying the same key numbers as plain labels.
"""

import math

from i18n import DRAWING
from models import AntennaDesign
from scene import INFO_BLOCK_H, Scene, _fmt_length, _place_info_block

TARGET_3D = 460.0  # iso projection combines x & z, so this is smaller than scene.py's TARGET_SIZE

_ISO_COS = math.cos(math.radians(30))
_ISO_SIN = math.sin(math.radians(30))


def _scale_for(natural_extent_m: float) -> float:
    if natural_extent_m <= 0:
        return 1.0
    return TARGET_3D / natural_extent_m


class _Builder3D:
    """Collects ops in 3D world coordinates, then projects + auto-fits them
    into a normal scene.py `Scene` in one pass -- see module docstring."""

    def __init__(self, scale):
        self.scale = scale
        self.ops = []

    def _proj(self, p):
        x, y, z = p
        x, y, z = x * self.scale, y * self.scale, z * self.scale
        sx = (x - z) * _ISO_COS
        sy = (x + z) * _ISO_SIN - y
        return sx, sy

    def line3(self, p1, p2, width=2.0, dashed=False, kind="element"):
        self.ops.append(("line", p1, p2, width, dashed, kind))

    def polygon3(self, points, width=2.0):
        self.ops.append(("polygon", points, width))

    def feed3(self, p):
        self.ops.append(("feed", p))

    def label3(self, p, dx, dy, text, size=8, bold=False, align="left"):
        self.ops.append(("text", p, dx, dy, text, size, bold, align))

    def balun3(self, p, dx, dy, text):
        self.ops.append(("balun", p, dx, dy, text))

    def tag3(self, p, dx, dy, text, kind):
        self.ops.append(("tag", p, dx, dy, text, kind))

    def finish(self, margin: float, design: AntennaDesign, t: dict) -> Scene:
        pts = []
        for op in self.ops:
            kind = op[0]
            if kind == "line":
                pts.append(self._proj(op[1]))
                pts.append(self._proj(op[2]))
            elif kind == "polygon":
                pts.extend(self._proj(p) for p in op[1])
            elif kind == "feed":
                pts.append(self._proj(op[1]))
            elif kind in ("text", "balun", "tag"):
                p = self._proj(op[1])
                pts.append((p[0] + op[2], p[1] + op[3]))

        min_x = min(p[0] for p in pts)
        max_x = max(p[0] for p in pts)
        min_y = min(p[1] for p in pts)
        max_y = max(p[1] for p in pts)
        shift_x = margin - min_x
        shift_y = margin - min_y
        width = (max_x - min_x) + margin * 2
        height = (max_y - min_y) + margin * 2 + INFO_BLOCK_H
        s = Scene(width, height)

        def P(p):
            sx, sy = self._proj(p)
            return sx + shift_x, sy + shift_y

        for op in self.ops:
            kind = op[0]
            if kind == "line":
                _, p1, p2, w, dashed, k = op
                x1, y1 = P(p1)
                x2, y2 = P(p2)
                s.line(x1, y1, x2, y2, width=w, dashed=dashed, kind=k)
            elif kind == "polygon":
                _, points, w = op
                s.polygon([P(p) for p in points], width=w)
            elif kind == "feed":
                x, y = P(op[1])
                s.feed_point(x, y)
            elif kind == "text":
                _, p, dx, dy, text, size, bold, align = op
                x, y = P(p)
                s.text(x + dx, y + dy, text, size=size, bold=bold, align=align)
            elif kind == "balun":
                _, p, dx, dy, text = op
                x, y = P(p)
                s.balun_box(x, y, x + dx, y + dy, text)
            elif kind == "tag":
                _, p, dx, dy, text, k = op
                x, y = P(p)
                s.tag_box(x, y, x + dx, y + dy, text, k)

        _place_info_block(s, t, design, margin)
        return s


def _ground_ring(b: _Builder3D, radius_m: float, n: int = 24):
    """A faint circle on the ground plane (y=0) for spatial context --
    purely decorative, not a real wire."""
    if radius_m <= 0:
        return
    pts = [(radius_m * math.cos(2 * math.pi * i / n), 0, radius_m * math.sin(2 * math.pi * i / n)) for i in range(n)]
    for i in range(n):
        b.line3(pts[i], pts[(i + 1) % n], width=0.75, dashed=True, kind="reference")


def _scene3d_vertical(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    t = DRAWING[lang]
    radiator = design.elements_with_role("radiator")[0]
    radials = design.elements_with_role("radial")
    h = radiator.length_m
    r = radials[0].length_m if radials else 0
    b = _Builder3D(_scale_for(max(h, r)))

    _ground_ring(b, r * 1.08)
    b.line3((0, 0, 0), (0, h, 0), width=2.5, kind="element")
    n = len(radials)
    for i in range(n):
        angle = 2 * math.pi * i / n
        tip = (r * math.cos(angle), 0, r * math.sin(angle))
        b.line3((0, 0, 0), tip, width=1.3, kind="radial")

    b.feed3((0, 0, 0))
    b.tag3((0, 0, 0), 12, -55, t["core_tag"], "core")
    b.tag3((0, 0, 0), 10, 18, t["shield_tag"], "shield")
    b.balun3((0, 0, 0), -110, -30, design.balun["type"])
    b.label3((0, h, 0), 8, -14, t["element_label"].format(length=_fmt_length(h, units)), bold=True)
    if radials:
        b.label3((r, 0, 0), 8, 6, t["radial_label"].format(
            count=n, length=_fmt_length(r, units), angle=360.0 / n if n else 0))
    return b.finish(margin, design, t)


def _scene3d_vertical_end_fed(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    t = DRAWING[lang]
    radiator = design.elements_with_role("radiator")[0]
    counterpoise = design.elements_with_role("counterpoise")[0]
    h = radiator.length_m
    cp = counterpoise.length_m
    b = _Builder3D(_scale_for(max(h, cp)))

    _ground_ring(b, cp * 1.1)
    b.line3((0, 0, 0), (0, h, 0), width=2.5, kind="element")
    cp_tip = (cp * math.cos(math.radians(40)), 0, cp * math.sin(math.radians(40)))
    b.line3((0, 0, 0), cp_tip, width=1.3, kind="radial")

    b.feed3((0, 0, 0))
    b.tag3((0, 0, 0), 12, -55, t["core_tag"], "core")
    b.tag3((0, 0, 0), 10, 18, t["shield_tag"], "shield")
    b.balun3((0, 0, 0), -110, -30, design.balun["type"])
    b.label3((0, h, 0), 8, -14, t["element_label"].format(length=_fmt_length(h, units)), bold=True)
    b.label3(cp_tip, 8, 6, t["counterpoise_label"].format(count=1, length=_fmt_length(cp, units)))
    return b.finish(margin, design, t)


def _scene3d_horizontal_center_fed(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    t = DRAWING[lang]
    leg_a, leg_b = design.elements_with_role("radiator")[:2]
    leg = leg_a.length_m
    support_h = max(leg * 0.35, 1.5)
    b = _Builder3D(_scale_for(leg * 2))

    _ground_ring(b, leg * 0.3)
    b.line3((0, support_h, 0), (0, 0, 0), width=1.2, kind="reference")
    b.line3((0, support_h, 0), (leg, support_h, 0), width=2.5, kind="element")
    b.line3((-leg, support_h, 0), (0, support_h, 0), width=2.5, kind="radial")

    b.feed3((0, support_h, 0))
    b.tag3((0, support_h, 0), 10, -50, t["core_tag"], "core")
    b.tag3((0, support_h, 0), -90, -10, t["shield_tag"], "shield")
    b.balun3((0, support_h, 0), 60, -40, design.balun["type"])
    b.label3((leg / 2, support_h, 0), 0, -16, t["element_label"].format(length=_fmt_length(leg, units)))
    b.label3((0, support_h, 0), -10, 20, t["total_label"].format(length=_fmt_length(leg + leg_b.length_m, units)), bold=True, align="right")
    return b.finish(margin, design, t)


def _scene3d_horizontal_end_fed(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    t = DRAWING[lang]
    radiator = design.elements_with_role("radiator")[0]
    counterpoise = design.elements_with_role("counterpoise")[0]
    radiator_len = radiator.length_m
    cp = counterpoise.length_m
    support_h = max(radiator_len * 0.12, 1.5)
    b = _Builder3D(_scale_for(max(radiator_len, support_h * 2)))

    _ground_ring(b, cp * 0.6)
    b.line3((0, support_h, 0), (0, 0, 0), width=1.2, kind="reference")
    b.line3((0, support_h, 0), (radiator_len, support_h, 0), width=2.5, kind="element")
    b.line3((0, 0, 0), (0, 0, cp), width=1.3, kind="radial")

    b.feed3((0, support_h, 0))
    b.tag3((0, support_h, 0), 10, -50, t["core_tag"], "core")
    b.tag3((0, 0, 0), 10, 16, t["shield_tag"], "shield")
    b.balun3((0, support_h, 0), -80, -30, design.balun["type"])
    b.label3((radiator_len / 2, support_h, 0), 0, -16, t["element_label"].format(length=_fmt_length(radiator_len, units)))
    b.label3((0, 0, cp), 8, 6, t["counterpoise_label"].format(count=1, length=_fmt_length(cp, units)))
    return b.finish(margin, design, t)


def _scene3d_horizontal_loop(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    t = DRAWING[lang]
    wire = design.elements_with_role("radiator")[0]
    side = wire.length_m / 4
    support_h = max(side * 0.5, 1.5)
    b = _Builder3D(_scale_for(side))

    _ground_ring(b, side * 0.45)
    corners = [(0, support_h, 0), (side, support_h, 0), (side, support_h, side), (0, support_h, side)]
    feed = ((corners[0][0] + corners[1][0]) / 2, support_h, 0)
    b.line3(feed, corners[1], width=2.5, kind="element")
    b.line3(corners[1], corners[2], width=2.5, kind="element")
    b.line3(corners[2], corners[3], width=2.5, kind="radial")
    b.line3(corners[3], feed, width=2.5, kind="radial")
    b.line3(feed, (feed[0], 0, feed[2]), width=1.2, kind="reference")

    b.feed3(feed)
    b.tag3(feed, 12, -45, t["core_tag"], "core")
    b.tag3(feed, -90, 10, t["shield_tag"], "shield")
    b.balun3(feed, 70, -35, design.balun["type"])
    b.label3(corners[0], -6, -10, t["loop_side_label"].format(length=_fmt_length(side, units), count=4))
    b.label3(corners[2], 8, 10, t["total_label"].format(length=_fmt_length(side * 4, units)), bold=True)
    return b.finish(margin, design, t)


def _scene3d_vertical_loop(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    t = DRAWING[lang]
    wire = design.elements_with_role("radiator")[0]
    side = wire.length_m / 3
    height = side * 0.87
    b = _Builder3D(_scale_for(side))

    left = (-side / 2, 0, 0)
    right = (side / 2, 0, 0)
    apex = (0, height, 0)
    b.line3(right, apex, width=2.5, kind="element")
    b.line3(left, apex, width=2.5, kind="radial")
    feed = (0, 0, 0)

    b.feed3(feed)
    b.tag3(feed, 10, -50, t["core_tag"], "core")
    b.tag3(feed, -90, -10, t["shield_tag"], "shield")
    b.balun3(feed, 60, -35, design.balun["type"])
    b.label3(left, -6, 12, t["loop_side_label"].format(length=_fmt_length(side, units), count=3))
    b.label3(apex, 0, -16, t["total_label"].format(length=_fmt_length(side * 3, units)), bold=True)
    return b.finish(margin, design, t)


def _scene3d_inverted_v(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    t = DRAWING[lang]
    leg_a, leg_b = design.elements_with_role("radiator")[:2]
    leg = leg_a.length_m
    droop = math.radians(30)
    dx = leg * math.cos(droop)
    dy = leg * math.sin(droop)
    apex_h = dy + 1.0
    b = _Builder3D(_scale_for(dx * 2))

    apex = (0, apex_h, 0)
    right = (dx, apex_h - dy, 0)
    left = (-dx, apex_h - dy, 0)
    _ground_ring(b, dx * 0.3)
    b.line3(apex, (0, 0, 0), width=1.2, kind="reference")
    b.line3(apex, right, width=2.5, kind="element")
    b.line3(apex, left, width=2.5, kind="radial")

    b.feed3(apex)
    b.tag3(apex, 10, -16, t["core_tag"], "core")
    b.tag3(apex, -90, -16, t["shield_tag"], "shield")
    b.balun3(apex, 70, 10, design.balun["type"])
    b.label3((dx / 2, (apex_h + apex_h - dy) / 2, 0), 6, 0, t["element_label"].format(length=_fmt_length(leg, units)))
    b.label3(apex, -10, -40, t["total_label"].format(length=_fmt_length(leg + leg_b.length_m, units)), bold=True, align="right")
    height_m = leg * math.sin(droop)
    b.label3((dx, apex_h - dy / 2, 0), 10, 0, t["height_label"].format(length=_fmt_length(height_m, units)))
    return b.finish(margin, design, t)


def _scene3d_horizontal_off_center_fed(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    t = DRAWING[lang]
    short_leg = design.elements_with_role("leg_short")[0]
    long_leg = design.elements_with_role("leg_long")[0]
    support_h = max(long_leg.length_m * 0.3, 1.5)
    b = _Builder3D(_scale_for(short_leg.length_m + long_leg.length_m))

    feed = (0, support_h, 0)
    left = (-short_leg.length_m, support_h, 0)
    right = (long_leg.length_m, support_h, 0)
    _ground_ring(b, support_h * 0.8)
    b.line3(feed, (0, 0, 0), width=1.2, kind="reference")
    b.line3(feed, right, width=2.5, kind="element")
    b.line3(left, feed, width=2.5, kind="radial")

    b.feed3(feed)
    b.balun3(feed, 60, -35, design.balun["type"])
    b.label3(left, -6, -14, t["element_label"].format(length=_fmt_length(short_leg.length_m, units)))
    b.label3(right, 0, -14, t["element_label"].format(length=_fmt_length(long_leg.length_m, units)))
    b.label3(feed, -10, 20, t["total_label"].format(length=_fmt_length(short_leg.length_m + long_leg.length_m, units)), bold=True)
    return b.finish(margin, design, t)


def _scene3d_j_pole(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    t = DRAWING[lang]
    radiator = design.elements_with_role("radiator")[0]
    stub = design.elements_with_role("matching_stub")[0]
    gap = max(radiator.length_m * 0.05, 0.1)
    b = _Builder3D(_scale_for(radiator.length_m))

    b.line3((0, 0, 0), (0, radiator.length_m, 0), width=2.5, kind="element")
    b.line3((gap, 0, 0), (gap, stub.length_m, 0), width=1.6, kind="radial")
    b.line3((0, 0, 0), (gap, 0, 0), width=2.0, kind="element")

    tap_fraction = design.extra.get("feed_tap_fraction", 0.2)
    tap = (gap, stub.length_m * tap_fraction, 0)
    b.feed3(tap)
    b.balun3(tap, 60, -20, design.balun["type"])
    b.label3((0, radiator.length_m / 2, 0), -10, 0, t["element_label"].format(length=_fmt_length(radiator.length_m, units)), align="right")
    b.label3((gap, stub.length_m / 2, 0), 8, 0, t["element_label"].format(length=_fmt_length(stub.length_m, units)))
    return b.finish(margin, design, t)


def _scene3d_yagi(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    t = DRAWING[lang]
    reflector = design.elements_with_role("reflector")[0]
    driven = design.elements_with_role("radiator")[0]
    director = design.elements_with_role("director")[0]
    boom_m = design.extra["boom_m"]
    refl_sp = design.extra["reflector_spacing_m"]
    dir_sp = design.extra["director_spacing_m"]
    max_len = max(reflector.length_m, driven.length_m, director.length_m)
    h = max_len * 0.6 + 1.0
    b = _Builder3D(_scale_for(max(boom_m, max_len)))

    z_refl, z_driven, z_dir = 0.0, refl_sp, refl_sp + dir_sp
    b.line3((0, h, 0), (0, h, boom_m), width=1.4, kind="radial")
    for z, elem, key in [(z_refl, reflector, "reflector_label"), (z_driven, driven, "element_label"), (z_dir, director, "director_label")]:
        half = elem.length_m / 2
        kind = "element" if elem is driven else "radial"
        b.line3((-half, h, z), (half, h, z), width=2.3, kind=kind)
        b.label3((half, h, z), 6, -6, t[key].format(length=_fmt_length(elem.length_m, units)), size=8)

    support = (0, 0, z_driven)
    b.line3((0, h, z_driven), support, width=1.2, kind="reference")
    b.feed3((0, h, z_driven))
    b.tag3((0, h, z_driven), 10, 12, t["core_tag"], "core")
    b.tag3((0, h, z_driven), -90, 12, t["shield_tag"], "shield")
    b.balun3((0, h, z_driven), 60, -35, design.balun["type"])
    b.label3((0, h, boom_m), 6, -6, t["boom_label"].format(length=_fmt_length(boom_m, units)))
    return b.finish(margin, design, t)


def _scene3d_quad(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    t = DRAWING[lang]
    driven = design.elements_with_role("driven_loop")[0]
    reflector = design.elements_with_role("reflector_loop")[0]
    driven_side = driven.length_m / 4
    reflector_side = reflector.length_m / 4
    spacing = design.extra["spacing_m"]
    b = _Builder3D(_scale_for(max(spacing, driven_side, reflector_side) * 1.3))

    def square(z, side):
        return [(-side / 2, 0, z), (side / 2, 0, z), (side / 2, side, z), (-side / 2, side, z)]

    refl_sq = square(0, reflector_side)
    driven_sq = square(spacing, driven_side)
    b.polygon3(refl_sq, width=1.6)
    feed = ((driven_sq[0][0] + driven_sq[1][0]) / 2, 0, spacing)
    b.line3(feed, driven_sq[1], width=2.3, kind="element")
    b.line3(driven_sq[1], driven_sq[2], width=2.3, kind="element")
    b.line3(driven_sq[2], driven_sq[3], width=2.3, kind="radial")
    b.line3(driven_sq[3], feed, width=2.3, kind="radial")

    b.feed3(feed)
    b.tag3(feed, 12, 12, t["core_tag"], "core")
    b.tag3(feed, -90, 12, t["shield_tag"], "shield")
    b.balun3(feed, 60, -30, design.balun["type"])
    b.label3(driven_sq[2], 8, -6, t["loop_side_label"].format(length=_fmt_length(driven_side, units), count=4), size=8)
    b.label3(refl_sq[2], -8, -6, t["reflector_label"].format(length=_fmt_length(reflector.length_m, units)), size=8, align="right")
    b.label3(feed, -10, 26, t["spacing_label"].format(length=_fmt_length(spacing, units)))
    return b.finish(margin, design, t)


def _scene3d_moxon(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    t = DRAWING[lang]
    a_m, b_m, c_m, d_m = design.extra["a_m"], design.extra["b_m"], design.extra["c_m"], design.extra["d_m"]
    depth = b_m + c_m + d_m
    b = _Builder3D(_scale_for(max(a_m, depth) * 1.2))

    left_x, right_x = -a_m / 2, a_m / 2
    driven_z, refl_z = depth, 0.0
    driven_tail = depth - b_m
    refl_tail = d_m
    feed = (0, 0, driven_z)

    b.line3(feed, (right_x, 0, driven_z), width=2.3, kind="element")
    b.line3((right_x, 0, driven_z), (right_x, driven_tail, driven_z), width=2.3, kind="element")
    b.line3((left_x, 0, driven_z), feed, width=2.3, kind="radial")
    b.line3((left_x, 0, driven_z), (left_x, driven_tail, driven_z), width=2.3, kind="radial")

    b.line3((left_x, 0, refl_z), (right_x, 0, refl_z), width=1.6, kind="reference")
    b.line3((left_x, 0, refl_z), (left_x, refl_tail, refl_z), width=1.6, kind="reference")
    b.line3((right_x, 0, refl_z), (right_x, refl_tail, refl_z), width=1.6, kind="reference")

    b.feed3(feed)
    b.tag3(feed, 12, 12, t["core_tag"], "core")
    b.tag3(feed, -90, 12, t["shield_tag"], "shield")
    b.balun3(feed, 60, -30, design.balun["type"])
    b.label3((left_x, 0, driven_z), -6, 16, f"A: {_fmt_length(a_m, units)}", size=8, align="right")
    b.label3((left_x, driven_tail / 2, driven_z), -8, 0,
              f"B: {_fmt_length(b_m, units)}  C: {_fmt_length(c_m, units)}  D: {_fmt_length(d_m, units)}", size=8, align="right")
    return b.finish(margin, design, t)


def _scene3d_discone(design: AntennaDesign, units: str, lang: str, margin: float) -> Scene:
    t = DRAWING[lang]
    cone = design.elements_with_role("radiator")[0]
    disc = design.elements_with_role("disc")[0]
    cone_h = cone.length_m
    disc_r = disc.length_m / 2
    rim_r = cone_h * math.tan(math.radians(design.extra.get("cone_angle_deg", 30)))
    apex_gap = cone_h * 0.05
    b = _Builder3D(_scale_for(cone_h + apex_gap))

    apex = (0, cone_h, 0)
    disc_y = cone_h + apex_gap
    n_skirt = 8
    for i in range(n_skirt):
        angle = 2 * math.pi * i / n_skirt
        tip = (rim_r * math.cos(angle), 0, rim_r * math.sin(angle))
        b.line3(apex, tip, width=1.4, kind="radial")
    rim_pts = [(rim_r * math.cos(2 * math.pi * i / 16), 0, rim_r * math.sin(2 * math.pi * i / 16)) for i in range(16)]
    for i in range(16):
        b.line3(rim_pts[i], rim_pts[(i + 1) % 16], width=0.9, kind="radial")
    disc_pts = [(disc_r * math.cos(2 * math.pi * i / 16), disc_y, disc_r * math.sin(2 * math.pi * i / 16)) for i in range(16)]
    for i in range(16):
        b.line3(disc_pts[i], disc_pts[(i + 1) % 16], width=2.3, kind="element")

    b.feed3(apex)
    b.tag3(apex, 12, -20, t["core_tag"], "core")
    b.tag3(apex, 12, 16, t["shield_tag"], "shield")
    b.balun3(apex, 70, -10, design.balun["type"])
    b.label3((disc_r, disc_y, 0), 8, -6, t["disc_label"].format(length=_fmt_length(disc.length_m, units)))
    b.label3((rim_r, 0, 0), 8, 6, t["cone_label"].format(length=_fmt_length(cone_h, units)))
    return b.finish(margin, design, t)


_SCENE3D_BUILDERS = {
    "vertical": _scene3d_vertical,
    "vertical_end_fed": _scene3d_vertical_end_fed,
    "horizontal_center_fed": _scene3d_horizontal_center_fed,
    "horizontal_end_fed": _scene3d_horizontal_end_fed,
    "horizontal_loop": _scene3d_horizontal_loop,
    "vertical_loop": _scene3d_vertical_loop,
    "inverted_v": _scene3d_inverted_v,
    "horizontal_off_center_fed": _scene3d_horizontal_off_center_fed,
    "j_pole": _scene3d_j_pole,
    "yagi": _scene3d_yagi,
    "quad": _scene3d_quad,
    "moxon": _scene3d_moxon,
    "discone": _scene3d_discone,
}


def build_scene_3d(design: AntennaDesign, units: str = "metric", lang: str = "en", margin: float = 50.0) -> Scene:
    if design.geometry not in _SCENE3D_BUILDERS:
        raise ValueError(f"No 3D scene builder for geometry '{design.geometry}'")
    return _SCENE3D_BUILDERS[design.geometry](design, units, lang, margin)
