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
ANTENNA_TYPES = _load("antenna_types.json")


def design_frequency(band: str) -> float:
    """Pick a sane design frequency: midpoint of the band, in MHz."""
    if band not in BANDS_MHZ:
        raise ValueError(f"Unknown band '{band}'. Known bands: {', '.join(BANDS_MHZ)}")
    low, high = BANDS_MHZ[band]
    return round((low + high) / 2, 4)


def cable_velocity_factor(cable_name: str) -> float:
    if cable_name not in CABLES:
        raise ValueError(f"Unknown cable '{cable_name}'. Known cables: {', '.join(CABLES)}")
    return CABLES[cable_name]["velocity_factor"]


def antenna_type_label(antenna_type: str, lang: str = "en") -> str:
    if antenna_type not in ANTENNA_TYPES:
        raise ValueError(f"Unknown antenna type '{antenna_type}'. Known: {', '.join(ANTENNA_TYPES)}")
    return ANTENNA_TYPES[antenna_type][f"label_{lang}"]
