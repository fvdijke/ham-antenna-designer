"""Full-wave vertical (end-fed at the base, radiating straight up) -- the
natural full-wavelength extension of the half-wave vertical / vertical EFHW.

Formula (documented, not derived/guessed):
- Radiator length (feet): 936/f(MHz) -- double the 468/f half-wave constant,
  the standard way ham references extend the half-wave end-fed formula to a
  full wavelength (the same wire principle EFHW antennas already rely on
  when operated on their 2nd harmonic, just designed for as the fundamental
  here instead).
- Counterpoise: same quarter-wave (234/f) ground-return wire as the
  half-wave vertical -- still just a return path for the unun, not a
  resonant radial system.
- Feedpoint impedance: a full-wavelength end-fed point runs even higher
  than a half-wave's already-high end impedance (commonly cited 2000-5000
  ohms for a half-wave end); ~5000 ohms is used here as a representative
  nominal value for the full-wave case.
- Unun: 64:1 -- a standard, commercially available ratio (sold specifically
  for higher-impedance end-fed/multiband EFHW use) better matched to this
  higher impedance than the usual 49:1.
"""

from data_store import design_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE_EFHW, BALUN_WHY_FULL_WAVE_VERTICAL
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register


@register("vertical_full_wave")
def design_full_wave_vertical(band: str, lang: str = "en", freq_mhz: float = None, wire_vf: float = 0.95) -> AntennaDesign:
    freq_mhz = design_frequency(band, freq_mhz)

    radiator_ft = round((936.0 / freq_mhz) * wire_vf, 3)
    radiator_m = round(radiator_ft * METERS_PER_FOOT, 3)

    counterpoise_ft = round((234.0 / freq_mhz) * wire_vf, 3)
    counterpoise_m = round(counterpoise_ft * METERS_PER_FOOT, 3)

    elements = [
        Element("radiator", radiator_ft, radiator_m, "radiator"),
        Element("counterpoise", counterpoise_ft, counterpoise_m, "counterpoise"),
    ]

    return AntennaDesign(
        antenna_type="vertical_full_wave",
        band=band,
        design_freq_mhz=freq_mhz,
        elements=elements,
        feedpoint_impedance_ohms=5000.0,
        feed_location="base",
        geometry="vertical_end_fed",
        balun={
            "type": BALUN_TYPE_LABELS["unun_64_1"][lang],
            "ratio": "64:1",
            "where": BALUN_WHERE_EFHW[lang],
            "why": BALUN_WHY_FULL_WAVE_VERTICAL[lang],
        },
    )
