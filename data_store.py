"""Loads the JSON reference data: HAM bands, feed cables (with velocity
factor), and antenna type metadata. Single source of truth for all three
lists requested in the original brief."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def _load(name: str) -> dict:
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


BANDS_MHZ = {k: tuple(v) for k, v in _load("bands.json").items()}
CABLES = _load("cables.json")
WIRES = _load("wires.json")
ANTENNA_TYPES = _load("antenna_types.json")

# Antenna types that share a physical shape but come in different wavelength
# fractions (e.g. vertical: 1/4, 1/2, 5/8, 1) are grouped here so the GUI can
# offer "shape" then "wave fraction" as two independent pickers instead of
# one long flat list. Types without a shape_family (Yagi, J-pole, OCF, ...)
# are distinct designs in their own right and stay as direct single picks.
SHAPE_FAMILIES = {}
for _type_key, _meta in ANTENNA_TYPES.items():
    if "shape_family" in _meta:
        SHAPE_FAMILIES.setdefault(_meta["shape_family"], {})[_meta["wave_fraction"]] = _type_key

STANDALONE_TYPES = [k for k, v in ANTENNA_TYPES.items() if "shape_family" not in v]

# Fraction sort order within a shape family (smallest to largest wavelength).
_FRACTION_ORDER = ["1/4", "1/2", "5/8", "1", "1.25"]


def wave_fractions_for(shape_family: str):
    """Wave fractions available for a shape family, in ascending order."""
    fractions = SHAPE_FAMILIES.get(shape_family, {})
    return sorted(fractions, key=lambda f: _FRACTION_ORDER.index(f) if f in _FRACTION_ORDER else 99)


def antenna_type_for(shape_family: str, wave_fraction: str) -> str:
    return SHAPE_FAMILIES[shape_family][wave_fraction]


def design_frequency(band: str, freq_mhz: float = None) -> float:
    """Pick the design frequency: the user's custom override if given,
    otherwise the midpoint of the band, in MHz."""
    if freq_mhz is not None:
        return freq_mhz
    if band not in BANDS_MHZ:
        raise ValueError(f"Unknown band '{band}'. Known bands: {', '.join(BANDS_MHZ)}")
    low, high = BANDS_MHZ[band]
    return round((low + high) / 2, 4)


def low_frequency(band: str, freq_mhz: float = None) -> float:
    """The frequency that sets a design's low-end cutoff: the user's custom
    override if given (no range to speak of -- it IS the target), otherwise
    the band's low edge."""
    if freq_mhz is not None:
        return freq_mhz
    if band not in BANDS_MHZ:
        raise ValueError(f"Unknown band '{band}'. Known bands: {', '.join(BANDS_MHZ)}")
    low, _high = BANDS_MHZ[band]
    return low


def cable_velocity_factor(cable_name: str) -> float:
    if cable_name not in CABLES:
        raise ValueError(f"Unknown cable '{cable_name}'. Known cables: {', '.join(CABLES)}")
    return CABLES[cable_name]["velocity_factor"]


def wire_velocity_factor(wire_name: str) -> float:
    if wire_name not in WIRES:
        raise ValueError(f"Unknown wire '{wire_name}'. Known wires: {', '.join(WIRES)}")
    return WIRES[wire_name]["velocity_factor"]


def antenna_type_label(antenna_type: str, lang: str = "en") -> str:
    if antenna_type not in ANTENNA_TYPES:
        raise ValueError(f"Unknown antenna type '{antenna_type}'. Known: {', '.join(ANTENNA_TYPES)}")
    return ANTENNA_TYPES[antenna_type][f"label_{lang}"]
