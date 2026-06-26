"""5/8-wave gain vertical.

Formula (documented, not derived/guessed -- standard published values):
- Radiator length (feet): 585 / f(MHz).
- Radials (feet): 246 / f(MHz) -- a quarter-wave ground plane, using the
  constant commonly published specifically for this antenna (slightly
  different rounding than the 234/f used for the plain quarter-wave vertical;
  both are valid quarter-wave rule-of-thumb constants from different sources).
- The 5/8-wave element is NOT naturally resonant (unlike 1/4 or 1/2 wave) --
  it needs a base loading coil to cancel reactance before the coax sees a
  clean match. Gives ~3 dB gain over a plain quarter-wave vertical.
"""

from data_store import design_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE_FIVE_EIGHTHS, BALUN_WHY_FIVE_EIGHTHS
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register


@register("five_eighths_vertical")
def design_five_eighths(band: str, radial_count: int = 4, lang: str = "en") -> AntennaDesign:
    freq_mhz = design_frequency(band)

    element_ft = round(585.0 / freq_mhz, 3)
    element_m = round(element_ft * METERS_PER_FOOT, 3)
    radial_ft = round(246.0 / freq_mhz, 3)
    radial_m = round(radial_ft * METERS_PER_FOOT, 3)

    elements = [Element("mast", element_ft, element_m, "radiator")]
    elements += [
        Element(f"radial_{i + 1}", radial_ft, radial_m, "radial")
        for i in range(radial_count)
    ]

    return AntennaDesign(
        antenna_type="five_eighths_vertical",
        band=band,
        design_freq_mhz=freq_mhz,
        elements=elements,
        feedpoint_impedance_ohms=50.0,  # after the loading coil cancels reactance;
        # the raw element impedance before the coil is much higher and partly reactive.
        feed_location="base",
        geometry="vertical",
        balun={
            "type": BALUN_TYPE_LABELS["base_loading_coil"][lang],
            "ratio": "n/a",
            "where": BALUN_WHERE_FIVE_EIGHTHS[lang],
            "why": BALUN_WHY_FIVE_EIGHTHS[lang],
        },
    )
