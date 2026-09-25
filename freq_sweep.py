"""SWR versus frequency for the antenna AS BUILT.

The dimensions are fixed at the design frequency f0 (they already include
the wire's length factor, so the built antenna resonates at f0); away from
f0 the feedpoint impedance changes. Near resonance every wire antenna
behaves like a resonant circuit:

* center/base-fed types (dipole, quarter-wave vertical, loops, beams):
  SERIES resonance      Z = R0 * (1 + j*Q*y)
* end-fed half/full-wave types (EFHW, half/full-wave vertical):
  PARALLEL resonance    Z = R0 / (1 + j*Q*y)

with y = f/f0 - f0/f. Q follows from the wire's average characteristic
impedance (Schelkunoff, thin dipole of length lambda/2 and radius a):

    Z0 = 120 * (ln(lambda / (2a)) - 1)       Q_dipole = pi * Z0 / (4 * 73)

(a half-wave dipole's reactance slope near resonance is Z0 * pi/2 per unit
of relative detuning). For 2 mm wire this gives Q ~ 10-11 on 20 m, i.e. a
2:1-SWR bandwidth of roughly 5 %, in line with measured wire dipoles. Each
antenna type scales that Q (beams store more energy, loops less). The
feedpoint impedance is then referred to the coax side through the balun or
unun ratio (49:1, 9:1, 4:1, ...) before the SWR is taken against 50 ohm.

Broadband receive antennas and tuner-fed antennas (EDZ on open-wire line)
have no meaningful single-resonance SWR curve: they are reported as such.
"""

import math

import calculators  # noqa: F401 -- registers all antenna calculator types
from registry import design as design_antenna
from swr_calc import calculate_return_loss, calculate_swr, transformer_ratio

WIRE_RADIUS_M = 0.001  # 2 mm wire, the same default as the Moxon calculator

# antenna type -> (resonance kind, Q multiplier relative to a wire dipole)
SWEEP_MODEL = {
    "dipole_half_wave": ("series", 1.0),
    "inverted_v_dipole": ("series", 1.1),
    "off_center_fed_dipole": ("series", 1.0),
    "vertical_quarter_wave": ("series", 1.0),
    "five_eighths_vertical": ("series", 1.3),   # base coil stores extra energy
    "j_pole": ("series", 1.5),                  # plus the quarter-wave stub
    "loop_full_wave": ("series", 0.8),
    "delta_loop_vertical": ("series", 0.8),
    "yagi_3_element": ("series", 2.0),
    "quad_2_element": ("series", 1.3),
    "moxon_2_element": ("series", 1.3),
    "efhw": ("parallel", 1.0),
    "vertical_half_wave": ("parallel", 1.0),
    "vertical_full_wave": ("parallel", 1.2),
}
BROADBAND_TYPES = {"longwire_receive", "discone_receive", "ground_loop_receive"}
TUNER_TYPES = {"extended_double_zepp"}


def dipole_q(freq_mhz: float) -> float:
    wavelength = 299.792458 / freq_mhz
    z0 = 120 * (math.log(wavelength / (2 * WIRE_RADIUS_M)) - 1)
    return math.pi * z0 / (4 * 73.0)


def model_impedance(design, freq_mhz: float) -> complex:
    """Feedpoint impedance of the built antenna at freq_mhz, referred to
    the coax side of its balun/unun."""
    kind, q_mult = SWEEP_MODEL[design.antenna_type]
    f0 = design.design_freq_mhz
    q = dipole_q(f0) * q_mult
    y = freq_mhz / f0 - f0 / freq_mhz
    r0 = float(design.feedpoint_impedance_ohms)
    z = r0 * (1 + 1j * q * y) if kind == "series" else r0 / (1 + 1j * q * y)
    return z / transformer_ratio(design.balun.get("ratio", "1:1"))


def _edges(design, f0: float, swr_limit: float, z0: float):
    """Frequencies where the SWR crosses swr_limit (bisection on the model)."""
    def excess(f):
        return calculate_swr(model_impedance(design, f), z0) - swr_limit

    if excess(f0) > 0:
        return None
    edges = []
    for direction in (-1, 1):
        inside, outside = f0, f0
        step = f0 * 0.005
        while excess(outside) <= 0 and step < f0 * 0.9:
            outside = f0 + direction * step
            step *= 1.6
        if excess(outside) <= 0:
            edges.append(outside)
            continue
        for _ in range(60):
            mid = (inside + outside) / 2
            if excess(mid) <= 0:
                inside = mid
            else:
                outside = mid
        edges.append(inside)
    return (min(edges), max(edges))


def sweep_design(design, freq_start_mhz: float, freq_end_mhz: float,
                 points: int = 301, z0: float = 50.0) -> dict:
    """SWR sweep of an existing AntennaDesign. The range is widened to at
    least +-1.5 % around the design frequency so narrow bands (60 m) still
    show the shape of the curve."""
    t = design.antenna_type
    if t in BROADBAND_TYPES:
        return {"not_applicable": "broadband"}
    if t in TUNER_TYPES or t not in SWEEP_MODEL:
        return {"not_applicable": "tuner"}

    f0 = design.design_freq_mhz
    lo = min(freq_start_mhz, f0 * 0.985)
    hi = max(freq_end_mhz, f0 * 1.015)
    step = (hi - lo) / (points - 1)
    freqs = [lo + i * step for i in range(points)]
    zs = [model_impedance(design, f) for f in freqs]
    swrs = [min(calculate_swr(z, z0), 999.0) for z in zs]

    i_min = min(range(points), key=lambda i: swrs[i])
    bw2 = _edges(design, f0, 2.0, z0)
    bw15 = _edges(design, f0, 1.5, z0)
    kind, q_mult = SWEEP_MODEL[t]
    return {
        "frequencies": [round(f, 5) for f in freqs],
        "swr_values": swrs,
        "impedances": zs,
        "return_loss": [calculate_return_loss(z, z0) for z in zs],
        "resonance_freq": round(f0, 4),
        "min_swr": round(calculate_swr(model_impedance(design, f0), z0), 2),
        "min_swr_sampled_freq": round(freqs[i_min], 4),
        "bandwidth_2": tuple(round(f, 4) for f in bw2) if bw2 else None,
        "bandwidth_15": tuple(round(f, 4) for f in bw15) if bw15 else None,
        "band_edges": (freq_start_mhz, freq_end_mhz),
        "q": round(dipole_q(f0) * q_mult, 1),
        "model": kind,
    }


def sweep_antenna_response(antenna_type: str, band: str, freq_start_mhz: float,
                           freq_end_mhz: float, step_mhz: float = None,
                           lang: str = "en", wire_vf: float = 1.0) -> dict:
    """Design the antenna for the band, then sweep it (compatibility API)."""
    design = design_antenna(antenna_type, band, lang=lang, wire_vf=wire_vf)
    points = 301
    if step_mhz:
        points = max(21, min(2001, int((freq_end_mhz - freq_start_mhz) / step_mhz) + 1))
    return sweep_design(design, freq_start_mhz, freq_end_mhz, points=points)


def calculate_bandwidth(sweep_data: dict, swr_limit: float = 2.0) -> dict:
    """Bandwidth summary for SWR <= 2 (or 1.5) from a sweep result."""
    edges = sweep_data.get("bandwidth_2" if swr_limit >= 2.0 else "bandwidth_15")
    if not edges:
        return {}
    low, high = edges
    center = (low + high) / 2
    return {
        "center_freq": round(center, 4),
        "bandwidth": round(high - low, 4),
        "relative_bandwidth": round((high - low) / center * 100, 1),
        "low_freq": low,
        "high_freq": high,
        "swr_limit": swr_limit,
    }
