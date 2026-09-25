"""Polar plots of radiation patterns on a Tkinter canvas.

Radius is linear in dB over a 30 dB range (the ARRL convention): the outer
ring is the pattern maximum, rings at -3, -6, -10 and -20 dB.
"""

import math

DB_RANGE = 30.0
RINGS_DB = (0, -3, -6, -10, -20)


def _radius(rel_db: float, radius: float) -> float:
    return radius * max(0.0, 1.0 + rel_db / DB_RANGE)


def draw_db_polar(canvas, center, radius, samples, mode="azimuth", line_color="#FFB000",
                  grid_color="#333333", text_color="#888888", fill_color=None):
    """Draw one pattern cut.

    samples: list of (angle_deg, gain_db) with gain relative to anything --
    it is normalised to its own maximum here.
    mode "azimuth":   angle 0 = top (forward), clockwise, full circle
    mode "elevation": angle 0 = right horizon (forward), 90 = up, 180 = left
                      horizon (back); a ground line when the cut is 0..180
    """
    cx, cy = center
    half = mode == "elevation" and min(a for a, _ in samples) >= 0 and max(a for a, _ in samples) <= 180

    def to_xy(angle_deg, r):
        if mode == "azimuth":
            a = math.radians(90 - angle_deg)
        else:
            a = math.radians(angle_deg)
        return cx + r * math.cos(a), cy - r * math.sin(a)

    # grid rings
    for db in RINGS_DB:
        r = _radius(db, radius)
        if half:
            canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=0, extent=180, style="arc",
                              outline=grid_color, width=1 if db else 1.5, dash=() if db == 0 else (2, 3))
        else:
            canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=grid_color,
                               width=1 if db else 1.5, dash=() if db == 0 else (2, 3))
        if db:
            canvas.create_text(cx + 3, cy - r - 1, text=f"{db}", fill=text_color,
                               font=("Helvetica", 7), anchor="sw")
    # spokes + angle labels
    step = 30
    angles = range(0, 181, step) if half else range(0, 360, step)
    for a in angles:
        x, y = to_xy(a, radius)
        canvas.create_line(cx, cy, x, y, fill=grid_color)
        lx, ly = to_xy(a, radius + 14)
        label = f"{a}°" if mode == "azimuth" or half else f"{a if a <= 90 else 180 - a if a <= 270 else a - 360}°"
        canvas.create_text(lx, ly, text=label, fill=text_color, font=("Helvetica", 7))
    if half:
        canvas.create_line(cx - radius - 6, cy, cx + radius + 6, cy, fill=text_color, width=2)

    # pattern
    peak = max(g for _, g in samples)
    pts = []
    for a, g in samples:
        pts.extend(to_xy(a, _radius(g - peak, radius)))
    if not half:
        pts.extend(pts[:2])
    if fill_color and len(pts) > 4:
        canvas.create_polygon(*(pts + ([cx, cy] if half else [])), fill=fill_color, outline="", stipple="gray25")
    canvas.create_line(*pts, fill=line_color, width=2)
