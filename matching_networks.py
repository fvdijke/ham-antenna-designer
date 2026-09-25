"""Impedance matching networks: L, Pi and T, for a real source (typically
50 ohm) and a possibly COMPLEX load (antenna R + jX).

Every network is returned as a list of components ordered from the source
to the load, each either "series" or "shunt" with its reactance X at the
design frequency (X > 0 = inductor, X < 0 = capacitor). The input impedance
is then recomputed by cascading the components onto the load, so every
result carries its own proof (``zin`` should equal the source resistance),
plus the SWR you get after rounding the parts to E12 standard values.

Design equations
----------------
L-network (Pozar, Microwave Engineering, ch. 5.1), load Z = R + jX, source Rs:
  * shunt element at the LOAD side (needs R^2 + X^2 > Rs*R, always when R > Rs):
        B = (X +- sqrt(R/Rs) * sqrt(R^2 + X^2 - Rs*R)) / (R^2 + X^2)
        Xs = 1/B + X*Rs/R - Rs/(B*R)
  * shunt element at the SOURCE side (needs R < Rs):
        Xs = +-sqrt(R*(Rs - R)) - X
        B  = +-sqrt((Rs - R)/R) / Rs
  Both signs are valid solutions; together they give up to four L-networks.

Pi (low-pass, C-L-C to ground) and T (high-pass, series C - shunt L -
series C, the usual amateur "T-match" tuner) use a virtual resistance Rv
set by the chosen loaded Q: two back-to-back L-sections, each designed as
Q_i = sqrt(Rbig/Rsmall - 1). The load reactance is absorbed in the element
next to the load (shunt for the Pi, series for the T).
"""

import math
import re

E12 = (1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2)

_EPS = 1e-9


# ---------------------------------------------------------------- helpers

def parse_impedance(text) -> complex:
    """Parse "73", "73+j42", "36-j20", "36 - 20j", "2450,5" -> complex ohms."""
    if isinstance(text, (int, float, complex)):
        return complex(text)
    s = str(text).strip().lower().replace(" ", "").replace(",", ".").replace("i", "j")
    s = s.replace("ω", "").replace("ohm", "").replace("ohms", "")
    m = re.fullmatch(r"([+-]?\d+(?:\.\d*)?)?(?:([+-])j?(\d+(?:\.\d*)?)j?)?", s)
    if not s or not m or (m.group(1) is None and m.group(2) is None):
        m2 = re.fullmatch(r"([+-]?)j(\d+(?:\.\d*)?)", s)  # pure reactance "j50"
        if m2:
            return complex(0, float(m2.group(2)) * (-1 if m2.group(1) == "-" else 1))
        raise ValueError(f"Cannot read impedance '{text}' (use e.g. 50, 73+j42 or 36-j20)")
    r = float(m.group(1)) if m.group(1) else 0.0
    x = 0.0
    if m.group(2):
        x = float(m.group(3)) * (-1 if m.group(2) == "-" else 1)
    return complex(r, x)


def format_impedance(z: complex) -> str:
    z = complex(z)
    sign = "+" if z.imag >= 0 else "-"
    return f"{z.real:.1f} {sign} j{abs(z.imag):.1f} Ω"


def nearest_e12(value: float) -> float:
    """Nearest E12 value (in the logarithmic sense) to a positive value."""
    if value <= 0:
        return value
    decade = math.floor(math.log10(value))
    mant = value / 10 ** decade
    candidates = list(E12) + [10.0]
    best = min(candidates, key=lambda e: abs(math.log(e / mant)))
    return best * 10 ** decade


def format_inductance(henry: float) -> str:
    uh = henry * 1e6
    if uh >= 1000:
        return f"{uh / 1000:.3g} mH"
    if uh >= 1:
        return f"{uh:.3g} µH"
    return f"{uh * 1000:.3g} nH"


def format_capacitance(farad: float) -> str:
    pf = farad * 1e12
    if pf >= 1e6:
        return f"{pf / 1e6:.3g} µF"
    if pf >= 1000:
        return f"{pf / 1000:.3g} nF"
    return f"{pf:.3g} pF"


def _component(position: str, x: float, omega: float) -> dict:
    """A series/shunt element with reactance x (ohm) at omega."""
    if x > 0:
        value = x / omega
        return {"position": position, "kind": "L", "reactance_ohm": x, "value": value,
                "display": format_inductance(value), "e12": format_inductance(nearest_e12(value)),
                "e12_value": nearest_e12(value)}
    value = -1 / (omega * x)
    return {"position": position, "kind": "C", "reactance_ohm": x, "value": value,
            "display": format_capacitance(value), "e12": format_capacitance(nearest_e12(value)),
            "e12_value": nearest_e12(value)}


def _element_x(comp: dict, omega: float, use_e12: bool) -> float:
    v = comp["e12_value"] if use_e12 else comp["value"]
    return omega * v if comp["kind"] == "L" else -1 / (omega * v)


def input_impedance(components: list, z_load: complex, omega: float, use_e12: bool = False) -> complex:
    """Cascade the components (ordered source -> load) onto the load."""
    z = complex(z_load)
    for comp in reversed(components):
        x = _element_x(comp, omega, use_e12)
        if comp["position"] == "series":
            z = z + 1j * x
        else:
            y = (1 / z if z != 0 else complex(1e12)) + 1 / (1j * x)
            z = 1 / y if y != 0 else complex(1e12)
    return z


def calculate_swr_from_impedance(z_antenna, z_source: float = 50) -> float:
    """SWR of a (complex) impedance against a real reference."""
    z = complex(z_antenna)
    if z + z_source == 0:
        return float("inf")
    gamma = abs((z - z_source) / (z + z_source))
    if gamma >= 1:
        return float("inf")
    return round((1 + gamma) / (1 - gamma), 2)


def nodal_q(components: list, z_load: complex, omega: float) -> float:
    """Loaded Q of a network: the highest |X|/R seen at any internal node
    while cascading from the load to the source (bandwidth ~ f / Q)."""
    z, q = complex(z_load), 0.0
    for comp in list(reversed(components))[:-1]:
        z = input_impedance([comp], z, omega)
        if z.real > 0:
            q = max(q, abs(z.imag) / z.real)
    if len(components) == 1:  # a single element: the Q of the load node it cancels
        q = abs(complex(z_load).imag) / complex(z_load).real
    return q


def _finish(net_type: str, components: list, z_load: complex, rs: float, omega: float) -> dict:
    components = [c for c in components if abs(c["reactance_ohm"]) < 1e9]
    q = nodal_q(components, z_load, omega)
    zin = input_impedance(components, z_load, omega)
    zin_e12 = input_impedance(components, z_load, omega, use_e12=True)
    kinds = tuple((c["position"], c["kind"]) for c in components)
    if net_type == "L":
        if set(kinds) == {("series", "L"), ("shunt", "C")}:
            name = "L_lowpass"
        elif set(kinds) == {("series", "C"), ("shunt", "L")}:
            name = "L_highpass"
        else:
            name = "L_other"
    else:
        name = net_type
    return {
        "type": net_type,
        "name": name,
        "components": components,
        "quality_factor": round(q, 2),
        "zin": zin,
        "swr": calculate_swr_from_impedance(zin, rs),
        "zin_e12": zin_e12,
        "swr_e12": calculate_swr_from_impedance(zin_e12, rs),
    }


def _validate(z_source: float, z_load: complex, freq_mhz: float):
    if z_source <= 0 or freq_mhz <= 0 or complex(z_load).real <= 0:
        raise ValueError("Source resistance, load resistance and frequency must be positive")


# ---------------------------------------------------------------- networks

def calculate_l_networks(z_source: float, z_load, freq_mhz: float) -> list:
    """All valid L-network solutions (2 to 4) for a real source and a
    complex load. Empty list when the load already equals the source."""
    zl = complex(z_load)
    _validate(z_source, zl, freq_mhz)
    rs, r, x = float(z_source), zl.real, zl.imag
    omega = 2 * math.pi * freq_mhz * 1e6
    if abs(zl - rs) < 1e-6:
        return []
    nets = []

    # shunt element across the load, series element toward the source
    disc = r * r + x * x - rs * r
    if disc >= 0:
        for sign in (1, -1):
            b = (x + sign * math.sqrt(r / rs) * math.sqrt(disc)) / (r * r + x * x)
            if abs(b) < _EPS:
                comps = [_component("series", -x, omega)] if abs(x) > _EPS else []
            else:
                xs = 1 / b + x * rs / r - rs / (b * r)
                comps = [_component("shunt", -1 / b, omega)]
                if abs(xs) > _EPS:
                    comps.insert(0, _component("series", xs, omega))
            if comps:
                nets.append(_finish("L", comps, zl, rs, omega))

    # series element at the load, shunt element across the source
    if r < rs:
        for sign in (1, -1):
            xs = sign * math.sqrt(r * (rs - r)) - x
            b = sign * math.sqrt((rs - r) / r) / rs
            comps = [_component("shunt", -1 / b, omega)]
            if abs(xs) > _EPS:
                comps.append(_component("series", xs, omega))
            nets.append(_finish("L", comps, zl, rs, omega))

    # drop numerical duplicates, lowpass first (harmonic suppression)
    unique, seen = [], set()
    for n in nets:
        key = tuple((c["position"], c["kind"], round(c["value"], 15)) for c in n["components"])
        if key not in seen:
            seen.add(key)
            unique.append(n)
    order = {"L_lowpass": 0, "L_highpass": 1, "L_other": 2}
    return sorted(unique, key=lambda n: order[n["name"]])


def minimum_q(z_source: float, z_load) -> float:
    """The (fixed) Q of an L-network; a Pi or T needs a higher Q."""
    zl = complex(z_load)
    rp = abs(zl) ** 2 / zl.real  # parallel-equivalent resistance
    lo, hi = min(z_source, zl.real, rp), max(z_source, zl.real, rp)
    return math.sqrt(hi / lo - 1)


def calculate_pi_network(z_source: float, z_load, freq_mhz: float, q_target: float = 5) -> dict:
    """Low-pass Pi: shunt C (source) - series L - shunt C (load)."""
    zl = complex(z_load)
    _validate(z_source, zl, freq_mhz)
    omega = 2 * math.pi * freq_mhz * 1e6
    rs = float(z_source)
    yl = 1 / zl
    rp, bl = 1 / yl.real, yl.imag  # load as Rp in parallel with susceptance bl
    q = max(q_target, math.sqrt(max(rs, rp) / min(rs, rp) - 1) * 1.1)
    rv = max(rs, rp) / (q * q + 1)
    q1 = math.sqrt(rs / rv - 1)
    q2 = math.sqrt(rp / rv - 1)
    comps = [
        _component("shunt", -1 / (q1 / rs), omega),
        _component("series", (q1 + q2) * rv, omega),
    ]
    b_load = q2 / rp - bl  # absorb the load susceptance
    if abs(b_load) > _EPS:
        comps.append(_component("shunt", -1 / b_load, omega))
    net = _finish("Pi", comps, zl, rs, omega)
    net["r_virtual_ohm"] = round(rv, 1)
    return net


def calculate_t_network(z_source: float, z_load, freq_mhz: float, q_target: float = 5) -> dict:
    """High-pass T: series C (source) - shunt L - series C (load)."""
    zl = complex(z_load)
    _validate(z_source, zl, freq_mhz)
    omega = 2 * math.pi * freq_mhz * 1e6
    rs, r, x = float(z_source), zl.real, zl.imag
    q = max(q_target, math.sqrt(max(rs, r) / min(rs, r) - 1) * 1.1)
    rv = min(rs, r) * (q * q + 1)
    q1 = math.sqrt(rv / rs - 1)
    q2 = math.sqrt(rv / r - 1)
    comps = [
        _component("series", -q1 * rs, omega),
        _component("shunt", rv / (q1 + q2), omega),
    ]
    x_load = -q2 * r - x  # absorb the load reactance
    if abs(x_load) > _EPS:
        comps.append(_component("series", x_load, omega))
    net = _finish("T", comps, zl, rs, omega)
    net["r_virtual_ohm"] = round(rv, 1)
    return net


def calculate_l_network(z_source: float, z_load, freq_mhz: float) -> dict:
    """The preferred single L-network (low-pass when possible)."""
    nets = calculate_l_networks(z_source, z_load, freq_mhz)
    return nets[0] if nets else {"error": "Load already matched"}


def suggest_matching_network(z_source: float, z_load, freq_mhz: float, q_target: float = None) -> list:
    """All L-network solutions plus a Pi and a T network. The Pi/T Q
    defaults to max(3, 1.5 x the L-network Q) -- a little above the minimum
    keeps the parts practical while the bandwidth stays usable."""
    zl = complex(z_load)
    nets = calculate_l_networks(z_source, zl, freq_mhz)
    if q_target is None:
        q_target = max(3.0, 1.5 * minimum_q(z_source, zl))
    nets.append(calculate_pi_network(z_source, zl, freq_mhz, q_target))
    nets.append(calculate_t_network(z_source, zl, freq_mhz, q_target))
    return nets


def standard_component_values(component_value: float, component_type: str = "L") -> str:
    """Nearest E12 value, formatted. component_value in µH (L) or pF (C)."""
    if component_type == "L":
        return format_inductance(nearest_e12(component_value * 1e-6))
    return format_capacitance(nearest_e12(component_value * 1e-12))
