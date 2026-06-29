"""Transmission line loss calculations for coaxial cables.

Calculate cable losses, attenuation, power budget, and efficiency for
different cable types at various frequencies and distances.

All loss values in dB per 100 feet at the specified frequency.
Formula: Loss (dB) = (loss_per_100ft @ frequency) * (distance_ft / 100)
"""

# Cable loss data: {cable_name: {freq_mhz: loss_db_per_100ft, ...}}
CABLE_LOSS_DB_PER_100FT = {
    "RG-58": {
        1.8: 0.43, 3.5: 0.58, 7.0: 0.85, 10: 1.0, 14: 1.25,
        21: 1.5, 28: 1.8, 50: 2.6, 144: 5.0, 432: 13.0
    },
    "RG-174": {
        1.8: 0.62, 3.5: 0.85, 7.0: 1.2, 10: 1.45, 14: 1.8,
        21: 2.2, 28: 2.6, 50: 3.8, 144: 7.2, 432: 18.0
    },
    "RG-213": {
        1.8: 0.26, 3.5: 0.35, 7.0: 0.50, 10: 0.60, 14: 0.75,
        21: 0.90, 28: 1.1, 50: 1.6, 144: 3.1, 432: 8.0
    },
    "RG-8": {
        1.8: 0.20, 3.5: 0.27, 7.0: 0.38, 10: 0.46, 14: 0.58,
        21: 0.70, 28: 0.85, 50: 1.2, 144: 2.4, 432: 6.2
    },
    "LMR-195": {
        1.8: 0.34, 3.5: 0.46, 7.0: 0.66, 10: 0.80, 14: 1.0,
        21: 1.2, 28: 1.5, 50: 2.2, 144: 4.2, 432: 11.0
    },
    "LMR-400": {
        1.8: 0.11, 3.5: 0.15, 7.0: 0.22, 10: 0.26, 14: 0.33,
        21: 0.40, 28: 0.49, 50: 0.70, 144: 1.4, 432: 3.6
    },
    "LMR-600": {
        1.8: 0.07, 3.5: 0.10, 7.0: 0.14, 10: 0.17, 14: 0.22,
        21: 0.26, 28: 0.32, 50: 0.46, 144: 0.92, 432: 2.4
    },
    "Heliax 1/2": {
        1.8: 0.04, 3.5: 0.06, 7.0: 0.08, 10: 0.10, 14: 0.12,
        21: 0.15, 28: 0.18, 50: 0.26, 144: 0.50, 432: 1.3
    },
    "Hardline 1/2": {
        1.8: 0.03, 3.5: 0.05, 7.0: 0.07, 10: 0.08, 14: 0.10,
        21: 0.12, 28: 0.15, 50: 0.22, 144: 0.43, 432: 1.1
    },
}


def get_cable_loss_per_100ft(cable_type: str, freq_mhz: float) -> float:
    """
    Get cable loss (dB per 100 feet) at specified frequency.

    Interpolates between known frequency points.

    Args:
        cable_type: Cable type name (e.g., "RG-213")
        freq_mhz: Frequency in MHz

    Returns:
        Loss in dB per 100 feet
    """
    if cable_type not in CABLE_LOSS_DB_PER_100FT:
        return 0.5  # Default fallback

    loss_table = CABLE_LOSS_DB_PER_100FT[cable_type]
    freqs = sorted(loss_table.keys())

    # Find nearest two frequencies for interpolation
    if freq_mhz <= freqs[0]:
        return loss_table[freqs[0]]
    if freq_mhz >= freqs[-1]:
        return loss_table[freqs[-1]]

    # Linear interpolation between closest frequencies
    for i in range(len(freqs) - 1):
        if freqs[i] <= freq_mhz <= freqs[i + 1]:
            f1, f2 = freqs[i], freqs[i + 1]
            l1, l2 = loss_table[f1], loss_table[f2]

            # Linear interpolation
            loss = l1 + (l2 - l1) * (freq_mhz - f1) / (f2 - f1)
            return loss

    return loss_table[freqs[-1]]


def calculate_cable_loss(cable_type: str, freq_mhz: float,
                        distance_ft: float) -> float:
    """
    Calculate total cable loss for given distance.

    Args:
        cable_type: Cable type
        freq_mhz: Frequency in MHz
        distance_ft: Cable length in feet

    Returns:
        Total loss in dB
    """
    loss_per_100ft = get_cable_loss_per_100ft(cable_type, freq_mhz)
    total_loss_db = loss_per_100ft * (distance_ft / 100.0)
    return round(total_loss_db, 2)


def calculate_cable_loss_meters(cable_type: str, freq_mhz: float,
                               distance_m: float) -> float:
    """
    Calculate total cable loss for distance in meters.

    Args:
        cable_type: Cable type
        freq_mhz: Frequency in MHz
        distance_m: Cable length in meters

    Returns:
        Total loss in dB
    """
    distance_ft = distance_m * 3.28084  # Convert to feet
    return calculate_cable_loss(cable_type, freq_mhz, distance_ft)


def calculate_power_at_antenna(transmit_power_watts: float,
                               cable_loss_db: float,
                               swr: float = 1.0) -> float:
    """
    Calculate power reaching antenna after cable loss and SWR reflection.

    Args:
        transmit_power_watts: Transmitter output power in watts
        cable_loss_db: Cable attenuation in dB
        swr: Standing Wave Ratio (default 1.0 for perfect match)

    Returns:
        Power reaching antenna in watts
    """
    # Cable loss in linear form
    cable_loss_linear = 10 ** (-cable_loss_db / 10)

    # SWR loss (power reflected by mismatch)
    if swr > 1.0:
        # Reflection coefficient from SWR
        gamma = (swr - 1) / (swr + 1)
        power_transmitted = 1 - (gamma ** 2)
    else:
        power_transmitted = 1.0

    # Total power reaching antenna
    power_at_antenna = transmit_power_watts * cable_loss_linear * power_transmitted

    return round(power_at_antenna, 2)


def calculate_efficiency(cable_type: str, freq_mhz: float,
                        distance_ft: float, swr: float = 1.0) -> float:
    """
    Calculate efficiency percentage after cable loss and SWR.

    Args:
        cable_type: Cable type
        freq_mhz: Frequency in MHz
        distance_ft: Cable length in feet
        swr: Standing Wave Ratio

    Returns:
        Efficiency as percentage (0-100)
    """
    cable_loss_db = calculate_cable_loss(cable_type, freq_mhz, distance_ft)

    # Cable loss efficiency
    cable_efficiency = 10 ** (-cable_loss_db / 10)

    # SWR loss efficiency
    if swr > 1.0:
        gamma = (swr - 1) / (swr + 1)
        swr_efficiency = 1 - (gamma ** 2)
    else:
        swr_efficiency = 1.0

    total_efficiency = cable_efficiency * swr_efficiency
    return round(total_efficiency * 100, 1)


def get_all_cable_types() -> list:
    """Get list of all available cable types."""
    return sorted(list(CABLE_LOSS_DB_PER_100FT.keys()))


def compare_cables(freq_mhz: float, distance_ft: float) -> dict:
    """
    Compare loss for all cable types at given frequency and distance.

    Args:
        freq_mhz: Frequency in MHz
        distance_ft: Cable length in feet

    Returns:
        Dict with cable names and their losses
    """
    comparison = {}
    for cable_type in get_all_cable_types():
        loss = calculate_cable_loss(cable_type, freq_mhz, distance_ft)
        comparison[cable_type] = loss

    return {k: v for k, v in sorted(comparison.items(), key=lambda x: x[1])}


def cable_loss_analysis(cable_type: str, freq_mhz: float,
                       max_distance_ft: float) -> dict:
    """
    Generate loss analysis across distance range.

    Args:
        cable_type: Cable type
        freq_mhz: Frequency in MHz
        max_distance_ft: Maximum distance to analyze

    Returns:
        Dict with distances and losses
    """
    distances = [10, 25, 50, 100, 150, 200, 300, 500]
    distances = [d for d in distances if d <= max_distance_ft]

    losses = {}
    for dist in distances:
        loss = calculate_cable_loss(cable_type, freq_mhz, dist)
        losses[dist] = loss

    return losses


def power_budget_summary(transmit_watts: float, cable_type: str,
                        freq_mhz: float, distance_m: float,
                        antenna_gain_dbi: float, swr: float = 1.0) -> dict:
    """
    Calculate complete power budget for a station.

    Args:
        transmit_watts: Transmitter output power in watts
        cable_type: Feed cable type
        freq_mhz: Frequency in MHz
        distance_m: Cable length in meters
        antenna_gain_dbi: Antenna gain in dBi
        swr: Antenna SWR

    Returns:
        Dict with power budget analysis
    """
    distance_ft = distance_m * 3.28084
    cable_loss_db = calculate_cable_loss(cable_type, freq_mhz, distance_ft)
    efficiency = calculate_efficiency(cable_type, freq_mhz, distance_ft, swr)
    power_at_antenna = calculate_power_at_antenna(transmit_watts, cable_loss_db, swr)

    # EIRP = Power at antenna + antenna gain
    eirp_watts = power_at_antenna * (10 ** (antenna_gain_dbi / 10))

    return {
        "transmit_power_watts": transmit_watts,
        "cable_loss_db": cable_loss_db,
        "swr_loss_db": round(-10 * __import__('math').log10(1 - ((swr-1)/(swr+1))**2), 2) if swr > 1 else 0,
        "efficiency_percent": efficiency,
        "power_at_antenna_watts": power_at_antenna,
        "antenna_gain_dbi": antenna_gain_dbi,
        "eirp_watts": round(eirp_watts, 2),
    }
