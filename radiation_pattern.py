"""Radiation pattern and antenna gain calculations.

Calculate antenna gain, directivity, F/B ratio, and generate polar patterns
for visualization. Patterns are idealized based on antenna type.

Gain values (dBi):
- Isotropic reference (0 dBi) = radiates equally in all directions
- Dipole: ~2.15 dBi (0 dBd)
- Vertical (1/4λ): ~0 dBi (has ground gain)
- Yagi: 8-15 dBi depending on boom length
- EFHW: ~1.6 dBi
"""

import math


def calculate_gain_dbi(antenna_type: str, band: str = None) -> float:
    """
    Calculate antenna gain in dBi (decibels relative to isotropic).

    Args:
        antenna_type: Antenna type (e.g., "dipole_half_wave")
        band: Band name (optional, for some calculations)

    Returns:
        Gain in dBi
    """
    # Reference values from ARRL Handbook and antenna literature
    gain_table = {
        "dipole_half_wave": 2.15,
        "vertical_quarter_wave": 0.0,  # Includes ground gain
        "vertical_half_wave": 1.5,
        "vertical_5_8_wave": 3.0,
        "vertical_full_wave": 0.5,  # Very high angle, not ideal
        "efhw_half_wave": 1.6,
        "inverted_v_dipole": 1.8,  # Slight loss vs flat dipole
        "ocfd_dipole": 2.0,
        "loop_full_wave": 1.2,  # Small loss vs dipole
        "delta_loop": 1.1,
        "jpole": 2.4,  # Slight gain from J match
        "yagi_3_element": 8.5,
        "yagi_5_element": 11.5,
        "quad_2_element": 7.0,
        "moxon_rectangle": 6.5,
        "longwire_receive": 0.0,  # Receive-only, varies with length
        "discone": 2.0,  # Average over bandwidth
        "ground_loop_receive": 1.0,  # Directional receive antenna
    }

    return gain_table.get(antenna_type, 2.0)  # Default: dipole-like gain


def calculate_f_b_ratio(antenna_type: str) -> float:
    """
    Calculate Front-to-Back (F/B) ratio in dB.

    F/B ratio measures directivity: how much stronger forward lobe is vs back.

    Args:
        antenna_type: Antenna type

    Returns:
        F/B ratio in dB (higher = more directional)
    """
    fb_table = {
        "dipole_half_wave": 0.0,  # Omnidirectional in azimuth, no F/B
        "vertical_quarter_wave": 0.0,
        "vertical_half_wave": 0.0,
        "vertical_5_8_wave": 0.0,
        "vertical_full_wave": 0.0,
        "efhw_half_wave": 1.5,  # Slight directivity
        "inverted_v_dipole": 0.0,
        "ocfd_dipole": 2.0,
        "loop_full_wave": 8.0,  # More directional
        "delta_loop": 6.0,
        "jpole": 15.0,  # Very directional (end-fire)
        "yagi_3_element": 12.0,
        "yagi_5_element": 15.0,
        "quad_2_element": 10.0,
        "moxon_rectangle": 8.0,
        "longwire_receive": 10.0,  # Receives well in one direction
        "discone": 0.0,  # Omnidirectional
        "ground_loop_receive": 12.0,  # Strongly directional
    }

    return fb_table.get(antenna_type, 0.0)


def calculate_takeoff_angle(antenna_type: str, band: str = None) -> float:
    """
    Calculate typical take-off angle (radiation angle) in degrees.

    Take-off angle affects DX vs local communication:
    - Low angle (10-20°) = better for DX
    - High angle (30-60°) = better for local
    - Very high (60°+) = NVIS (Near Vertical Incidence)

    Args:
        antenna_type: Antenna type
        band: Band (optional)

    Returns:
        Take-off angle in degrees
    """
    angle_table = {
        "dipole_half_wave": 25.0,  # Moderate take-off
        "vertical_quarter_wave": 30.0,  # Over real ground
        "vertical_half_wave": 15.0,  # Lower angle
        "vertical_5_8_wave": 20.0,
        "vertical_full_wave": 45.0,  # High angle
        "efhw_half_wave": 30.0,
        "inverted_v_dipole": 35.0,  # Higher angle than flat dipole
        "ocfd_dipole": 25.0,
        "loop_full_wave": 20.0,
        "delta_loop": 25.0,
        "jpole": 15.0,  # Low angle
        "yagi_3_element": 15.0,  # Depends on height
        "yagi_5_element": 12.0,
        "quad_2_element": 18.0,
        "moxon_rectangle": 18.0,
        "longwire_receive": 20.0,
        "discone": 35.0,  # Broad angle
        "ground_loop_receive": 25.0,
    }

    return angle_table.get(antenna_type, 25.0)


def generate_azimuth_pattern(antenna_type: str, num_points: int = 360) -> dict:
    """
    Generate polar radiation pattern for azimuth (horizontal) plane.

    Returns relative power at each azimuth angle (0-360°).

    Args:
        antenna_type: Antenna type
        num_points: Number of points in pattern (default 360, one per degree)

    Returns:
        Dict with angles and relative power (normalized 0-1)
    """
    gain_db = calculate_gain_dbi(antenna_type)
    fb_ratio_db = calculate_f_b_ratio(antenna_type)

    angles = list(range(num_points))
    power = []

    for angle_deg in angles:
        # Normalize angle to 0-180° (front to back)
        angle_norm = min(angle_deg, 360 - angle_deg)

        # Generate pattern based on F/B ratio
        if fb_ratio_db == 0:
            # Omnidirectional (dipole, vertical)
            relative_power = 1.0

        elif antenna_type in ["jpole", "yagi_3_element", "yagi_5_element",
                             "quad_2_element", "moxon_rectangle"]:
            # End-fire or directional antennas
            # Main lobe narrowing based on F/B ratio
            beamwidth = 60 / (1 + fb_ratio_db / 20)  # Narrower with more FB

            if angle_norm < beamwidth / 2:
                # Main lobe (raised cosine)
                relative_power = (1 + math.cos(math.radians(angle_norm))) / 2
            else:
                # Side lobes and back lobe
                sidelobe_level = 10 ** (-fb_ratio_db / 20)
                relative_power = sidelobe_level * 0.5

        elif antenna_type in ["loop_full_wave", "delta_loop"]:
            # Directional but not end-fire
            if angle_norm < 90:
                relative_power = math.cos(math.radians(angle_norm / 2))
            else:
                relative_power = 0.3

        elif antenna_type in ["ocfd_dipole", "efhw_half_wave"]:
            # Slightly directional
            if angle_norm < 60:
                relative_power = 1.0
            else:
                relative_power = 0.5 + 0.5 * math.cos(math.radians(angle_norm))

        else:
            # Default: omnidirectional or nearly so
            relative_power = 1.0

        # Normalize to 0-1
        relative_power = max(0.0, min(1.0, relative_power))
        power.append(relative_power)

    return {
        "angles": angles,
        "power": power,
        "gain_dbi": gain_db,
        "fb_ratio_db": fb_ratio_db,
    }


def generate_elevation_pattern(antenna_type: str, height_wavelengths: float = 0.5,
                               num_points: int = 180) -> dict:
    """
    Generate radiation pattern in elevation plane (vertical angle).

    Args:
        antenna_type: Antenna type
        height_wavelengths: Antenna height in wavelengths (affects pattern)
        num_points: Number of points in pattern (default 180 for 0-180°)

    Returns:
        Dict with angles and relative power
    """
    takeoff_angle = calculate_takeoff_angle(antenna_type)

    angles = list(range(num_points))
    power = []

    for angle_deg in angles:
        # Gaussian-like pattern centered on takeoff angle
        deviation = angle_deg - takeoff_angle
        pattern_width = 30.0  # Degrees, controls beamwidth

        # Main lobe (raised cosine bell curve)
        if abs(deviation) < 60:
            relative_power = math.exp(-(deviation ** 2) / (2 * pattern_width ** 2))
        else:
            relative_power = 0.1

        relative_power = max(0.0, min(1.0, relative_power))
        power.append(relative_power)

    return {
        "angles": angles,
        "power": power,
        "takeoff_angle": takeoff_angle,
        "description": f"Elevation pattern (takeoff {takeoff_angle}°)",
    }


def calculate_gain_description(antenna_type: str) -> dict:
    """
    Return comprehensive antenna characteristics.

    Args:
        antenna_type: Antenna type

    Returns:
        Dict with gain, F/B, takeoff angle, and description
    """
    return {
        "antenna_type": antenna_type,
        "gain_dbi": calculate_gain_dbi(antenna_type),
        "gain_dbd": calculate_gain_dbi(antenna_type) - 2.15,  # Relative to dipole
        "f_b_ratio_db": calculate_f_b_ratio(antenna_type),
        "takeoff_angle_deg": calculate_takeoff_angle(antenna_type),
    }
