"""Center-fed half-wave dipole.

Formula (documented, not derived/guessed):
- Total length (feet): 468 / f(MHz) -- the standard ham radio half-wave dipole
  rule of thumb (accounts for end effect; this is why it isn't exactly twice
  the 234/f quarter-wave constant).
- Each leg is half the total length.
- Feedpoint impedance: ~73 ohms, the textbook free-space center-fed half-wave
  dipole value.
- Balun: a 1:1 (current-type) balun at the center feedpoint -- needed any time
  a balanced dipole is fed with unbalanced coax, regardless of band.
"""

from data_store import design_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE_DIPOLE, BALUN_WHY_DIPOLE
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register


@register("dipole_half_wave")
def design_dipole(band: str, lang: str = "en", freq_mhz: float = None, wire_vf: float = 0.95) -> AntennaDesign:
    freq_mhz = design_frequency(band, freq_mhz)
    total_ft = (468.0 / freq_mhz) * wire_vf
    leg_ft = round(total_ft / 2, 3)
    leg_m = round(leg_ft * METERS_PER_FOOT, 3)

    elements = [
        Element("leg_a", leg_ft, leg_m, "radiator"),
        Element("leg_b", leg_ft, leg_m, "radiator"),
    ]

    return AntennaDesign(
        antenna_type="dipole_half_wave",
        band=band,
        design_freq_mhz=freq_mhz,
        elements=elements,
        feedpoint_impedance_ohms=73.0,
        feed_location="center",
        geometry="horizontal_center_fed",
        balun={
            "type": BALUN_TYPE_LABELS["current_balun_1_1"][lang],
            "ratio": "1:1",
            "where": BALUN_WHERE_DIPOLE[lang],
            "why": BALUN_WHY_DIPOLE[lang],
        },
    )
