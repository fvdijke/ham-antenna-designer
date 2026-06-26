"""Moxon rectangle (2-element directional, driven + reflector).

Uses the published L.B. Cebik (W4RNL) regression-equation method for Moxon
dimensions (the equation-based approach from his Moxon Rectangle design
notes), not a simplified guess. The equations are parametrized by wire
diameter as a fraction of wavelength:

    x = log10(wire_diameter / wavelength)
    A = AA*x^2 + AB*x + AC      (side-to-side span, both elements)
    B = BA*x^2 + BB*x + BC      (driven element tail length)
    C = CA*x^2 + CB*x + CC      (gap between driven and reflector tail tips)
    D = DA*x   + DB             (reflector element tail length)
    E = B + C + D               (front-to-back depth / boom length)

All of A-E are fractions of a wavelength. We assume a default wire diameter
of 2mm (roughly AWG12 bare copper or thin aluminum tubing, a common practical
choice) since the tool doesn't otherwise collect a wire-gauge input -- this
assumption is the one place this calculator's precision depends on a default
rather than a user choice.

Each element is modeled as a straight run of length A with both ends bent
back toward the other element by B (driven) or D (reflector) -- the open
rectangle ("Moxon rectangle") shape. Total wire per element = A + 2 x tail.
"""

from data_store import design_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE_MOXON, BALUN_WHY_MOXON
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register

DEFAULT_WIRE_DIAMETER_M = 0.002  # ~2mm, AWG12-ish bare wire/thin tubing

# Cebik W4RNL regression coefficients (y = a*x^2 + b*x + c, except D which is linear).
_AA, _AB, _AC = -0.0008571428571, -0.009571428571, 0.3398571429
_BA, _BB, _BC = -0.002142857143, -0.02035714286, 0.008285714286
_CA, _CB, _CC = 0.001809523381, 0.01780952381, 0.05164285714
_DA, _DB = 0.001, 0.07178571429


@register("moxon_2_element")
def design_moxon(band: str, wire_diameter_m: float = DEFAULT_WIRE_DIAMETER_M, lang: str = "en") -> AntennaDesign:
    freq_mhz = design_frequency(band)
    wavelength_m = 300.0 / freq_mhz

    import math
    x = math.log10(wire_diameter_m / wavelength_m)

    a = _AA * x**2 + _AB * x + _AC
    b = _BA * x**2 + _BB * x + _BC
    c = _CA * x**2 + _CB * x + _CC
    d = _DA * x + _DB
    e = b + c + d

    a_m, b_m, c_m, d_m, e_m = (round(v * wavelength_m, 3) for v in (a, b, c, d, e))

    driven_total_m = round(a_m + 2 * b_m, 3)
    reflector_total_m = round(a_m + 2 * d_m, 3)
    driven_total_ft = round(driven_total_m / METERS_PER_FOOT, 3)
    reflector_total_ft = round(reflector_total_m / METERS_PER_FOOT, 3)

    elements = [
        Element("driven", driven_total_ft, driven_total_m, "radiator"),
        Element("reflector", reflector_total_ft, reflector_total_m, "reflector"),
    ]

    return AntennaDesign(
        antenna_type="moxon_2_element",
        band=band,
        design_freq_mhz=freq_mhz,
        elements=elements,
        feedpoint_impedance_ohms=50.0,  # the Moxon geometry is specifically shaped to land near 50 ohms
        feed_location="driven_element",
        geometry="moxon",
        balun={
            "type": BALUN_TYPE_LABELS["current_balun_1_1"][lang],
            "ratio": "1:1",
            "where": BALUN_WHERE_MOXON[lang],
            "why": BALUN_WHY_MOXON[lang],
        },
        extra={
            "wire_diameter_m": wire_diameter_m,
            "a_m": a_m, "b_m": b_m, "c_m": c_m, "d_m": d_m, "e_m": e_m,
            "a_ft": round(a_m / METERS_PER_FOOT, 3),
            "b_ft": round(b_m / METERS_PER_FOOT, 3),
            "c_ft": round(c_m / METERS_PER_FOOT, 3),
            "d_ft": round(d_m / METERS_PER_FOOT, 3),
            "e_ft": round(e_m / METERS_PER_FOOT, 3),
        },
    )
