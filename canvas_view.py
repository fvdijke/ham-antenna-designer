"""In-app schematic viewer: renders a Scene (see scene.py) onto a tk.Canvas
in the dark/amber HAMIOS-style theme, with a soft glow on the antenna lines
(inspired by the common-mode-current style illustration: bright amber core,
dimmer amber halo, on a dark background).

Not true-to-scale -- same disclaimer as the SVG export -- but every element
shown has its computed dimension labeled, same as the SVG.
"""

import tkinter as tk

from scene import Scene, build_scene

BG = "#1a1a1a"
PANEL_BG = "#141414"
AMBER = "#ffb000"
AMBER_DIM = "#5a3d00"
FG = "#e8e8e8"

# Radials/counterpoise are drawn darker than the main radiating element
# (the "waveform"), so the part that actually carries the wave stands out
# from the supporting ground system at a glance.
AMBER_RADIAL = "#9a6c00"
REFERENCE_GRAY = "#555555"

MAX_CANVAS = 380.0  # fit the largest scene dimension into this many pixels


def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#%02x%02x%02x" % rgb


def _blend(c1, c2, t):
    """t=0 -> c1, t=1 -> c2"""
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    return _rgb_to_hex((
        int(r1 + (r2 - r1) * t),
        int(g1 + (g2 - g1) * t),
        int(b1 + (b2 - b1) * t),
    ))


def _glow_layers_for(core_color):
    """Glow halo colors for a given core color, from outermost (faintest)
    to innermost (the core itself, drawn at the line's own width)."""
    return [
        (_blend(PANEL_BG, core_color, 0.25), 5.0),
        (_blend(PANEL_BG, core_color, 0.55), 2.5),
        (core_color, 0.0),
    ]


# Glow halo colors, from outermost (faintest) to innermost (brightest core).
_GLOW_LAYERS = _glow_layers_for(AMBER)
_GLOW_LAYERS_RADIAL = _glow_layers_for(AMBER_RADIAL)

_LINE_COLORS_BY_KIND = {
    "element": _GLOW_LAYERS,
    "radial": _GLOW_LAYERS_RADIAL,
}


def _draw_glow_line(canvas, x1, y1, x2, y2, width, dashed=False, kind="element"):
    dash = (5, 3) if dashed else None
    if kind == "reference":
        canvas.create_line(x1, y1, x2, y2, fill=REFERENCE_GRAY, width=width, dash=dash)
        return
    layers = _LINE_COLORS_BY_KIND.get(kind, _GLOW_LAYERS)
    for color, extra in layers[:-1]:
        canvas.create_line(x1, y1, x2, y2, fill=color, width=width + extra, capstyle=tk.ROUND, dash=dash)
    core_color = layers[-1][0]
    canvas.create_line(x1, y1, x2, y2, fill=core_color, width=width, capstyle=tk.ROUND, dash=dash)


def _draw_glow_polygon(canvas, points, width):
    flat = [c for p in points for c in p]
    closed = flat + [flat[0], flat[1]]
    for i in range(0, len(closed) - 2, 2):
        _draw_glow_line(canvas, closed[i], closed[i + 1], closed[i + 2], closed[i + 3], width)


def _draw_glow_dot(canvas, x, y, r):
    for color, extra in _GLOW_LAYERS[:-1]:
        rr = r + extra
        canvas.create_oval(x - rr, y - rr, x + rr, y + rr, fill=color, outline="")
    canvas.create_oval(x - r, y - r, x + r, y + r, fill=AMBER, outline="")


def _draw_dim_line(canvas, x1, y1, x2, y2):
    canvas.create_line(x1, y1, x2, y2, fill=FG, width=1, arrow=tk.BOTH, arrowshape=(6, 7, 3))


def _draw_feed_point(canvas, x, y, r):
    """Feedpoint: the glow dot plus a crisp white ring around it, so it
    reads as 'the feed' rather than just another junction dot."""
    _draw_glow_dot(canvas, x, y, r)
    ring_r = r + 4
    canvas.create_oval(x - ring_r, y - ring_r, x + ring_r, y + ring_r, outline=FG, width=1.5)


def _draw_balun_box(canvas, feed_x, feed_y, box_x, box_y, text):
    """Balun/unun/choke: a dashed leader line from the feedpoint to a small
    component-box symbol carrying the label -- like a part inserted in the
    feedline on a real schematic, not just floating text."""
    canvas.create_line(feed_x, feed_y, box_x, box_y, fill=AMBER, width=1, dash=(3, 2))
    font = ("Helvetica", 10, "bold")
    text_id = canvas.create_text(box_x, box_y, text=text, fill="#1a1a1a", font=font, anchor="center")
    bbox = canvas.bbox(text_id)
    pad = 5
    box = canvas.create_rectangle(bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad,
                                   fill=AMBER, outline="#1a1a1a", width=1.5)
    canvas.tag_raise(text_id, box)


def render_scene(canvas: tk.Canvas, scene: Scene, scale: float = 1.0, ox: float = 0.0, oy: float = 0.0):
    """Draw every op in `scene` onto `canvas`, scaled by `scale` and offset
    by (ox, oy) -- lets the same scene fit canvases of different sizes."""

    def tx(x):
        return x * scale + ox

    def ty(y):
        return y * scale + oy

    for x1, y1, x2, y2, width, dashed, kind in scene.lines:
        _draw_glow_line(canvas, tx(x1), ty(y1), tx(x2), ty(y2), max(width * scale, 1.0), dashed, kind)

    for points, width in scene.polygons:
        scaled_points = [(tx(x), ty(y)) for x, y in points]
        _draw_glow_polygon(canvas, scaled_points, max(width * scale, 1.0))

    for x1, y1, x2, y2 in scene.dim_lines:
        _draw_dim_line(canvas, tx(x1), ty(y1), tx(x2), ty(y2))

    for x, y, text, size, bold in scene.texts:
        font = ("Helvetica", max(int(size * scale * 1.3), 9), "bold" if bold else "normal")
        canvas.create_text(tx(x), ty(y), text=text, fill=FG, font=font, anchor="nw")

    for x, y, r in scene.feed_points:
        _draw_feed_point(canvas, tx(x), ty(y), max(r * scale, 3.0))

    for feed_x, feed_y, box_x, box_y, text in scene.balun_boxes:
        _draw_balun_box(canvas, tx(feed_x), ty(feed_y), tx(box_x), ty(box_y), text)


def show_drawing(parent: tk.Widget, design, units: str, lang: str, window_title: str, not_to_scale_note: str):
    """Open a Toplevel with the schematic drawing for `design`."""
    scene = build_scene(design, units=units, lang=lang, margin=50.0)

    scale = MAX_CANVAS / max(scene.width, scene.height)
    canvas_w = scene.width * scale + 40
    canvas_h = scene.height * scale + 70

    win = tk.Toplevel(parent)
    win.title(window_title)
    win.configure(bg=BG)

    note = tk.Label(win, text=not_to_scale_note, bg=BG, fg=AMBER, font=("Helvetica", 9, "italic"))
    note.pack(anchor="w", padx=12, pady=(10, 0))

    canvas = tk.Canvas(win, width=canvas_w, height=canvas_h - 30, bg=PANEL_BG, highlightthickness=0)
    canvas.pack(padx=12, pady=12)

    render_scene(canvas, scene, scale=scale, ox=20, oy=20)

    win.geometry(f"{int(canvas_w) + 24}x{int(canvas_h) + 24}")
    win.resizable(True, True)
    return win
