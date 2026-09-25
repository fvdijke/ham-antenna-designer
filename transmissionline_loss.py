"""Transmission line loss: matched loss per cable, extra loss from SWR on
the line, and the resulting power budget.

Matched loss model
------------------
Every cable in data/cables.json carries two typical datasheet points,
``loss_db_100m = [loss @ 10 MHz, loss @ 100 MHz]`` (dB per 100 m, matched).
Coax loss is conductor loss (grows with sqrt(f), skin effect) plus
dielectric loss (grows with f), so the two points are fitted to

    L(f) = k1 * sqrt(f) + k2 * f        [dB/100 m, f in MHz]

That form needs L100 / L10 >= sqrt(10). Very thin cables (RG-174, LMR-195,
...) are steeper than sqrt(f) below ~10 MHz because the skin depth there is
no longer small compared to the conductor; for those a power law through
both points is used instead: L(f) = L10 * (f / 10) ** n.

SWR on the line (ARRL Antenna Book, "additional loss due to SWR")
-----------------------------------------------------------------
With matched loss ML (dB) and SWR S at the ANTENNA end of the line:

    a  = 10 ** (ML / 10)
    G  = (S - 1) / (S + 1)
    TL = 10 * log10((a**2 - G**2) / (a * (1 - G**2)))     [dB, total]

TL is the ratio of the power into the line to the power absorbed by the
antenna, assuming the transmitter (or a tuner in the shack) is matched to
the line input -- reflected power is re-reflected, not lost, it only makes
extra passes through the lossy line. The SWR must be taken against the
line's own impedance (450/600 ohms for ladder line, not 50 ohms).
"""

import math

from data_store import CABLES

METERS_PER_FOOT = 0.3048


def _loss_coefficients(cable_type: str):
    """("sqrt", k1, k2) or ("power", L10, n) for a cable."""
    if cable_type not in CABLES:
        raise ValueError(f"Unknown cable '{cable_type}'. Known cables: {', '.join(CABLES)}")
    l10, l100 = CABLES[cable_type]["loss_db_100m"]
    k1 = (10 * l10 - l100) / (10 * (math.sqrt(10) - 1))
    k2 = (l10 - k1 * math.sqrt(10)) / 10
    if k1 >= 0 and k2 >= 0:
        return ("sqrt", k1, k2)
    return ("power", l10, math.log10(l100 / l10))


def matched_loss_db_per_100m(cable_type: str, freq_mhz: float) -> float:
    """Matched-line loss in dB per 100 m at freq_mhz."""
    kind, p1, p2 = _loss_coefficients(cable_type)
    if kind == "sqrt":
        return p1 * math.sqrt(freq_mhz) + p2 * freq_mhz
    return p1 * (freq_mhz / 10.0) ** p2


def get_cable_loss_per_100ft(cable_type: str, freq_mhz: float) -> float:
    """Matched-line loss in dB per 100 ft (kept for API compatibility)."""
    return matched_loss_db_per_100m(cable_type, freq_mhz) * 100 * METERS_PER_FOOT / 100


def calculate_cable_loss(cable_type: str, freq_mhz: float, distance_ft: float) -> float:
    """Matched-line loss in dB for a run of distance_ft feet."""
    return round(get_cable_loss_per_100ft(cable_type, freq_mhz) * distance_ft / 100.0, 2)


def calculate_cable_loss_meters(cable_type: str, freq_mhz: float, distance_m: float) -> float:
    """Matched-line loss in dB for a run of distance_m metres."""
    return round(matched_loss_db_per_100m(cable_type, freq_mhz) * distance_m / 100.0, 2)


def total_line_loss_db(matched_loss_db: float, swr: float = 1.0) -> float:
    """Total line loss (dB) including the extra loss caused by SWR at the
    antenna end (ARRL formula, see module docstring)."""
    if swr <= 1.0 or matched_loss_db <= 0:
        return matched_loss_db
    a = 10 ** (matched_loss_db / 10)
    g = (swr - 1) / (swr + 1)
    return 10 * math.log10((a * a - g * g) / (a * (1 - g * g)))


def swr_extra_loss_db(matched_loss_db: float, swr: float = 1.0) -> float:
    """The part of the total line loss that is caused by the SWR."""
    return total_line_loss_db(matched_loss_db, swr) - matched_loss_db


def calculate_power_at_antenna(transmit_power_watts: float, cable_loss_db: float,
                               swr: float = 1.0) -> float:
    """Power absorbed by the antenna (W) for matched loss cable_loss_db and
    SWR at the antenna, with the transmitter/tuner matched to the line."""
    return round(transmit_power_watts * 10 ** (-total_line_loss_db(cable_loss_db, swr) / 10), 2)


def calculate_efficiency(cable_type: str, freq_mhz: float, distance_ft: float,
                         swr: float = 1.0) -> float:
    """Percentage of the transmitter power that reaches the antenna."""
    ml = calculate_cable_loss(cable_type, freq_mhz, distance_ft)
    return round(100 * 10 ** (-total_line_loss_db(ml, swr) / 10), 1)


def cable_impedance(cable_type: str) -> float:
    return float(CABLES[cable_type]["impedance_ohms"])


def get_all_cable_types() -> list:
    """All cable names, in data-file order (grouped by family)."""
    return list(CABLES)


def compare_cables(freq_mhz: float, distance_ft: float) -> dict:
    """Matched loss of every cable for one run, lowest loss first."""
    comparison = {c: calculate_cable_loss(c, freq_mhz, distance_ft) for c in CABLES}
    return dict(sorted(comparison.items(), key=lambda x: x[1]))


def cable_loss_analysis(cable_type: str, freq_mhz: float, max_distance_ft: float) -> dict:
    """Matched loss at a set of standard run lengths up to max_distance_ft."""
    distances = [d for d in (10, 25, 50, 100, 150, 200, 300, 500) if d <= max_distance_ft]
    return {d: calculate_cable_loss(cable_type, freq_mhz, d) for d in distances}


def power_budget_summary(transmit_watts: float, cable_type: str, freq_mhz: float,
                         distance_m: float, antenna_gain_dbi: float,
                         swr: float = 1.0) -> dict:
    """Complete power budget for one station."""
    matched = matched_loss_db_per_100m(cable_type, freq_mhz) * distance_m / 100.0
    total = total_line_loss_db(matched, swr)
    power_at_antenna = transmit_watts * 10 ** (-total / 10)
    return {
        "transmit_power_watts": transmit_watts,
        "cable_loss_db": round(matched, 2),
        "swr_loss_db": round(total - matched, 2),
        "total_loss_db": round(total, 2),
        "efficiency_percent": round(100 * power_at_antenna / transmit_watts, 1),
        "power_at_antenna_watts": round(power_at_antenna, 2),
        "antenna_gain_dbi": antenna_gain_dbi,
        "eirp_watts": round(power_at_antenna * 10 ** (antenna_gain_dbi / 10), 2),
    }
