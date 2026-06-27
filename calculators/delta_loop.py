"""Vertical delta loop.

Same full-wave wire-length formula as the horizontal loop (1005/f) -- this is
a mounting/shape variant: a triangle (3 equal sides) hung vertically between
3 supports, instead of a square hung horizontally. Vertical orientation gives
a lower-angle radiation pattern, useful for DX.
"""

from data_store import design_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE_LOOP, BALUN_WHY_LOOP
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register


@register("delta_loop_vertical")
def design_delta_loop(band: str, lang: str = "en", freq_mhz: float = None) -> AntennaDesign:
    freq_mhz = design_frequency(band, freq_mhz)
    total_ft = round(1005.0 / freq_mhz, 3)
    total_m = round(total_ft * METERS_PER_FOOT, 3)

    elements = [Element("loop_wire", total_ft, total_m, "radiator")]

    return AntennaDesign(
        antenna_type="delta_loop_vertical",
        band=band,
        design_freq_mhz=freq_mhz,
        elements=elements,
        feedpoint_impedance_ohms=100.0,
        feed_location="bottom_side",
        geometry="vertical_loop",
        balun={
            "type": BALUN_TYPE_LABELS["current_balun_1_1"][lang],
            "ratio": "1:1",
            "where": BALUN_WHERE_LOOP[lang],
            "why": BALUN_WHY_LOOP[lang],
        },
        extra={"sides": 3},
    )
