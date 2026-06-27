"""Tkinter GUI for the HAM Antenna Designer.

Visual style matches HAMIOS: dark background, amber (#FFB000) accents,
amber-bordered panels. Lets you pick an antenna type, band, units, and
language, see the computed design + build advice, and export the scaled SVG
drawing. A feed-cable dropdown shows velocity factor for reference (per the
original cable/VF list requirement) -- informational only, not yet wired
into a feedline calculation.

No print-template (PDF) export -- by design, this tool gives you precise
measurements and a scaled drawing; cutting wire/tubing is done with a tape
measure against those numbers, not a taped-together paper template.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import calculators  # noqa: F401 -- registers all antenna calculator types
from build_notes import build_advice
from data_store import BANDS_MHZ, CABLES, antenna_type_label
from drawing import draw_antenna
from format_text import format_summary
from registry import REGISTRY, design as design_antenna
from settings import load_settings, save_settings
from widgets import RoundedButton, RoundedPanel

BG = "#1a1a1a"
PANEL_BG = "#1f1f1f"
FG = "#e8e8e8"
AMBER = "#ffb000"
AMBER_DIM = "#8a6000"
FONT_TITLE = ("Helvetica", 13, "bold")
FONT_LABEL = ("Helvetica", 10)
FONT_MONO = ("Menlo", 10)
FONT_COURIER = ("Courier New", 11)


def _band_display(band: str) -> str:
    low, high = BANDS_MHZ[band]
    return f"{band} ({low:g}-{high:g} MHz)"


_BAND_DISPLAY_TO_KEY = {_band_display(b): b for b in BANDS_MHZ}

UI_TEXT = {
    "en": {
        "window_title": "HAM Antenna Designer",
        "antenna_type": "Antenna",
        "band": "Band",
        "units": "Units",
        "language": "Language",
        "feed_cable": "Feed cable (VF)",
        "calculate": "Calculate",
        "export_svg": "Export SVG drawing...",
        "results": "Design",
        "advice": "Build notes",
        "saved": "Saved to {path}",
        "error": "Error",
        "vf_label": "Velocity factor: {vf} ({notes})",
    },
    "nl": {
        "window_title": "HAM Antenne Ontwerper",
        "antenna_type": "Antenne",
        "band": "Band",
        "units": "Eenheden",
        "language": "Taal",
        "feed_cable": "Voedingskabel (VF)",
        "calculate": "Berekenen",
        "export_svg": "SVG-tekening exporteren...",
        "results": "Ontwerp",
        "advice": "Bouwnotities",
        "saved": "Opgeslagen naar {path}",
        "error": "Fout",
        "vf_label": "Velocity factor (VF): {vf} ({notes})",
    },
}


class AntennaDesignerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.design = None
        saved = load_settings()
        self.lang = tk.StringVar(value=saved["lang"])
        self.units = tk.StringVar(value=saved["units"])
        self.band = tk.StringVar(value="20m")
        self.antenna_type = tk.StringVar(value="vertical_quarter_wave")
        self.feed_cable = tk.StringVar(value=next(iter(CABLES)))

        self._configure_style()
        self.title(UI_TEXT[self.lang.get()]["window_title"])
        self.configure(bg=BG)

        self._build_layout()
        self._calculate()

        # Size the window to fit its actual content -- the rounded panels'
        # auto-sizing means required height can exceed any fixed guess.
        self.update_idletasks()
        width = max(820, self.winfo_reqwidth())
        height = max(720, self.winfo_reqheight())
        self.geometry(f"{width}x{height}")
        self.minsize(700, 600)

    def _configure_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=BG, foreground=FG, fieldbackground=PANEL_BG)
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL_BG)
        style.configure("TLabel", background=BG, foreground=FG, font=FONT_LABEL)
        style.configure("Panel.TLabel", background=PANEL_BG, foreground=FG, font=FONT_LABEL)
        style.configure("Title.TLabel", background=BG, foreground=AMBER, font=FONT_TITLE)
        style.configure("PanelTitle.TLabel", background=PANEL_BG, foreground=AMBER, font=FONT_TITLE)
        style.configure("TButton", background=PANEL_BG, foreground=AMBER, font=FONT_LABEL, borderwidth=1)
        style.map("TButton", background=[("active", AMBER_DIM)], foreground=[("active", "#000000")])
        style.configure(
            "TCombobox",
            fieldbackground=PANEL_BG, background=PANEL_BG, foreground=FG,
            arrowcolor=AMBER, selectbackground=PANEL_BG, selectforeground=AMBER,
            bordercolor=AMBER, lightcolor=PANEL_BG, darkcolor=PANEL_BG,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", PANEL_BG)],
            foreground=[("readonly", FG)],
            background=[("readonly", PANEL_BG)],
        )
        self.option_add("*TCombobox*Listbox.background", PANEL_BG)
        self.option_add("*TCombobox*Listbox.foreground", FG)
        self.option_add("*TCombobox*Listbox.selectBackground", AMBER_DIM)
        self.option_add("*TCombobox*Listbox.selectForeground", "#000000")
        style.configure("TRadiobutton", background=PANEL_BG, foreground=FG, font=FONT_LABEL)
        style.map(
            "TRadiobutton",
            indicatorcolor=[("selected", AMBER)],
            background=[("active", PANEL_BG)],
        )

    def _make_panel(self, parent) -> RoundedPanel:
        """An amber-bordered, rounded-corner panel matching the HAMIOS
        DraggablePanel look, drawn on a Canvas so corners can be rounded
        (ttk.Frame can't do that) and colors are guaranteed to render
        consistently across platforms."""
        panel = RoundedPanel(parent, bg_outer=BG, bg_inner=PANEL_BG, border_color=AMBER, radius=14, border_width=2)
        return panel, panel.inner

    def _t(self, key):
        return UI_TEXT[self.lang.get()][key]

    def _antenna_type_values(self):
        lang = self.lang.get()
        return [antenna_type_label(t, lang) for t in REGISTRY]

    def _antenna_type_from_label(self, label):
        lang = self.lang.get()
        for t in REGISTRY:
            if antenna_type_label(t, lang) == label:
                return t
        return self.antenna_type.get()

    def _build_layout(self):
        # Header.
        header = ttk.Frame(self)
        header.pack(fill="x", padx=12, pady=(12, 6))
        self.title_label = ttk.Label(header, text=self._t("window_title"), style="Title.TLabel")
        self.title_label.pack(side="left")

        # Controls panel (amber-bordered, like HAMIOS panels).
        controls_border, controls = self._make_panel(self)
        controls_border.pack(fill="x", padx=12, pady=6)

        self.type_label = ttk.Label(controls, text=self._t("antenna_type"), style="Panel.TLabel")
        self.type_label.grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.type_combo_var = tk.StringVar(value=antenna_type_label(self.antenna_type.get(), self.lang.get()))
        self.type_combo = ttk.Combobox(
            controls, textvariable=self.type_combo_var, values=self._antenna_type_values(),
            state="readonly", width=26,
        )
        self.type_combo.grid(row=0, column=1, padx=8, pady=8, sticky="w")
        self.type_combo.bind("<<ComboboxSelected>>", self._on_type_change)

        self.band_label = ttk.Label(controls, text=self._t("band"), style="Panel.TLabel")
        self.band_label.grid(row=0, column=2, padx=8, pady=8, sticky="w")
        self.band_combo_var = tk.StringVar(value=_band_display(self.band.get()))
        self.band_combo = ttk.Combobox(
            controls, textvariable=self.band_combo_var, values=list(_BAND_DISPLAY_TO_KEY), state="readonly", width=20,
        )
        self.band_combo.grid(row=0, column=3, padx=8, pady=8, sticky="w")
        self.band_combo.bind("<<ComboboxSelected>>", self._on_band_change)

        self.units_label = ttk.Label(controls, text=self._t("units"), style="Panel.TLabel")
        self.units_label.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="w")
        units_frame = ttk.Frame(controls, style="Panel.TFrame")
        units_frame.grid(row=1, column=1, padx=8, pady=(0, 8), sticky="w")
        for i, val in enumerate(["metric", "imperial"]):
            rb = ttk.Radiobutton(units_frame, text=val, value=val, variable=self.units, command=self._on_units_change)
            rb.grid(row=0, column=i, padx=(0, 6))

        self.lang_label = ttk.Label(controls, text=self._t("language"), style="Panel.TLabel")
        self.lang_label.grid(row=1, column=2, padx=8, pady=(0, 8), sticky="w")
        lang_frame = ttk.Frame(controls, style="Panel.TFrame")
        lang_frame.grid(row=1, column=3, padx=8, pady=(0, 8), sticky="w")
        for i, val in enumerate(["en", "nl"]):
            rb = ttk.Radiobutton(lang_frame, text=val.upper(), value=val, variable=self.lang, command=self._on_lang_change)
            rb.grid(row=0, column=i, padx=(0, 6))

        self.cable_label = ttk.Label(controls, text=self._t("feed_cable"), style="Panel.TLabel")
        self.cable_label.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="w")
        cable_combo = ttk.Combobox(controls, textvariable=self.feed_cable, values=list(CABLES), state="readonly", width=20)
        cable_combo.grid(row=2, column=1, padx=8, pady=(0, 8), sticky="w")
        cable_combo.bind("<<ComboboxSelected>>", lambda e: self._update_cable_label())
        self.cable_vf_label = ttk.Label(controls, text="", style="Panel.TLabel")
        self.cable_vf_label.grid(row=2, column=2, columnspan=2, padx=8, pady=(0, 8), sticky="w")

        # Results panel.
        results_border, results_frame = self._make_panel(self)
        results_border.pack(fill="x", padx=12, pady=6)
        self.results_title = ttk.Label(results_frame, text=self._t("results"), style="PanelTitle.TLabel")
        self.results_title.pack(anchor="w", padx=8, pady=(8, 0))
        self.results_text = tk.Text(
            results_frame, height=6, bg=PANEL_BG, fg=AMBER, insertbackground=AMBER,
            font=FONT_MONO, relief="flat", borderwidth=0,
        )
        self.results_text.pack(fill="x", padx=8, pady=8)

        # Build advice panel.
        advice_border, advice_frame = self._make_panel(self)
        advice_border.pack(fill="both", expand=True, padx=12, pady=6)
        self.advice_title = ttk.Label(advice_frame, text=self._t("advice"), style="PanelTitle.TLabel")
        self.advice_title.pack(anchor="w", padx=8, pady=(8, 0))
        self.advice_text = tk.Text(
            advice_frame, bg=PANEL_BG, fg=FG, insertbackground=AMBER,
            font=FONT_COURIER, relief="flat", borderwidth=0, wrap="word",
        )
        self.advice_text.pack(fill="both", expand=True, padx=8, pady=8)

        # Footer / export buttons.
        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=12, pady=(6, 12))
        self.calc_button = RoundedButton(
            footer, text=self._t("calculate"), command=self._calculate,
            bg=AMBER, fg="#1a1a1a", active_bg="#ffcb4d", font=FONT_LABEL,
        )
        self.calc_button.pack(side="left")
        self.svg_button = RoundedButton(
            footer, text=self._t("export_svg"), command=self._export_svg,
            bg=PANEL_BG, fg=AMBER, active_bg=AMBER_DIM, font=FONT_LABEL,
        )
        self.svg_button.pack(side="left", padx=(8, 0))

        self._update_cable_label()

    def _update_cable_label(self):
        cable = CABLES[self.feed_cable.get()]
        self.cable_vf_label.config(
            text=self._t("vf_label").format(vf=cable["velocity_factor"], notes=cable["notes"])
        )

    def _on_type_change(self, event=None):
        self.antenna_type.set(self._antenna_type_from_label(self.type_combo_var.get()))
        self._calculate()

    def _on_band_change(self, event=None):
        self.band.set(_BAND_DISPLAY_TO_KEY[self.band_combo_var.get()])
        self._calculate()

    def _on_units_change(self):
        save_settings(units=self.units.get())
        self._calculate()

    def _on_lang_change(self):
        save_settings(lang=self.lang.get())
        t = UI_TEXT[self.lang.get()]
        self.title(t["window_title"])
        self.title_label.config(text=t["window_title"])
        self.type_label.config(text=t["antenna_type"])
        self.band_label.config(text=t["band"])
        self.units_label.config(text=t["units"])
        self.lang_label.config(text=t["language"])
        self.cable_label.config(text=t["feed_cable"])
        self.results_title.config(text=t["results"])
        self.advice_title.config(text=t["advice"])
        self.calc_button.set_text(t["calculate"])
        self.svg_button.set_text(t["export_svg"])
        # Re-translate the antenna type dropdown without changing the selected type.
        self.type_combo["values"] = self._antenna_type_values()
        self.type_combo_var.set(antenna_type_label(self.antenna_type.get(), self.lang.get()))
        self._update_cable_label()
        self._calculate()

    def _calculate(self):
        lang = self.lang.get()
        units = self.units.get()
        band = self.band.get()
        antenna_type = self.antenna_type.get()

        self.design = design_antenna(antenna_type, band, lang=lang)

        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", format_summary(self.design, units=units, lang=lang))

        self.advice_text.delete("1.0", "end")
        self.advice_text.insert("1.0", build_advice(self.design, units=units, lang=lang))

    def _export_svg(self):
        if not self.design:
            return
        path = filedialog.asksaveasfilename(defaultextension=".svg", filetypes=[("SVG", "*.svg")])
        if not path:
            return
        dwg = draw_antenna(self.design, units=self.units.get(), lang=self.lang.get())
        dwg.saveas(path)
        messagebox.showinfo(self._t("window_title"), self._t("saved").format(path=path))



if __name__ == "__main__":
    app = AntennaDesignerApp()
    app.mainloop()
