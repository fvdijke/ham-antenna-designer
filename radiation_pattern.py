"""Radiation patterns computed from the antenna's actual geometry.

Every antenna is modelled as wire paths (polylines, in metres) carrying its
standing-wave current:

* center-fed wires   I(s) = sin(k * distance to the nearest wire end)
* end-fed wires      I(s) = sin(k * distance to the far end)
* resonant loops     I(s) = cos(k * distance from the feedpoint)

The far field is the sum over short segments (Hertzian dipoles):
    E(r) ~ sum  I * dl * [u - (u.r) r] * exp(j k r.p)
split into its horizontally and vertically polarised parts.

Ground: the reflected wave comes from the mirror image (horizontal currents
reversed, vertical currents unchanged, as over a perfect conductor) and is
weighted with the Fresnel reflection coefficients of real ground
(average ground: eps_r = 13, sigma = 0.005 S/m):
    Rv = (ec*s - sqrt(ec - c^2)) / (ec*s + sqrt(ec - c^2))
    Rh = (s - sqrt(ec - c^2)) / (s + sqrt(ec - c^2))
    s = sin(elevation), c = cos(elevation), ec = eps_r - j*60*lambda*sigma
so vertical antennas lose their lowest angles over real ground exactly as
they do in practice. The gain is the directivity over the upper hemisphere:
ground reflection included, ground LOSSES (and wire losses) not -- real
verticals typically lose a further 1-3 dB in the ground.

Beams: the element currents of the 3-element Yagi and the 2-element quad
are solved from the mutual impedances of parallel half-wave dipoles
(induced-EMF method, Kraus) and each element's self-reactance from its
length relative to the resonant driven element. The Moxon's reflector
current is set for its design goal, a null straight to the back.

Coordinates: x along the (driven) wire, y = forward / broadside, z = up.
Azimuth 0 deg = +y, clockwise; elevation 0 deg = horizon.
"""

import cmath
import math

C_MPS = 299.792458  # m * MHz
EULER_GAMMA = 0.5772156649015329
WIRE_RADIUS_M = 0.001

GROUNDS = {"average": (13.0, 0.005), "perfect": None, "free": None}


# ------------------------------------------------------------ math helpers

def _simpson(fn, a, b, n=400):
    h = (b - a) / n
    total = fn(a) + fn(b)
    for i in range(1, n):
        total += (4 if i % 2 else 2) * fn(a + i * h)
    return total * h / 3


def _si(x):
    return _simpson(lambda t: math.sin(t) / t if t else 1.0, 0.0, x)


def _ci(x):
    return EULER_GAMMA + math.log(x) + _simpson(lambda t: (math.cos(t) - 1) / t if t else 0.0, 0.0, x)


def mutual_impedance(d_m: float, wavelength: float) -> complex:
    """Mutual impedance of two parallel side-by-side half-wave dipoles
    at spacing d (induced-EMF method, Kraus 'Antennas' eq. 10-4)."""
    k = 2 * math.pi / wavelength
    L = wavelength / 2
    u0 = k * d_m
    u1 = k * (math.sqrt(d_m ** 2 + L ** 2) + L)
    u2 = k * (math.sqrt(d_m ** 2 + L ** 2) - L)
    r = 30 * (2 * _ci(u0) - _ci(u1) - _ci(u2))
    x = -30 * (2 * _si(u0) - _si(u1) - _si(u2))
    return complex(r, x)


def _z0_wire(wavelength: float) -> float:
    return 120 * (math.log(wavelength / (2 * WIRE_RADIUS_M)) - 1)


def self_impedance(length_m: float, resonant_m: float, wavelength: float, r_rad: float = 73.1) -> complex:
    """Self impedance of a (near) resonant element: radiation resistance plus
    a reactance proportional to its detuning from the resonant length (the
    same reactance slope, pi * Z0 per wavelength, as the SWR sweep model)."""
    return complex(r_rad, _z0_wire(wavelength) * math.pi * (length_m - resonant_m) / wavelength)


# ------------------------------------------------------------ wire model

class _Model:
    def __init__(self, wavelength: float):
        self.wavelength = wavelength
        self.k = 2 * math.pi / wavelength
        self.segs = []  # (x, y, z, ux, uy, uz, I*dl)
        self.vertical = False  # dominant polarisation (for the info line)

    def path(self, points, current_fn, scale=1.0, seg_per_wl=40):
        """Add a polyline; current_fn(s, total_length) gives the current at
        path distance s (along the path direction)."""
        lengths = [math.dist(points[i], points[i + 1]) for i in range(len(points) - 1)]
        total = sum(lengths)
        s0 = 0.0
        for (p, q), seg_len in zip(zip(points, points[1:]), lengths):
            if seg_len <= 0:
                continue
            n = max(3, int(math.ceil(seg_len / self.wavelength * seg_per_wl)))
            dl = seg_len / n
            ux, uy, uz = ((q[i] - p[i]) / seg_len for i in range(3))
            for j in range(n):
                t = (j + 0.5) * dl
                x, y, z = (p[i] + (q[i] - p[i]) * t / seg_len for i in range(3))
                self.segs.append((x, y, z, ux, uy, uz, scale * current_fn(s0 + t, total) * dl))
            s0 += seg_len
        return total

    # standing-wave current shapes
    def center_fed(self, s, total):
        return math.sin(self.k * min(s, total - s))

    def end_fed(self, s, total):  # fed at s = 0, open far end
        return math.sin(self.k * (total - s))

    def loop(self, s, total):  # fed at s = 0 (and s = total)
        return math.cos(self.k * min(s, total - s))


def _square_horizontal(side, z):
    h = side / 2
    # starts at the middle of the front (-y) side, feedpoint there
    return [(0, -h, z), (h, -h, z), (h, h, z), (-h, h, z), (-h, -h, z), (0, -h, z)]


def _square_vertical(side, y, z_bottom):
    h = side / 2
    zt = z_bottom + side
    return [(0, y, z_bottom), (h, y, z_bottom), (h, y, zt), (-h, y, zt), (-h, y, z_bottom), (0, y, z_bottom)]


def _lengths(design, role):
    return [e.length_m for e in design.elements if e.role == role]


def default_height(design) -> float:
    """Height of the lowest point (feed/base) used when the user gives none."""
    t = design.antenna_type
    if t in ("vertical_quarter_wave", "five_eighths_vertical", "vertical_half_wave", "vertical_full_wave"):
        return 0.0
    if t == "ground_loop_receive":
        return 0.05
    return 10.0


def default_ground(design) -> str:
    return "average" if design.design_freq_mhz < 50 else "free"


def build_model(design, height_m: float, ground: str = "average") -> _Model:
    """Wire model at height_m. Ground-plane verticals get their radials
    modelled when they are elevated (free space or more than 0.5 m up);
    on the ground the buried/laid radials only act as the ground return."""
    wavelength = C_MPS / design.design_freq_mhz
    elevated = ground == "free" or height_m > 0.5
    m = _Model(wavelength)
    t = design.antenna_type
    H = max(0.0, height_m)
    radiators = _lengths(design, "radiator")

    if t in ("dipole_half_wave", "extended_double_zepp", "off_center_fed_dipole"):
        L = sum(e.length_m for e in design.elements)
        m.path([(-L / 2, 0, H), (L / 2, 0, H)], m.center_fed)
    elif t in ("efhw", "longwire_receive"):
        L = radiators[0]
        m.path([(-L / 2, 0, H), (L / 2, 0, H)], m.end_fed)
    elif t == "inverted_v_dipole":
        leg = radiators[0]
        droop = math.radians(45) if H - 1.0 >= leg * math.sin(math.radians(45)) else \
            math.asin(max(0.0, min(1.0, (H - 1.0) / leg))) if H > 1.0 else 0.0
        dx, dz = leg * math.cos(droop), leg * math.sin(droop)
        m.path([(-dx, 0, H - dz), (0, 0, H), (dx, 0, H - dz)], m.center_fed)
    elif t in ("vertical_quarter_wave", "five_eighths_vertical"):
        L = radiators[0]
        m.path([(0, 0, H), (0, 0, H + L)], m.end_fed)  # current maximum at the base
        m.vertical = True
        if elevated:
            # Elevated ground plane: the base current returns through the
            # radials (each I0/4 flowing INTO the base, zero at the tip).
            radials = _lengths(design, "radial")
            i0 = math.sin(m.k * L)
            for n, lr in enumerate(radials):
                ang = 2 * math.pi * n / len(radials) + math.pi / 4
                tip = (lr * math.cos(ang), lr * math.sin(ang), H)
                scale = i0 / (len(radials) * math.sin(m.k * lr)) if math.sin(m.k * lr) else 0.0
                m.path([tip, (0, 0, H)], lambda s, total: math.sin(m.k * s), scale=scale)
    elif t in ("vertical_half_wave", "vertical_full_wave"):
        L = radiators[0]
        m.path([(0, 0, H), (0, 0, H + L)], m.end_fed)
        m.vertical = True
    elif t == "j_pole":
        L = radiators[0]
        stub = _lengths(design, "matching_stub")[0]
        m.path([(0, 0, H + stub), (0, 0, H + stub + L)], m.end_fed)
        m.vertical = True
    elif t == "discone_receive":
        L = 0.95 * wavelength / 2  # behaves like a vertical dipole at the design frequency
        m.path([(0, 0, H + 0.1), (0, 0, H + 0.1 + L)], m.center_fed)
        m.vertical = True
    elif t in ("loop_full_wave", "ground_loop_receive"):
        m.path(_square_horizontal(radiators[0] / 4, H), m.loop)
    elif t == "delta_loop_vertical":
        side = radiators[0] / 3
        apex = H + side * math.sqrt(3) / 2
        m.path([(0, 0, H), (side / 2, 0, H), (0, 0, apex), (-side / 2, 0, H), (0, 0, H)], m.loop)
    elif t == "yagi_3_element":
        _yagi(design, m, H)
    elif t == "quad_2_element":
        _quad(design, m, H)
    elif t == "moxon_2_element":
        _moxon(design, m, H)
    else:
        raise ValueError(f"No pattern model for '{t}'")
    return m


def _yagi(design, m, H):
    lam = m.wavelength
    driven = _lengths(design, "radiator")[0]
    refl = _lengths(design, "reflector")[0]
    direc = _lengths(design, "director")[0]
    sr, sd = design.extra["reflector_spacing_m"], design.extra["director_spacing_m"]
    ys = [-sr, 0.0, sd]
    lens = [refl, driven, direc]
    z = [[None] * 3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            z[i][j] = self_impedance(lens[i], driven, lam) if i == j else mutual_impedance(abs(ys[i] - ys[j]), lam)
    currents = _solve3(z, [0, 1, 0])
    m.feed_impedance = 1 / currents[1]
    for y, L, cur in zip(ys, lens, currents):
        m.path([(-L / 2, y, H), (L / 2, y, H)], m.center_fed, scale=cur)


def _solve3(a, b):
    """Gaussian elimination for a small complex system."""
    n = len(b)
    a = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(a[r][c]))
        a[c], a[p] = a[p], a[c]
        for r in range(n):
            if r != c:
                f = a[r][c] / a[c][c]
                for k in range(c, n + 1):
                    a[r][k] -= f * a[c][k]
    return [a[i][n] / a[i][i] for i in range(n)]


def _quad(design, m, H):
    lam = m.wavelength
    pd = design.elements_with_role("driven_loop")[0].length_m
    pr = design.elements_with_role("reflector_loop")[0].length_m
    s = design.extra["spacing_m"]
    # a one-wavelength loop ~ two half-wave dipoles stacked lambda/4 apart:
    # self resistance ~120 ohm, mutual ~2x that of single dipoles
    z11 = self_impedance(pd, pd, lam, r_rad=120.0)
    z22 = self_impedance(pr / 2, pd / 2, lam, r_rad=120.0)
    z12 = 2 * mutual_impedance(s, lam)
    i_r = -z12 / z22
    m.feed_impedance = z11 + z12 * i_r
    m.path(_square_vertical(pd / 4, 0.0, H), m.loop)
    m.path(_square_vertical(pr / 4, -s, H), m.loop, scale=i_r)


def _moxon(design, m, H):
    ex = design.extra
    a, b, d, e = ex["a_m"], ex["b_m"], ex["d_m"], ex["e_m"]
    k = m.k
    driven = [(-a / 2, -b, H), (-a / 2, 0, H), (a / 2, 0, H), (a / 2, -b, H)]
    refl = [(-a / 2, -e + d, H), (-a / 2, -e, H), (a / 2, -e, H), (a / 2, -e + d, H)]
    m.path(driven, m.center_fed)
    # Moxon design goal: the reflector cancels the driven element straight
    # to the back (-y): I_r = -0.9 * exp(-j k E)  (0.9 keeps a finite F/B,
    # as the real antenna has)
    m.path(refl, m.center_fed, scale=-0.9 * cmath.exp(-1j * k * e))


# ------------------------------------------------------------ far field

def _field(model: _Model, elev_deg: float, az_deg: float, ground: str):
    """|E|^2 (arbitrary units) in one direction."""
    el, az = math.radians(elev_deg), math.radians(az_deg)
    ce, se, ca, sa = math.cos(el), math.sin(el), math.cos(az), math.sin(az)
    rx, ry, rz = ce * sa, ce * ca, se
    hx, hy = ca, -sa  # horizontal polarisation unit (hz = 0)
    vx, vy, vz = -se * sa, -se * ca, ce
    k = model.k
    eh = ev = 0j
    ih = iv = 0j
    use_ground = ground in ("average", "perfect") and elev_deg >= 0
    for x, y, z, ux, uy, uz, idl in model.segs:
        ph = cmath.exp(1j * k * (rx * x + ry * y + rz * z)) * idl
        eh += (ux * hx + uy * hy) * ph
        ev += (ux * vx + uy * vy + uz * vz) * ph
        if use_ground:
            # image: horizontal current reversed, vertical kept, z mirrored
            phi = cmath.exp(1j * k * (rx * x + ry * y - rz * z)) * idl
            ih += (-ux * hx - uy * hy) * phi
            iv += (-ux * vx - uy * vy + uz * vz) * phi
    if use_ground:
        if ground == "perfect":
            rh, rv = -1.0, 1.0
        else:
            eps_r, sigma = GROUNDS["average"]
            ec = complex(eps_r, -60 * model.wavelength * sigma)
            root = cmath.sqrt(ec - ce * ce)
            rv = (ec * se - root) / (ec * se + root)
            rh = (se - root) / (se + root)
        eh += -rh * ih
        ev += rv * iv
    return abs(eh) ** 2 + abs(ev) ** 2


def compute_pattern(design, height_m: float = None, ground: str = None) -> dict:
    """Full analysis: gain (dBi), take-off angle, F/B, beamwidth, and the
    azimuth and elevation cuts (dBi per degree)."""
    if height_m is None:
        height_m = default_height(design)
    if ground is None:
        ground = default_ground(design)
    model = build_model(design, height_m, ground)
    over_ground = ground in ("average", "perfect")

    # directivity: integrate U over the sphere / upper hemisphere (3 x 6 deg grid)
    d_el, d_az = 3.0, 6.0
    el_lo = 0.0 if over_ground else -90.0
    total = 0.0
    best = (-1.0, 0.0, 0.0)
    el = el_lo + d_el / 2
    while el < 90:
        w = math.cos(math.radians(el)) * math.radians(d_el) * math.radians(d_az)
        az = d_az / 2
        while az < 360:
            u = _field(model, el, az, ground)
            total += u * w
            if u > best[0]:
                best = (u, el, az)
            az += d_az
        el += d_el
    # refine the maximum on a 1-degree grid around the coarse peak
    _, el0, az0 = best
    for el in [el0 + i for i in range(-3, 4)]:
        if el < el_lo or el > 90:
            continue
        for az in [az0 + i for i in range(-6, 7)]:
            u = _field(model, el, az % 360, ground)
            if u > best[0]:
                best = (u, el, az % 360)
    u_max, el_max, az_max = best
    gain_dbi = 10 * math.log10(4 * math.pi * u_max / total) if total > 0 else 0.0

    def dbi(u):
        return gain_dbi + 10 * math.log10(max(u, 1e-30) / u_max)

    # azimuth cut at the take-off angle (at 30 deg when radiation goes mostly up)
    az_elev = el_max if el_max <= 60 else 30.0
    if not over_ground:
        az_elev = max(0.0, min(el_max, 60.0))
    az_cut = [dbi(_field(model, az_elev, a, ground)) for a in range(360)]
    # elevation cut through the main azimuth: 0..180 over ground, full circle in free space
    el_range = range(0, 181) if over_ground else range(-90, 271)
    el_cut = []
    for e in el_range:
        if e <= 90:
            el_cut.append(dbi(_field(model, e, az_max, ground)))
        else:
            el_cut.append(dbi(_field(model, 180 - e, (az_max + 180) % 360, ground)))

    front = _field(model, az_elev, az_max, ground)
    back = _field(model, az_elev, (az_max + 180) % 360, ground)
    fb_db = 10 * math.log10(front / back) if back > 0 else 60.0

    # -3 dB azimuth beamwidth around the main lobe
    peak_idx = max(range(360), key=lambda i: az_cut[i])
    peak = az_cut[peak_idx]
    width = 0
    for direction in (-1, 1):
        i = 0
        while i < 180 and az_cut[(peak_idx + direction * (i + 1)) % 360] >= peak - 3:
            i += 1
        width += i
    beamwidth = None if width >= 358 else width

    return {
        "gain_dbi": round(gain_dbi, 1),
        "gain_dbd": round(gain_dbi - 2.15, 1),
        "takeoff_angle_deg": round(el_max) if over_ground else None,  # no horizon in free space
        "max_azimuth_deg": round(az_max),
        "f_b_ratio_db": round(min(fb_db, 40.0), 1),
        "beamwidth_deg": beamwidth,
        "azimuth_elevation_deg": round(az_elev),
        "azimuth_cut": az_cut,
        "elevation_cut": el_cut,
        "elevation_angles": list(el_range),
        "height_m": height_m,
        "ground": ground,
        "polarization": "vertical" if model.vertical else "horizontal",
        "feed_impedance": getattr(model, "feed_impedance", None),
    }


# ------------------------------------------------------------ compatibility

def calculate_gain_description(design_or_type, height_m: float = None, ground: str = None) -> dict:
    """Gain, F/B and take-off angle of a design (default height/ground)."""
    if isinstance(design_or_type, str):
        raise TypeError("calculate_gain_description needs an AntennaDesign in v5.8")
    p = compute_pattern(design_or_type, height_m, ground)
    return {
        "antenna_type": design_or_type.antenna_type,
        "gain_dbi": p["gain_dbi"],
        "gain_dbd": p["gain_dbd"],
        "f_b_ratio_db": p["f_b_ratio_db"],
        "takeoff_angle_deg": p["takeoff_angle_deg"],
        "height_m": p["height_m"],
        "ground": p["ground"],
    }
