"""Antenna schematics: ONE world model per antenna, laid out for a 2D or a
3D view, with every label placed clear of the drawing.

1. A builder turns an AntennaDesign into a `Model` in world coordinates
   (metres; x right, y up, z towards the viewer). Everything carries a ROLE:
   radiator, parasitic element, matching stub, counterpoise/radials, support
   (mast, boom), rope -- plus the feed line (coax or ladder line) with its
   route to the shack, the balun/unun/choke box AT the feedpoint, insulators
   and the ground point.
2. `layout()` projects the model (2D: a cabinet-oblique front view or a top
   view, chosen per antenna; 3D: isometric), scales it into a drawing box and
   places the text:
     - callout cards (title + detail) in columns BESIDE the drawing, joined
       to their part by a leader line -- so they never cover the drawing;
     - dimension labels next to their dimension line, at the first offset
       where the label box touches no wire, symbol or other label.
   Text is measured with the renderer's real font metrics.
3. A theme (schematic_render.py) paints the layout through a small painter
   interface -- the same code draws on the Tk canvas and into SVG.

Not to scale: tiny parts (a 2 m counterpoise next to a 20 m wire) are drawn
at a readable minimum; the labels always carry the calculated values.
"""

import math
from dataclasses import dataclass, field

from data_store import antenna_type_label
from i18n import SCHEMATIC

# cabinet-oblique 2D projection: depth (z) drawn at 50 %, 35 deg towards the lower right
_CAB_K = 0.5
_CAB_DX = _CAB_K * math.cos(math.radians(35))
_CAB_DY = _CAB_K * math.sin(math.radians(35))
_ISO_C = math.cos(math.radians(30))
_ISO_S = math.sin(math.radians(30))

ROLES_WIRE = ("support", "rope", "boom", "counterpoise", "stub", "parasitic", "radiator")


@dataclass
class Model:
    view2d: str = "cabinet"          # "cabinet" or "top"
    wires: list = field(default_factory=list)      # (points3, role)
    feedline: tuple = None                         # (points3, "coax"|"ladder")
    boxes: list = field(default_factory=list)      # (p3, kind, short_text)
    feed: tuple = None
    earths: list = field(default_factory=list)
    insulators: list = field(default_factory=list)
    shack: tuple = None
    ground: bool = True
    dims: list = field(default_factory=list)       # (p1, p2, label, views)
    callouts: list = field(default_factory=list)   # (p3, cat, title, detail, views)

    def wire(self, pts, role="radiator"):
        self.wires.append((list(pts), role))

    def dim(self, p1, p2, label, views=("2d", "3d")):
        self.dims.append((p1, p2, label, views))

    def callout(self, p, cat, title, detail, views=("2d", "3d")):
        self.callouts.append((p, cat, title, detail, views))


# ------------------------------------------------------------------ helpers

def fmt_len(m: float, units: str, lang: str) -> str:
    if units == "metric":
        s = f"{m:.2f} m"
    else:
        s = f"{m / 0.3048:.2f} ft"
    return s.replace(".", ",") if lang == "nl" else s


def _fmt_num(v: float, fmt: str, lang: str) -> str:
    s = format(v, fmt)
    return s.replace(".", ",") if lang == "nl" else s


def _box_kind(design):
    ratio = str(design.balun.get("ratio", ""))
    t = design.antenna_type
    if t == "extended_double_zepp":
        return "tuner", "tuner"
    if t == "five_eighths_vertical":
        return "coil", "L"
    if ":" in ratio:
        return ("choke" if ratio == "1:1" else "transformer"), ratio
    return None, ""


def _add_box_and_feed(m, d, p, T, z):
    kind, text = _box_kind(d)
    m.feed = p
    if kind in ("choke", "transformer", "coil"):
        m.boxes.append((p, kind, text))
        detail = T["coil_detail"] if kind == "coil" else T["box_detail"].format(z=z)
        m.callout(p, "box", d.balun["type"], detail)
    return kind


def _feedline(m, pts, T, cable, ladder=False, anchor_i=1):
    m.feedline = (pts, "ladder" if ladder else "coax")
    m.shack = pts[-1]
    m.earths.append(pts[-1])
    a, b = pts[anchor_i], pts[min(anchor_i + 1, len(pts) - 1)]
    mid = tuple((a[i] + b[i]) / 2 for i in range(3))
    if ladder:
        m.callout(mid, "feedline", T["feed_ladder"], T["feed_ladder_detail"])
    else:
        m.callout(mid, "feedline", T["feed_coax"], T["feed_coax_detail"].format(cable=cable))
    m.callout(pts[-1], "earth", T["earth"], T["earth_detail"])


def _mast(m, x, top, z=0.0):
    m.wire([(x, 0, z), (x, top, z)], "support")


# ------------------------------------------------------------------ builders

def _b_vertical(d, T, L_, cable, z):
    m = Model("cabinet")
    L = d.elements_with_role("radiator")[0].length_m
    radials = d.elements_with_role("radial")
    n = len(radials)
    R = radials[0].length_m if radials else 0.5 * L
    m.wire([(0, 0, 0), (0, L, 0)], "radiator")
    for i in range(n):
        a = math.radians(30 + 360 * i / n)
        m.wire([(0, 0, 0), (R * math.cos(a), 0, R * math.sin(a))], "counterpoise")
    _add_box_and_feed(m, d, (0, 0, 0), T, z)
    a = math.radians(-15)
    dist = 1.35 * max(R, 0.5 * L)
    _feedline(m, [(0, 0, 0), (dist * math.cos(a), 0, dist * math.sin(a))], T, cable, anchor_i=0)
    m.dim((0, 0, 0), (0, L, 0), L_(L))
    m.callout((0, 0.62 * L, 0), "radiator", T["radiator"], T["radiator_vertical"].format(len=L_(L)))
    if n:
        a = math.radians(30 + 360 * (n // 2) / n)
        m.callout((0.55 * R * math.cos(a), 0, 0.55 * R * math.sin(a)), "counterpoise", T["radials"],
                  T["radials_detail"].format(n=n, len=L_(R)))
    return m


def _b_vertical_end_fed(d, T, L_, cable, z):
    m = Model("cabinet")
    L = d.elements_with_role("radiator")[0].length_m
    cp = d.elements_with_role("counterpoise")[0].length_m
    cpd = max(cp, 0.15 * L)
    m.wire([(0, 0, 0), (0, L, 0)], "radiator")
    a = math.radians(210)
    tip = (cpd * math.cos(a), 0, cpd * math.sin(a))
    m.wire([(0, 0, 0), tip], "counterpoise")
    _add_box_and_feed(m, d, (0, 0, 0), T, z)
    a = math.radians(-15)
    dist = 0.55 * L
    _feedline(m, [(0, 0, 0), (dist * math.cos(a), 0, dist * math.sin(a))], T, cable, anchor_i=0)
    m.dim((0, 0, 0), (0, L, 0), L_(L))
    m.callout((0, 0.62 * L, 0), "radiator", T["radiator"], T["radiator_vertical"].format(len=L_(L)))
    m.callout(tuple(v * 0.7 for v in tip), "counterpoise", T["counterpoise"], T["cp_detail"].format(len=L_(cp)))
    return m


def _b_center_fed(d, T, L_, cable, z, ocf=False):
    m = Model("cabinet")
    if ocf:
        la = d.elements_with_role("leg_short")[0].length_m
        lb = d.elements_with_role("leg_long")[0].length_m
    else:
        la, lb = (e.length_m for e in d.elements_with_role("radiator")[:2])
    tot = la + lb
    h = max(0.3 * tot, 3.0)
    r = 0.06 * tot
    m.wire([(-la, h, 0), (0, h, 0), (lb, h, 0)], "radiator")
    for x, xm in ((-la, -la - r), (lb, lb + r)):
        m.insulators.append((x, h, 0))
        m.wire([(x, h, 0), (xm, h, 0)], "rope")
        _mast(m, xm, h + 0.03 * tot)
    ladder = d.antenna_type == "extended_double_zepp"
    route = [(0, h, 0), (0, 0, 0), (0.18 * tot, 0, 0.5 * tot)]
    if ladder:
        m.feed = (0, h, 0)
        m.boxes.append((route[-1], "tuner", "tuner"))
        m.callout(route[-1], "box", d.balun["type"], T["tuner_detail"])
    else:
        _add_box_and_feed(m, d, (0, h, 0), T, z)
    _feedline(m, route, T, cable, ladder=ladder, anchor_i=0)
    m.dim((-la, h, 0), (0, h, 0), L_(la))
    m.dim((0, h, 0), (lb, h, 0), L_(lb))
    detail = (T["radiator_ocf"].format(short=L_(la), long=L_(lb), total=L_(tot)) if ocf
              else T["radiator_legs"].format(len=L_(la), total=L_(tot)))
    m.callout((-0.55 * la, h, 0), "radiator", T["radiator"], detail)
    return m


def _b_end_fed(d, T, L_, cable, z):
    m = Model("cabinet")
    L = d.elements_with_role("radiator")[0].length_m
    cp = d.elements_with_role("counterpoise")[0].length_m
    h = max(0.3 * L, 3.0)
    _mast(m, 0, h + 0.04 * L)
    m.wire([(0, h, 0), (L, h, 0)], "radiator")
    m.insulators.append((L, h, 0))
    m.wire([(L, h, 0), (1.06 * L, h, 0)], "rope")
    _mast(m, 1.06 * L, h + 0.02 * L)
    cpd = max(cp, 0.14 * L)
    a = math.radians(55)
    tip = (cpd * math.cos(a), h - cpd * math.sin(a), 0)
    m.wire([(0, h, 0), tip], "counterpoise")
    _add_box_and_feed(m, d, (0, h, 0), T, z)
    x = -0.018 * L
    _feedline(m, [(0, h, 0), (x, h - 0.03 * L, 0), (x, 0, 0), (-0.22 * L, 0, 0.35 * L)], T, cable, anchor_i=1)
    m.dim((0, h, 0), (L, h, 0), L_(L))
    m.callout((0.62 * L, h, 0), "radiator", T["radiator"], T["radiator_len"].format(len=L_(L)))
    m.callout(tuple((0 + tip[i]) / 2 if i != 1 else (h + tip[1]) / 2 for i in range(3)), "counterpoise",
              T["counterpoise"], T["cp_detail"].format(len=L_(cp)))
    return m


def _b_horizontal_loop(d, T, L_, cable, z):
    m = Model("top")
    P = d.elements_with_role("radiator")[0].length_m
    a = P / 4
    on_ground = d.antenna_type == "ground_loop_receive"
    h = 0.05 if on_ground else max(0.6 * a, 3.0)
    f = (0, h, a / 2)
    corners = [(a / 2, h, a / 2), (a / 2, h, -a / 2), (-a / 2, h, -a / 2), (-a / 2, h, a / 2)]
    m.wire([f] + corners + [f], "radiator")
    if not on_ground:
        for c in corners:
            m.insulators.append(c)
            _mast(m, c[0], h + 0.05 * a, c[2])
    _add_box_and_feed(m, d, f, T, z)
    _feedline(m, [f, (0, 0, a / 2), (0.25 * a, 0, 1.15 * a)], T, cable, anchor_i=1)
    m.dim((-a / 2, h, -a / 2), (a / 2, h, -a / 2), L_(a))
    m.callout((a / 2, h, 0), "radiator", T["loop"], T["loop_detail"].format(n=4, side=L_(a), total=L_(P)))
    return m


def _b_vertical_loop(d, T, L_, cable, z):
    m = Model("cabinet")
    P = d.elements_with_role("radiator")[0].length_m
    a = P / 3
    hb = max(0.12 * a, 1.5)
    apex = (0, hb + 0.866 * a, 0)
    f = (0, hb, 0)
    m.wire([f, (a / 2, hb, 0), apex, (-a / 2, hb, 0), f], "radiator")
    for x in (-a / 2, a / 2):
        m.insulators.append((x, hb, 0))
        m.wire([(x, hb, 0), (x * 1.25, 0, 0)], "rope")
    m.insulators.append(apex)
    m.wire([apex, (-0.8 * a, apex[1] + 0.03 * a, 0)], "rope")
    _mast(m, -0.8 * a, apex[1] + 0.06 * a)
    _add_box_and_feed(m, d, f, T, z)
    _feedline(m, [f, (0, 0, 0), (0.2 * a, 0, 0.55 * a)], T, cable, anchor_i=0)
    m.dim((-a / 2, hb, 0), (a / 2, hb, 0), L_(a))
    m.callout((a / 4, hb + 0.433 * a, 0), "radiator", T["loop"], T["loop_detail"].format(n=3, side=L_(a), total=L_(P)))
    return m


def _b_inverted_v(d, T, L_, cable, z):
    m = Model("cabinet")
    la, lb = (e.length_m for e in d.elements_with_role("radiator")[:2])
    droop = math.radians(35)
    dx, dy = la * math.cos(droop), la * math.sin(droop)
    hA = dy + max(0.2 * la, 1.5)
    apex = (0, hA, 0)
    left, right = (-dx, hA - dy, 0), (dx, hA - dy, 0)
    m.wire([left, apex, right], "radiator")
    for p, s in ((left, -1), (right, 1)):
        m.insulators.append(p)
        m.wire([p, (s * (dx + 0.12 * la), 0, 0)], "rope")
    _mast(m, 0, hA + 0.03 * la)
    _add_box_and_feed(m, d, apex, T, z)
    x = 0.035 * la
    _feedline(m, [apex, (x, hA - 0.05 * la, 0), (x, 0, 0), (0.3 * la, 0, 0.6 * la)], T, cable, anchor_i=1)
    m.dim(left, apex, L_(la))
    m.dim(apex, right, L_(lb))
    m.callout((0.5 * dx, hA - 0.5 * dy, 0), "radiator", T["radiator"],
              T["radiator_legs"].format(len=L_(la), total=L_(la + lb)))
    return m


def _b_j_pole(d, T, L_, cable, z):
    m = Model("cabinet")
    Lr = d.elements_with_role("radiator")[0].length_m
    Ls = d.elements_with_role("matching_stub")[0].length_m
    L = Lr + Ls
    g = 0.06 * L
    hm = 0.35 * L
    m.wire([(0, hm, 0), (0, hm + Ls, 0)], "stub")
    m.wire([(g, hm, 0), (g, hm + Ls, 0)], "stub")
    m.wire([(0, hm, 0), (g, hm, 0)], "stub")
    m.wire([(0, hm + Ls, 0), (0, hm + L, 0)], "radiator")
    _mast(m, g / 2, hm)
    frac = d.extra.get("feed_tap_fraction", 0.2)
    ty = hm + Ls * frac
    m.feed = (g / 2, ty, 0)
    xr = g + 0.12 * L
    _feedline(m, [(0, ty, 0), (xr, ty, 0), (xr, 0, 0), (xr + 0.3 * L, 0, 0.45 * L)], T, cable, anchor_i=1)
    m.dim((0, hm + Ls, 0), (0, hm + L, 0), L_(Lr))
    m.dim((g, hm, 0), (g, hm + Ls, 0), L_(Ls))
    m.callout((0, hm + Ls + 0.6 * Lr, 0), "radiator", T["radiator"], T["radiator_len"].format(len=L_(Lr)))
    m.callout((g, hm + 0.75 * Ls, 0), "stub", T["stub"], T["stub_detail"].format(len=L_(Ls)))
    m.callout((g / 2, ty, 0), "box", T["tap"], T["tap_detail"].format(len=L_(d.extra.get("feed_tap_m", Ls * frac))))
    return m


def _b_yagi(d, T, L_, cable, z):
    m = Model("top")
    refl = d.elements_with_role("reflector")[0].length_m
    drv = d.elements_with_role("radiator")[0].length_m
    dire = d.elements_with_role("director")[0].length_m
    sr, sd = d.extra["reflector_spacing_m"], d.extra["director_spacing_m"]
    b = sr + sd
    M = max(refl, drv, dire)
    h = max(0.5 * M, 4.0)
    m.wire([(-0.04 * b, h, 0), (1.04 * b, h, 0)], "boom")
    _mast(m, b / 2, h)
    for x, ln, role in ((0, refl, "parasitic"), (sr, drv, "radiator"), (b, dire, "parasitic")):
        m.wire([(x, h, -ln / 2), (x, h, ln / 2)], role)
    _add_box_and_feed(m, d, (sr, h, 0), T, z)
    zc = 0.035 * M
    _feedline(m, [(sr, h, 0), (sr, h, zc), (b / 2, h, zc), (b / 2, 0, zc), (b / 2 + 0.3 * b, 0, 0.8 * M)],
              T, cable, anchor_i=1)
    for x, ln in ((0, refl), (sr, drv), (b, dire)):
        m.dim((x, h, -ln / 2), (x, h, ln / 2), L_(ln))
    zt = M / 2  # spacings measured just past the element tips, clear of the boom
    m.dim((0, h, zt), (sr, h, zt), L_(sr))
    m.dim((sr, h, zt), (b, h, zt), L_(sd))
    m.callout((0, h, -0.38 * refl), "parasitic", T["reflector"], L_(refl))
    m.callout((sr, h, -0.38 * drv), "radiator", T["driven"], L_(drv))
    m.callout((b, h, -0.38 * dire), "parasitic", T["director"], L_(dire))
    return m


def _b_quad(d, T, L_, cable, z):
    m = Model("cabinet")
    pd = d.elements_with_role("driven_loop")[0].length_m
    pr = d.elements_with_role("reflector_loop")[0].length_m
    s = d.extra["spacing_m"]
    ad, ar = pd / 4, pr / 4
    hb = max(0.6 * ad, 3.0)
    yb = hb + ad / 2
    f = (0, hb, 0)
    m.wire([f, (ad / 2, hb, 0), (ad / 2, hb + ad, 0), (-ad / 2, hb + ad, 0), (-ad / 2, hb, 0), f], "radiator")
    rb = yb - ar / 2
    m.wire([(-ar / 2, rb, -s), (ar / 2, rb, -s), (ar / 2, rb + ar, -s), (-ar / 2, rb + ar, -s), (-ar / 2, rb, -s)],
           "parasitic")
    m.wire([(0, yb, 0.05 * s), (0, yb, -1.05 * s)], "boom")
    _mast(m, 0, yb, -s / 2)
    _add_box_and_feed(m, d, f, T, z)
    _feedline(m, [f, (0, 0, 0), (0.35 * ad, 0, 0.9 * ad)], T, cable, anchor_i=0)
    m.dim((-ad / 2, hb, 0), (ad / 2, hb, 0), L_(ad))
    m.dim((0, yb, 0), (0, yb, -s), L_(s))
    m.callout((ad / 2, hb + 0.62 * ad, 0), "radiator", T["driven_loop"],
              T["loop_detail"].format(n=4, side=L_(ad), total=L_(pd)))
    m.callout((-ar / 2, rb + 0.7 * ar, -s), "parasitic", T["reflector_loop"],
              T["loop_detail"].format(n=4, side=L_(ar), total=L_(pr)))
    return m


def _b_moxon(d, T, L_, cable, z):
    m = Model("top")
    ex = d.extra
    A, B, C, D, E = ex["a_m"], ex["b_m"], ex["c_m"], ex["d_m"], ex["e_m"]
    h = max(0.5 * A, 4.0)
    zd, zr = E / 2, -E / 2
    m.wire([(-A / 2, h, zd - B), (-A / 2, h, zd), (A / 2, h, zd), (A / 2, h, zd - B)], "radiator")
    m.wire([(-A / 2, h, zr + D), (-A / 2, h, zr), (A / 2, h, zr), (A / 2, h, zr + D)], "parasitic")
    m.wire([(0, h, zd), (0, h, zr)], "boom")
    _mast(m, 0, h)
    _add_box_and_feed(m, d, (0, h, zd), T, z)
    x = 0.04 * A
    _feedline(m, [(0, h, zd), (x, h, zd - 0.03 * A), (x, h, 0), (x, 0, 0), (0.35 * A, 0, zd + 0.45 * A)],
              T, cable, anchor_i=1)
    m.dim((-A / 2, h, zd), (A / 2, h, zd), "A " + L_(A))
    m.dim((A / 2, h, zd), (A / 2, h, zd - B), "B " + L_(B))
    m.dim((A / 2, h, zr), (A / 2, h, zr + D), "D " + L_(D))
    m.dim((-A / 2, h, zd), (-A / 2, h, zr), "E " + L_(E))
    m.callout((-A / 4, h, zd), "radiator", T["driven"], T["moxon_driven"].format(len=L_(A + 2 * B)))
    m.callout((-A / 4, h, zr), "parasitic", T["reflector"], T["moxon_reflector"].format(len=L_(A + 2 * D)))
    m.callout((A / 2, h, zd - B - C / 2), "support", T["moxon_gap"], T["moxon_gap_detail"].format(len=L_(C)))
    return m


def _b_discone(d, T, L_, cable, z):
    m = Model("cabinet")
    cone = d.elements_with_role("radiator")[0].length_m
    disc = d.elements_with_role("disc")[0].length_m
    ch = d.extra.get("cone_height_m", cone)
    rim = d.extra.get("cone_base_m", cone) / 2
    n = d.extra.get("skirt_count", 12)
    hm = max(1.2 * ch, 3.0)
    ya = hm + ch
    yd = ya + 0.06 * ch
    apex = (0, ya, 0)
    _mast(m, 0, ya)
    for i in range(n):
        a = 2 * math.pi * i / n
        m.wire([apex, (rim * math.cos(a), hm, rim * math.sin(a))], "counterpoise")
    ring = [(rim * math.cos(2 * math.pi * i / 36), hm, rim * math.sin(2 * math.pi * i / 36)) for i in range(37)]
    m.wire(ring, "counterpoise")
    dr = disc / 2
    disc_ring = [(dr * math.cos(2 * math.pi * i / 36), yd, dr * math.sin(2 * math.pi * i / 36)) for i in range(37)]
    m.wire(disc_ring, "radiator")
    m.wire([(-dr, yd, 0), (dr, yd, 0)], "radiator")
    m.feed = apex
    x = 0.05 * ch
    _feedline(m, [apex, (x, ya - 0.06 * ch, 0), (x, 0, 0), (0.6 * ch + rim, 0, 0.9 * ch)], T, cable, anchor_i=1)
    m.dim((-dr, yd, 0), (dr, yd, 0), L_(disc))
    m.dim(apex, (rim, hm, 0), L_(cone))
    m.callout((-dr * 0.8, yd, 0), "radiator", T["disc"], T["disc_detail"].format(len=L_(disc)))
    a = math.radians(200)
    m.callout((0.5 * rim * math.cos(a), (ya + hm) / 2, 0.5 * rim * math.sin(a)), "counterpoise", T["cone"],
              T["cone_detail"].format(n=n, len=L_(cone)))
    m.callout(apex, "box", T["feed_direct"], T["feed_direct_detail"])
    return m


_BUILDERS = {
    "vertical": _b_vertical,
    "vertical_end_fed": _b_vertical_end_fed,
    "horizontal_center_fed": _b_center_fed,
    "horizontal_off_center_fed": lambda d, T, L_, c, z: _b_center_fed(d, T, L_, c, z, ocf=True),
    "horizontal_end_fed": _b_end_fed,
    "horizontal_loop": _b_horizontal_loop,
    "vertical_loop": _b_vertical_loop,
    "inverted_v": _b_inverted_v,
    "j_pole": _b_j_pole,
    "yagi": _b_yagi,
    "quad": _b_quad,
    "moxon": _b_moxon,
    "discone": _b_discone,
}


def build_model(design, units: str = "metric", lang: str = "en", cable: str = None) -> Model:
    if design.geometry not in _BUILDERS:
        raise ValueError(f"No schematic builder for geometry '{design.geometry}'")
    T = SCHEMATIC[lang]
    z = f"{design.feedpoint_impedance_ohms:.0f}"

    def L_(v):
        return fmt_len(v, units, lang)

    return _BUILDERS[design.geometry](design, T, L_, cable or "coax 50 Ω", z)


# ------------------------------------------------------------------ geometry helpers

def project(p, view):
    x, y, z = p
    if view == "top":
        return x, z
    if view == "iso":
        return (x - z) * _ISO_C, (x + z) * _ISO_S - y
    return x + _CAB_DX * z, -y + _CAB_DY * z


def _seg_hits_rect(p, q, r, pad=0.0):
    """Does segment p-q intersect rect r=(x0,y0,x1,y1) (grown by pad)?"""
    x0, y0, x1, y1 = r[0] - pad, r[1] - pad, r[2] + pad, r[3] + pad
    (px, py), (qx, qy) = p, q
    t0, t1 = 0.0, 1.0
    dx, dy = qx - px, qy - py
    for pv, qv in ((-dx, px - x0), (dx, x1 - px), (-dy, py - y0), (dy, y1 - py)):
        if pv == 0:
            if qv < 0:
                return False
        else:
            t = qv / pv
            if pv < 0:
                if t > t1:
                    return False
                t0 = max(t0, t)
            else:
                if t < t0:
                    return False
                t1 = min(t1, t)
    return t0 <= t1


def _rects_overlap(a, b, pad=0.0):
    return not (a[2] + pad <= b[0] or b[2] + pad <= a[0] or a[3] + pad <= b[1] or b[3] + pad <= a[1])


def _wrap(text, width, measure, font):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if cur and measure(font, trial) > width:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------ layout

MARGIN = 24
COL_W = 236
COL_GAP = 34
GEO_W, GEO_H = 620, 440
GEO_PAD = 34            # room around the geometry for symbols (box, earth, shack)
CARD_GAP = 10
CARD_PAD = 10
SYMBOL_BOX = (46, 30)


@dataclass
class Layout:
    width: float
    height: float
    view: str
    geo: tuple                      # x0, y0, x1, y1 of the drawing area
    ground_poly: list = None
    wires: list = field(default_factory=list)       # (pts, role)
    mast_dots: list = field(default_factory=list)   # vertical supports seen from above
    feedline: tuple = None                          # (pts, kind)
    boxes: list = field(default_factory=list)       # (x, y, kind, text)
    feed: tuple = None
    earths: list = field(default_factory=list)
    insulators: list = field(default_factory=list)
    shack: tuple = None
    dims: list = field(default_factory=list)        # dict
    callouts: list = field(default_factory=list)    # dict
    header: list = field(default_factory=list)      # (x, y, text, font, anchor)
    legend: list = field(default_factory=list)      # (x, y, cat, label)
    roles: set = field(default_factory=set)


def layout(design, model: Model, view: str, measure, line_h, lang: str = "en") -> Layout:
    """Place the model on a page. `measure(font, text)` returns a width in px,
    `line_h(font)` a line height; view is "2d" or "3d"."""
    T = SCHEMATIC[lang]
    proj_view = "iso" if view == "3d" else model.view2d
    P = lambda p: project(p, proj_view)  # noqa: E731

    # ---- world points -> fit into the drawing box
    pts = []
    for wpts, _ in model.wires:
        pts += [P(p) for p in wpts]
    if model.feedline:
        pts += [P(p) for p in model.feedline[0]]
    ground_world = None
    if model.ground and proj_view != "top":
        xs = [p[0] for w, _ in model.wires for p in w] + ([p[0] for p in model.feedline[0]] if model.feedline else [])
        zs = [p[2] for w, _ in model.wires for p in w] + ([p[2] for p in model.feedline[0]] if model.feedline else [])
        span = max(max(xs) - min(xs), 1e-6)
        mg = 0.07 * span
        ground_world = [(min(xs) - mg, 0, min(min(zs), 0) - mg), (max(xs) + mg, 0, min(min(zs), 0) - mg),
                        (max(xs) + mg, 0, max(max(zs), 0) + mg), (min(xs) - mg, 0, max(max(zs), 0) + mg)]
        pts += [P(p) for p in ground_world]
    minx, maxx = min(p[0] for p in pts), max(p[0] for p in pts)
    miny, maxy = min(p[1] for p in pts), max(p[1] for p in pts)
    w, h = max(maxx - minx, 1e-6), max(maxy - miny, 1e-6)
    s = min(GEO_W / w, GEO_H / h)
    gw, gh = w * s + 2 * GEO_PAD, h * s + 2 * GEO_PAD
    gw, gh = max(gw, 260), max(gh, 200)

    # ---- callout cards (measure first: they decide the columns and height)
    cards = []
    for (p3, cat, title, detail, views) in model.callouts:
        if view not in views:
            continue
        tl = _wrap(title, COL_W - 2 * CARD_PAD - 40, measure, "card_title")  # room for a component code
        dl = _wrap(detail, COL_W - 2 * CARD_PAD, measure, "card_detail") if detail else []
        ch = 2 * CARD_PAD + len(tl) * line_h("card_title") + len(dl) * line_h("card_detail")
        cards.append({"p3": p3, "cat": cat, "title": tl, "detail": dl, "h": ch})

    header_h = line_h("title") + line_h("sub") + 16
    top = MARGIN + header_h

    # provisional geo placement to split the cards left/right
    def to_px(p, gx0, gy0):
        x, y = P(p)
        return gx0 + GEO_PAD + (x - minx) * s + (gw - 2 * GEO_PAD - w * s) / 2, \
            gy0 + GEO_PAD + (y - miny) * s + (gh - 2 * GEO_PAD - h * s) / 2

    for c in cards:
        c["pp"] = to_px(c["p3"], 0, 0)
    left = [c for c in cards if c["pp"][0] < gw / 2]
    right = [c for c in cards if c["pp"][0] >= gw / 2]
    need_l = sum(c["h"] for c in left) + CARD_GAP * max(len(left) - 1, 0)
    need_r = sum(c["h"] for c in right) + CARD_GAP * max(len(right) - 1, 0)
    area_h = max(gh, need_l, need_r)

    gx0 = MARGIN + (COL_W + COL_GAP if left else 0)
    gy0 = top + (area_h - gh) / 2
    geo = (gx0, gy0, gx0 + gw, gy0 + gh)
    width = gx0 + gw + (COL_GAP + COL_W if right else 0) + MARGIN

    L = Layout(width=0, height=0, view=view, geo=geo)

    def PX(p):
        return to_px(p, gx0, gy0)

    # ---- geometry in px
    if ground_world:
        L.ground_poly = [PX(p) for p in ground_world]
    for wpts, role in model.wires:
        q = [PX(p) for p in wpts]
        if role == "support" and proj_view == "top":
            if math.dist(q[0], q[-1]) < 3:
                L.mast_dots.append(q[0])
                L.roles.add(role)
                continue
        L.wires.append((q, role))
        L.roles.add(role)
    if model.feedline:
        q = []
        for p in model.feedline[0]:
            pp = PX(p)
            if not q or math.dist(q[-1], pp) > 0.5:
                q.append(pp)
        L.feedline = (q, model.feedline[1])
        L.roles.add(model.feedline[1])
    L.boxes = [(*PX(p), k, t) for p, k, t in model.boxes]
    if L.boxes:
        L.roles.add("box")
    L.feed = PX(model.feed) if model.feed else None
    L.earths = [PX(p) for p in model.earths]
    if L.earths:
        L.roles.add("earth")
    L.insulators = [PX(p) for p in model.insulators]
    L.shack = PX(model.shack) if model.shack else None

    # obstacles for dimension labels
    segs = []
    for q, _ in L.wires:
        segs += list(zip(q, q[1:]))
    if L.feedline:
        segs += list(zip(L.feedline[0], L.feedline[0][1:]))
    rects = []
    bw, bh = SYMBOL_BOX
    for x, y, *_ in L.boxes:
        rects.append((x - bw / 2 - 2, y - bh / 2 - 2, x + bw / 2 + 2, y + bh / 2 + 2))
    for x, y in L.earths:
        rects.append((x - 14, y + 8, x + 14, y + 38))
    if L.shack:
        x, y = L.shack
        rects.append((x - 28, y - 46, x + 28, y + 12))
    if L.feed:
        rects.append((L.feed[0] - 7, L.feed[1] - 7, L.feed[0] + 7, L.feed[1] + 7))

    # ---- dimension lines + labels
    placed = []
    for p1, p2, label, views in model.dims:
        if view not in views:
            continue
        a, b = PX(p1), PX(p2)
        ln = math.dist(a, b)
        if ln < 26:
            continue
        ux, uy = (b[0] - a[0]) / ln, (b[1] - a[1]) / ln
        nx, ny = -uy, ux
        tw = measure("dim", label) + 8
        th = line_h("dim") + 2
        best = None
        for off in (22, -22, 38, -38, 56, -56, 76, -76, 100, -100):
            q1 = (a[0] + nx * off, a[1] + ny * off)
            q2 = (b[0] + nx * off, b[1] + ny * off)
            sgn = 1 if off > 0 else -1
            ext = abs(nx) * tw / 2 + abs(ny) * th / 2 + 3
            base = abs(off) / 100
            for sa, sb in ((q1, q2), (a, q1), (b, q2)):
                base += 8 * sum(_seg_hits_rect(sa, sb, r, 1) for r in rects)
            base += 2 * sum(_seg_hits_rect(sa, sb, (min(q1[0], q2[0]), min(q1[1], q2[1]),
                                                   max(q1[0], q2[0]), max(q1[1], q2[1])), 0)
                            for sa, sb in segs if not _seg_parallel(sa, sb, ux, uy))
            for tpos in (0.5, 0.32, 0.68, 0.18, 0.82):
                cx = q1[0] + (q2[0] - q1[0]) * tpos + nx * sgn * ext
                cy = q1[1] + (q2[1] - q1[1]) * tpos + ny * sgn * ext
                lr = (cx - tw / 2, cy - th / 2, cx + tw / 2, cy + th / 2)
                cost = base + abs(tpos - 0.5) * 1.5
                if lr[0] < geo[0] or lr[2] > geo[2] or lr[1] < geo[1] - 6 or lr[3] > geo[3] + 6:
                    cost += 50
                cost += 20 * sum(_seg_hits_rect(sa, sb, lr, 3) for sa, sb in segs)
                cost += 20 * sum(_rects_overlap(lr, r, 2) for r in rects)
                cost += 20 * sum(_rects_overlap(lr, pr, 3) for pr in placed)
                if best is None or cost < best[0]:
                    best = (cost, q1, q2, lr, (cx, cy))
        if best[0] >= 20:
            continue  # no clean spot: leave this dimension out rather than cover the drawing
        _, q1, q2, lr, mid = best
        placed.append(lr)
        L.dims.append({"p1": a, "p2": b, "q1": q1, "q2": q2, "label": label, "rect": lr, "mid": mid})

    # ---- callouts in the side columns
    for c in cards:
        c["pp"] = PX(c["p3"])
    col_top, col_bot = top, top + area_h
    code_n = {}
    for side, group in (("left", sorted(left, key=lambda c: c["pp"][1])),
                        ("right", sorted(right, key=lambda c: c["pp"][1]))):
        if not group:
            continue
        cx0 = MARGIN if side == "left" else geo[2] + COL_GAP
        y = col_top
        for c in group:
            c["y"] = max(y, min(c["pp"][1] - c["h"] / 2 + 30, col_bot - c["h"]))
            y = c["y"] + c["h"] + CARD_GAP
        overflow = group[-1]["y"] + group[-1]["h"] - col_bot
        if overflow > 0:
            limit = col_bot
            for c in reversed(group):
                c["y"] = min(c["y"], limit - c["h"])
                limit = c["y"] - CARD_GAP
        for c in group:
            rect = (cx0, c["y"], cx0 + COL_W, c["y"] + c["h"])
            cy = c["y"] + min(c["h"] / 2, CARD_PAD + line_h("card_title") / 2)
            edge = rect[2] if side == "left" else rect[0]
            knee = edge + (12 if side == "left" else -12)
            ax, ay = _anchor_on_edge(c, L, side)
            prefix = {"box": "T", "feedline": "F", "earth": "E"}.get(c["cat"], "W")
            code_n[prefix] = code_n.get(prefix, 0) + 1
            L.callouts.append({"anchor": (ax, ay), "rect": rect, "cat": c["cat"], "title": c["title"],
                               "detail": c["detail"], "leader": [(ax, ay), (knee, cy), (edge, cy)],
                               "side": side, "code": f"{prefix}{code_n[prefix]}"})

    # ---- header
    label = antenna_type_label(design.antenna_type, lang)
    title = T["title"].format(label=label, band=design.band, freq=_fmt_num(design.design_freq_mhz, ".3f", lang))
    sub = T["subtitle"].format(z=f"{design.feedpoint_impedance_ohms:.0f}", balun=design.balun["type"])
    L.header.append((MARGIN, MARGIN, title, "title", "nw"))
    L.header.append((MARGIN, MARGIN + line_h("title") + 2, sub + "   ·   " + T["note"], "sub", "nw"))
    width = max(width, MARGIN * 2 + measure("title", title) + 20,
                MARGIN * 2 + measure("sub", sub + "   ·   " + T["note"]) + 20)

    # ---- legend
    order = [("radiator", "legend_radiator"), ("parasitic", "legend_parasitic"), ("stub", "legend_stub"),
             ("counterpoise", "legend_counterpoise"), ("coax", "legend_coax"), ("ladder", "legend_ladder"),
             ("box", "legend_box"), ("earth", "legend_earth"), ("support", "legend_support")]
    present = set(L.roles) | ({"support"} if {"rope", "boom"} & L.roles else set())
    items = [(k, T[t]) for k, t in order if k in present]
    x, y = MARGIN, top + area_h + 18
    lh = max(line_h("legend"), 18)
    for k, txt in items:
        wi = 40 + measure("legend", txt) + 26
        if x + wi > width - MARGIN and x > MARGIN:
            x, y = MARGIN, y + lh + 8
        L.legend.append((x, y, k, txt))
        x += wi
    L.width = width
    L.height = y + lh + MARGIN
    # re-centre the drawing when the header made the page wider than the columns
    extra = L.width - (gx0 + gw + (COL_GAP + COL_W if right else 0) + MARGIN)
    if extra > 1:
        _shift_x(L, extra / 2, right_cards_extra=extra / 2)
    return L


def _anchor_on_edge(c, L, side):
    """A callout on a symbol (box, TX/shack, ground rod) is anchored on the
    symbol's edge facing its card, so the leader never crosses its text."""
    ax, ay = c["pp"]
    sgn = -1 if side == "left" else 1
    if c["cat"] == "box":
        for x, y, *_ in L.boxes:
            if abs(x - ax) < 1 and abs(y - ay) < 1:
                return x + sgn * 23, y
    if c["cat"] == "earth":
        return ax + sgn * 13, ay + 30
    return ax, ay


def _seg_parallel(a, b, ux, uy):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    return n > 0 and abs(dx / n * uy - dy / n * ux) < 0.05


def _shift_x(L: Layout, dx: float, right_cards_extra: float = 0.0):
    """Move the drawing (and its right-hand column) sideways by dx."""
    def sh(p):
        return (p[0] + dx, p[1])
    L.geo = (L.geo[0] + dx, L.geo[1], L.geo[2] + dx, L.geo[3])
    if L.ground_poly:
        L.ground_poly = [sh(p) for p in L.ground_poly]
    L.wires = [([sh(p) for p in q], r) for q, r in L.wires]
    L.mast_dots = [sh(p) for p in L.mast_dots]
    if L.feedline:
        L.feedline = ([sh(p) for p in L.feedline[0]], L.feedline[1])
    L.boxes = [(x + dx, y, k, t) for x, y, k, t in L.boxes]
    L.feed = sh(L.feed) if L.feed else None
    L.earths = [sh(p) for p in L.earths]
    L.insulators = [sh(p) for p in L.insulators]
    L.shack = sh(L.shack) if L.shack else None
    for dm in L.dims:
        for k in ("p1", "p2", "q1", "q2", "mid"):
            dm[k] = sh(dm[k])
        r = dm["rect"]
        dm["rect"] = (r[0] + dx, r[1], r[2] + dx, r[3])
    for c in L.callouts:
        cdx = dx + (right_cards_extra if c["side"] == "right" else 0)
        c["anchor"] = sh(c["anchor"])
        r = c["rect"]
        c["rect"] = (r[0] + (cdx if c["side"] == "right" else 0), r[1], r[2] + (cdx if c["side"] == "right" else 0), r[3])
        lead = c["leader"]
        if c["side"] == "right":
            c["leader"] = [sh(lead[0]), (lead[1][0] + cdx, lead[1][1]), (lead[2][0] + cdx, lead[2][1])]
        else:
            c["leader"] = [sh(lead[0]), lead[1], lead[2]]
