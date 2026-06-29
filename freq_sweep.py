"""Frequency sweep and impedance vs frequency calculations.

Sweep antenna impedance over a frequency range to show SWR curve,
resonance frequency, and bandwidth characteristics.
"""

from registry import design as design_antenna
from swr_calc import calculate_swr, calculate_return_loss


def sweep_antenna_response(antenna_type: str, band: str, freq_start_mhz: float,
                           freq_end_mhz: float, step_mhz: float = 0.01,
                           lang: str = "en", wire_vf: float = 0.95) -> dict:
    """
    Sweep antenna impedance over frequency range.

    Args:
        antenna_type: Antenna type (e.g., "dipole_half_wave")
        band: Band name (used for initial design)
        freq_start_mhz: Start frequency in MHz
        freq_end_mhz: End frequency in MHz
        step_mhz: Frequency step in MHz
        lang: Language ("en" or "nl")
        wire_vf: Wire velocity factor

    Returns:
        Dict with sweep data:
        {
            "frequencies": [f1, f2, ...],
            "swr_values": [swr1, swr2, ...],
            "impedances": [z1, z2, ...],
            "return_loss": [rl1, rl2, ...],
            "resonance_freq": resonance_mhz,
            "min_swr": minimum_swr,
            "bandwidth_3db": (f_low, f_high),
        }
    """
    frequencies = []
    swr_values = []
    impedances = []
    return_loss_values = []

    freq = freq_start_mhz
    while freq <= freq_end_mhz:
        try:
            # Design antenna at this frequency
            design = design_antenna(antenna_type, band, lang=lang,
                                   freq_mhz=freq, wire_vf=wire_vf)

            # Get feedpoint impedance
            z_antenna = float(design.feedpoint_impedance_ohms)

            # Calculate SWR and return loss
            swr = calculate_swr(z_antenna, z0=50)
            rl = calculate_return_loss(z_antenna, z0=50)

            frequencies.append(freq)
            impedances.append(z_antenna)
            swr_values.append(swr if swr != float('inf') else 999)
            return_loss_values.append(rl)

        except Exception:
            # Skip frequencies that fail
            pass

        freq = round(freq + step_mhz, 3)

    if not frequencies:
        return {}

    # Find resonance (minimum SWR)
    min_swr_idx = min(range(len(swr_values)), key=lambda i: swr_values[i])
    resonance_freq = frequencies[min_swr_idx]
    min_swr = swr_values[min_swr_idx]

    # Find -3dB bandwidth (SWR ≤ 1.5:1 typically, or return loss ≥ 14dB)
    bandwidth_freq = [f for f, s in zip(frequencies, swr_values) if s <= 1.5]
    if bandwidth_freq:
        bandwidth_3db = (min(bandwidth_freq), max(bandwidth_freq))
    else:
        bandwidth_3db = (resonance_freq, resonance_freq)

    return {
        "frequencies": frequencies,
        "swr_values": swr_values,
        "impedances": impedances,
        "return_loss": return_loss_values,
        "resonance_freq": round(resonance_freq, 3),
        "min_swr": round(min_swr, 2),
        "bandwidth_3db": (round(bandwidth_3db[0], 3), round(bandwidth_3db[1], 3)),
        "design_freq": frequencies[0],  # Original design frequency
    }


def find_resonance_frequency(antenna_type: str, band: str,
                            freq_start_mhz: float, freq_end_mhz: float,
                            lang: str = "en", wire_vf: float = 0.95) -> float:
    """
    Find frequency with minimum SWR (resonance).

    Args:
        antenna_type: Antenna type
        band: Band name
        freq_start_mhz: Search range start
        freq_end_mhz: Search range end
        lang: Language
        wire_vf: Wire velocity factor

    Returns:
        Resonance frequency in MHz
    """
    sweep = sweep_antenna_response(antenna_type, band, freq_start_mhz,
                                   freq_end_mhz, step_mhz=0.05,
                                   lang=lang, wire_vf=wire_vf)
    return sweep.get("resonance_freq", 0)


def calculate_bandwidth(sweep_data: dict, swr_limit: float = 1.5) -> dict:
    """
    Calculate bandwidth for given SWR limit.

    Args:
        sweep_data: Output from sweep_antenna_response()
        swr_limit: SWR threshold (default 1.5:1)

    Returns:
        {
            "center_freq": center frequency in MHz,
            "bandwidth": bandwidth in MHz,
            "relative_bandwidth": bandwidth % of center,
            "low_freq": low frequency in MHz,
            "high_freq": high frequency in MHz,
        }
    """
    if "frequencies" not in sweep_data or not sweep_data["frequencies"]:
        return {}

    # Find frequencies within SWR limit
    limited_freq = [f for f, s in zip(sweep_data["frequencies"],
                                      sweep_data["swr_values"])
                   if s <= swr_limit]

    if not limited_freq:
        return {}

    low_freq = min(limited_freq)
    high_freq = max(limited_freq)
    center_freq = (low_freq + high_freq) / 2
    bandwidth = high_freq - low_freq
    rel_bandwidth = (bandwidth / center_freq) * 100

    return {
        "center_freq": round(center_freq, 3),
        "bandwidth": round(bandwidth, 3),
        "relative_bandwidth": round(rel_bandwidth, 1),
        "low_freq": round(low_freq, 3),
        "high_freq": round(high_freq, 3),
        "swr_limit": swr_limit,
    }
