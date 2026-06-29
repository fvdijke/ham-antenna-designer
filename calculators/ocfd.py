"""Off-center-fed dipole (Windom-style).

Formula (documented, not derived/guessed):
- Total length (feet): 468 / f(MHz) -- same half-wave wire length as a plain
  dipole; the only difference is WHERE it's fed.
- Feedpoint at the 1/3 point along the wire (short leg = total/3, long leg =
  total*2/3) -- the classic Windom feed ratio.
- Feedpoint impedance: ~200 ohms at the 1/3 point (commonly cited value for
  this feed ratio), hence a 4:1 (not 1:1) balun to reach 50 ohms.

Note: real-world OCF dipoles built for MULTIBAND use often use a longer
compromise length tuned across several bands rather than this single-band
half-wave length. This calculator gives the single-band resonant length for
the selected band, consistent with the rest of this tool.
"""

from data_store import design_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE_OCFD, BALUN_WHY_OCFD
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register


@register("off_center_fed_dipole")
def design_ocfd(band: str, lang: str = "en", freq_mhz: float = None, wire_vf: float = 0.95) -> AntennaDesign:
    freq_mhz = design_frequency(band, freq_mhz)
    total_ft = (468.0 / freq_mhz) * wire_vf

    short_ft = round(total_ft / 3, 3)
    long_ft = round(total_ft * 2 / 3, 3)
    short_m = round(short_ft * METERS_PER_FOOT, 3)
    long_m = round(long_ft * METERS_PER_FOOT, 3)

    elements = [
        Element("leg_short", short_ft, short_m, "leg_short"),
        Element("leg_long", long_ft, long_m, "leg_long"),
    ]

    return AntennaDesign(
        antenna_type="off_center_fed_dipole",
        band=band,
        design_freq_mhz=freq_mhz,
        elements=elements,
        feedpoint_impedance_ohms=200.0,
        feed_location="off_center",
        geometry="horizontal_off_center_fed",
        balun={
            "type": BALUN_TYPE_LABELS["current_balun_4_1"][lang],
            "ratio": "4:1",
            "where": BALUN_WHERE_OCFD[lang],
            "why": BALUN_WHY_OCFD[lang],
        },
    )
