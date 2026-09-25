"""In-app schematic viewer: a Toplevel showing the antenna schematic
(schematic.py) in the night (electronics schematic) or day (technical
drawing) theme, in 2D or 3D. The page is scaled down as a whole -- lines,
symbols and text together -- when it would not fit on the screen, so the
label layout stays exactly as computed.
"""

import tkinter as tk

from i18n import SCHEMATIC
from schematic import build_model, layout
from schematic_render import THEMES, TkPainter
from settings import load_settings, save_settings
from widgets import RoundedButton

BG = "#10131a"
PANEL_BG = "#161a22"
AMBER = "#ffb000"
AMBER_DIM = "#8a6000"
CYAN = "#00d4ff"
CYAN_DIM = "#0099cc"


def show_drawing(parent: tk.Widget, design, units: str, lang: str, window_title: str,
                 not_to_scale_note: str = "", cable: str = None):
    T = SCHEMATIC[lang]
    model = build_model(design, units=units, lang=lang, cable=cable)
    saved = load_settings().get("drawing_theme", "night")
    state = {"view": "2d", "theme": saved if saved in ("night", "day") else "night"}

    win = tk.Toplevel(parent)
    win.title(window_title)
    win.configure(bg=BG)

    header = tk.Frame(win, bg=BG)
    header.pack(fill="x", padx=12, pady=(10, 6))
    RoundedButton(header, "Exit", win.destroy, PANEL_BG, AMBER, AMBER_DIM,
                  font=("Helvetica", 9, "bold")).pack(side="right", padx=(10, 0))

    def toggle_group(options, key):
        frame = tk.Frame(header, bg=BG)
        frame.pack(side="right", padx=(10, 0))
        buttons = {}

        def restyle():
            for name, btn in buttons.items():
                active = state[key] == name
                btn._bg = CYAN if active else PANEL_BG
                btn._fg = PANEL_BG if active else CYAN
                btn._render()

        def choose(name):
            state[key] = name
            if key == "theme":
                save_settings(drawing_theme=name)
            restyle()
            render()

        for name, text in options:
            b = RoundedButton(frame, text=text, command=lambda n=name: choose(n), bg=PANEL_BG, fg=CYAN,
                              active_bg=CYAN_DIM, font=("Helvetica", 9, "bold"))
            b.pack(side="left", padx=(0, 6))
            buttons[name] = b
        restyle()

    toggle_group([("night", T["night"]), ("day", T["day"])], "theme")
    toggle_group([("2d", "2D"), ("3d", "3D")], "view")

    canvas = tk.Canvas(win, bg=BG, highlightthickness=0)
    canvas.pack(padx=12, pady=(0, 12))

    def render():
        canvas.delete("all")
        theme = THEMES[state["theme"]]
        painter = TkPainter(canvas, theme, f=1.0)
        L = layout(design, model, state["view"], painter.measure, painter.line_h, lang)
        max_w = win.winfo_screenwidth() - 60
        max_h = win.winfo_screenheight() - 150
        f = min(1.0, max_w / L.width, max_h / L.height)
        painter.f = f
        canvas.configure(width=L.width * f, height=L.height * f, bg=theme.PAGE)
        theme.paint(L, painter)
        win.update_idletasks()
        win.geometry("")

    render()
    win.resizable(False, False)
    return win
