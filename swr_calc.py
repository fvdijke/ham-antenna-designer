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
    if isinstance(z_antenna_ohms, (int, float)):
        z_antenna = complex(z_antenna_ohms, 0)
    else:
        z_antenna = z_antenna_ohms

    z0_complex = complex(z0, 0)

    gamma = (z_antenna - z0_complex) / (z_antenna + z0_complex)
    magnitude = abs(gamma)
    phase_rad = math.atan2(gamma.imag, gamma.real)
    phase_deg = math.degrees(phase_rad)

    return magnitude, phase_deg


def calculate_swr(z_antenna_ohms, z0=50):
    """
    Calculate Standing Wave Ratio (SWR).

    Args:
        z_antenna_ohms: Antenna impedance (real part only)
        z0: Characteristic impedance (default 50Ω)

    Returns:
        SWR ratio (e.g., 1.5 means 1.5:1)
    """
    if isinstance(z_antenna_ohms, complex):
        z_r = z_antenna_ohms.real
    else:
        z_r = z_antenna_ohms

    gamma_magnitude, _ = calculate_reflection_coefficient(z_r, z0)

    if gamma_magnitude >= 1.0:
        return float('inf')

    swr = (1 + gamma_magnitude) / (1 - gamma_magnitude)
    return round(swr, 2)


def calculate_return_loss(z_antenna_ohms, z0=50):
    """
    Calculate return loss in dB.

    Return loss = -20 * log₁₀(|Γ|)

    Negative value means reflection loss (typical).
    Higher magnitude = better match.

    Args:
        z_antenna_ohms: Antenna impedance
        z0: Characteristic impedance (default 50Ω)

    Returns:
        Return loss in dB (typically negative)
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


def feedpoint_impedance_from_design(design):
    """
    Extract feedpoint impedance from antenna design.

    Args:
        design: AntennaDesign object

    Returns:
        Float: feedpoint impedance in ohms
    """
    return float(design.feedpoint_impedance_ohms)
