"""Broadband long-wire / random-wire SWL receive antenna (LW through HF).

Formula (documented, not derived/guessed):
- This is a receive-only, intentionally non-resonant antenna -- there is no
  single "correct" length the way there is for a transmit antenna. The
  practical rule of thumb (repeated across SWL guides) is: longer is better
  for low-frequency response, with a commonly used PRACTICAL MINIMUM of
  roughly a quarter-wavelength at the lowest frequency of interest -- the
  same 234/f(MHz) constant used for the quarter-wave vertical, repurposed
  here as a floor, not a precision cut. Applied to the selected band's LOW
  edge, since that's what sets the antenna's low-frequency usefulness.
- Counterpoise: a short return-path wire, sized the same way the EFHW's
  counterpoise is (quarter-wave) -- far less critical here than for a
  transmit antenna, just needs to give the unun a return path.
- Feedpoint impedance: end-fed long wires present a high impedance, commonly
  cited in the 500-1000 ohm range; ~500 ohms is used here as the nominal
  value a 9:1 unun is built around (50 ohm x 9 = 450 ohm).
- Unun: 9:1, the standard ratio sold for SWL longwire matching (e.g. Palomar
  Engineers' MLB-2, rated 100 kHz-30 MHz).
"""

from data_store import BANDS_MHZ, design_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE_LONGWIRE, BALUN_WHY_LONGWIRE
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register


@register("longwire_receive")
def design_longwire_receive(band: str, lang: str = "en") -> AntennaDesign:
    low_mhz, _high_mhz = BANDS_MHZ[band]
    freq_mhz = design_frequency(band)

    min_length_ft = round(234.0 / low_mhz, 3)
    min_length_m = round(min_length_ft * METERS_PER_FOOT, 3)

    counterpoise_ft = round(234.0 / low_mhz, 3)
    counterpoise_m = round(counterpoise_ft * METERS_PER_FOOT, 3)

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
