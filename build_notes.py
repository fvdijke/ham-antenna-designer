"""Plain-language build advice, parameterized by an AntennaDesign.

Per the design doc: build advice is templated text with values filled in from
the calculator output, not fully static and not derived from new formulas.
Dispatches on antenna_type; each type has its own EN/NL template in i18n.py
since the build steps genuinely differ (radials vs. counterpoise vs. dipole
legs), but the choke-winding sizing logic is shared where relevant.
"""

from i18n import (
    BUILD_NOTES,
    BUILD_NOTES_DELTA_LOOP,
    BUILD_NOTES_DIPOLE,
    BUILD_NOTES_DISCONE,
    BUILD_NOTES_EDZ,
    BUILD_NOTES_EFHW,
    BUILD_NOTES_FIVE_EIGHTHS,
    BUILD_NOTES_GROUND_LOOP,
    BUILD_NOTES_INVERTED_V,
    BUILD_NOTES_JPOLE,
    BUILD_NOTES_LONGWIRE,
    BUILD_NOTES_LOOP,
    BUILD_NOTES_MOXON,
    BUILD_NOTES_OCFD,
    BUILD_NOTES_QUAD,
    BUILD_NOTES_YAGI,
    CHOKE_SPEC,
)
from models import AntennaDesign

# Rough choke winding guidance by band -- lower bands need more turns of a
# larger core to present enough common-mode impedance. (turns_toroid, turns_pipe, pipe_size)
_CHOKE_BANDS = [
    (5, "10-12", "8-10", "6"),
    (11, "8-10", "6-8", "6"),
    (20, "6-8", "5-6", "4-6"),
]
_CHOKE_DEFAULT = ("5-6", "4-5", "4")


def _choke_spec(freq_mhz: float, lang: str = "en") -> str:
    turns_toroid, turns_pipe, pipe_size = _CHOKE_DEFAULT
    for threshold, t_toroid, t_pipe, p_size in _CHOKE_BANDS:
        if freq_mhz < threshold:
            turns_toroid, turns_pipe, pipe_size = t_toroid, t_pipe, p_size
            break
    return CHOKE_SPEC[lang].format(turns_toroid=turns_toroid, turns_pipe=turns_pipe, pipe_size=pipe_size)


def _length_str(length_ft: float, length_m: float, units: str) -> str:
    return f"{length_m:.2f} m" if units == "metric" else f"{length_ft:.2f} ft"


def _advice_vertical(design: AntennaDesign, units: str, lang: str) -> str:
    t = BUILD_NOTES[lang]
    radiator = design.elements_with_role("radiator")[0]
    radials = design.elements_with_role("radial")
    length_str = _length_str(radiator.length_ft, radiator.length_m, units)
    radial_str = _length_str(radials[0].length_ft, radials[0].length_m, units) if radials else ""

    return "\n".join([
        t["title"].format(band=design.band), "",
        t["step1"].format(length=length_str), "",
        t["step2"].format(count=len(radials), length=radial_str), "",
        t["step3"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}"), "",
        t["step4"].format(
            choke=_choke_spec(design.design_freq_mhz, lang),
            balun_type=design.balun["type"], balun_ratio=design.balun["ratio"], balun_why=design.balun["why"],
        ), "",
        t["step5"],
    ])


def _advice_dipole(design: AntennaDesign, units: str, lang: str) -> str:
    t = BUILD_NOTES_DIPOLE[lang]
    leg = design.elements_with_role("radiator")[0]
    length_str = _length_str(leg.length_ft, leg.length_m, units)

    return "\n".join([
        t["title"].format(band=design.band), "",
        t["step1"].format(length=length_str), "",
        t["step2"], "",
        t["step3"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}"), "",
        t["step4"].format(balun_type=design.balun["type"], balun_ratio=design.balun["ratio"], balun_why=design.balun["why"]), "",
        t["step5"],
    ])


def _advice_efhw(design: AntennaDesign, units: str, lang: str) -> str:
    t = BUILD_NOTES_EFHW[lang]
    radiator = design.elements_with_role("radiator")[0]
    counterpoise = design.elements_with_role("counterpoise")[0]
    length_str = _length_str(radiator.length_ft, radiator.length_m, units)
    length_cp_str = _length_str(counterpoise.length_ft, counterpoise.length_m, units)

    return "\n".join([
        t["title"].format(band=design.band), "",
        t["step1"].format(length=length_str), "",
        t["step2"].format(length_cp=length_cp_str), "",
        t["step3"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}"), "",
        t["step4"].format(balun_type=design.balun["type"], balun_ratio=design.balun["ratio"], balun_why=design.balun["why"]), "",
        t["step5"],
    ])


def _advice_loop(design: AntennaDesign, units: str, lang: str) -> str:
    t = BUILD_NOTES_LOOP[lang]
    wire = design.elements_with_role("radiator")[0]
    length_str = _length_str(wire.length_ft, wire.length_m, units)
    side_str = _length_str(wire.length_ft / 4, wire.length_m / 4, units)

    return "\n".join([
        t["title"].format(band=design.band), "",
        t["step1"].format(length=length_str, side_length=side_str), "",
        t["step2"], "",
        t["step3"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}"), "",
        t["step4"].format(balun_type=design.balun["type"], balun_ratio=design.balun["ratio"], balun_why=design.balun["why"]), "",
        t["step5"],
    ])


def _advice_inverted_v(design: AntennaDesign, units: str, lang: str) -> str:
    t = BUILD_NOTES_INVERTED_V[lang]
    leg = design.elements_with_role("radiator")[0]
    length_str = _length_str(leg.length_ft, leg.length_m, units)

    return "\n".join([
        t["title"].format(band=design.band), "",
        t["step1"].format(length=length_str), "",
        t["step2"], "",
        t["step3"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}"), "",
        t["step4"].format(balun_type=design.balun["type"], balun_ratio=design.balun["ratio"], balun_why=design.balun["why"]), "",
        t["step5"],
    ])


def _advice_ocfd(design: AntennaDesign, units: str, lang: str) -> str:
    t = BUILD_NOTES_OCFD[lang]
    short_leg = design.elements_with_role("leg_short")[0]
    long_leg = design.elements_with_role("leg_long")[0]
    length_short = _length_str(short_leg.length_ft, short_leg.length_m, units)
    length_long = _length_str(long_leg.length_ft, long_leg.length_m, units)

    return "\n".join([
        t["title"].format(band=design.band), "",
        t["step1"].format(length_short=length_short, length_long=length_long), "",
        t["step2"], "",
        t["step3"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}"), "",
        t["step4"].format(balun_type=design.balun["type"], balun_ratio=design.balun["ratio"], balun_why=design.balun["why"]), "",
        t["step5"],
    ])


def _advice_jpole(design: AntennaDesign, units: str, lang: str) -> str:
    t = BUILD_NOTES_JPOLE[lang]
    radiator = design.elements_with_role("radiator")[0]
    stub = design.elements_with_role("matching_stub")[0]
    length_str = _length_str(radiator.length_ft, radiator.length_m, units)
    length_stub = _length_str(stub.length_ft, stub.length_m, units)
    tap_length = _length_str(design.extra["feed_tap_ft"], design.extra["feed_tap_m"], units)

    return "\n".join([
        t["title"].format(band=design.band), "",
        t["step1"].format(length=length_str, length_stub=length_stub), "",
        t["step2"], "",
        t["step3"].format(tap_length=tap_length, ohms=f"{design.feedpoint_impedance_ohms:.0f}"), "",
        t["step4"].format(balun_type=design.balun["type"], balun_why=design.balun["why"]), "",
        t["step5"],
    ])


def _advice_five_eighths(design: AntennaDesign, units: str, lang: str) -> str:
    t = BUILD_NOTES_FIVE_EIGHTHS[lang]
    radiator = design.elements_with_role("radiator")[0]
    radials = design.elements_with_role("radial")
    length_str = _length_str(radiator.length_ft, radiator.length_m, units)
    radial_str = _length_str(radials[0].length_ft, radials[0].length_m, units)

    return "\n".join([
        t["title"].format(band=design.band), "",
        t["step1"].format(length=length_str), "",
        t["step2"].format(count=len(radials), length_radial=radial_str), "",
        t["step3"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}"), "",
        t["step4"].format(balun_type=design.balun["type"], balun_why=design.balun["why"]), "",
        t["step5"],
    ])


def _advice_edz(design: AntennaDesign, units: str, lang: str) -> str:
    t = BUILD_NOTES_EDZ[lang]
    leg = design.elements_with_role("radiator")[0]
    length_str = _length_str(leg.length_ft, leg.length_m, units)

    return "\n".join([
        t["title"].format(band=design.band), "",
        t["step1"].format(length=length_str), "",
        t["step2"], "",
        t["step3"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}"), "",
        t["step4"].format(balun_type=design.balun["type"], balun_why=design.balun["why"]), "",
        t["step5"],
    ])


def _advice_delta_loop(design: AntennaDesign, units: str, lang: str) -> str:
    t = BUILD_NOTES_DELTA_LOOP[lang]
    wire = design.elements_with_role("radiator")[0]
    length_str = _length_str(wire.length_ft, wire.length_m, units)
    side_str = _length_str(wire.length_ft / 3, wire.length_m / 3, units)

    return "\n".join([
        t["title"].format(band=design.band), "",
        t["step1"].format(length=length_str, side_length=side_str), "",
        t["step2"], "",
        t["step3"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}"), "",
        t["step4"].format(balun_type=design.balun["type"], balun_ratio=design.balun["ratio"], balun_why=design.balun["why"]), "",
        t["step5"],
    ])


def _advice_yagi(design: AntennaDesign, units: str, lang: str) -> str:
    t = BUILD_NOTES_YAGI[lang]
    driven = design.elements_with_role("radiator")[0]
    reflector = design.elements_with_role("reflector")[0]
    director = design.elements_with_role("director")[0]
    extra = design.extra

    return "\n".join([
        t["title"].format(band=design.band), "",
        t["warning"], "",
        t["step1"].format(
            length_driven=_length_str(driven.length_ft, driven.length_m, units),
            length_reflector=_length_str(reflector.length_ft, reflector.length_m, units),
            length_director=_length_str(director.length_ft, director.length_m, units),
        ), "",
        t["step2"].format(
            length_boom=_length_str(extra["boom_ft"], extra["boom_m"], units),
            length_reflector_spacing=_length_str(extra["reflector_spacing_ft"], extra["reflector_spacing_m"], units),
            length_director_spacing=_length_str(extra["director_spacing_ft"], extra["director_spacing_m"], units),
        ), "",
        t["step3"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}"), "",
        t["step4"].format(balun_type=design.balun["type"], balun_ratio=design.balun["ratio"], balun_why=design.balun["why"]), "",
        t["step5"],
    ])


def _advice_quad(design: AntennaDesign, units: str, lang: str) -> str:
    t = BUILD_NOTES_QUAD[lang]
    driven = design.elements_with_role("driven_loop")[0]
    reflector = design.elements_with_role("reflector_loop")[0]
    extra = design.extra

    return "\n".join([
        t["title"].format(band=design.band), "",
        t["warning"], "",
        t["step1"].format(
            length_driven=_length_str(driven.length_ft, driven.length_m, units),
            length_driven_side=_length_str(driven.length_ft / 4, driven.length_m / 4, units),
            length_reflector=_length_str(reflector.length_ft, reflector.length_m, units),
            length_reflector_side=_length_str(reflector.length_ft / 4, reflector.length_m / 4, units),
        ), "",
        t["step2"].format(length_spacing=_length_str(extra["spacing_ft"], extra["spacing_m"], units)), "",
        t["step3"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}"), "",
        t["step4"].format(balun_type=design.balun["type"], balun_ratio=design.balun["ratio"], balun_why=design.balun["why"]), "",
        t["step5"],
    ])


def _advice_moxon(design: AntennaDesign, units: str, lang: str) -> str:
    t = BUILD_NOTES_MOXON[lang]
    driven = design.elements_with_role("radiator")[0]
    reflector = design.elements_with_role("reflector")[0]
    extra = design.extra
    wire_mm = extra["wire_diameter_m"] * 1000

    return "\n".join([
        t["title"].format(band=design.band), "",
        t["warning"].format(wire_diameter=f"{wire_mm:.1f}"), "",
        t["step1"].format(
            length_driven=_length_str(driven.length_ft, driven.length_m, units),
            length_a=_length_str(extra["a_ft"], extra["a_m"], units),
            length_b=_length_str(extra["b_ft"], extra["b_m"], units),
            length_reflector=_length_str(reflector.length_ft, reflector.length_m, units),
            length_d=_length_str(extra["d_ft"], extra["d_m"], units),
        ), "",
        t["step2"].format(length_c=_length_str(extra["c_ft"], extra["c_m"], units)), "",
        t["step3"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}"), "",
        t["step4"].format(balun_type=design.balun["type"], balun_ratio=design.balun["ratio"], balun_why=design.balun["why"]), "",
        t["step5"],
    ])


def _advice_longwire(design: AntennaDesign, units: str, lang: str) -> str:
    t = BUILD_NOTES_LONGWIRE[lang]
    radiator = design.elements_with_role("radiator")[0]
    counterpoise = design.elements_with_role("counterpoise")[0]
    length_str = _length_str(radiator.length_ft, radiator.length_m, units)
    length_cp_str = _length_str(counterpoise.length_ft, counterpoise.length_m, units)

    return "\n".join([
        t["title"].format(band=design.band), "",
        t["warning"].format(length=length_str), "",
        t["step1"].format(length=length_str), "",
        t["step2"].format(length_cp=length_cp_str), "",
        t["step3"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}"), "",
        t["step4"].format(balun_type=design.balun["type"], balun_ratio=design.balun["ratio"], balun_why=design.balun["why"]), "",
        t["step5"],
    ])


def _advice_discone(design: AntennaDesign, units: str, lang: str) -> str:
    t = BUILD_NOTES_DISCONE[lang]
    cone = design.elements_with_role("radiator")[0]
    disc = design.elements_with_role("disc")[0]
    extra = design.extra

    return "\n".join([
        t["title"].format(band=design.band), "",
        t["warning"].format(skirt_count=extra["skirt_count"], cone_angle=extra["cone_angle_deg"]), "",
        t["step1"].format(
            length_cone=_length_str(cone.length_ft, cone.length_m, units),
            length_disc=_length_str(disc.length_ft, disc.length_m, units),
        ), "",
        t["step2"].format(skirt_count=extra["skirt_count"], cone_angle=extra["cone_angle_deg"]), "",
        t["step3"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}"), "",
        t["step4"].format(balun_type=design.balun["type"], balun_why=design.balun["why"]), "",
        t["step5"],
    ])


def _advice_ground_loop(design: AntennaDesign, units: str, lang: str) -> str:
    t = BUILD_NOTES_GROUND_LOOP[lang]
    wire = design.elements_with_role("radiator")[0]
    length_str = _length_str(wire.length_ft, wire.length_m, units)
    side_str = _length_str(wire.length_ft / 4, wire.length_m / 4, units)

    return "\n".join([
        t["title"].format(band=design.band), "",
        t["warning"].format(length=length_str), "",
        t["step1"].format(length=length_str, side_length=side_str), "",
        t["step2"], "",
        t["step3"].format(ohms=f"{design.feedpoint_impedance_ohms:.0f}"), "",
        t["step4"].format(balun_type=design.balun["type"], balun_why=design.balun["why"]), "",
        t["step5"],
    ])


_ADVICE_BY_TYPE = {
    "vertical_quarter_wave": _advice_vertical,
    "dipole_half_wave": _advice_dipole,
    "efhw": _advice_efhw,
    "loop_full_wave": _advice_loop,
    "inverted_v_dipole": _advice_inverted_v,
    "off_center_fed_dipole": _advice_ocfd,
    "j_pole": _advice_jpole,
    "five_eighths_vertical": _advice_five_eighths,
    "extended_double_zepp": _advice_edz,
    "delta_loop_vertical": _advice_delta_loop,
    "yagi_3_element": _advice_yagi,
    "quad_2_element": _advice_quad,
    "moxon_2_element": _advice_moxon,
    "longwire_receive": _advice_longwire,
    "discone_receive": _advice_discone,
    "ground_loop_receive": _advice_ground_loop,
}


def build_advice(design: AntennaDesign, units: str = "metric", lang: str = "en") -> str:
    if design.antenna_type not in _ADVICE_BY_TYPE:
        raise ValueError(f"No build advice template for antenna type '{design.antenna_type}'")
    return _ADVICE_BY_TYPE[design.antenna_type](design, units, lang)


def _build_argparser():
    import argparse

    from data_store import BANDS_MHZ
    from registry import REGISTRY

    parser = argparse.ArgumentParser(description="Print build advice for an antenna design")
    parser.add_argument("antenna_type", nargs="?", default="vertical_quarter_wave", help=f"One of: {', '.join(REGISTRY)}")
    parser.add_argument("band", nargs="?", default="20m", help=f"HAM band, one of: {', '.join(BANDS_MHZ)}")
    parser.add_argument("--units", choices=["metric", "imperial"], default="metric")
    parser.add_argument("--lang", choices=["en", "nl"], default="en")
    return parser


if __name__ == "__main__":
    import calculators  # noqa: F401
    from registry import design as design_fn

    args = _build_argparser().parse_args()
    d = design_fn(args.antenna_type, args.band, lang=args.lang)
    print(build_advice(d, units=args.units, lang=args.lang))
