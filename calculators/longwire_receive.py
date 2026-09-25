"""Broadband long-wire / random-wire SWL receive antenna (LW through HF).

Formula (documented, not derived/guessed):
- This is a receive-only, intentionally non-resonant antenna -- there is no
  single "correct" length the way there is for a transmit antenna. The
  practical rule of thumb (repeated across SWL guides) is: longer is better
  for low-frequency response, with a commonly used PRACTICAL MINIMUM of
  roughly a quarter-wavelength at the lowest frequency of interest -- the
  same 234/f(MHz) constant used for the quarter-wave vertical, repurposed
  here as a floor, not a precision cut. Applied to the selected band's LOW
  edge, since that's what sets the antenna's low-frequency usefulness, and
  kept within 10-50 m (a quarter wave at 150 kHz would be ~500 m).
- Counterpoise: a short return-path wire, 20 % of the wire length, 2-10 m --
  far less critical here than for a transmit antenna, it just needs to give
  the unun a return path.
- Feedpoint impedance: end-fed long wires present a high impedance, commonly
  cited in the 500-1000 ohm range; ~500 ohms is used here as the nominal
  value a 9:1 unun is built around (50 ohm x 9 = 450 ohm).
- Unun: 9:1, the standard ratio sold for SWL longwire matching (e.g. Palomar
  Engineers' MLB-2, rated 100 kHz-30 MHz).
"""

from data_store import design_frequency, low_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE_LONGWIRE, BALUN_WHY_LONGWIRE
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register

MIN_LENGTH_M = 10.0
MAX_LENGTH_M = 50.0


@register("longwire_receive")
def design_longwire_receive(band: str, lang: str = "en", freq_mhz: float = None, wire_vf: float = 1.0) -> AntennaDesign:
    low_mhz = low_frequency(band, freq_mhz)
    freq_mhz = design_frequency(band, freq_mhz)

    # Untuned wire: the insulation factor is irrelevant here, and a raw
    # quarter wave on LW/MW would be hundreds of metres -- keep it buildable.
    quarter_m = 234.0 / low_mhz * METERS_PER_FOOT
    min_length_m = round(min(max(quarter_m, MIN_LENGTH_M), MAX_LENGTH_M), 3)
    min_length_ft = round(min_length_m / METERS_PER_FOOT, 3)

    counterpoise_m = round(min(max(0.2 * min_length_m, 2.0), 10.0), 3)
    counterpoise_ft = round(counterpoise_m / METERS_PER_FOOT, 3)

    elements = [
        Element("radiator", min_length_ft, min_length_m, "radiator"),
        Element("counterpoise", counterpoise_ft, counterpoise_m, "counterpoise"),
    ]

    return AntennaDesign(
        antenna_type="longwire_receive",
        band=band,
        design_freq_mhz=freq_mhz,
        elements=elements,
        feedpoint_impedance_ohms=500.0,
        feed_location="end",
        geometry="horizontal_end_fed",
        balun={
            "type": BALUN_TYPE_LABELS["unun_9_1"][lang],
            "ratio": "9:1",
            "where": BALUN_WHERE_LONGWIRE[lang],
            "why": BALUN_WHY_LONGWIRE[lang],
        },
    )
