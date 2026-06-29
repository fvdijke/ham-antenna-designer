"""End-fed half-wave (EFHW).

Formula (documented, not derived/guessed):
- Radiator length (feet): 468 / f(MHz) -- same half-wave wire length as a
  center-fed dipole; it's still a half-wavelength of wire, just fed at the end
  instead of the center.
- Counterpoise: a short quarter-wave (234/f) counterpoise wire at the feed end,
  the standard practical approach to give the unun a return path and reduce
  RF-in-the-shack -- not a resonant radial system like the ground-mounted
  vertical.
- Feedpoint impedance: ~2450 ohms at the high-impedance end-feed point
  (the nominal value a 49:1 unun is designed around: 50 ohm x 49 = 2450 ohm).
- Balun: 49:1 unun at the feedpoint, not a 1:1 choke -- this antenna needs an
  impedance transformation, not just balanced/unbalanced conversion.
"""

from data_store import design_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE_EFHW, BALUN_WHY_EFHW
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register


@register("efhw")
def design_efhw(band: str, lang: str = "en", freq_mhz: float = None, wire_vf: float = 0.95) -> AntennaDesign:
    freq_mhz = design_frequency(band, freq_mhz)

    radiator_ft = round((468.0 / freq_mhz) * wire_vf, 3)
    radiator_m = round(radiator_ft * METERS_PER_FOOT, 3)

    counterpoise_ft = round((234.0 / freq_mhz) * wire_vf, 3)
    counterpoise_m = round(counterpoise_ft * METERS_PER_FOOT, 3)

    elements = [
        Element("radiator", radiator_ft, radiator_m, "radiator"),
        Element("counterpoise", counterpoise_ft, counterpoise_m, "counterpoise"),
    ]

    return AntennaDesign(
        antenna_type="efhw",
        band=band,
        design_freq_mhz=freq_mhz,
        elements=elements,
        feedpoint_impedance_ohms=2450.0,
        feed_location="end",
        geometry="horizontal_end_fed",
        balun={
            "type": BALUN_TYPE_LABELS["unun_49_1"][lang],
            "ratio": "49:1",
            "where": BALUN_WHERE_EFHW[lang],
            "why": BALUN_WHY_EFHW[lang],
        },
    )
