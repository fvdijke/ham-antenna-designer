"""Discone antenna for broadband VHF/UHF receive (scanner/SWL use).

Formula (documented, not derived/guessed -- see Electronics Notes' discone
design reference and the IJLRET discone design paper):
- Cone skirt (slant) length: a free-space quarter wavelength (75/f(MHz) m)
  at the LOWEST frequency to be covered -- the band's low edge, since that
  sets the antenna's low-frequency cutoff.
- Cone half-angle: 30 degrees from vertical (within the commonly cited
  25-40 degree range), so height = slant x cos 30 and base diameter =
  2 x slant x sin 30.
- Disc diameter: 0.7 x the cone's base diameter (a commonly published ratio).
- Cone skirt: modeled as 12 wires (within the commonly cited 8-16 range --
  a practical compromise between an easy build and a good approximation of
  a solid cone).
- Feedpoint: fed directly with 50 ohm coax (center conductor to disc, shield
  to cone) -- no balun needed; the geometry itself gives a low, fairly
  constant impedance across a very wide bandwidth (published discone
  literature commonly cites ~1:10 bandwidth with VSWR < 2.5:1 in receive use).
"""

import math

from data_store import design_frequency, low_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE_DISCONE, BALUN_WHY_DISCONE
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register

SKIRT_COUNT = 12
CONE_ANGLE_DEG = 30
DISC_RATIO = 0.7


@register("discone_receive")
def design_discone(band: str, lang: str = "en", freq_mhz: float = None, wire_vf: float = 1.0) -> AntennaDesign:
    low_mhz = low_frequency(band, freq_mhz)
    freq_mhz = design_frequency(band, freq_mhz)

    # Skirt wire (slant) = free-space quarter wave at the low edge: a discone
    # is a broadband structure, not a resonant wire, so no end-effect factor.
    cone_m = round(0.25 * 300.0 / low_mhz, 3)
    cone_ft = round(cone_m / METERS_PER_FOOT, 3)
    half_angle = math.radians(CONE_ANGLE_DEG)
    cone_height_m = round(cone_m * math.cos(half_angle), 3)
    cone_base_m = round(2 * cone_m * math.sin(half_angle), 3)
    disc_m = round(cone_base_m * DISC_RATIO, 3)
    disc_ft = round(disc_m / METERS_PER_FOOT, 3)

    elements = [
        Element("cone", cone_ft, cone_m, "radiator"),
        Element("disc", disc_ft, disc_m, "disc"),
    ]

    return AntennaDesign(
        antenna_type="discone_receive",
        band=band,
        design_freq_mhz=freq_mhz,
        elements=elements,
        feedpoint_impedance_ohms=50.0,
        feed_location="apex",
        geometry="discone",
        balun={
            "type": BALUN_TYPE_LABELS["direct_coax_feed"][lang],
            "ratio": "-",
            "where": BALUN_WHERE_DISCONE[lang],
            "why": BALUN_WHY_DISCONE[lang],
        },
        extra={
            "skirt_count": SKIRT_COUNT,
            "cone_angle_deg": CONE_ANGLE_DEG,
            "cone_height_m": cone_height_m,
            "cone_base_m": cone_base_m,
        },
    )
