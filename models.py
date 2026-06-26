"""Shared data model for antenna designs, independent of antenna type."""

from dataclasses import dataclass, field
from typing import List

METERS_PER_FOOT = 0.3048


@dataclass
class Element:
    """A single physical piece of wire/tubing in the antenna."""
    name: str
    length_ft: float
    length_m: float
    role: str  # "radiator" | "radial" | "counterpoise"


@dataclass
class AntennaDesign:
    antenna_type: str
    band: str
    design_freq_mhz: float
    elements: List[Element]
    feedpoint_impedance_ohms: float
    feed_location: str  # "base" | "center" | "end" | ...
    geometry: str  # "vertical" | "horizontal_center_fed" | "horizontal_end_fed" | ...
    balun: dict = field(default_factory=dict)
    extra: dict = field(default_factory=dict)  # type-specific structured data that
    # isn't a cuttable wire element: spacing/boom length, feed tap position, etc.

    def elements_with_role(self, role: str) -> List[Element]:
        return [e for e in self.elements if e.role == role]
