"""Discone antenna for broadband VHF/UHF receive (scanner/SWL use).

Formula (documented, not derived/guessed -- see Electronics Notes' discone
design reference and the IJLRET discone design paper):
- Cone (vertical element) height: quarter wavelength of the LOWEST frequency
  to be covered -- the same 234/f(MHz) constant as any other quarter-wave
  element, applied to the band's low edge since that sets the antenna's
  low-frequency cutoff.
- Disc diameter: 0.7 x the cone height (a commonly published ratio).
- Cone skirt: modeled as 12 wires (within the commonly cited 8-16 range --
  a practical compromise between an easy build and a good approximation of
  a solid cone), angled at 30 degrees below horizontal from the apex
  (within the commonly cited 25-40 degree range).
- Feedpoint: fed directly with 50 ohm coax (center conductor to disc, shield
  to cone) -- no balun needed; the geometry itself gives a low, fairly
  constant impedance across a very wide bandwidth (published discone
  literature commonly cites ~1:10 bandwidth with VSWR < 2.5:1 in receive use).
"""

from data_store import BANDS_MHZ, design_frequency
from i18n import BALUN_TYPE_LABELS, BALUN_WHERE_DISCONE, BALUN_WHY_DISCONE
from models import METERS_PER_FOOT, AntennaDesign, Element
from registry import register

SKIRT_COUNT = 12
CONE_ANGLE_DEG = 30
DISC_RATIO = 0.7


@register("discone_receive")
def design_discone(band: str, lang: str = "en") -> AntennaDesign:
    low_mhz, _high_mhz = BANDS_MHZ[band]
    freq_mhz = design_frequency(band)

    cone_ft = round(234.0 / low_mhz, 3)
    cone_m = round(cone_ft * METERS_PER_FOOT, 3)
    disc_ft = round(cone_ft * DISC_RATIO, 3)
    disc_m = round(disc_ft * METERS_PER_FOOT, 3)

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
        },
    )
