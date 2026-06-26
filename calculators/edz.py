"""Extended double Zepp (EDZ).

Formula (documented, not derived/guessed):
- Each leg (feet): 600 / f(MHz) -- standard published EDZ leg length, giving
  a total antenna length of about 1.25 wavelengths (two in-phase collinear
  half-waves), which is what produces the gain over a plain dipole.
- Feedpoint impedance is high and varies considerably with height/surroundings
  (commonly several hundred ohms) -- we cite a representative ~300 ohms, but
  this is far less crisp than a dipole's 73 ohms. A balanced tuner via
  open-wire/ladder line is the practical feed method, not a fixed coax balun.
"""

from data_store import design_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE_EDZ, BALUN_WHY_EDZ
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register


@register("extended_double_zepp")
def design_edz(band: str, lang: str = "en") -> AntennaDesign:
    freq_mhz = design_frequency(band)
    leg_ft = round(600.0 / freq_mhz, 3)
    leg_m = round(leg_ft * METERS_PER_FOOT, 3)

    elements = [
        Element("leg_a", leg_ft, leg_m, "radiator"),
        Element("leg_b", leg_ft, leg_m, "radiator"),
    ]

    return AntennaDesign(
        antenna_type="extended_double_zepp",
        band=band,
        design_freq_mhz=freq_mhz,
        elements=elements,
        feedpoint_impedance_ohms=300.0,  # representative only -- varies a lot with height/surroundings
        feed_location="center",
        geometry="horizontal_center_fed",
        balun={
            "type": BALUN_TYPE_LABELS["balanced_tuner"][lang],
            "ratio": "n/a",
            "where": BALUN_WHERE_EDZ[lang],
            "why": BALUN_WHY_EDZ[lang],
        },
    )
