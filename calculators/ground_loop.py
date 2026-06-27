"""Loop-on-Ground (LoG) receive antenna -- a noise-canceling DX loop laid
flat on the ground, popular for LW/MW/lower-HF reception.

Formula (documented, not derived/guessed):
- Total perimeter: receive-only and untuned, same floor-length logic as the
  long-wire receive antenna -- a quarter-wave (234/f(MHz)) reference at the
  band's low edge. This lands close to published field reports: a 120 ft
  loop is commonly cited as performing well at MW, a 250 ft loop better but
  with a higher noise floor (kk5jy.net LoG writeups, SWLing Post LoG
  build articles) -- our MW low-edge (0.525 MHz) gives ~446 ft, the same
  order of magnitude as those field-tested sizes.
- Feedpoint impedance: a loop lying on the ground has a low impedance that
  varies a lot with frequency and ground conditions; sources commonly cite
  a working range of roughly 300-1500 ohms, with ~450 ohms used here as a
  representative nominal value.
- Matching: a step-up transformer wound with a ~5:2 turns ratio (~6:1
  impedance ratio) on a ferrite binocular/toroid core (Fair-Rite #73 mix is
  commonly cited) -- not a 1:1 choke or a fixed-ratio unun, since the loop's
  native impedance is far below 50 ohms (the opposite problem from an
  end-fed long wire).
"""

from data_store import BANDS_MHZ, design_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE_GROUND_LOOP, BALUN_WHY_GROUND_LOOP
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register


@register("ground_loop_receive")
def design_ground_loop(band: str, lang: str = "en") -> AntennaDesign:
    low_mhz, _high_mhz = BANDS_MHZ[band]
    freq_mhz = design_frequency(band)

    total_ft = round(234.0 / low_mhz, 3)
    total_m = round(total_ft * METERS_PER_FOOT, 3)

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
            "type": BALUN_TYPE_LABELS["stepup_transformer_5_2"][lang],
            "ratio": "5:2",
            "where": BALUN_WHERE_GROUND_LOOP[lang],
            "why": BALUN_WHY_GROUND_LOOP[lang],
        },
    )
