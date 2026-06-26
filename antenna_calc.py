"""Quarter-wave ground-mounted vertical antenna calculator.

Formulas used (documented per design doc decisions, not derived/guessed):
- Quarter-wave element length (feet): 234 / f(MHz)  [standard ham radio rule of thumb,
  accounts for end effect / velocity of propagation in wire antennas]
- Radials: 4x quarter-wave radials (lambda/4), the most commonly cited rule of thumb
  for a ground-mounted quarter-wave vertical.
- Balun/unun: lookup table, not derived. A ground-mounted quarter-wave vertical fed
  directly with coax typically needs only a 1:1 current choke at the feedpoint to
  suppress common-mode current -- no impedance-transforming unun required.
"""

from dataclasses import dataclass, field

from i18n import BALUN_WHERE, BALUN_WHY, CALC_OUTPUT

METERS_PER_FOOT = 0.3048

# HAM band reference list: name -> (low_mhz, high_mhz)
BANDS_MHZ = {
    "160m": (1.8, 2.0),
    "80m": (3.5, 4.0),
    "40m": (7.0, 7.3),
    "30m": (10.1, 10.15),
    "20m": (14.0, 14.35),
    "17m": (18.068, 18.168),
    "15m": (21.0, 21.45),
    "12m": (24.89, 24.99),
    "10m": (28.0, 29.7),
    "6m": (50.0, 54.0),
}

# Balun/unun lookup table, keyed by antenna type. "type"/"ratio" are kept in
# standard RF shorthand (not translated); "where"/"why" come from i18n per lang.
BALUN_TABLE = {
    "vertical_quarter_wave": {
        "type": "1:1 current choke",
        "ratio": "1:1",
    }
}


def balun_for(antenna_type: str, lang: str = "en") -> dict:
    entry = dict(BALUN_TABLE[antenna_type])
    entry["where"] = BALUN_WHERE[lang]
    entry["why"] = BALUN_WHY[lang]
    return entry


@dataclass
class VerticalDesign:
    band: str
    design_freq_mhz: float
    element_length_ft: float
    element_length_m: float
    radial_count: int
    radial_length_ft: float
    radial_length_m: float
    feedpoint_impedance_ohms: float
    balun: dict = field(default_factory=dict)


def design_frequency(band: str) -> float:
    """Pick a sane design frequency: midpoint of the band, in MHz."""
    if band not in BANDS_MHZ:
        raise ValueError(
            f"Unknown band '{band}'. Known bands: {', '.join(BANDS_MHZ)}"
        )
    low, high = BANDS_MHZ[band]
    return round((low + high) / 2, 4)


def quarter_wave_length_ft(freq_mhz: float) -> float:
    """Standard quarter-wave rule of thumb: 234 / f(MHz), in feet."""
    if freq_mhz <= 0:
        raise ValueError("freq_mhz must be positive")
    return 234.0 / freq_mhz


def design_vertical(band: str, radial_count: int = 4, lang: str = "en") -> VerticalDesign:
    """Design a ground-mounted quarter-wave vertical for the given band.

    radial_count: number of quarter-wave radials (4 is the standard rule of thumb).
    lang: "en" or "nl" -- controls only the balun advice text, not the math.
    """
    if radial_count < 1:
        raise ValueError("radial_count must be at least 1")

    freq_mhz = design_frequency(band)
    element_ft = quarter_wave_length_ft(freq_mhz)
    radial_ft = element_ft  # radials are also quarter-wave length

    return VerticalDesign(
        band=band,
        design_freq_mhz=freq_mhz,
        element_length_ft=round(element_ft, 3),
        element_length_m=round(element_ft * METERS_PER_FOOT, 3),
        radial_count=radial_count,
        radial_length_ft=round(radial_ft, 3),
        radial_length_m=round(radial_ft * METERS_PER_FOOT, 3),
        feedpoint_impedance_ohms=36.0,  # standard textbook value for an ideal quarter-wave
        # vertical over a perfect ground; real-world radials bring it closer to 25-35 ohms.
        balun=balun_for("vertical_quarter_wave", lang=lang),
    )


def _fmt(value_ft: float, value_m: float, units: str) -> str:
    return f"{value_m} m" if units == "metric" else f"{value_ft} ft"


def _build_argparser():
    import argparse

    parser = argparse.ArgumentParser(description="Ground-mounted quarter-wave vertical antenna calculator")
    parser.add_argument("band", nargs="?", default="20m", help=f"HAM band, one of: {', '.join(BANDS_MHZ)}")
    parser.add_argument(
        "--units", choices=["metric", "imperial"], default="metric",
        help="Display units for lengths (default: metric)",
    )
    parser.add_argument(
        "--lang", choices=["en", "nl"], default="en",
        help="Language for output text (default: en)",
    )
    return parser


if __name__ == "__main__":
    args = _build_argparser().parse_args()

    d = design_vertical(args.band, lang=args.lang)
    t = CALC_OUTPUT[args.lang]
    print(t["heading"].format(band=d.band))
    print(t["freq"].format(freq=d.design_freq_mhz))
    print(t["element"].format(length=_fmt(d.element_length_ft, d.element_length_m, args.units)))
    print(t["radials"].format(count=d.radial_count, length=_fmt(d.radial_length_ft, d.radial_length_m, args.units)))
    print(t["impedance"].format(ohms=d.feedpoint_impedance_ohms))
    print(t["balun"].format(type=d.balun["type"], ratio=d.balun["ratio"], where=d.balun["where"]))
