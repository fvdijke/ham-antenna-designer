"""Inverted-V dipole.

Same half-wave formula as the plain dipole (468/f) -- this is a mounting
variant, not a different antenna electrically. Legs slope down from a single
high support point instead of running flat between two supports, trading a
little gain/pattern symmetry for needing only one mast.
"""

from data_store import design_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE_DIPOLE, BALUN_WHY_DIPOLE
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register


@register("inverted_v_dipole")
def design_inverted_v(band: str, lang: str = "en", freq_mhz: float = None) -> AntennaDesign:
    freq_mhz = design_frequency(band, freq_mhz)
    total_ft = 468.0 / freq_mhz
    leg_ft = round(total_ft / 2, 3)
    leg_m = round(leg_ft * METERS_PER_FOOT, 3)

    elements = [
        Element("leg_a", leg_ft, leg_m, "radiator"),
        Element("leg_b", leg_ft, leg_m, "radiator"),
    ]

    return AntennaDesign(
        antenna_type="inverted_v_dipole",
        band=band,
        design_freq_mhz=freq_mhz,
        elements=elements,
        feedpoint_impedance_ohms=70.0,  # slightly below flat dipole's 73 ohm -- the
        # bent geometry typically lowers it a little, exact value depends on apex angle/height.
        feed_location="apex",
        geometry="inverted_v",
        balun={
            "type": BALUN_TYPE_LABELS["current_balun_1_1"][lang],
            "ratio": "1:1",
            "where": BALUN_WHERE_DIPOLE[lang],
            "why": BALUN_WHY_DIPOLE[lang],
        },
    )
