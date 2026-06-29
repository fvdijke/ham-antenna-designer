"""Impedance matching network calculator.

Design L-networks, T-networks, and Pi-networks for impedance matching
between source (typically 50Ω) and load (antenna impedance).

Matching networks transform impedance for maximum power transfer and
bandwidth optimization.
"""

import math


def calculate_l_network(z_source: float, z_load: float,
                       freq_mhz: float) -> dict:
    """
    Calculate L-network (single inductor + capacitor) for impedance matching.

    L-networks have two configurations:
    1. L-High: Series inductor then shunt capacitor (high Q, narrow bandwidth)
    2. L-Low: Shunt capacitor then series inductor (low Q, wide bandwidth)

    Args:
        z_source: Source impedance (typically 50Ω)
        z_load: Load impedance (antenna impedance)
        freq_mhz: Frequency in MHz

    Returns:
        Dict with two L-network options (high and low Q configurations)
    """
    if z_source <= 0 or z_load <= 0 or freq_mhz <= 0:
        return {"error": "Invalid impedance or frequency"}

    omega = 2 * math.pi * freq_mhz * 1e6
    impedance_ratio = z_load / z_source

    if impedance_ratio < 1:
        # Load impedance is lower than source - use Low network
        q_value = math.sqrt((z_source / z_load) - 1)

        # Series inductance (between source and load)
        l_series_h = q_value * z_source / omega
        l_series_uh = l_series_h * 1e6

        # Shunt capacitance (at load end)
        c_shunt_f = 1 / (q_value * z_load * omega)
        c_shunt_pf = c_shunt_f * 1e12

        return {
            "type": "L-Low",
            "topology": "Series L, Shunt C",
            "quality_factor": round(q_value, 2),
            "l_series_uh": round(l_series_uh, 2),
            "c_shunt_pf": round(c_shunt_pf, 2),
            "description": f"Inductor {l_series_uh:.2f}µH in series, Capacitor {c_shunt_pf:.0f}pF to ground"
        }
    else:
        # Load impedance is higher than source - use High network
        q_value = math.sqrt((z_load / z_source) - 1)

        # Shunt inductance (at source end)
        l_shunt_h = z_source / (q_value * omega)
        l_shunt_uh = l_shunt_h * 1e6

        # Series capacitance (between source and load)
        c_series_f = 1 / (q_value * z_load * omega)
        c_series_pf = c_series_f * 1e12

        return {
            "type": "L-High",
            "topology": "Shunt L, Series C",
            "quality_factor": round(q_value, 2),
            "l_shunt_uh": round(l_shunt_uh, 2),
            "c_series_pf": round(c_series_pf, 2),
            "description": f"Inductor {l_shunt_uh:.2f}µH to ground, Capacitor {c_series_pf:.0f}pF in series"
        }


def calculate_t_network(z_source: float, z_load: float,
                       freq_mhz: float, q_target: float = 5) -> dict:
    """
    Calculate T-network (2 inductors + 1 capacitor) for impedance matching.

    T-networks provide better impedance transformation and wider bandwidth
    than L-networks due to lower Q factor.

    Args:
        z_source: Source impedance (typically 50Ω)
        z_load: Load impedance (antenna impedance)
        freq_mhz: Frequency in MHz
        q_target: Target quality factor (default 5, lower Q = wider bandwidth)

    Returns:
        Dict with T-network component values
    """
    if z_source <= 0 or z_load <= 0 or freq_mhz <= 0:
        return {"error": "Invalid impedance or frequency"}

    omega = 2 * math.pi * freq_mhz * 1e6

    # T-network: Shunt L1, Series C, Shunt L2
    # Q1 = Q2 = Qtotal / 2 (split Q between inductors)
    q1 = q_target / 2
    q2 = q_target / 2

    # Shunt inductance at source (Z1 transformation stage)
    l1_h = z_source / (q1 * omega)
    l1_uh = l1_h * 1e6

    # Series capacitance (resonance element)
    # Impedance at midpoint
    z_mid = math.sqrt(z_source * z_load)
    c_series_f = q_target / (z_mid * omega)
    c_series_pf = c_series_f * 1e12

    # Shunt inductance at load (Z2 transformation stage)
    l2_h = z_load / (q2 * omega)
    l2_uh = l2_h * 1e6

    return {
        "type": "T-Network",
        "topology": "Shunt L, Series C, Shunt L",
        "quality_factor": round(q_target, 2),
        "l1_shunt_uh": round(l1_uh, 2),
        "c_series_pf": round(c_series_pf, 2),
        "l2_shunt_uh": round(l2_uh, 2),
        "z_mid_ohm": round(z_mid, 1),
        "description": f"L1 {l1_uh:.2f}µH, C {c_series_pf:.0f}pF, L2 {l2_uh:.2f}µH (Q={q_target})"
    }


def calculate_pi_network(z_source: float, z_load: float,
                        freq_mhz: float, q_target: float = 5) -> dict:
    """
    Calculate Pi-network (2 capacitors + 1 inductor) for impedance matching.

    Pi-networks are popular in amateur radio tuners, provide good filtering,
    and allow continuous impedance adjustment.

    Args:
        z_source: Source impedance (typically 50Ω)
        z_load: Load impedance (antenna impedance)
        freq_mhz: Frequency in MHz
        q_target: Target quality factor (default 5)

    Returns:
        Dict with Pi-network component values
    """
    if z_source <= 0 or z_load <= 0 or freq_mhz <= 0:
        return {"error": "Invalid impedance or frequency"}

    omega = 2 * math.pi * freq_mhz * 1e6

    # Pi-network: Shunt C1, Series L, Shunt C2
    # Similar structure to T-network but with capacitors

    # Shunt capacitance at source
    q1 = q_target / 2
    c1_f = q1 / (z_source * omega)
    c1_pf = c1_f * 1e12

    # Series inductance (resonance element)
    z_mid = math.sqrt(z_source * z_load)
    l_series_h = z_mid / (q_target * omega)
    l_series_uh = l_series_h * 1e6

    # Shunt capacitance at load
    q2 = q_target / 2
    c2_f = q2 / (z_load * omega)
    c2_pf = c2_f * 1e12

    return {
        "type": "Pi-Network",
        "topology": "Shunt C, Series L, Shunt C",
        "quality_factor": round(q_target, 2),
        "c1_shunt_pf": round(c1_pf, 2),
        "l_series_uh": round(l_series_uh, 2),
        "c2_shunt_pf": round(c2_pf, 2),
        "z_mid_ohm": round(z_mid, 1),
        "description": f"C1 {c1_pf:.0f}pF, L {l_series_uh:.2f}µH, C2 {c2_pf:.0f}pF (Q={q_target})"
    }


def suggest_matching_network(z_source: float, z_load: float,
                            freq_mhz: float) -> list:
    """
    Suggest best matching networks for given impedances.

    Returns multiple network options (L-network, T-network, Pi-network)
    for user to choose based on bandwidth requirements.

    Args:
        z_source: Source impedance
        z_load: Load impedance
        freq_mhz: Frequency in MHz

    Returns:
        List of matching network suggestions
    """
    networks = []

    # L-network (simplest, narrowest bandwidth)
    l_net = calculate_l_network(z_source, z_load, freq_mhz)
    if "error" not in l_net:
        networks.append(l_net)

    # T-network (moderate complexity, medium bandwidth)
    t_net = calculate_t_network(z_source, z_load, freq_mhz, q_target=5)
    if "error" not in t_net:
        networks.append(t_net)

    # Pi-network (moderate complexity, good filtering, variable adjustment)
    pi_net = calculate_pi_network(z_source, z_load, freq_mhz, q_target=5)
    if "error" not in pi_net:
        networks.append(pi_net)

    return networks


def calculate_swr_from_impedance(z_antenna: float, z_source: float = 50) -> float:
    """Calculate SWR from impedance."""
    gamma = abs((z_antenna - z_source) / (z_antenna + z_source))
    if gamma >= 1:
        return float('inf')
    swr = (1 + gamma) / (1 - gamma)
    return round(swr, 2)


def standard_component_values(component_value: float, component_type: str = "L") -> str:
    """
    Find nearest standard component value (E12 series).

    Args:
        component_value: Calculated component value
        component_type: "L" for inductors (µH), "C" for capacitors (pF)

    Returns:
        Standard value as string
    """
    # E12 standard values
    if component_type == "L":
        # Inductor values in µH
        e12_values = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
        multipliers = [1, 10, 100, 1000]  # 1µH, 10µH, 100µH, 1000µH (1mH)
    else:
        # Capacitor values in pF
        e12_values = [10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82]
        multipliers = [1, 10, 100, 1000, 10000]  # pF to µF range

    closest = None
    min_ratio = float('inf')

    for mult in multipliers:
        for e12 in e12_values:
            value = e12 * mult
            ratio = abs(value - component_value) / component_value

            if ratio < min_ratio:
                min_ratio = ratio
                closest = value

    if component_type == "L":
        if closest >= 1000:
            return f"{closest/1000:.1f} mH"
        elif closest >= 1:
            return f"{closest:.1f} µH"
        else:
            return f"{closest*1000:.0f} nH"
    else:
        if closest >= 1000:
            return f"{closest/1000:.2f} µF"
        elif closest >= 1:
            return f"{closest:.0f} pF"
        else:
            return f"{closest*1000:.0f} nF"
