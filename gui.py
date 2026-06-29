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

import re
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

import calculators  # noqa: F401 -- registers all antenna calculator types
from build_notes import build_advice
from data_store import (
    BANDS_MHZ, CABLES, WIRES, SHAPE_FAMILIES, STANDALONE_TYPES,
    antenna_type_for, antenna_type_label, wave_fractions_for, wire_velocity_factor,
)
from drawing import draw_antenna
from format_text import format_summary
from i18n import SHAPE_FAMILY_LABELS, WAVE_FRACTION_LABELS, WIRE_LABELS
from registry import REGISTRY, design as design_antenna
from settings import load_settings, save_settings
from widgets import LogoCanvas, RoundedButton, RoundedPanel
from canvas_view import show_drawing
from swr_calc import impedance_to_swr_table
from smith_chart import (
    draw_smith_chart_grid, plot_impedance_point, plot_swr_circle,
    complex_to_smith_coords
)
from freq_sweep import sweep_antenna_response, calculate_bandwidth
from radiation_pattern import generate_azimuth_pattern, calculate_gain_description
from polar_plot import draw_polar_grid, plot_azimuth_pattern
from transmissionline_loss import (
    calculate_cable_loss, compare_cables, power_budget_summary, get_all_cable_types
)

# Shape families with 2+ wavelength-fraction options get a second "Wave"
# picker; families with only one fraction (or standalone types like Yagi,
# J-pole, OCF...) skip it entirely -- a dropdown with one possible answer
# isn't a choice, it's noise.
SHAPE_FAMILY_ORDER = ["vertical", "horizontal_center_fed", "horizontal_end_fed", "horizontal_loop"]


def _primary_choice_keys():
    return [f for f in SHAPE_FAMILY_ORDER if f in SHAPE_FAMILIES] + STANDALONE_TYPES


def _primary_label(key, lang):
    if key in SHAPE_FAMILIES:
        return SHAPE_FAMILY_LABELS[key][lang]
    return antenna_type_label(key, lang)

BG = "#1a1a1a"
PANEL_BG = "#1f1f1f"
FG = "#e8e8e8"
AMBER = "#ffb000"
AMBER_DIM = "#8a6000"
FONT_TITLE = ("Helvetica", 13, "bold")
FONT_LABEL = ("Helvetica", 10)
FONT_COURIER = ("Courier New", 11)


def _band_display(band: str) -> str:
    low, high = BANDS_MHZ[band]
    return f"{band} ({low:g}-{high:g} MHz)"


def _wire_label(key: str, lang: str) -> str:
    """Get translated wire name for display."""
    return WIRE_LABELS.get(key, {}).get(lang, key)


def _wire_display_values(lang: str):
    """Get all wire names translated to the selected language."""
    return [_wire_label(k, lang) for k in WIRES.keys()]


def _wire_key_from_display(display_name: str, lang: str) -> str:
    """Convert translated wire display name back to English key."""
    for key in WIRES.keys():
        if _wire_label(key, lang) == display_name:
            return key
    return display_name


_BAND_DISPLAY_TO_KEY = {_band_display(b): b for b in BANDS_MHZ}

UI_TEXT = {
    "en": {
        "window_title": "HAM Antenna Designer",
        "antenna_type": "Antenna",
        "wave": "Wave",
        "band": "Band",
        "units": "Units",
        "language": "Language",
        "antenna_wire": "Antenna wire (VF)",
        "feed_cable": "Feed cable (VF)",
        "calculate": "Calculate",
        "export_svg": "Export SVG drawing...",
        "view_drawing": "View drawing",
        "exit": "Exit",
        "drawing_window_title": "Antenna drawing -- {label} ({band})",
        "not_to_scale": "Schematic only -- NOT to scale. Dimensions shown are the calculated values.",
        "results": "Design",
        "advice": "Build notes",
        "saved": "Saved to {path}",
        "error": "Error",
        "vf_label": "Velocity factor: {vf} ({notes})",
        "custom_freq": "Custom freq (MHz)",
        "custom_freq_hint": "Optional -- overrides the band, calculates for this exact frequency",
        "custom_freq_invalid": "Not a valid frequency -- using the band's default instead",
        "balun_help": "Balun/Unun Guide",
        "swr": "Matching",
        "swr_value": "SWR",
        "return_loss": "Return loss",
        "power_reflected": "Power reflected",
        "power_transmitted": "Power transmitted",
        "gamma": "Reflection coeff.",
        "swr_explanation_title": "SWR & Impedance Matching Explained",
        "smith_explanation_title": "Smith Chart Explanation",
    },
    "nl": {
        "window_title": "HAM Antenne Ontwerper",
        "antenna_type": "Antenne",
        "wave": "Golf",
        "band": "Band",
        "units": "Eenheden",
        "language": "Taal",
        "antenna_wire": "Antennedraad (VF)",
        "feed_cable": "Voedingskabel (VF)",
        "calculate": "Berekenen",
        "export_svg": "SVG-tekening exporteren...",
        "view_drawing": "Bekijk tekening",
        "exit": "Afsluiten",
        "drawing_window_title": "Antennetekening -- {label} ({band})",
        "not_to_scale": "Alleen schematisch -- NIET op schaal. De getoonde maten zijn de berekende waarden.",
        "results": "Ontwerp",
        "advice": "Bouwnotities",
        "saved": "Opgeslagen naar {path}",
        "error": "Fout",
        "vf_label": "Velocity factor (VF): {vf} ({notes})",
        "custom_freq": "Eigen freq (MHz)",
        "custom_freq_hint": "Optioneel -- overschrijft de band, rekent op deze exacte frequentie",
        "custom_freq_invalid": "Geen geldige frequentie -- standaardwaarde van de band gebruikt",
        "balun_help": "Balun/Unun Gids",
        "swr": "Aanpassing",
        "swr_value": "SWR",
        "return_loss": "Return loss",
        "power_reflected": "Gereflecteerd vermogen",
        "power_transmitted": "Doorgegeven vermogen",
        "gamma": "Reflectiecoëff.",
        "swr_explanation_title": "SWR & Impedantie Aanpassing Uitgelegd",
        "smith_explanation_title": "Smith Chart Uitleg",
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
        self.primary_choice = tk.StringVar(value="vertical")
        self.wave_fraction = tk.StringVar(value="1/4")
        self.antenna_type = tk.StringVar(value="vertical_quarter_wave")
        self.antenna_wire = tk.StringVar(value=next(iter(WIRES)))
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
        style.configure(
            "TEntry",
            fieldbackground=PANEL_BG, foreground=FG, insertcolor=AMBER,
            bordercolor=AMBER, lightcolor=PANEL_BG, darkcolor=PANEL_BG,
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

    def _primary_choice_values(self):
        lang = self.lang.get()
        return [_primary_label(k, lang) for k in _primary_choice_keys()]

    def _primary_choice_from_label(self, label):
        lang = self.lang.get()
        for k in _primary_choice_keys():
            if _primary_label(k, lang) == label:
                return k
        return self.primary_choice.get()

    def _build_layout(self):
        # Header -- title on the left, action buttons on the right (incl.
        # a red Exit button), so the whole control bar lives at the very
        # top of the window instead of a separate footer.
        header = ttk.Frame(self)
        header.pack(fill="x", padx=12, pady=(12, 6))
        self.logo = LogoCanvas(header, bg=BG, core_color=AMBER, size=32)
        self.logo.pack(side="left", padx=(0, 8))
        self.title_label = ttk.Label(header, text=self._t("window_title"), style="Title.TLabel")
        self.title_label.pack(side="left")

        button_bar = tk.Frame(header, bg=BG)
        button_bar.pack(side="right")

        self.exit_button = RoundedButton(
            button_bar, text=self._t("exit"), command=self.destroy,
            bg="#c0392b", fg="#ffffff", active_bg="#e74c3c", font=FONT_LABEL,
        )
        self.exit_button.pack(side="right")
        self.view_button = RoundedButton(
            button_bar, text=self._t("view_drawing"), command=self._view_drawing,
            bg=PANEL_BG, fg=AMBER, active_bg=AMBER_DIM, font=FONT_LABEL,
        )
        self.view_button.pack(side="right", padx=(0, 8))
        self.svg_button = RoundedButton(
            button_bar, text=self._t("export_svg"), command=self._export_svg,
            bg=PANEL_BG, fg=AMBER, active_bg=AMBER_DIM, font=FONT_LABEL,
        )
        self.svg_button.pack(side="right", padx=(0, 8))
        self.calc_button = RoundedButton(
            button_bar, text=self._t("calculate"), command=self._calculate,
            bg=AMBER, fg="#1a1a1a", active_bg="#ffcb4d", font=FONT_LABEL,
        )
        self.calc_button.pack(side="right", padx=(0, 8))

        # Controls panel (amber-bordered, like HAMIOS panels).
        controls_border, controls = self._make_panel(self)
        controls_border.pack(fill="x", padx=14, pady=8)

        self.type_label = ttk.Label(controls, text=self._t("antenna_type"), style="Panel.TLabel")
        self.type_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.type_combo_var = tk.StringVar(value=_primary_label(self.primary_choice.get(), self.lang.get()))
        self.type_combo = ttk.Combobox(
            controls, textvariable=self.type_combo_var, values=self._primary_choice_values(),
            state="readonly", width=26,
        )
        self.type_combo.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.type_combo.bind("<<ComboboxSelected>>", self._on_primary_change)

        self.band_label = ttk.Label(controls, text=self._t("band"), style="Panel.TLabel")
        self.band_label.grid(row=0, column=2, padx=10, pady=10, sticky="w")
        self.band_combo_var = tk.StringVar(value=_band_display(self.band.get()))
        self.band_combo = ttk.Combobox(
            controls, textvariable=self.band_combo_var, values=list(_BAND_DISPLAY_TO_KEY), state="readonly", width=20,
        )
        self.band_combo.grid(row=0, column=3, padx=10, pady=10, sticky="w")
        self.band_combo.bind("<<ComboboxSelected>>", self._on_band_change)

        self.custom_freq_label = ttk.Label(controls, text="or/or", style="Panel.TLabel")
        self.custom_freq_label.grid(row=1, column=2, padx=10, pady=(0, 10), sticky="w")
        self.custom_freq = tk.StringVar(value="")
        custom_freq_entry = ttk.Entry(controls, textvariable=self.custom_freq, width=20)
        custom_freq_entry.grid(row=1, column=3, padx=10, pady=(0, 10), sticky="w")
        custom_freq_entry.bind("<KeyRelease>", lambda e: self._calculate())
        self.custom_freq_hint = ttk.Label(controls, text=self._t("custom_freq_hint"), style="Panel.TLabel")
        self.custom_freq_hint.grid(row=1, column=4, padx=10, pady=(0, 10), sticky="w")

        # Wave (wavelength fraction) picker -- only gridded when the current
        # shape family actually has 2+ fractions to choose between.
        self.wave_label = ttk.Label(controls, text=self._t("wave"), style="Panel.TLabel")
        self.wave_combo_var = tk.StringVar(value="")
        self.wave_combo = ttk.Combobox(controls, textvariable=self.wave_combo_var, state="readonly", width=22)
        self.wave_combo.bind("<<ComboboxSelected>>", self._on_wave_change)
        self._refresh_wave_picker()

        self.units_label = ttk.Label(controls, text=self._t("units"), style="Panel.TLabel")
        self.units_label.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="w")
        units_frame = ttk.Frame(controls, style="Panel.TFrame")
        units_frame.grid(row=2, column=1, padx=10, pady=(0, 10), sticky="w")
        for i, val in enumerate(["metric", "imperial"]):
            rb = ttk.Radiobutton(units_frame, text=val, value=val, variable=self.units, command=self._on_units_change)
            rb.grid(row=0, column=i, padx=(0, 6))

        self.lang_label = ttk.Label(controls, text=self._t("language"), style="Panel.TLabel")
        self.lang_label.grid(row=2, column=2, padx=10, pady=(0, 10), sticky="w")
        lang_frame = ttk.Frame(controls, style="Panel.TFrame")
        lang_frame.grid(row=2, column=3, padx=10, pady=(0, 10), sticky="w")
        for i, val in enumerate(["en", "nl"]):
            rb = ttk.Radiobutton(lang_frame, text=val.upper(), value=val, variable=self.lang, command=self._on_lang_change)
            rb.grid(row=0, column=i, padx=(0, 6))

        self.wire_label = ttk.Label(controls, text=self._t("antenna_wire"), style="Panel.TLabel")
        self.wire_label.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="w")
        self.wire_combo = ttk.Combobox(controls, state="readonly", width=40)
        self.wire_combo.grid(row=3, column=1, padx=10, pady=(0, 10), sticky="w")
        self._update_wire_combo_display()
        self.wire_combo.bind("<<ComboboxSelected>>", self._on_wire_change)
        self.wire_vf_label = ttk.Label(controls, text="", style="Panel.TLabel")
        self.wire_vf_label.grid(row=3, column=2, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        self.cable_label = ttk.Label(controls, text=self._t("feed_cable"), style="Panel.TLabel")
        self.cable_label.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="w")
        cable_combo = ttk.Combobox(controls, textvariable=self.feed_cable, values=list(CABLES), state="readonly", width=40)
        cable_combo.grid(row=4, column=1, padx=10, pady=(0, 10), sticky="w")
        cable_combo.bind("<<ComboboxSelected>>", lambda e: (self._update_cable_label(), self._calculate()))
        self.cable_vf_label = ttk.Label(controls, text="", style="Panel.TLabel")
        self.cable_vf_label.grid(row=4, column=2, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        # Results panel.
        results_border, results_frame = self._make_panel(self)
        results_border.pack(fill="x", padx=14, pady=8)
        self.results_title = ttk.Label(results_frame, text=self._t("results"), style="PanelTitle.TLabel")
        self.results_title.pack(anchor="w", padx=12, pady=(12, 0))
        self.results_text = tk.Text(
            results_frame, height=6, bg=PANEL_BG, fg=FG, insertbackground=AMBER,
            font=FONT_COURIER, relief="flat", borderwidth=0, padx=10, pady=10,
            highlightthickness=0,
        )
        self.results_text.pack(fill="x", padx=12, pady=12)

        # SWR & Matching panel.
        swr_border, swr_frame = self._make_panel(self)
        swr_border.pack(fill="x", padx=14, pady=8)
        self.swr_title = ttk.Label(swr_frame, text=self._t("swr"), style="PanelTitle.TLabel")
        self.swr_title.pack(anchor="w", padx=12, pady=(12, 0))
        self.swr_text = tk.Text(
            swr_frame, height=4, bg=PANEL_BG, fg=FG, insertbackground=AMBER,
            font=FONT_COURIER, relief="flat", borderwidth=0, padx=10, pady=10,
            highlightthickness=0,
        )
        self.swr_text.pack(fill="x", padx=12, pady=12)

        # Buttons for Smith Chart and Sweep popups
        chart_buttons_frame = ttk.Frame(self, style="Panel.TFrame")
        chart_buttons_frame.pack(fill="x", padx=14, pady=8)

        self.smith_btn = RoundedButton(chart_buttons_frame, "View Smith Chart", self._show_smith_chart,
                                       PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
        self.smith_btn.pack(side="left", padx=5)

        self.sweep_btn = RoundedButton(chart_buttons_frame, "View SWR Sweep", self._show_sweep_window,
                                       PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
        self.sweep_btn.pack(side="left", padx=5)

        self.pattern_btn = RoundedButton(chart_buttons_frame, "View Radiation", self._show_radiation_pattern,
                                        PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
        self.pattern_btn.pack(side="left", padx=5)

        self.loss_btn = RoundedButton(chart_buttons_frame, "Cable Loss", self._show_cable_loss,
                                     PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
        self.loss_btn.pack(side="left", padx=5)

        # Build advice panel.
        advice_border, advice_frame = self._make_panel(self)
        advice_border.pack(fill="both", expand=True, padx=14, pady=8)

        # Title with help button
        advice_title_frame = ttk.Frame(advice_frame, style="Panel.TFrame")
        advice_title_frame.pack(anchor="w", padx=12, pady=(12, 0), fill="x")

        self.advice_title = ttk.Label(advice_title_frame, text=self._t("advice"), style="PanelTitle.TLabel")
        self.advice_title.pack(anchor="w", side="left")

        self.balun_help_btn = RoundedButton(advice_title_frame, self._t("balun_help"), self._show_balun_help,
                                            PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
        self.balun_help_btn.pack(side="right", padx=(10, 0))
        self.advice_text = tk.Text(
            advice_frame, bg=PANEL_BG, fg=FG, insertbackground=AMBER,
            font=FONT_COURIER, relief="flat", borderwidth=0, wrap="word", padx=12, pady=12,
            highlightthickness=0,
        )
        self.advice_text.pack(fill="both", expand=True, padx=12, pady=12)

        self._update_wire_label()
        self._update_cable_label()

    def _update_cable_label(self):
        cable = CABLES[self.feed_cable.get()]
        self.cable_vf_label.config(
            text=self._t("vf_label").format(vf=cable["velocity_factor"], notes=cable["notes"])
        )

    def _update_wire_combo_display(self):
        """Update wire combo values with current language translations."""
        lang = self.lang.get()
        wire_keys = list(WIRES.keys())
        self.wire_combo["values"] = [_wire_label(k, lang) for k in wire_keys]
        # Update the display to show the translated name of the currently selected wire
        current_wire = self.antenna_wire.get()
        if current_wire in WIRES:
            self.wire_combo.set(_wire_label(current_wire, lang))

    def _on_wire_change(self, event=None):
        """Handle wire combo selection - convert display name to English key."""
        display_name = self.wire_combo.get()
        lang = self.lang.get()
        wire_key = _wire_key_from_display(display_name, lang)
        self.antenna_wire.set(wire_key)
        self._update_wire_label()
        self._calculate()

    def _update_wire_label(self):
        wire = WIRES[self.antenna_wire.get()]
        self.wire_vf_label.config(
            text=self._t("vf_label").format(vf=wire["velocity_factor"], notes=wire["notes"])
        )

    def _refresh_wave_picker(self):
        """Show/populate the Wave dropdown only when the current primary
        choice is a shape family with 2+ wavelength fractions -- otherwise
        there's nothing to choose, so hide it entirely."""
        primary = self.primary_choice.get()
        fractions = wave_fractions_for(primary) if primary in SHAPE_FAMILIES else []
        lang = self.lang.get()

        if len(fractions) >= 2:
            if self.wave_fraction.get() not in fractions:
                self.wave_fraction.set(fractions[0])
            self.wave_combo["values"] = [WAVE_FRACTION_LABELS[f][lang] for f in fractions]
            self.wave_combo_var.set(WAVE_FRACTION_LABELS[self.wave_fraction.get()][lang])
            self.wave_label.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")
            self.wave_combo.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="w")
        else:
            self.wave_label.grid_remove()
            self.wave_combo.grid_remove()
            if fractions:
                self.wave_fraction.set(fractions[0])

        self._sync_antenna_type()

    def _sync_antenna_type(self):
        primary = self.primary_choice.get()
        if primary in SHAPE_FAMILIES:
            self.antenna_type.set(antenna_type_for(primary, self.wave_fraction.get()))
        else:
            self.antenna_type.set(primary)

    def _on_primary_change(self, event=None):
        self.primary_choice.set(self._primary_choice_from_label(self.type_combo_var.get()))
        self._refresh_wave_picker()
        self._calculate()

    def _on_wave_change(self, event=None):
        lang = self.lang.get()
        primary = self.primary_choice.get()
        for f in wave_fractions_for(primary):
            if WAVE_FRACTION_LABELS[f][lang] == self.wave_combo_var.get():
                self.wave_fraction.set(f)
                break
        self._sync_antenna_type()
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
        self.wave_label.config(text=t["wave"])
        self.band_label.config(text=t["band"])
        self.units_label.config(text=t["units"])
        self.lang_label.config(text=t["language"])
        self.wire_label.config(text=t["antenna_wire"])
        self._update_wire_combo_display()
        self.cable_label.config(text=t["feed_cable"])
        self.custom_freq_label.config(text=t["custom_freq"])
        self.results_title.config(text=t["results"])
        self.advice_title.config(text=t["advice"])
        self.calc_button.set_text(t["calculate"])
        self.svg_button.set_text(t["export_svg"])
        self.view_button.set_text(t["view_drawing"])
        self.exit_button.set_text(t["exit"])
        # Re-translate the antenna/wave dropdowns without changing the selected type.
        self.type_combo["values"] = self._primary_choice_values()
        self.type_combo_var.set(_primary_label(self.primary_choice.get(), self.lang.get()))
        self._refresh_wave_picker()
        self._update_cable_label()
        self._calculate()

    def _parse_custom_freq(self):
        raw = self.custom_freq.get().strip()
        if not raw:
            self.custom_freq_hint.config(text=self._t("custom_freq_hint"))
            return None
        try:
            freq = float(raw.replace(",", "."))
            if freq <= 0:
                raise ValueError
            self.custom_freq_hint.config(text=self._t("custom_freq_hint"))
            return freq
        except ValueError:
            self.custom_freq_hint.config(text=self._t("custom_freq_invalid"))
            return None

    _NUMBERED_LINE = re.compile(r"^\d+\.\s+")

    def _set_text_with_hanging_indent(self, text_widget, content, highlight_title=False):
        """Insert `content` and make word-wrapped continuation lines indent
        to line up under the text (not back to column 0) -- matches the
        leading spaces of manually-broken lines, or the width of a numbered
        marker ("1. ") for lines that wrap on their own."""
        text_widget.delete("1.0", "end")
        text_widget.insert("1.0", content)
        fnt = tkfont.Font(font=text_widget["font"])
        space_w = fnt.measure(" ")
        for i, line in enumerate(content.split("\n"), start=1):
            match = self._NUMBERED_LINE.match(line)
            if match:
                indent_chars = len(match.group(0))
            else:
                indent_chars = len(line) - len(line.lstrip(" "))
            if indent_chars:
                tag = f"hang{i}"
                text_widget.tag_configure(tag, lmargin1=0, lmargin2=indent_chars * space_w)
                text_widget.tag_add(tag, f"{i}.0", f"{i}.end")

        if highlight_title:
            text_widget.tag_configure("title", foreground=AMBER, font=(fnt.actual("family"), fnt.actual("size"), "bold"))
            text_widget.tag_add("title", "1.0", "1.end")

    def _calculate(self):
        lang = self.lang.get()
        units = self.units.get()
        band = self.band.get()
        antenna_type = self.antenna_type.get()
        freq_mhz = self._parse_custom_freq()
        wire_vf = wire_velocity_factor(self.antenna_wire.get())

        self.design = design_antenna(antenna_type, band, lang=lang, freq_mhz=freq_mhz, wire_vf=wire_vf)

        self._set_text_with_hanging_indent(self.results_text, format_summary(self.design, units=units, lang=lang), highlight_title=True)
        self._update_swr_display(lang)
        self._set_text_with_hanging_indent(self.advice_text, build_advice(self.design, units=units, lang=lang))

    def _export_svg(self):
        if not self.design:
            return
        path = filedialog.asksaveasfilename(defaultextension=".svg", filetypes=[("SVG", "*.svg")])
        if not path:
            return
        dwg = draw_antenna(self.design, units=self.units.get(), lang=self.lang.get())
        dwg.saveas(path)
        messagebox.showinfo(self._t("window_title"), self._t("saved").format(path=path))

    def _view_drawing(self):
        if not self.design:
            return
        lang = self.lang.get()
        label = antenna_type_label(self.antenna_type.get(), lang)
        title = self._t("drawing_window_title").format(label=label, band=self.design.band)
        show_drawing(self, self.design, units=self.units.get(), lang=lang,
                      window_title=title, not_to_scale_note=self._t("not_to_scale"))

    def _update_swr_display(self, lang):
        """Update SWR & matching display from design impedance."""
        if not self.design:
            return

        try:
            feedpoint_z = float(self.design.feedpoint_impedance_ohms)
            swr_data = impedance_to_swr_table(feedpoint_z, z0=50)

            # Format SWR display
            swr_text = (
                f"{self._t('swr_value')}: {swr_data['swr']}:1\n"
                f"{self._t('return_loss')}: {swr_data['return_loss_db']} dB\n"
                f"{self._t('gamma')}: {swr_data['gamma_magnitude']:.4f}\n"
                f"{self._t('power_reflected')}: {swr_data['power_reflected_percent']}%"
            )

            self.swr_text.config(state="normal")
            self.swr_text.delete(1.0, tk.END)
            self.swr_text.insert(1.0, swr_text)
            self.swr_text.config(state="disabled")
        except Exception as e:
            self.swr_text.config(state="normal")
            self.swr_text.delete(1.0, tk.END)
            self.swr_text.insert(1.0, f"Error: {str(e)}")
            self.swr_text.config(state="disabled")

    def _show_smith_info(self, lang):
        """Show Smith Chart explanation in popup."""
        info_text = {
            "en": """SMITH CHART - EXPLANATION

The Smith Chart is a graphical tool for visualizing complex impedance and
transmission line calculations. Each point represents an impedance value.

KEY CONCEPTS:

Center Point (middle):
• Represents 50Ω (perfect match, SWR 1:1)
• No reflection, 100% power transmitted

Your Antenna Point (AMBER crosshair):
• Shows your antenna's impedance
• Distance from center = how far from 50Ω match

Circles on Chart:
• Horizontal curves = Resistance circles (R = 0.5, 1, 2, 5Ω normalized)
• Vertical curves = Reactance arcs (X = inductive/capacitive)

SWR Circle (dashed AMBER line):
• All impedances on this circle have the same SWR
• Moving along circle changes impedance but keeps SWR constant
• Closer to center = lower SWR (better match)

INTERPRETATION:

If your point is at center → Perfect 50Ω match (SWR 1:1)
If your point is far from center → High SWR, antenna mismatch
If your point is to the right → Higher impedance (inductive)
If your point is to the left → Lower impedance (capacitive)

HOW TO USE:

1. Check your antenna impedance on the chart
2. Look at the SWR circle (dashed line around your point)
3. Use the circle to understand matching network needs
4. Closer to center always = better match
""",
            "nl": """SMITH CHART - UITLEG

De Smith Chart is een grafisch hulpmiddel voor het visualiseren van complexe
impedantie en transmissielijncalculates. Elk punt vertegenwoordigt een impedantiewaarde.

SLEUTELCONCEPTEN:

Centrumpunt (midden):
• Vertegenwoordigt 50Ω (perfecte aanpassing, SWR 1:1)
• Geen reflectie, 100% vermogen doorgestuurd

Uw Antenne Punt (AMBER kruisje):
• Toont de impedantie van uw antenne
• Afstand tot centrum = hoe ver van 50Ω aanpassing

Cirkels op kaart:
• Horizontale curves = Weerstand cirkels (R = 0.5, 1, 2, 5Ω genormaliseerd)
• Verticale curves = Reactantie bogen (X = inductief/capacitief)

SWR Cirkel (gestippelde AMBER lijn):
• Alle impedanties op deze cirkel hebben dezelfde SWR
• Langs de cirkel bewegen verandert impedantie maar houdt SWR gelijk
• Dichter bij centrum = lagere SWR (betere aanpassing)

INTERPRETATIE:

Als uw punt in het centrum ligt → Perfecte 50Ω aanpassing (SWR 1:1)
Als uw punt ver van centrum → Hoge SWR, antenne mismatch
Als uw punt aan de rechterkant → Hogere impedantie (inductief)
Als uw punt aan de linkerkant → Lagere impedantie (capacitief)

HOE TE GEBRUIKEN:

1. Controleer uw antenneimpedantie op de kaart
2. Kijk naar de SWR cirkel (gestippelde lijn rond uw punt)
3. Gebruik de cirkel om matchnetwerk behoeften te begrijpen
4. Dichter bij centrum is altijd beter
"""
        }

        popup = tk.Toplevel(self)
        popup.title("Smith Chart Explanation")
        popup.geometry("700x700")
        popup.configure(bg=BG)

        text_widget = tk.Text(
            popup, bg=PANEL_BG, fg=FG, font=FONT_COURIER, wrap="word",
            relief="flat", borderwidth=0, padx=15, pady=15, highlightthickness=0
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        text_widget.insert(1.0, info_text.get(lang, info_text["en"]))
        text_widget.config(state="disabled")

        close_btn = RoundedButton(popup, "Close", popup.destroy,
                                 PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
        close_btn.pack(pady=10)

    def _show_smith_chart(self):
        """Open Smith Chart in popup window."""
        if not self.design:
            messagebox.showwarning(self._t("error"), "Design antenna first")
            return

        try:
            popup = tk.Toplevel(self)
            popup.title("Smith Chart - " + antenna_type_label(self.antenna_type.get(), self.lang.get()))
            popup.geometry("700x900")
            popup.configure(bg=BG)

            lang = self.lang.get()

            # Title frame with explanation button
            title_frame = ttk.Frame(popup, style="Panel.TFrame")
            title_frame.pack(fill="x", padx=10, pady=(10, 5))

            title_label = ttk.Label(title_frame, text="Smith Chart (50Ω)", style="PanelTitle.TLabel")
            title_label.pack(anchor="w", side="left")

            info_btn = RoundedButton(title_frame, "? Info", lambda: self._show_smith_info(lang),
                                    PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 7, "bold"))
            info_btn.pack(side="right", padx=5)

            # Canvas for Smith Chart
            canvas = tk.Canvas(
                popup, width=680, height=450, bg=PANEL_BG, highlightthickness=0,
                relief="flat", borderwidth=0
            )
            canvas.pack(padx=10, pady=(5, 5))

            # Button frame
            btn_frame = ttk.Frame(popup, style="Panel.TFrame")
            btn_frame.pack(fill="x", padx=10, pady=(5, 10))

            close_btn = RoundedButton(btn_frame, "Close", popup.destroy,
                                     PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
            close_btn.pack()

            # Chart parameters
            center = (290, 290)
            radius = 250

            # Draw grid
            draw_smith_chart_grid(canvas, center, radius, grid_color=AMBER_DIM, line_width=1)

            # Plot antenna impedance
            feedpoint_z = float(self.design.feedpoint_impedance_ohms)
            z_complex = complex(feedpoint_z, 0)

            plot_impedance_point(canvas, z_complex, center, radius,
                                point_color=AMBER, point_size=10)

            # Plot SWR circle
            swr_data = impedance_to_swr_table(feedpoint_z, z0=50)
            if swr_data['swr'] > 1.0 and swr_data['swr'] < 999:
                plot_swr_circle(canvas, swr_data['swr'], center, radius,
                               circle_color=AMBER, line_width=2)

            # Add labels and info
            canvas.create_text(center[0], center[1] + radius + 20,
                              text="Smith Chart (50Ω)", fill=FG,
                              font=("Helvetica", 10, "bold"))

            info_text = (
                f"Z = {feedpoint_z:.1f}Ω | "
                f"SWR = {swr_data['swr']}:1 | "
                f"Γ = {swr_data['gamma_magnitude']:.3f}"
            )
            canvas.create_text(center[0], 15, text=info_text, fill=AMBER,
                              font=("Helvetica", 9))

        except Exception as e:
            messagebox.showerror(self._t("error"), f"Smith Chart error: {str(e)}")

    def _show_cable_loss(self):
        """Open Cable Loss Calculator in popup window."""
        try:
            lang = self.lang.get()
            freq_mhz = float(self.design.design_freq_mhz) if self.design else 14.0

            popup = tk.Toplevel(self)
            popup.title("Transmission Line Loss Calculator")
            popup.geometry("800x700")
            popup.configure(bg=BG)

            # Title
            title_label = ttk.Label(popup, text="Transmission Line Loss Analysis", style="PanelTitle.TLabel")
            title_label.pack(anchor="w", padx=10, pady=(10, 5))

            # Input frame
            input_frame = ttk.Frame(popup, style="Panel.TFrame")
            input_frame.pack(fill="x", padx=10, pady=5)

            # Frequency
            ttk.Label(input_frame, text="Frequency (MHz):", style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=3)
            freq_var = tk.StringVar(value=str(freq_mhz))
            freq_entry = ttk.Entry(input_frame, textvariable=freq_var, width=10)
            freq_entry.grid(row=0, column=1, sticky="w", padx=5, pady=3)

            # Distance
            ttk.Label(input_frame, text="Cable length (meters):", style="Panel.TLabel").grid(row=1, column=0, sticky="w", padx=5, pady=3)
            dist_var = tk.StringVar(value="30")
            dist_entry = ttk.Entry(input_frame, textvariable=dist_var, width=10)
            dist_entry.grid(row=1, column=1, sticky="w", padx=5, pady=3)

            # Cable type
            ttk.Label(input_frame, text="Cable type:", style="Panel.TLabel").grid(row=2, column=0, sticky="w", padx=5, pady=3)
            cable_var = tk.StringVar(value="RG-213")
            cable_combo = ttk.Combobox(input_frame, textvariable=cable_var,
                                       values=get_all_cable_types(), width=15, state="readonly")
            cable_combo.grid(row=2, column=1, sticky="w", padx=5, pady=3)

            # SWR
            ttk.Label(input_frame, text="Antenna SWR:", style="Panel.TLabel").grid(row=3, column=0, sticky="w", padx=5, pady=3)
            swr_var = tk.StringVar(value="1.5")
            swr_entry = ttk.Entry(input_frame, textvariable=swr_var, width=10)
            swr_entry.grid(row=3, column=1, sticky="w", padx=5, pady=3)

            # Calculate button
            def calculate_loss():
                try:
                    freq = float(freq_var.get())
                    distance_m = float(dist_var.get())
                    cable = cable_var.get()
                    swr = float(swr_var.get())

                    distance_ft = distance_m * 3.28084

                    # Calculate losses
                    cable_loss = calculate_cable_loss(cable, freq, distance_ft)

                    # SWR loss
                    if swr > 1.0:
                        gamma = (swr - 1) / (swr + 1)
                        swr_loss_db = -10 * __import__('math').log10(1 - gamma**2)
                    else:
                        swr_loss_db = 0

                    total_loss = cable_loss + swr_loss_db

                    # Power budget (assume 100W TX)
                    power_budget = power_budget_summary(100, cable, freq, distance_m, 2.15, swr)

                    # Update info panel
                    info_text.config(state="normal")
                    info_text.delete(1.0, tk.END)

                    result_text = (
                        f"Frequency: {freq} MHz\n"
                        f"Cable: {cable} ({distance_m}m = {distance_ft:.0f}ft)\n"
                        f"Antenna SWR: {swr}:1\n\n"
                        f"LOSSES:\n"
                        f"  Cable loss: {cable_loss:.2f} dB\n"
                        f"  SWR loss: {swr_loss_db:.2f} dB\n"
                        f"  Total loss: {total_loss:.2f} dB\n\n"
                        f"POWER BUDGET (100W TX):\n"
                        f"  Power at antenna: {power_budget['power_at_antenna_watts']:.1f}W\n"
                        f"  Efficiency: {100 - (10**(-total_loss/10))*100:.1f}%\n"
                        f"  EIRP: {power_budget['eirp_watts']:.2f}W\n"
                    )
                    info_text.insert(1.0, result_text)
                    info_text.config(state="disabled")

                except Exception as e:
                    info_text.config(state="normal")
                    info_text.delete(1.0, tk.END)
                    info_text.insert(1.0, f"Error: {str(e)}")
                    info_text.config(state="disabled")

            calc_btn = RoundedButton(input_frame, "Calculate", calculate_loss,
                                    PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
            calc_btn.grid(row=4, column=0, columnspan=2, pady=10)

            # Results panel
            info_text = tk.Text(
                popup, height=20, bg=PANEL_BG, fg=FG, font=FONT_COURIER,
                relief="flat", borderwidth=0, padx=15, pady=15, highlightthickness=0
            )
            info_text.pack(fill="both", expand=True, padx=10, pady=5)

            # Close button
            close_btn = RoundedButton(popup, "Close", popup.destroy,
                                     PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
            close_btn.pack(pady=10)

            # Auto-calculate on open
            calculate_loss()

        except Exception as e:
            messagebox.showerror(self._t("error"), f"Cable Loss error: {str(e)}")

    def _show_radiation_pattern(self):
        """Open Radiation Pattern polar plot in popup window."""
        if not self.design:
            messagebox.showwarning(self._t("error"), "Design antenna first")
            return

        try:
            antenna_type = self.design.antenna_type
            lang = self.lang.get()

            # Generate radiation pattern
            pattern = generate_azimuth_pattern(antenna_type)
            gain_info = calculate_gain_description(antenna_type)

            # Create popup
            popup = tk.Toplevel(self)
            popup.title("Radiation Pattern - " + antenna_type_label(antenna_type, lang))
            popup.geometry("750x800")
            popup.configure(bg=BG)

            # Title frame with info button
            title_frame = ttk.Frame(popup, style="Panel.TFrame")
            title_frame.pack(fill="x", padx=10, pady=(10, 5))

            title_label = ttk.Label(title_frame, text="Azimuth Radiation Pattern (Horizontal Plane)",
                                    style="PanelTitle.TLabel")
            title_label.pack(anchor="w", side="left")

            info_btn = RoundedButton(title_frame, "? Info", lambda: self._show_pattern_info(lang),
                                    PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 7, "bold"))
            info_btn.pack(side="right", padx=5)

            # Polar plot canvas
            canvas = tk.Canvas(
                popup, width=700, height=500, bg=PANEL_BG, highlightthickness=0,
                relief="flat", borderwidth=0
            )
            canvas.pack(padx=10, pady=(5, 5))

            # Draw polar grid and pattern
            center = (350, 250)
            radius = 200

            draw_polar_grid(canvas, center, radius, grid_color=AMBER_DIM, text_color=AMBER_DIM)
            plot_azimuth_pattern(canvas, pattern, center, radius, line_color=AMBER,
                                line_width=2, fill_color=None)

            # Add antenna label
            canvas.create_text(center[0], center[1] + radius + 25,
                              text="Azimuth Pattern (Top View)", fill=FG,
                              font=("Helvetica", 9, "bold"))

            # Information panel
            info_frame = ttk.Frame(popup, style="Panel.TFrame")
            info_frame.pack(fill="x", padx=10, pady=(5, 0))

            info_text = (
                f"Gain: {gain_info['gain_dbi']:.1f} dBi  •  "
                f"F/B Ratio: {gain_info['f_b_ratio_db']:.1f} dB  •  "
                f"Take-off: {gain_info['takeoff_angle_deg']:.0f}°"
            )

            info_label = ttk.Label(info_frame, text=info_text, style="Panel.TLabel")
            info_label.pack(anchor="w", padx=10, pady=10)

            # Close button
            close_btn = RoundedButton(popup, "Close", popup.destroy,
                                     PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
            close_btn.pack(pady=(0, 10))

        except Exception as e:
            messagebox.showerror(self._t("error"), f"Pattern error: {str(e)}")

    def _show_pattern_info(self, lang):
        """Show Radiation Pattern explanation."""
        info_text = {
            "en": """RADIATION PATTERN - EXPLANATION

The radiation pattern shows how an antenna radiates energy in different
directions. The plot is viewed from above (azimuth/horizontal plane).

KEY CONCEPTS:

Distance from Center:
• Shows antenna directivity and gain
• Farther from center = stronger radiation in that direction
• Closer to center = weaker radiation

Polar Grid:
• Center = 0 dBi reference (isotropic)
• Circles = 3dB, 6dB, 10dB power loss
• Radial lines = compass directions (0°, 45°, 90°, ...)

Pattern Shape:

Circular (Omnidirectional):
• Dipole, vertical radiates equally in all directions
• No preferred azimuth direction
• 0 dB Front-to-Back ratio

Cardioid/Directional:
• Yagi, loop, end-fire antennas
• Stronger in forward direction, weaker in back
• High Front-to-Back ratio

Antenna Specifications:

Gain (dBi):
• Relative to isotropic radiator
• Higher gain = more concentrated energy
• Dipole = 2.15 dBi (0 dBd reference)

F/B Ratio (Front-to-Back):
• How much stronger forward than backward
• Higher = more directional
• 0 dB = omnidirectional, 15 dB = very directional

Take-off Angle:
• Radiation angle from horizontal
• Low (10-20°) = better for DX
• High (40-60°) = better for local

PRACTICAL USE:

1. Look at pattern shape to understand directivity
2. Check gain for power and signal strength
3. Use F/B ratio to reject unwanted directions
4. Adjust antenna orientation for best coverage
""",
            "nl": """STRALINGSPATROON - UITLEG

Het stralingspatroon toont hoe een antenne energie in verschillende richtingen
uitstraalt. De plot wordt van bovenaf bekeken (azimut/horizontaal vlak).

SLEUTELCONCEPTEN:

Afstand tot Centrum:
• Toont antennegerichtheid en versterking
• Verder van centrum = sterkere straling in die richting
• Dichter bij centrum = zwakkere straling

Polaire Raster:
• Centrum = 0 dBi referentie (isotroop)
• Cirkels = 3dB, 6dB, 10dB vermogensverlies
• Radiale lijnen = kompasrichtingen (0°, 45°, 90°, ...)

Patroonvorm:

Circulair (Omnidirectionaal):
• Dipole, verticale stralen gelijk in alle richtingen
• Geen voorkeur richting
• 0 dB Voor-naar-Achter verhouding

Cardioid/Gericht:
• Yagi, loop, end-fire antennes
• Sterker vooruit, zwakker achter
• Hoge Voor-naar-Achter verhouding

Antenne Specificaties:

Versterking (dBi):
• Relatief tot isotroop radiator
• Hogere versterking = meer geconcentreerde energie
• Dipole = 2.15 dBi (0 dBd referentie)

V/A Verhouding (Voor-naar-Achter):
• Hoeveel sterker vooruit dan achter
• Hoger = directer gericht
• 0 dB = omnidirectionaal, 15 dB = zeer gericht

Straalhhoek:
• Stralingshoek vanaf horizontaal
• Laag (10-20°) = beter voor DX
• Hoog (40-60°) = beter voor lokaal

PRAKTISCH GEBRUIK:

1. Kijk naar patroonvorm om gerichte werking te begrijpen
2. Controleer versterking voor vermogen en signaalsterkte
3. Gebruik V/A verhouding om ongewenste richtingen af te wijzen
4. Pas antenneoriëntatie aan voor beste dekking
"""
        }

        popup = tk.Toplevel(self)
        popup.title("Radiation Pattern Explanation")
        popup.geometry("700x800")
        popup.configure(bg=BG)

        text_widget = tk.Text(
            popup, bg=PANEL_BG, fg=FG, font=FONT_COURIER, wrap="word",
            relief="flat", borderwidth=0, padx=15, pady=15, highlightthickness=0
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        text_widget.insert(1.0, info_text.get(lang, info_text["en"]))
        text_widget.config(state="disabled")

        close_btn = RoundedButton(popup, "Close", popup.destroy,
                                 PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
        close_btn.pack(pady=10)

    def _show_swr_info(self, lang):
        """Show SWR explanation in popup."""
        info_text = {
            "en": """SWR & IMPEDANCE MATCHING - EXPLANATION

SWR (Standing Wave Ratio) measures how well your antenna is matched to your
transmitter through the 50Ω coaxial cable. Lower SWR is better.

KEY METRICS:

SWR Ratio (e.g., 1.46:1):
• 1:1 = Perfect match (50Ω antenna on 50Ω cable, ideal)
• 1.5:1 = Good match (acceptable for most applications)
• 2:1 = Fair match (some power reflected, acceptable)
• 3:1 or higher = Poor match (many systems won't transmit)

Return Loss (e.g., 14.56 dB):
• Measures how much power is reflected back
• Higher dB value = better match
• -14 dB return loss = same SWR as 1.46:1
• -20 dB = very good match (SWR ≤ 1.2:1)

Reflection Coefficient Gamma (Γ):
• Magnitude between 0 and 1
• 0 = perfect match (no reflection)
• 1 = complete mismatch (total reflection)
• Formula: Γ = (Z - 50) / (Z + 50)

Power Reflected (%):
• Percentage of transmit power reflected back
• 3.5% reflected = 96.5% transmitted to antenna
• Formula: Reflected = |Γ|² × 100

FREQUENCY SWEEP INTERPRETATION:

Resonance Frequency:
• The frequency where SWR is lowest
• Best matching point in the band
• Example: 14.0 MHz for a 20m dipole

Bandwidth:
• Frequency range where SWR ≤ 1.5:1
• Wider bandwidth = more usable frequency range
• Example: 13.8 - 14.4 MHz = 0.6 MHz bandwidth

SWR Curve:
• Shows how SWR changes across the band
• V-shaped curve with minimum at resonance
• Steeper sides = narrower bandwidth

PRACTICAL USE:

• SWR 1:1 to 1.5:1 = No tuner needed
• SWR 1.5:1 to 2:1 = Tuner recommended
• SWR above 2:1 = Tuner required or redesign antenna
• Matching networks (L, T, Pi) can improve SWR at one frequency
""",
            "nl": """SWR & IMPEDANTIE AANPASSING - UITLEG

SWR (Staande Golf Verhouding) meet hoe goed uw antenne is aangepast aan uw
zender via de 50Ω coaxiale kabel. Lagere SWR is beter.

SLEUTELMETRIEKEN:

SWR Verhouding (bijv. 1,46:1):
• 1:1 = Perfecte aanpassing (50Ω antenne op 50Ω kabel, ideaal)
• 1,5:1 = Goede aanpassing (acceptabel voor meeste toepassingen)
• 2:1 = Redelijke aanpassing (enig vermogen gereflecteerd, acceptabel)
• 3:1 of hoger = Slechte aanpassing (veel systemen zenden niet)

Return Loss (bijv. 14,56 dB):
• Meet hoeveel vermogen wordt gereflecteerd
• Hogere dB waarde = betere aanpassing
• -14 dB return loss = zelfde SWR als 1,46:1
• -20 dB = zeer goede aanpassing (SWR ≤ 1,2:1)

Reflectiecoëfficiënt Gamma (Γ):
• Magnitude tussen 0 en 1
• 0 = perfecte aanpassing (geen reflectie)
• 1 = volledige mismatch (totale reflectie)
• Formule: Γ = (Z - 50) / (Z + 50)

Gereflecteerd Vermogen (%):
• Percentage zendvermogen dat terugkaatst
• 3,5% gereflecteerd = 96,5% naar antenne
• Formule: Gereflecteerd = |Γ|² × 100

FREQUENTIE SWEEP INTERPRETATIE:

Resonantiefrequentie:
• De frequentie waar SWR het laagst is
• Beste aanpassingspunt in de band
• Voorbeeld: 14,0 MHz voor een 20m dipole

Bandbreedte:
• Frequentiebereik waar SWR ≤ 1,5:1
• Breder bereik = meer bruikbaar frequentiebereik
• Voorbeeld: 13,8 - 14,4 MHz = 0,6 MHz bandbreedte

SWR Curve:
• Toont hoe SWR verandert over de band
• V-vormige curve met minimum bij resonantie
• Steilere zijkanten = snaller bereik

PRAKTISCH GEBRUIK:

• SWR 1:1 tot 1,5:1 = Geen tuner nodig
• SWR 1,5:1 tot 2:1 = Tuner aanbevolen
• SWR hoger dan 2:1 = Tuner vereist of antenne herontwerpen
• Matchnetwerken (L, T, Pi) kunnen SWR op één frequentie verbeteren
"""
        }

        popup = tk.Toplevel(self)
        popup.title("SWR & Impedance Matching Explanation")
        popup.geometry("700x800")
        popup.configure(bg=BG)

        text_widget = tk.Text(
            popup, bg=PANEL_BG, fg=FG, font=FONT_COURIER, wrap="word",
            relief="flat", borderwidth=0, padx=15, pady=15, highlightthickness=0
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        text_widget.insert(1.0, info_text.get(lang, info_text["en"]))
        text_widget.config(state="disabled")

        close_btn = RoundedButton(popup, "Close", popup.destroy,
                                 PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
        close_btn.pack(pady=10)

    def _show_sweep_window(self):
        """Open SWR Sweep in popup window."""
        if not self.design:
            messagebox.showwarning(self._t("error"), "Design antenna first")
            return

        try:
            antenna_type = self.antenna_type.get()
            band = self.band.get()
            wire_vf = wire_velocity_factor(self.antenna_wire.get())

            # Get band frequency range
            if band not in BANDS_MHZ:
                messagebox.showwarning(self._t("error"), "Invalid band")
                return

            freq_range = BANDS_MHZ[band]
            freq_start = freq_range[0]
            freq_end = freq_range[1]

            # Perform sweep
            sweep = sweep_antenna_response(antenna_type, band, freq_start,
                                          freq_end, step_mhz=0.1, wire_vf=wire_vf)

            if not sweep or "frequencies" not in sweep:
                messagebox.showwarning(self._t("error"), "Sweep data unavailable")
                return

            # Create popup
            popup = tk.Toplevel(self)
            popup.title("SWR Sweep - " + antenna_type_label(antenna_type, self.lang.get()))
            popup.geometry("800x750")
            popup.configure(bg=BG)

            lang = self.lang.get()

            # Title frame with info button
            title_frame = ttk.Frame(popup, style="Panel.TFrame")
            title_frame.pack(fill="x", padx=10, pady=(10, 5))

            title_label = ttk.Label(title_frame, text="SWR Sweep Analysis", style="PanelTitle.TLabel")
            title_label.pack(anchor="w", side="left")

            info_btn = RoundedButton(title_frame, "? Info", lambda: self._show_swr_info(lang),
                                    PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 7, "bold"))
            info_btn.pack(side="right", padx=5)

            # Canvas for SWR curve
            canvas = tk.Canvas(
                popup, width=780, height=380, bg=PANEL_BG, highlightthickness=0,
                relief="flat", borderwidth=0
            )
            canvas.pack(padx=10, pady=(5, 5))

            # Plot SWR curve
            freqs = sweep["frequencies"]
            swrs = sweep["swr_values"]

            canvas_w = 780
            canvas_h = 380
            margin = 50

            freq_min, freq_max = min(freqs), max(freqs)
            swr_max = min(max(swrs), 5.0)

            # Draw grid
            for i in range(0, int(swr_max) + 1):
                y = canvas_h - margin - (i / swr_max) * (canvas_h - 2 * margin)
                canvas.create_line(margin, y, canvas_w - margin, y,
                                  fill=AMBER_DIM, width=0.5, dash=(2, 2))
                canvas.create_text(15, y, text=str(i), fill=FG,
                                  font=("Helvetica", 8), anchor="e")

            # Draw axes
            canvas.create_line(margin, canvas_h - margin, canvas_w - margin,
                              canvas_h - margin, fill=AMBER, width=2)
            canvas.create_line(margin, margin, margin, canvas_h - margin,
                              fill=AMBER, width=2)

            # Axis labels
            canvas.create_text(canvas_w // 2, canvas_h - 10, text="Frequency (MHz)",
                              fill=FG, font=("Helvetica", 9))
            canvas.create_text(15, canvas_h // 2, text="SWR", fill=FG,
                              font=("Helvetica", 9), angle=90)

            # Plot SWR curve
            for i in range(len(freqs) - 1):
                x1 = margin + (freqs[i] - freq_min) / (freq_max - freq_min) * (canvas_w - 2 * margin)
                y1 = canvas_h - margin - min(swrs[i], swr_max) / swr_max * (canvas_h - 2 * margin)

                x2 = margin + (freqs[i + 1] - freq_min) / (freq_max - freq_min) * (canvas_w - 2 * margin)
                y2 = canvas_h - margin - min(swrs[i + 1], swr_max) / swr_max * (canvas_h - 2 * margin)

                canvas.create_line(x1, y1, x2, y2, fill=AMBER, width=2)

            # Mark resonance
            res_freq = sweep["resonance_freq"]
            res_x = margin + (res_freq - freq_min) / (freq_max - freq_min) * (canvas_w - 2 * margin)
            res_y = canvas_h - margin - sweep["min_swr"] / swr_max * (canvas_h - 2 * margin)
            canvas.create_oval(res_x - 4, res_y - 4, res_x + 4, res_y + 4,
                              fill=AMBER, outline=AMBER)

            # Info panel
            info_frame = ttk.Frame(popup, style="Panel.TFrame")
            info_frame.pack(fill="x", padx=10, pady=(5, 0))

            bw_low, bw_high = sweep["bandwidth_3db"]
            bw = bw_high - bw_low

            info_text = (
                f"Resonance: {res_freq} MHz (SWR {sweep['min_swr']}:1)  •  "
                f"Bandwidth (SWR ≤1.5): {bw_low}-{bw_high} MHz ({bw:.1f} MHz)"
            )

            info_label = ttk.Label(info_frame, text=info_text, style="Panel.TLabel")
            info_label.pack(anchor="w", padx=10, pady=10)

            # Close button
            close_btn = RoundedButton(popup, "Close", popup.destroy,
                                     BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
            close_btn.pack(pady=(0, 10))

        except Exception as e:
            messagebox.showerror(self._t("error"), f"Sweep error: {str(e)}")

    def _show_balun_help(self):
        """Show balun/unun construction guide popup."""
        lang = self.lang.get()

        help_text = {
            "en": """BALUN/UNUN CONSTRUCTION GUIDE

1:1 CURRENT BALUN (Dipoles, Balanced Antennas)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use: Center-fed dipoles, quad loops, balanced antennas
Core: FT240-43, FT240-52 (HF bands)
Construction:
• Wind 10-15 turns of coax through toroid
• Connect center to balanced element
• Connect shield to radial/ground

1:1 VOLTAGE BALUN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use: High impedance antennas (G5RV, multiband doublets)
Core: Ferrite rod or binocular core
Primary winding: 10 turns
Secondary winding: 10 turns (isolated)

2:1 UNUN (Matching 50Ω to 200Ω)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use: Loop antennas, some end-fed variants
Construction:
• Primary: 10 turns on FT240-43
• Secondary: 5 turns on same core
• Impedance transformation: Z_out = 4 × Z_in

4:1 CURRENT UNUN (Matching 50Ω to 12.5Ω)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use: Small loops, some delta loops
Construction:
• Primary: 10 turns
• Secondary: 5 turns
• For current balun: use parallel secondary windings
• For unun: use series connection

9:1 UNUN (Matching 50Ω to ~450Ω)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use: End-fed half-wave antennas, EFHW
Core: FT240-43, FT240-52
Construction:
• Primary: 10 turns (thin wire)
• Secondary: 3 turns (thicker wire for current handling)
• Critical for end-fed designs
• Provides impedance matching + isolation

16:1 UNUN (Matching 50Ω to 3.1kΩ)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use: Random-length end-fed antennas, tuned end-feds
Core: FT240-43, FT240-52, or FT82-43
Construction:
• Primary: 10 turns
• Secondary: 2-3 turns (for current handling)
• Turns ratio squared = impedance ratio (4² = 16)

49:1 UNUN (Matching 50Ω to ~2450Ω)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use: Long-wire receive antennas, some end-fed designs
Core: FT240-43 or larger for power handling
Construction:
• Primary: 10 turns
• Secondary: 2 turns (very heavy wire for current)
• Turns ratio = 7:1 (7² = 49)
• Excellent for high-impedance loads

64:1 UNUN (Matching 50Ω to 3200Ω)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use: High-impedance random-wire antennas
Core: FT240-43 or FT82-43
Construction:
• Primary: 10 turns
• Secondary: 1.25 turns (wrapped half-turn twice)
• Turns ratio = 8:1 (8² = 64)
• For very high impedance loads

IMPEDANCE MATCHING FORMULA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For any transformer ratio N:
Z_out = Z_in × N²

Examples:
• 4:1 = 50 × 16 = 800Ω
• 9:1 = 50 × 81 = 4050Ω
• 16:1 = 50 × 256 = 12,800Ω
• 49:1 = 50 × 2401 = 120kΩ
• 64:1 = 50 × 4096 = 204kΩ

MATERIAL SELECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HF Bands (1.8-30 MHz):  FT240-43 or FT240-52
VHF/UHF (50-450 MHz):   Smaller cores (FT50-43)
Low Bands (160m, 80m):  Larger cores for better flux handling

KEY CONSTRUCTION TIPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Use good quality coax (RG-58, RG-213)
✓ Keep winding wire gauge appropriate for power level
✓ Wind toroid in same direction for all windings
✓ Use #18-20 wire for HF bands
✓ Seal/weatherproof with silicone or epoxy
✓ Mount in PVC or metal enclosure
✓ Test with antenna analyzer (if available)
✓ Add ferrite beads for EMI suppression""",

            "nl": """BALUN/UNUN CONSTRUCTIEGIDS

1:1 STROOMBALUN (Dipolen, Gebalanceerde Antennes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gebruik: Middengevoed dipolen, quad loops, gebalanceerde antennes
Kern: FT240-43, FT240-52 (HF-banden)
Constructie:
• 10-15 windingen coax door toroid
• Verbind midden met gebalanceerd element
• Verbind scherm met radiale/aarde

1:1 SPANNINGSBALUN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gebruik: Hoge impedantie-antennes (G5RV, multiband doublets)
Kern: Ferrietstaaaf of binoculaire kern
Primaire winding: 10 windingen
Secundaire winding: 10 windingen (geïsoleerd)

2:1 UNUN (50Ω naar 200Ω)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gebruik: Loop antennes, sommige end-fed varianten
Constructie:
• Primair: 10 windingen op FT240-43
• Secundair: 5 windingen op dezelfde kern
• Impedantietransformatie: Z_uit = 4 × Z_in

4:1 STROOMUNUN (50Ω naar 12,5Ω)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gebruik: Kleine loops, sommige delta loops
Constructie:
• Primair: 10 windingen
• Secundair: 5 windingen
• Voor stroombalun: parallel secundaire windingen
• Voor unun: serieschakeling

9:1 UNUN (50Ω naar ~450Ω)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gebruik: End-fed halve-golf antennes, EFHW
Kern: FT240-43, FT240-52
Constructie:
• Primair: 10 windingen (dunne draad)
• Secundair: 3 windingen (dikkere draad voor stroomvermogen)
• Kritisch voor end-fed designs
• Biedt impedantietransformatie + isolatie

16:1 UNUN (50Ω naar 3,1kΩ)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gebruik: Random-length end-fed antennes, afgestemde end-feds
Kern: FT240-43, FT240-52, of FT82-43
Constructie:
• Primair: 10 windingen
• Secundair: 2-3 windingen (voor stroomvermogen)
• Windingsverhouding kwadraat = impedantieverhouding (4² = 16)

49:1 UNUN (50Ω naar ~2450Ω)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gebruik: Ontvangst lange-draad antennes, sommige end-fed designs
Kern: FT240-43 of groter voor vermogensvermogen
Constructie:
• Primair: 10 windingen
• Secundair: 2 windingen (zeer dikke draad voor stroom)
• Windingsverhouding = 7:1 (7² = 49)
• Uitstekend voor hoge-impedantie belastingen

64:1 UNUN (50Ω naar 3200Ω)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gebruik: Hoge-impedantie random-wire antennes
Kern: FT240-43 of FT82-43
Constructie:
• Primair: 10 windingen
• Secundair: 1,25 windingen (halve windingen tweemaal)
• Windingsverhouding = 8:1 (8² = 64)
• Voor zeer hoge impedantie belastingen

IMPEDANTIE TRANSFORMATIE FORMULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Voor elke transformator verhouding N:
Z_uit = Z_in × N²

Voorbeelden:
• 4:1 = 50 × 16 = 800Ω
• 9:1 = 50 × 81 = 4050Ω
• 16:1 = 50 × 256 = 12.800Ω
• 49:1 = 50 × 2401 = 120kΩ
• 64:1 = 50 × 4096 = 204kΩ

MATERIAALKEUZE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HF-banden (1,8-30 MHz):   FT240-43 of FT240-52
VHF/UHF (50-450 MHz):     Kleinere kernen (FT50-43)
Lage banden (160m, 80m):  Grotere kernen voor beter flux

CONSTRUCTIE-TIPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Gebruik kwaliteit-coax (RG-58, RG-213)
✓ Draaddikte passend aan vermogensniveau
✓ Wind toroid in dezelfde richting
✓ Gebruik #18-20 draad voor HF-banden
✓ Seal met siliconen of epoxy
✓ Mount in PVC of metalen behuizing
✓ Test met antenne-analyzer (indien beschikbaar)
✓ Voeg ferrietparels toe voor EMI-suppressie"""
        }

        # Create popup window
        popup = tk.Toplevel(self)
        popup.title(self._t("balun_help"))
        popup.geometry("700x600")
        popup.resizable(True, True)
        popup.configure(bg=BG)

        # Create text widget with scrollbar
        text_frame = ttk.Frame(popup, style="Panel.TFrame")
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        text_widget = tk.Text(
            text_frame, height=25, bg=PANEL_BG, fg=FG, font=("Courier", 9),
            relief="flat", borderwidth=0, padx=10, pady=10, wrap="word"
        )
        text_widget.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        text_widget.config(yscrollcommand=scrollbar.set)

        text_widget.insert(1.0, help_text.get(lang, help_text["en"]))
        text_widget.config(state="disabled")

        # Close button
        close_btn = RoundedButton(popup, "Close" if lang == "en" else "Sluiten", popup.destroy,
                                 PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 9, "bold"))
        close_btn.pack(pady=10)



if __name__ == "__main__":
    app = AntennaDesignerApp()
    app.mainloop()
