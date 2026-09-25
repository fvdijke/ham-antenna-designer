"""Loop-on-Ground (LoG) receive antenna -- a noise-canceling DX loop laid
flat on the ground, popular for LW/MW/lower-HF reception.

Formula (documented, not derived/guessed):
- Total perimeter: receive-only and untuned; a LoG is deliberately small
  (electrically short). Published field reports (kk5jy.net LoG writeups)
  use roughly 7-9 m (25-30 ft) per side; larger loops pick up more signal
  but also more noise. Here: 0.1 wavelength at the band's low edge, kept
  within 20-60 m perimeter (a quarter wave on MW would be ~140 m).
- Feedpoint impedance: a loop lying on the ground presents a fairly high
  impedance that varies with frequency and ground conditions; sources cite
  roughly 300-1500 ohms, with ~450 ohms used here as a representative value.
- Matching: a 9:1 STEP-DOWN transformer (3:1 turns) on a ferrite
  binocular/toroid core (Fair-Rite #73 mix is commonly cited): 450 -> 50 ohms.
"""

from data_store import design_frequency, low_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE_GROUND_LOOP, BALUN_WHY_GROUND_LOOP
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register

MIN_PERIMETER_M = 20.0
MAX_PERIMETER_M = 60.0


@register("ground_loop_receive")
def design_ground_loop(band: str, lang: str = "en", freq_mhz: float = None, wire_vf: float = 1.0) -> AntennaDesign:
    low_mhz = low_frequency(band, freq_mhz)
    freq_mhz = design_frequency(band, freq_mhz)

    tenth_wave_m = 0.1 * 300.0 / low_mhz
    total_m = round(min(max(tenth_wave_m, MIN_PERIMETER_M), MAX_PERIMETER_M), 3)
    total_ft = round(total_m / METERS_PER_FOOT, 3)

    elements = [Element("loop_wire", total_ft, total_m, "radiator")]

    return AntennaDesign(
        antenna_type="ground_loop_receive",
        band=band,
        design_freq_mhz=freq_mhz,
        elements=elements,
        feedpoint_impedance_ohms=450.0,
        feed_location="side",
        geometry="horizontal_loop",
        balun={
            "type": BALUN_TYPE_LABELS["stepdown_transformer_3_1"][lang],
            "ratio": "9:1",
            "where": BALUN_WHERE_GROUND_LOOP[lang],
            "why": BALUN_WHY_GROUND_LOOP[lang],
        },
    )
