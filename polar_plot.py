"""Polar plot visualization for antenna radiation patterns.

Render radiation patterns on a polar (azimuth/elevation) coordinate system
for Tkinter canvas display.
"""

import math
from typing import Tuple, List


def draw_polar_grid(canvas, center: Tuple[float, float], radius: float,
                    grid_color: str = "#333333", text_color: str = "#888888"):
    """
    Draw polar coordinate grid on canvas.

    Args:
        canvas: Tkinter canvas
        center: (cx, cy) chart center
        radius: radius in pixels
        grid_color: grid line color
        text_color: label text color
    """
    cx, cy = center

    # Draw outer circle (0 dB ring)
    canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                       outline=grid_color, width=1)

    # Draw inner circles (db rings at -3dB, -6dB, -10dB)
    for db_loss in [3, 6, 10]:
        ring_radius = radius * (1 - db_loss / 20)  # dB to linear conversion
        if ring_radius > 10:
            canvas.create_oval(cx - ring_radius, cy - ring_radius,
                              cx + ring_radius, cy + ring_radius,
                              outline=grid_color, width=0.5, dash=(2, 2))
            canvas.create_text(cx + ring_radius + 5, cy,
                              text=f"-{db_loss}dB", fill=text_color,
                              font=("Helvetica", 7), anchor="w")

    # Draw radial lines (azimuth angles: 0°, 45°, 90°, 135°, 180°, ...)
    for angle_deg in range(0, 360, 45):
        angle_rad = math.radians(angle_deg)
        x = cx + radius * math.cos(angle_rad)
        y = cy - radius * math.sin(angle_rad)  # Flip Y for canvas

        canvas.create_line(cx, cy, x, y, fill=grid_color, width=0.5)

        # Label angles
        label_dist = radius + 25
        label_x = cx + label_dist * math.cos(angle_rad)
        label_y = cy - label_dist * math.sin(angle_rad)

        angle_label = f"{angle_deg}°"
        canvas.create_text(label_x, label_y, text=angle_label, fill=text_color,
                          font=("Helvetica", 8), anchor="center")


def plot_azimuth_pattern(canvas, pattern_data: dict, center: Tuple[float, float],
                         radius: float, line_color: str = "#FFB000",
                         line_width: int = 2, fill_color: str = None):
    """
    Plot azimuth (horizontal) radiation pattern on polar grid.

    Args:
        canvas: Tkinter canvas
        pattern_data: Dict from generate_azimuth_pattern() with 'angles' and 'power'
        center: (cx, cy) chart center
        radius: radius in pixels
        line_color: pattern line color
        line_width: pattern line width
        fill_color: optional fill color for pattern
    """
    cx, cy = center
    angles = pattern_data["angles"]
    power = pattern_data["power"]

    # Convert polar to cartesian coordinates
    points = []
    for angle_deg, relative_power in zip(angles, power):
        angle_rad = math.radians(angle_deg)
        # Radius is proportional to relative power
        r = relative_power * radius
        x = cx + r * math.cos(angle_rad)
        y = cy - r * math.sin(angle_rad)  # Flip Y for canvas
        points.append((x, y))

    # Draw filled polygon if requested
    if fill_color and len(points) > 2:
        flat_points = [coord for point in points for coord in point]
        try:
            canvas.create_polygon(*flat_points, fill=fill_color, outline=None,
                                 stipple="gray25")  # Semi-transparent via stipple
        except Exception:
            pass  # If polygon fails, continue with line

    # Draw pattern outline
    if len(points) > 1:
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            canvas.create_line(x1, y1, x2, y2, fill=line_color, width=line_width)

        # Close the pattern (connect last to first)
        x1, y1 = points[-1]
        x2, y2 = points[0]
        canvas.create_line(x1, y1, x2, y2, fill=line_color, width=line_width)

    # Draw center point
    canvas.create_oval(cx - 2, cy - 2, cx + 2, cy + 2,
                       fill=line_color, outline=line_color)


def plot_elevation_pattern(canvas, pattern_data: dict, center: Tuple[float, float],
                          radius: float, line_color: str = "#FFB000",
                          line_width: int = 2):
    """
    Plot elevation (vertical) radiation pattern.

    Args:
        canvas: Tkinter canvas
        pattern_data: Dict from generate_elevation_pattern()
        center: (cx, cy) chart center
        radius: radius in pixels
        line_color: pattern line color
        line_width: pattern line width
    """
    cx, cy = center
    angles = pattern_data["angles"]
    power = pattern_data["power"]

    # Draw elevation pattern as 2D plot (left-right = angle, up-down = power)
    points = []
    for angle_deg, relative_power in zip(angles, power):
        # Map 0-180° to horizontal position, power to vertical
        x = cx - radius + (angle_deg / 180) * (2 * radius)
        y = cy - relative_power * radius

        points.append((x, y))

    # Draw pattern curve
    if len(points) > 1:
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            canvas.create_line(x1, y1, x2, y2, fill=line_color, width=line_width)

    # Draw axes
    # Horizontal axis (0° to 180°)
    canvas.create_line(cx - radius, cy, cx + radius, cy, fill="#666666", width=1)

    # Vertical axis (power/gain)
    canvas.create_line(cx, cy - radius, cx, cy, fill="#666666", width=1)

    # Labels
    canvas.create_text(cx - radius - 10, cy, text="0°", fill="#888888",
                      font=("Helvetica", 8), anchor="e")
    canvas.create_text(cx + radius + 10, cy, text="180°", fill="#888888",
                      font=("Helvetica", 8), anchor="w")
    canvas.create_text(cx - 15, cy - radius, text="Max", fill="#888888",
                      font=("Helvetica", 8), anchor="e")


def polar_to_cartesian(angle_deg: float, radius: float,
                       center: Tuple[float, float]) -> Tuple[float, float]:
    """
    Convert polar coordinates to cartesian for canvas plotting.

    Args:
        angle_deg: Azimuth angle in degrees (0° = right/east)
        radius: Radial distance
        center: Canvas center (cx, cy)

    Returns:
        (x, y) canvas coordinates
    """
    angle_rad = math.radians(angle_deg)
    cx, cy = center

    x = cx + radius * math.cos(angle_rad)
    y = cy - radius * math.sin(angle_rad)  # Flip Y for canvas coordinates

    return x, y
