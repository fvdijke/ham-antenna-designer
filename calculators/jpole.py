"""J-pole (VHF/UHF, no radials/ground plane needed).

Formula (documented, not derived/guessed -- standard published J-pole values):
- Radiator (half-wave): 468 / f(MHz) feet.
- Matching stub (quarter-wave, shorted at the bottom): 234 / f(MHz) feet.
- Feed tap point on the stub: stub_length x k, where k is an empirically
  found ~0.18-0.22 for a 50 ohm match; we use k=0.20 (the documented
  midpoint) as a starting point -- real builds commonly fine-tune the tap
  position with a sliding clamp.
- No balun: the tap point itself provides the impedance match, so this
  antenna is fed directly with 50 ohm coax.
"""

from data_store import design_frequency
from i18n import BALUN_TYPE_LABELS, JPOLE_BALUN_WHERE, JPOLE_BALUN_WHY
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register

FEED_TAP_FRACTION = 0.20


@register("j_pole")
def design_jpole(band: str, lang: str = "en") -> AntennaDesign:
    freq_mhz = design_frequency(band)

    radiator_ft = round(468.0 / freq_mhz, 3)
    radiator_m = round(radiator_ft * METERS_PER_FOOT, 3)
    stub_ft = round(234.0 / freq_mhz, 3)
    stub_m = round(stub_ft * METERS_PER_FOOT, 3)

    elements = [
        Element("radiator", radiator_ft, radiator_m, "radiator"),
        Element("stub", stub_ft, stub_m, "matching_stub"),
    ]

    feed_tap_m = round(stub_m * FEED_TAP_FRACTION, 3)
    feed_tap_ft = round(stub_ft * FEED_TAP_FRACTION, 3)

    return AntennaDesign(
        antenna_type="j_pole",
        band=band,
        design_freq_mhz=freq_mhz,
        elements=elements,
        feedpoint_impedance_ohms=50.0,
        feed_location="stub_tap",
        geometry="j_pole",
        balun={
            "type": BALUN_TYPE_LABELS["tap_point_match"][lang],
            "ratio": "-",
            "where": JPOLE_BALUN_WHERE[lang].format(fraction=f"{FEED_TAP_FRACTION:.0%}"),
            "why": JPOLE_BALUN_WHY[lang],
        },
        extra={
            "feed_tap_fraction": FEED_TAP_FRACTION,
            "feed_tap_m": feed_tap_m,
            "feed_tap_ft": feed_tap_ft,
        },
    )
