"""SWR & Impedance Matching Calculator.

Calculate Standing Wave Ratio (SWR), return loss, and reflection coefficient
from antenna impedance and transmission line impedance (typically 50Ω).

Formulas:
- Reflection coefficient Γ = (Z - Z₀) / (Z + Z₀)
- SWR = (1 + |Γ|) / (1 - |Γ|)
- Return loss (dB) = -20 * log₁₀(|Γ|)
- Power reflected (%) = |Γ|² * 100
"""

import math


def calculate_reflection_coefficient(z_antenna_ohms, z0=50):
    """
    Calculate complex reflection coefficient.

    Args:
        z_antenna_ohms: Complex impedance (R + jX) or just R for real part
        z0: Characteristic impedance (default 50Ω for coax)

    Returns:
        Tuple: (magnitude, phase_degrees)
    """
    z_antenna = complex(z_antenna_ohms)
    z0_complex = complex(z0)
    if z_antenna + z0_complex == 0:
        return 1.0, 180.0

    gamma = (z_antenna - z0_complex) / (z_antenna + z0_complex)
    magnitude = abs(gamma)
    phase_rad = math.atan2(gamma.imag, gamma.real)
    phase_deg = math.degrees(phase_rad)

    return magnitude, phase_deg


def calculate_swr(z_antenna_ohms, z0=50):
    """
    Calculate Standing Wave Ratio (SWR).

    Args:
        z_antenna_ohms: Antenna impedance, real (R) or complex (R + jX) --
            the reactance counts: 50 + j50 ohms is SWR 2.6, not 1.0
        z0: Characteristic impedance (default 50Ω)

    Returns:
        SWR ratio (e.g., 1.5 means 1.5:1)
    """
    gamma_magnitude, _ = calculate_reflection_coefficient(z_antenna_ohms, z0)

    if gamma_magnitude >= 1.0:
        return float('inf')

    swr = (1 + gamma_magnitude) / (1 - gamma_magnitude)
    return round(swr, 2)


def calculate_return_loss(z_antenna_ohms, z0=50):
    """
    Calculate return loss in dB.

    Return loss = -20 * log₁₀(|Γ|)

    Positive number; higher = better match (20 dB is SWR 1.22).

    Args:
        z_antenna_ohms: Antenna impedance
        z0: Characteristic impedance (default 50Ω)

    Returns:
        Return loss in dB
    """
    gamma_magnitude, _ = calculate_reflection_coefficient(z_antenna_ohms, z0)

    if gamma_magnitude == 0:
        return float('inf')

    return_loss_db = -20 * math.log10(gamma_magnitude)
    return round(return_loss_db, 2)


def calculate_power_reflected(z_antenna_ohms, z0=50):
    """
    Calculate percentage of power reflected.

    Power reflected (%) = |Γ|² × 100

    Args:
        z_antenna_ohms: Antenna impedance
        z0: Characteristic impedance (default 50Ω)

    Returns:
        Percentage of power reflected (0-100%)
    """
    gamma_magnitude, _ = calculate_reflection_coefficient(z_antenna_ohms, z0)
    power_reflected = (gamma_magnitude ** 2) * 100
    return round(power_reflected, 2)


def calculate_power_transmitted(z_antenna_ohms, z0=50):
    """
    Calculate percentage of power transmitted to antenna.

    Power transmitted (%) = 100 - Power reflected (%)

    Args:
        z_antenna_ohms: Antenna impedance
        z0: Characteristic impedance (default 50Ω)

    Returns:
        Percentage of power transmitted (0-100%)
    """
    power_reflected = calculate_power_reflected(z_antenna_ohms, z0)
    return round(100 - power_reflected, 2)


def impedance_to_swr_table(z_antenna_ohms, z0=50):
    """
    Generate comprehensive SWR analysis table.

    Args:
        z_antenna_ohms: Antenna impedance
        z0: Characteristic impedance (default 50Ω)

    Returns:
        Dict with all calculated values
    """
    gamma_mag, gamma_phase = calculate_reflection_coefficient(z_antenna_ohms, z0)
    swr = calculate_swr(z_antenna_ohms, z0)
    return_loss = calculate_return_loss(z_antenna_ohms, z0)
    power_reflected = calculate_power_reflected(z_antenna_ohms, z0)
    power_transmitted = calculate_power_transmitted(z_antenna_ohms, z0)

    return {
        "impedance_ohms": z_antenna_ohms if isinstance(z_antenna_ohms, (int, float)) else z_antenna_ohms.real,
        "swr": swr,
        "gamma_magnitude": round(gamma_mag, 4),
        "gamma_phase_deg": round(gamma_phase, 2),
        "return_loss_db": return_loss,
        "power_reflected_percent": power_reflected,
        "power_transmitted_percent": power_transmitted,
    }


def transformer_ratio(ratio_text) -> float:
    """Impedance ratio from a balun label such as "49:1" (1.0 when the
    label is not a ratio, e.g. "-", "n/a" or "1:1")."""
    try:
        a, b = str(ratio_text).split(":")
        return float(a) / float(b)
    except (ValueError, ZeroDivisionError):
        return 1.0


def coax_side_impedance(design) -> float:
    """The antenna's feedpoint impedance as the COAX sees it, i.e. after the
    design's balun/unun (a 2450-ohm EFHW behind its 49:1 unun is 50 ohm)."""
    return float(design.feedpoint_impedance_ohms) / transformer_ratio(design.balun.get("ratio", "1:1"))


def feedpoint_impedance_from_design(design):
    """
    Extract feedpoint impedance from antenna design.

    Args:
        design: AntennaDesign object

    Returns:
        Float: feedpoint impedance in ohms
    """
    return float(design.feedpoint_impedance_ohms)
