"""Half-wave vertical (a vertical EFHW -- end-fed at the base, radiating
straight up).

Formula (documented, not derived/guessed):
- Radiator length (feet): 468/f(MHz) -- the same half-wave constant as the
  horizontal EFHW; it's still a half-wavelength of wire, just oriented
  vertically and fed at the bottom instead of horizontally and fed at one
  end. Running the wire vertically (even just for part of its length)
  gives a lower radiation angle than a purely horizontal EFHW, which is
  the usual reason to mount one this way (single tall support, better DX).
- Counterpoise: a short quarter-wave (234/f) ground-return wire, same
  practical role as the horizontal EFHW's counterpoise -- gives the unun
  a return path, not a resonant radial system.
- Feedpoint impedance: ~2450 ohms, the same high end-fed value as the
  horizontal EFHW (commonly cited 2000-5000 ohm range for a half-wave
  end-fed point).
- Unun: 49:1, same standard ratio as the horizontal EFHW.
"""

from data_store import design_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE_EFHW, BALUN_WHY_EFHW
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register


@register("vertical_half_wave")
def design_half_wave_vertical(band: str, lang: str = "en", freq_mhz: float = None) -> AntennaDesign:
    freq_mhz = design_frequency(band, freq_mhz)

    radiator_ft = round(468.0 / freq_mhz, 3)
    radiator_m = round(radiator_ft * METERS_PER_FOOT, 3)

    counterpoise_ft = round(234.0 / freq_mhz, 3)
    counterpoise_m = round(counterpoise_ft * METERS_PER_FOOT, 3)

    elements = [
        Element("radiator", radiator_ft, radiator_m, "radiator"),
        Element("counterpoise", counterpoise_ft, counterpoise_m, "counterpoise"),
    ]

    return AntennaDesign(
        antenna_type="vertical_half_wave",
        band=band,
        design_freq_mhz=freq_mhz,
        elements=elements,
        feedpoint_impedance_ohms=2450.0,
        feed_location="base",
        geometry="vertical_end_fed",
        balun={
            "type": BALUN_TYPE_LABELS["unun_49_1"][lang],
            "ratio": "49:1",
            "where": BALUN_WHERE_EFHW[lang],
            "why": BALUN_WHY_EFHW[lang],
        },
    )
