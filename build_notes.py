"""Plain-language build advice, parameterized by a VerticalDesign.

Per the design doc: build advice is templated text with values filled in from
the calculator output, not fully static and not derived from new formulas.
Available in English and Dutch (--lang en|nl).
"""

from antenna_calc import VerticalDesign
from i18n import BUILD_NOTES, CHOKE_SPEC

# Rough choke winding guidance by band -- lower bands need more turns of a
# larger core to present enough common-mode impedance. (turns_toroid, turns_pipe, pipe_size)
_CHOKE_BANDS = [
    (5, "10-12", "8-10", "6"),
    (11, "8-10", "6-8", "6"),
    (20, "6-8", "5-6", "4-6"),
]
_CHOKE_DEFAULT = ("5-6", "4-5", "4")


def _choke_spec(design: VerticalDesign, lang: str = "en") -> str:
    freq = design.design_freq_mhz
    turns_toroid, turns_pipe, pipe_size = _CHOKE_DEFAULT
    for threshold, t_toroid, t_pipe, p_size in _CHOKE_BANDS:
        if freq < threshold:
            turns_toroid, turns_pipe, pipe_size = t_toroid, t_pipe, p_size
            break
    return CHOKE_SPEC[lang].format(turns_toroid=turns_toroid, turns_pipe=turns_pipe, pipe_size=pipe_size)


def build_advice(design: VerticalDesign, units: str = "metric", lang: str = "en") -> str:
    t = BUILD_NOTES[lang]
    length = design.element_length_m if units == "metric" else design.element_length_ft
    unit_label = "m" if units == "metric" else "ft"
    radial_length = design.radial_length_m if units == "metric" else design.radial_length_ft
    length_str = f"{length:.2f} {unit_label}"
    radial_str = f"{radial_length:.2f} {unit_label}"

    lines = [
        t["title"].format(band=design.band),
        "",
        t["step1"].format(length=length_str),
        "",
        t["step2"].format(count=design.radial_count, length=radial_str),
        "",
        t["step3"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}"),
        "",
        t["step4"].format(
            choke=_choke_spec(design, lang=lang),
            balun_type=design.balun["type"],
            balun_ratio=design.balun["ratio"],
            balun_why=design.balun["why"],
        ),
        "",
        t["step5"],
    ]
    return "\n".join(lines)


def _build_argparser():
    import argparse
    from antenna_calc import BANDS_MHZ

    parser = argparse.ArgumentParser(description="Print build advice for a vertical antenna design")
    parser.add_argument("band", nargs="?", default="20m", help=f"HAM band, one of: {', '.join(BANDS_MHZ)}")
    parser.add_argument(
        "--units", choices=["metric", "imperial"], default="metric",
        help="Units for lengths in the advice text (default: metric)",
    )
    parser.add_argument(
        "--lang", choices=["en", "nl"], default="en",
        help="Language for the advice text (default: en)",
    )
    return parser


if __name__ == "__main__":
    from antenna_calc import design_vertical

    args = _build_argparser().parse_args()
    d = design_vertical(args.band, lang=args.lang)
    print(build_advice(d, units=args.units, lang=args.lang))
