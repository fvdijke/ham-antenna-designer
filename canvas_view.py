"""In-app schematic viewer: renders a Scene (see scene.py) onto a tk.Canvas
in the dark/amber HAMIOS-style theme, with a soft glow on the antenna lines
(inspired by the common-mode-current style illustration: bright amber core,
dimmer amber halo, on a dark background).

Not true-to-scale -- same disclaimer as the SVG export -- but every element
shown has its computed dimension labeled, same as the SVG.
"""

import tkinter as tk
from tkinter import ttk

from scene import Scene, build_scene
from scene3d import _SCENE3D_BUILDERS, build_scene_3d
from widgets import RoundedButton, _rounded_rect_points, glow_layers_for

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

# Cyan accent for dimension lines -- a third color so "this is a measured
# distance" reads as visually distinct from both the amber wire and the
# plain white caption text.
DIM_COLOR = "#7fd8ff"

# Blueprint-style grid background, drawn behind everything else.
GRID_MINOR = "#1c1c1c"
GRID_MAJOR = "#242424"
GRID_SPACING = 32
GRID_MAJOR_EVERY = 4

MAX_CANVAS = 760.0  # fit the largest scene dimension into this many pixels


# Glow halo colors, from outermost (faintest) to innermost (brightest core).
_GLOW_LAYERS = glow_layers_for(AMBER, PANEL_BG)
_GLOW_LAYERS_RADIAL = glow_layers_for(AMBER_RADIAL, PANEL_BG)

_LINE_COLORS_BY_KIND = {
    "element": _GLOW_LAYERS,
    "radial": _GLOW_LAYERS_RADIAL,
}


def _draw_grid_background(canvas, w, h):
    """Faint blueprint-style grid, drawn first so everything else sits on
    top of it -- reads as 'engineering drawing' rather than a blank panel."""
    for i, x in enumerate(range(0, int(w) + 1, GRID_SPACING)):
        color = GRID_MAJOR if i % GRID_MAJOR_EVERY == 0 else GRID_MINOR
        canvas.create_line(x, 0, x, h, fill=color, width=1)
    for i, y in enumerate(range(0, int(h) + 1, GRID_SPACING)):
        color = GRID_MAJOR if i % GRID_MAJOR_EVERY == 0 else GRID_MINOR
        canvas.create_line(0, y, w, y, fill=color, width=1)


def _draw_frame(canvas, w, h):
    """Amber corner-bracket frame around the viewport, HUD-style -- a
    decorative border that matches the glow theme instead of a plain edge."""
    bracket = 26
    inset = 3
    pts = [(inset, inset), (w - inset, inset), (w - inset, h - inset), (inset, h - inset)]
    for i, (cx, cy) in enumerate(pts):
        dx = 1 if cx < w / 2 else -1
        dy = 1 if cy < h / 2 else -1
        canvas.create_line(cx, cy, cx + bracket * dx, cy, fill=AMBER_DIM, width=2)
        canvas.create_line(cx, cy, cx, cy + bracket * dy, fill=AMBER_DIM, width=2)


def _draw_ground_hatching(canvas, x1, y, x2, n=14):
    """Classic schematic ground symbol -- short diagonal ticks below a
    horizontal reference line, instead of a bare dashed line."""
    if x2 < x1:
        x1, x2 = x2, x1
    span = x2 - x1
    if span <= 0:
        return
    step = span / n
    tick = step * 0.6
    for i in range(n + 1):
        tx = x1 + i * step
        canvas.create_line(tx, y, tx - tick, y + tick, fill=REFERENCE_GRAY, width=1)


def _rounded_box(canvas, x1, y1, x2, y2, radius, fill, outline, width):
    canvas.create_polygon(_rounded_rect_points(x1, y1, x2, y2, radius), smooth=True,
                           fill=fill, outline=outline, width=width)


def _draw_glow_line(canvas, x1, y1, x2, y2, width, dashed=False, kind="element"):
    dash = (5, 3) if dashed else None
    if kind == "reference":
        canvas.create_line(x1, y1, x2, y2, fill=REFERENCE_GRAY, width=width, dash=dash)
        if abs(y1 - y2) < 0.01 and abs(x2 - x1) > 20:
            _draw_ground_hatching(canvas, x1, max(y1, y2), x2)
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
    canvas.create_line(x1, y1, x2, y2, fill=DIM_COLOR, width=1, arrow=tk.BOTH, arrowshape=(6, 7, 3))


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
    _rounded_box(canvas, bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad,
                 radius=6, fill=AMBER, outline="#1a1a1a", width=1.5)
    canvas.tag_raise(text_id)


_TAG_BOX_COLORS = {"core": AMBER, "shield": AMBER_RADIAL}


def _draw_tag_box(canvas, anchor_x, anchor_y, box_x, box_y, text, kind):
    """Core/shield tag, boxed and filled with that wire's own color -- same
    look as the balun box, connected to the point it's labeling by a dashed
    leader line so the box itself can sit well clear of the feedpoint and
    other labels without losing its meaning."""
    color = _TAG_BOX_COLORS.get(kind, AMBER)
    canvas.create_line(anchor_x, anchor_y, box_x, box_y, fill=color, width=1, dash=(3, 2))
    font = ("Helvetica", 10, "bold")
    text_id = canvas.create_text(box_x, box_y, text=text, fill="#1a1a1a", font=font, anchor="center")
    bbox = canvas.bbox(text_id)
    pad = 4
    _rounded_box(canvas, bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad,
                 radius=5, fill=color, outline="#1a1a1a", width=1.2)
    canvas.tag_raise(text_id)


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

    for x, y, text, size, bold, align in scene.texts:
        font = ("Helvetica", max(int(size * scale * 1.45), 11), "bold" if bold else "normal")
        anchor = "ne" if align == "right" else "nw"
        canvas.create_text(tx(x), ty(y), text=text, fill=FG, font=font, anchor=anchor)

    for x, y, r in scene.feed_points:
        _draw_feed_point(canvas, tx(x), ty(y), max(r * scale, 3.0))

    for feed_x, feed_y, box_x, box_y, text in scene.balun_boxes:
        _draw_balun_box(canvas, tx(feed_x), ty(feed_y), tx(box_x), ty(box_y), text)

    for anchor_x, anchor_y, box_x, box_y, text, kind in scene.tag_boxes:
        _draw_tag_box(canvas, tx(anchor_x), ty(anchor_y), tx(box_x), ty(box_y), text, kind)


def show_drawing(parent: tk.Widget, design, units: str, lang: str, window_title: str, not_to_scale_note: str):
    """Open a Toplevel with the schematic drawing for `design` -- a 2D
    side-view by default, with a 2D/3D toggle (when this antenna's geometry
    has an isometric 3D builder) that re-renders in place."""
    has_3d = design.geometry in _SCENE3D_BUILDERS

    win = tk.Toplevel(parent)
    win.title(window_title)
    win.configure(bg=BG)

    header = tk.Frame(win, bg=BG)
    header.pack(fill="x", padx=12, pady=(10, 6))
    note = tk.Label(header, text=not_to_scale_note, bg=BG, fg=AMBER, font=("Helvetica", 9, "italic"))
    note.pack(side="left")

    mode = tk.StringVar(value="2d")

    # A bigger schematic can be taller than the screen -- wrap the canvas in
    # a scrollable container instead of letting the window manager silently
    # shrink the window (which used to clip the bottom of the drawing).
    container = tk.Frame(win, bg=BG)
    container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    canvas = tk.Canvas(container, bg=PANEL_BG, highlightthickness=0)
    vbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vbar.set)
    canvas.pack(side="left", fill="both", expand=True)

    def render():
        canvas.delete("all")
        vbar.pack_forget()
        if mode.get() == "3d" and has_3d:
            scene = build_scene_3d(design, units=units, lang=lang, margin=50.0)
        else:
            scene = build_scene(design, units=units, lang=lang, margin=50.0)

        scale = MAX_CANVAS / max(scene.width, scene.height)
        canvas_w = scene.width * scale + 40
        canvas_h = scene.height * scale + 40
        canvas.configure(width=canvas_w, height=canvas_h, scrollregion=(0, 0, canvas_w, canvas_h))

        _draw_grid_background(canvas, canvas_w, canvas_h)
        render_scene(canvas, scene, scale=scale, ox=20, oy=20)
        _draw_frame(canvas, canvas_w, canvas_h)

        # Decide up front whether the scrollbar is needed and pack it *before*
        # measuring the window's required size -- packing it afterwards would
        # leave it zero-width (canvas already claims the full window via
        # fill="both"/expand=True), so it would never actually show up.
        win.update_idletasks()
        max_h = win.winfo_screenheight() - 80
        note_overhead = header.winfo_reqheight() + 12 + 18 + 24
        if canvas_h + note_overhead > max_h:
            vbar.pack(side="right", fill="y")

        win.update_idletasks()
        req_w, req_h = win.winfo_reqwidth(), win.winfo_reqheight()
        win.geometry(f"{req_w}x{min(req_h, max_h)}")

    if has_3d:
        toggle = tk.Frame(header, bg=BG)
        toggle.pack(side="right")

        def _restyle():
            for name, btn in (("2d", btn_2d), ("3d", btn_3d)):
                active = mode.get() == name
                btn._bg = AMBER if active else PANEL_BG
                btn._fg = "#1a1a1a" if active else AMBER
                btn._render()

        def set_mode(m):
            mode.set(m)
            _restyle()
            render()

        btn_2d = RoundedButton(toggle, text="2D", command=lambda: set_mode("2d"),
                                bg=AMBER, fg="#1a1a1a", active_bg="#ffcb4d", font=("Helvetica", 9, "bold"))
        btn_3d = RoundedButton(toggle, text="3D", command=lambda: set_mode("3d"),
                                bg=PANEL_BG, fg=AMBER, active_bg=AMBER_DIM, font=("Helvetica", 9, "bold"))
        btn_2d.pack(side="left", padx=(0, 6))
        btn_3d.pack(side="left")

    render()
    win.resizable(True, True)
    return win
