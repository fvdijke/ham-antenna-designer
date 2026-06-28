"""Shared text formatting for an AntennaDesign -- used by the CLI and the GUI
so both stay in sync without duplicating logic per antenna type."""

from collections import OrderedDict

from data_store import antenna_type_label
from i18n import ROLE_LABELS, SUMMARY_LABELS
from models import AntennaDesign


def _fmt_len(length_ft: float, length_m: float, units: str) -> str:
    return f"{length_m} m" if units == "metric" else f"{length_ft} ft"


def format_summary(design: AntennaDesign, units: str = "metric", lang: str = "en") -> str:
    t = SUMMARY_LABELS[lang]
    label = antenna_type_label(design.antenna_type, lang)
    lines = [f"{label} -- {design.band} band", "", f"  {t['freq']}: {design.design_freq_mhz} MHz"]

    groups = OrderedDict()
    for e in design.elements:
        groups.setdefault(e.role, []).append(e)

    for role, elems in groups.items():
        role_label = ROLE_LABELS[role][lang]
        sample = elems[0]
        if len(elems) == 1:
            lines.append(f"  {role_label}: {_fmt_len(sample.length_ft, sample.length_m, units)}")
        else:
            lines.append(f"  {role_label}: {len(elems)} x {_fmt_len(sample.length_ft, sample.length_m, units)} {t['each']}")

    lines.append(f"  {t['impedance']}: ~{design.feedpoint_impedance_ohms:.0f} {t['ohms']}")
    lines.append(f"  {t['balun']}: {design.balun['type']} ({design.balun['ratio']}) -- {design.balun['where']}")
    return "\n".join(lines)
