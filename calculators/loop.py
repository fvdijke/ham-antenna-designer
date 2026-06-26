"""Full-wave horizontal loop.

Formula (documented, not derived/guessed):
- Total wire length (feet): 1005 / f(MHz) -- the standard ham radio full-wave
  loop rule of thumb.
- Shape barely matters (square, circle, triangle) -- only total length does.
  We model it as a square (4 equal sides) since that's the most common
  practical layout with 4 corner supports.
- Feedpoint impedance: ~100 ohms, the commonly cited free-space value for a
  full-wave horizontal loop -- about a 2:1 SWR against 50 ohm coax, which most
  radios tolerate directly.
- Balun: 1:1 current balun at the feedpoint (balanced/unbalanced conversion,
  same reasoning as the dipole -- this is not an impedance-transforming unun).
"""

from data_store import design_frequency
from i18n import BALUN_WHERE_LOOP, BALUN_WHY_LOOP
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register


@register("loop_full_wave")
def design_loop(band: str, lang: str = "en") -> AntennaDesign:
    freq_mhz = design_frequency(band)
    total_ft = round(1005.0 / freq_mhz, 3)
    total_m = round(total_ft * METERS_PER_FOOT, 3)

    elements = [Element("loop_wire", total_ft, total_m, "radiator")]

    return AntennaDesign(
        antenna_type="loop_full_wave",
        band=band,
        design_freq_mhz=freq_mhz,
        elements=elements,
        feedpoint_impedance_ohms=100.0,
        feed_location="side",
        geometry="horizontal_loop",
        balun={
            "type": "1:1 current balun",
            "ratio": "1:1",
            "where": BALUN_WHERE_LOOP[lang],
            "why": BALUN_WHY_LOOP[lang],
        },
    )
