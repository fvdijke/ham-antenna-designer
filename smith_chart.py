"""Smith Chart visualization and manipulation.

The Smith Chart is a polar plot of the complex reflection coefficient Γ,
where impedance lines and admittance lines are orthogonal curves. This module
provides calculation and rendering functions for Tkinter canvas display.

Key concepts:
- Center (Γ = 0) = perfect 50Ω match (SWR 1:1)
- Right edge (Γ = 1, real axis) = open circuit
- Left edge (Γ = -1, real axis) = short circuit
- Resistance circles: constant real impedance
- Reactance arcs: constant imaginary impedance
"""

import math
from typing import Tuple


def complex_to_smith_coords(z_complex: complex, chart_center: Tuple[float, float],
                            chart_radius: float, z0: float = 50.0) -> Tuple[float, float]:
    """
    Convert complex impedance to Smith Chart canvas coordinates.

    Smith Chart maps normalized impedance to reflection coefficient:
    Γ = (Z - Z₀) / (Z + Z₀)

    Args:
        z_complex: Complex impedance (R + jX)
        chart_center: (cx, cy) canvas center
        chart_radius: radius in pixels
        z0: characteristic impedance (default 50Ω)

    Returns:
        (x, y) canvas coordinates
    """
    # Normalize impedance
    z_normalized = z_complex / z0

    # Calculate reflection coefficient
    numerator = z_normalized - 1
    denominator = z_normalized + 1

    if abs(denominator) < 1e-10:
        # Avoid division by zero
        gamma = complex(1, 0)
    else:
        gamma = numerator / denominator

    # Map reflection coefficient to canvas coordinates
    # Smith Chart: real axis is horizontal, imaginary axis is vertical
    cx, cy = chart_center
    x = cx + gamma.real * chart_radius
    y = cy - gamma.imag * chart_radius  # Flip Y for canvas (top = negative)

    return x, y


def smith_coords_to_impedance(gamma_magnitude: float, gamma_phase_deg: float,
                              z0: float = 50.0) -> complex:
    """
    Convert reflection coefficient to impedance.

    Z = Z₀ * (1 + Γ) / (1 - Γ)

    Args:
        gamma_magnitude: Magnitude of reflection coefficient
        gamma_phase_deg: Phase in degrees
        z0: Characteristic impedance (default 50Ω)

    Returns:
        Complex impedance
    """
    gamma_phase_rad = math.radians(gamma_phase_deg)
    gamma = complex(
        gamma_magnitude * math.cos(gamma_phase_rad),
        gamma_magnitude * math.sin(gamma_phase_rad)
    )

    numerator = 1 + gamma
    denominator = 1 - gamma

    if abs(denominator) < 1e-10:
        return complex(float('inf'), 0)

    z = z0 * numerator / denominator
    return z


def draw_smith_chart_grid(canvas, center: Tuple[float, float], radius: float,
                          grid_color: str = "#333333", line_width: int = 1):
    """
    Draw Smith Chart grid (resistance and reactance curves).

    Args:
        canvas: Tkinter canvas
        center: (cx, cy) chart center
        radius: chart radius in pixels
        grid_color: color for grid lines
        line_width: thickness of grid lines
    """
    cx, cy = center

    # Draw outer circle (Γ = 1, unity circle)
    canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                       outline=grid_color, width=line_width)

    # Draw real axis (horizontal)
    canvas.create_line(cx - radius, cy, cx + radius, cy,
                       fill=grid_color, width=line_width)

    # Draw imaginary axis (vertical)
    canvas.create_line(cx, cy - radius, cx, cy + radius,
                       fill=grid_color, width=line_width)

    # Resistance circles (R = 0, 0.5, 1, 2, ∞ normalized)
    resistance_values = [0.5, 1.0, 2.0, 5.0]
    for r_norm in resistance_values:
        # Circle center and radius in Γ space
        center_gamma = r_norm / (1 + r_norm)
        radius_gamma = 1 / (1 + r_norm)

        # Convert to canvas coordinates
        x1 = cx + (center_gamma - radius_gamma) * radius
        y1 = cy
        x2 = cx + (center_gamma + radius_gamma) * radius
        y2 = cy

        canvas.create_oval(x1, y1 - radius_gamma * radius,
                          x2, y1 + radius_gamma * radius,
                          outline=grid_color, width=line_width // 2)

    # Reactance arcs (X = 0.5, 1, 2, ∞ normalized) -- positive (inductive)
    reactance_values = [0.2, 0.5, 1.0, 2.0, 5.0]
    for x_norm in reactance_values:
        # Inductive (positive X) arc
        center_x = cx + 1.0 * radius
        center_y = cy - (1 / x_norm) * radius

        arc_radius = (1 / x_norm) * radius
        canvas.create_oval(center_x - arc_radius, center_y - arc_radius,
                          center_x + arc_radius, center_y + arc_radius,
                          outline=grid_color, width=line_width // 2)

        # Capacitive (negative X) arc
        center_y_cap = cy + (1 / x_norm) * radius
        canvas.create_oval(center_x - arc_radius, center_y_cap - arc_radius,
                          center_x + arc_radius, center_y_cap + arc_radius,
                          outline=grid_color, width=line_width // 2)


def plot_impedance_point(canvas, z_complex: complex, center: Tuple[float, float],
                         radius: float, point_color: str = "#FFB000",
                         point_size: int = 6, z0: float = 50.0):
    """
    Plot a single impedance point on Smith Chart.

    Args:
        canvas: Tkinter canvas
        z_complex: Complex impedance
        center: Chart center (cx, cy)
        radius: Chart radius in pixels
        point_color: Marker color
        point_size: Marker size in pixels
        z0: Characteristic impedance
    """
    x, y = complex_to_smith_coords(z_complex, center, radius, z0)

    # Draw point marker
    r = point_size / 2
    canvas.create_oval(x - r, y - r, x + r, y + r,
                       fill=point_color, outline=point_color)

    # Draw crosshair
    canvas.create_line(x - 8, y, x + 8, y, fill=point_color, width=1)
    canvas.create_line(x, y - 8, x, y + 8, fill=point_color, width=1)


def plot_swr_circle(canvas, swr: float, center: Tuple[float, float],
                    radius: float, circle_color: str = "#FF8800",
                    line_width: int = 2, z0: float = 50.0):
    """
    Plot SWR constant circle on Smith Chart.

    All impedances with the same SWR lie on a circle centered at the
    real axis with radius r = (SWR - 1) / (SWR + 1) normalized.

    Args:
        canvas: Tkinter canvas
        swr: Standing Wave Ratio
        center: Chart center (cx, cy)
        radius: Chart radius in pixels
        circle_color: Circle color
        line_width: Circle line width
        z0: Characteristic impedance
    """
    if swr <= 1.0:
        return  # Perfect match, no circle needed

    cx, cy = center

    # Gamma magnitude for this SWR
    gamma_mag = (swr - 1) / (swr + 1)

    # Circle in Γ space: centered on real axis, radius = gamma_mag
    circle_center_x = cx + 0 * radius  # Center on real axis (Γ.real = 0)
    circle_center_y = cy

    circle_radius_pixels = gamma_mag * radius

    canvas.create_oval(
        circle_center_x - circle_radius_pixels,
        circle_center_y - circle_radius_pixels,
        circle_center_x + circle_radius_pixels,
        circle_center_y + circle_radius_pixels,
        outline=circle_color, width=line_width, dash=(4, 4)
    )


def impedance_from_swr_and_angle(swr: float, angle_deg: float,
                                 z0: float = 50.0) -> complex:
    """
    Get impedance at specific angle on SWR circle.

    Args:
        swr: Standing Wave Ratio
        angle_deg: Angle on Smith Chart (0° = real axis, 90° = positive imag)
        z0: Characteristic impedance

    Returns:
        Complex impedance at that point on the SWR circle
    """
    gamma_mag = (swr - 1) / (swr + 1)
    angle_rad = math.radians(angle_deg)

    gamma = complex(
        gamma_mag * math.cos(angle_rad),
        gamma_mag * math.sin(angle_rad)
    )

    z = z0 * (1 + gamma) / (1 - gamma)
    return z
