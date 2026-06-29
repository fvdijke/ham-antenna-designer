"""2-element cubical quad (driven loop + reflector loop).

Directional gain antenna -- like the Yagi, real builds are normally tuned
with an antenna analyzer; these are published beginner rule-of-thumb
dimensions, not an optimized design.

Formula (documented sources, not derived/guessed):
- Driven loop circumference: 1005 / f(MHz) feet -- the same full-wave loop
  constant used elsewhere in this tool. Side length = circumference / 4.
- Reflector loop: ~5% longer circumference than the driven loop (within the
  commonly cited 3-5% range).
- Spacing between driven and reflector: 0.15 wavelength (within the commonly
  cited 0.12-0.2 wavelength range; chosen here because it conveniently lands
  close to a 50 ohm driven-loop feedpoint, needing no extra matching network).
"""

from data_store import design_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE_QUAD, BALUN_WHY_QUAD
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register

REFLECTOR_FACTOR = 1.05
SPACING_WAVELENGTHS = 0.15


@register("quad_2_element")
def design_quad(band: str, lang: str = "en", freq_mhz: float = None, wire_vf: float = 0.95) -> AntennaDesign:
    freq_mhz = design_frequency(band, freq_mhz)
    wavelength_ft = (984.0 / freq_mhz) * wire_vf

    driven_circumference_ft = (1005.0 / freq_mhz) * wire_vf
    reflector_circumference_ft = driven_circumference_ft * REFLECTOR_FACTOR
    spacing_ft = round(wavelength_ft * SPACING_WAVELENGTHS, 3)

    def ft_m(ft):
        return round(ft, 3), round(ft * METERS_PER_FOOT, 3)

    driven_ft, driven_m = ft_m(driven_circumference_ft)
    reflector_ft, reflector_m = ft_m(reflector_circumference_ft)

    elements = [
        Element("driven_loop", driven_ft, driven_m, "driven_loop"),
        Element("reflector_loop", reflector_ft, reflector_m, "reflector_loop"),
    ]

    return AntennaDesign(
        antenna_type="quad_2_element",
        band=band,
        design_freq_mhz=freq_mhz,
        elements=elements,
        feedpoint_impedance_ohms=50.0,  # the chosen spacing is meant to land close
        # to 50 ohms directly; real builds vary and may need a small matching network.
        feed_location="driven_element",
        geometry="quad",
        balun={
            "type": BALUN_TYPE_LABELS["current_choke_1_1"][lang],
            "ratio": "1:1",
            "where": BALUN_WHERE_QUAD[lang],
            "why": BALUN_WHY_QUAD[lang],
        },
        extra={
            "spacing_ft": spacing_ft,
            "spacing_m": round(spacing_ft * METERS_PER_FOOT, 3),
        },
    )
