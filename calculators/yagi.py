"""3-element Yagi (reflector - driven element - director).

This is a directional, gain antenna -- unlike the wire antennas elsewhere in
this tool, real Yagi designs are normally optimized with NEC modeling
software (e.g. EZNEC, 4nec2) for a specific gain/F-B/bandwidth tradeoff.
What follows are widely published BEGINNER rule-of-thumb dimensions, not an
optimized design -- treat this as a solid starting point to build and tune,
not a final answer.

Formula (documented sources, not derived/guessed):
- Driven element (half-wave dipole): 468 / f(MHz) feet.
- Reflector: ~5% longer than the driven element.
- Director: ~5% shorter than the driven element.
- Reflector spacing from driven element: 0.2 wavelength (within the commonly
  cited 0.1-0.25 wavelength range; 0.2 is a frequently used "sweet spot").
- Director spacing from driven element: 0.15 wavelength (within the commonly
  cited 0.1-0.2 wavelength range for a single director).
- Boom length: sum of the two spacings.
"""

from data_store import design_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE_YAGI, BALUN_WHY_YAGI
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register

REFLECTOR_FACTOR = 1.05
DIRECTOR_FACTOR = 0.95
REFLECTOR_SPACING_WAVELENGTHS = 0.2
DIRECTOR_SPACING_WAVELENGTHS = 0.15


@register("yagi_3_element")
def design_yagi(band: str, lang: str = "en", freq_mhz: float = None, wire_vf: float = 0.95) -> AntennaDesign:
    freq_mhz = design_frequency(band, freq_mhz)
    wavelength_ft = (984.0 / freq_mhz) * wire_vf  # standard free-space wavelength in feet (984/f)

    driven_ft = (468.0 / freq_mhz) * wire_vf
    reflector_ft = driven_ft * REFLECTOR_FACTOR
    director_ft = driven_ft * DIRECTOR_FACTOR

    reflector_spacing_ft = round(wavelength_ft * REFLECTOR_SPACING_WAVELENGTHS, 3)
    director_spacing_ft = round(wavelength_ft * DIRECTOR_SPACING_WAVELENGTHS, 3)
    boom_ft = round(reflector_spacing_ft + director_spacing_ft, 3)

    def ft_m(ft):
        return round(ft, 3), round(ft * METERS_PER_FOOT, 3)

    driven_ft, driven_m = ft_m(driven_ft)
    reflector_ft, reflector_m = ft_m(reflector_ft)
    director_ft, director_m = ft_m(director_ft)

    elements = [
        Element("driven", driven_ft, driven_m, "radiator"),
        Element("reflector", reflector_ft, reflector_m, "reflector"),
        Element("director", director_ft, director_m, "director"),
    ]

    return AntennaDesign(
        antenna_type="yagi_3_element",
        band=band,
        design_freq_mhz=freq_mhz,
        elements=elements,
        feedpoint_impedance_ohms=25.0,  # typically lower than a plain dipole's 73 ohms
        # once a reflector is added; varies with exact spacing/tuning.
        feed_location="driven_element",
        geometry="yagi",
        balun={
            "type": BALUN_TYPE_LABELS["current_balun_1_1"][lang],
            "ratio": "1:1",
            "where": BALUN_WHERE_YAGI[lang],
            "why": BALUN_WHY_YAGI[lang],
        },
        extra={
            "reflector_spacing_ft": reflector_spacing_ft,
            "reflector_spacing_m": round(reflector_spacing_ft * METERS_PER_FOOT, 3),
            "director_spacing_ft": director_spacing_ft,
            "director_spacing_m": round(director_spacing_ft * METERS_PER_FOOT, 3),
            "boom_ft": boom_ft,
            "boom_m": round(boom_ft * METERS_PER_FOOT, 3),
        },
    )
