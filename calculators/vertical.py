"""Ground-mounted quarter-wave vertical.

Formulas (documented, not derived/guessed):
- Quarter-wave element length (feet): 234 / f(MHz) -- standard ham radio rule
  of thumb, accounts for end effect / velocity of propagation in wire antennas.
- Radials: 4x quarter-wave radials (lambda/4), the most commonly cited rule of
  thumb for a ground-mounted quarter-wave vertical.
- Balun: 1:1 current choke at the feedpoint -- a vertical fed directly with
  coax over ground-mounted radials needs no impedance-transforming unun.
"""

from data_store import design_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE, BALUN_WHY
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register


@register("vertical_quarter_wave")
def design_vertical(band: str, radial_count: int = 4, lang: str = "en", freq_mhz: float = None, wire_vf: float = 0.95) -> AntennaDesign:
    if radial_count < 1:
        raise ValueError("radial_count must be at least 1")

    freq_mhz = design_frequency(band, freq_mhz)
    length_ft = round((234.0 / freq_mhz) * wire_vf, 3)
    length_m = round(length_ft * METERS_PER_FOOT, 3)

    elements = [Element("mast", length_ft, length_m, "radiator")]
    elements += [
        Element(f"radial_{i + 1}", length_ft, length_m, "radial")
        for i in range(radial_count)
    ]

    return AntennaDesign(
        antenna_type="vertical_quarter_wave",
        band=band,
        design_freq_mhz=freq_mhz,
        elements=elements,
        feedpoint_impedance_ohms=36.0,  # textbook value over a perfect ground;
        # real-world radials bring it closer to 25-35 ohms.
        feed_location="base",
        geometry="vertical",
        balun={
            "type": BALUN_TYPE_LABELS["current_choke_1_1"][lang],
            "ratio": "1:1",
            "where": BALUN_WHERE[lang],
            "why": BALUN_WHY[lang],
        },
    )
