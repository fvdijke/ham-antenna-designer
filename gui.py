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

import math
import re
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

import calculators  # noqa: F401 -- registers all antenna calculator types
from build_notes import build_advice
from data_store import (
    BANDS_MHZ, CABLES, WIRES, SHAPE_FAMILIES, STANDALONE_TYPES,
    antenna_type_for, antenna_type_label, bands_for, set_region, wave_fractions_for,
    wire_length_factor,
)
from drawing import draw_antenna
from format_text import format_summary
from i18n import SHAPE_FAMILY_LABELS, WAVE_FRACTION_LABELS, WIRE_LABELS
from registry import design as design_antenna
from settings import load_settings, save_settings
from version import __version__
from widgets import LogoCanvas, RoundedButton, RoundedPanel, logo_image
from canvas_view import show_drawing
from swr_calc import coax_side_impedance, impedance_to_swr_table
from smith_chart import (
    draw_smith_chart_grid, plot_impedance_point, plot_swr_circle,
)
from freq_sweep import sweep_design
from radiation_pattern import calculate_gain_description, compute_pattern, default_ground, default_height
from polar_plot import draw_db_polar
from transmissionline_loss import (
    cable_impedance, calculate_cable_loss, power_budget_summary, get_all_cable_types
)
from matching_networks import (
    calculate_swr_from_impedance, format_impedance, parse_impedance, suggest_matching_network,
)
from popup_text import pt

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


# Wire notes in wires.json are English, cable notes in cables.json Dutch:
# translate phrase by phrase to the UI language.
_NOTES_NL = {
    "Budget friendly, common": "Voordelig, veel gebruikt", "Budget option": "Voordelige keuze",
    "Corrosion resistant": "Corrosiebestendig", "Durable": "Duurzaam", "Easy to bend": "Makkelijk te buigen",
    "Flexible, many strands": "Soepel, veel aders", "High frequency": "Hoge frequentie",
    "High strength": "Zeer sterk", "High temperature": "Hoge temperatuur", "High-end": "Topklasse",
    "Lightweight, affordable": "Licht en betaalbaar", "Professional grade": "Professionele kwaliteit",
    "Standard option": "Standaardkeuze", "Stiff, mechanically strong": "Stijf, mechanisch sterk",
    "Strength + insulation": "Sterk + geïsoleerd", "Twisted pair": "Getwist paar", "UV resistant": "UV-bestendig",
    "Very flexible": "Zeer soepel", "WD-1/TT standard": "WD-1/TT-standaard", "Winding wire": "Wikkeldraad",
}
_NOTES_EN = {
    "Massief PE": "Solid PE", "Afhankelijk van fabrikant": "depends on the manufacturer",
    "Japanse equivalent LMR-240": "Japanese equivalent of LMR-240", "Populair bij zendamateurs": "popular with hams",
    "Populaire HF-kabel": "popular HF cable", "Veel gebruikt voor VHF/UHF": "widely used on VHF/UHF",
    "Zeer lage demping": "very low loss", "Zeer populair": "very popular", "Professioneel": "professional",
    "Dubbele afscherming": "double shield", "Dunne coax": "thin coax", "Klassieke dikke coax": "classic thick coax",
    "Robuuste HF-kabel": "rugged HF cable", "TV/coax": "TV coax", "Zeer veel gebruikt": "very widely used",
    "Laagste verlies": "lowest loss", "Zeer laag verlies": "very low loss", "Hoge temperatuur": "high temperature",
    "Veel gebruikt voor pigtails": "widely used for pigtails",
}


def _note(text: str, lang: str) -> str:
    table = _NOTES_EN if lang == "en" else _NOTES_NL
    if text in table:
        return table[text]
    return " - ".join(table.get(part, part) for part in text.split(" - "))


def _rl(value) -> str:
    """Return loss for display: a perfect match has infinite return loss."""
    return "∞ dB" if value == float("inf") else f"{value} dB"


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
        "wire_vf_label": "VF {vf} -> length x{factor} vs. bare wire ({notes})",
        "region": "IARU region",
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
        "wire_vf_label": "VF {vf} -> lengte x{factor} t.o.v. blanke draad ({notes})",
        "region": "IARU-regio",
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
    def __init__(self, lang: str | None = None):
        super().__init__()
        self.design = None
        saved = load_settings()
        # --lang (bijv. vanuit HAMIOS) gaat voor de eigen opgeslagen voorkeur
        self.lang = tk.StringVar(value=lang if lang in UI_TEXT else saved["lang"])
        self.units = tk.StringVar(value=saved["units"])
        self.region = tk.StringVar(value=saved["region"] if saved["region"] in ("1", "2") else "1")
        set_region(self.region.get())
        self._band_display_to_key = {}
        self.band = tk.StringVar(value="20m")
        self.primary_choice = tk.StringVar(value="vertical")
        self.wave_fraction = tk.StringVar(value="1/4")
        self.antenna_type = tk.StringVar(value="vertical_quarter_wave")
        self.antenna_wire = tk.StringVar(value=next(iter(WIRES)))
        self.feed_cable = tk.StringVar(value=next(iter(CABLES)))

        self._configure_style()
        # window/taskbar icon (also used by every popup window)
        self._icons = [logo_image(self, 64), logo_image(self, 32)]
        self.iconphoto(True, *self._icons)
        self.title(f"{UI_TEXT[self.lang.get()]['window_title']}  v{__version__}")
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
            controls, textvariable=self.band_combo_var, state="readonly", width=20,
        )
        self.band_combo.grid(row=0, column=3, padx=10, pady=10, sticky="w")
        self.band_combo.bind("<<ComboboxSelected>>", self._on_band_change)

        self.custom_freq_label = ttk.Label(controls, text=self._t("custom_freq"), style="Panel.TLabel")
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

        region_frame = ttk.Frame(controls, style="Panel.TFrame")
        region_frame.grid(row=2, column=4, padx=10, pady=(0, 10), sticky="w")
        self.region_label = ttk.Label(region_frame, text=self._t("region"), style="Panel.TLabel")
        self.region_label.grid(row=0, column=0, padx=(0, 8))
        for i, val in enumerate(["1", "2"]):
            rb = ttk.Radiobutton(region_frame, text=val, value=val, variable=self.region, command=self._on_region_change)
            rb.grid(row=0, column=i + 1, padx=(0, 6))

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

        self.match_btn = RoundedButton(chart_buttons_frame, "Matching", self._show_matching_networks,
                                      PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
        self.match_btn.pack(side="left", padx=5)

        self.briefing_btn = RoundedButton(chart_buttons_frame, "Final Briefing", self._show_final_briefing,
                                         PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
        self.briefing_btn.pack(side="left", padx=5)

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
            text=self._t("vf_label").format(vf=cable["velocity_factor"], notes=_note(cable["notes"], self.lang.get()))
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
        key = self.antenna_wire.get()
        wire = WIRES[key]
        self.wire_vf_label.config(
            text=self._t("wire_vf_label").format(
                vf=wire["velocity_factor"], factor=f"{wire_length_factor(key):.3f}", notes=_note(wire["notes"], self.lang.get()))
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
        self._refresh_band_combo()

    def _refresh_band_combo(self):
        """Fill the band list for the current antenna type and IARU region.
        Keeps the selected band when it is still offered, else falls back
        to 20m (or the first band in the list)."""
        if not hasattr(self, "band_combo"):
            return
        bands = bands_for(self.antenna_type.get())
        self._band_display_to_key = {_band_display(b): b for b in bands}
        self.band_combo["values"] = list(self._band_display_to_key)
        if self.band.get() not in bands:
            self.band.set("20m" if "20m" in bands else bands[0])
        self.band_combo_var.set(_band_display(self.band.get()))

    def _on_region_change(self):
        set_region(self.region.get())
        save_settings(region=self.region.get())
        self._refresh_band_combo()
        self._calculate()

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
        self.band.set(self._band_display_to_key[self.band_combo_var.get()])
        self._calculate()

    def _on_units_change(self):
        save_settings(units=self.units.get())
        self._calculate()

    def _on_lang_change(self):
        save_settings(lang=self.lang.get())
        t = UI_TEXT[self.lang.get()]
        self.title(f"{t['window_title']}  v{__version__}")
        self.title_label.config(text=t["window_title"])
        self.type_label.config(text=t["antenna_type"])
        self.wave_label.config(text=t["wave"])
        self.band_label.config(text=t["band"])
        self.units_label.config(text=t["units"])
        self.lang_label.config(text=t["language"])
        self.region_label.config(text=t["region"])
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
        self._update_wire_label()
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
        wire_vf = wire_length_factor(self.antenna_wire.get())

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
        dwg = draw_antenna(self.design, units=self.units.get(), lang=self.lang.get(), cable=self.feed_cable.get())
        dwg.saveas(path)
        messagebox.showinfo(self._t("window_title"), self._t("saved").format(path=path))

    def _view_drawing(self):
        if not self.design:
            return
        lang = self.lang.get()
        label = antenna_type_label(self.antenna_type.get(), lang)
        title = self._t("drawing_window_title").format(label=label, band=self.design.band)
        show_drawing(self, self.design, units=self.units.get(), lang=lang,
                      window_title=title, not_to_scale_note=self._t("not_to_scale"), cable=self.feed_cable.get())

    def _update_swr_display(self, lang):
        """Update SWR & matching display from design impedance."""
        if not self.design:
            return

        try:
            feedpoint_z = coax_side_impedance(self.design)  # after the balun/unun
            swr_data = impedance_to_swr_table(feedpoint_z, z0=50)

            # Format SWR display
            swr_text = (
                f"{self._t('swr_value')}: {swr_data['swr']}:1\n"
                f"{self._t('return_loss')}: {_rl(swr_data['return_loss_db'])}\n"
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
        popup.title(pt(self.lang.get(), "smith_expl_title"))
        popup.geometry("700x700")
        popup.configure(bg=BG)

        text_widget = tk.Text(
            popup, bg=PANEL_BG, fg=FG, font=FONT_COURIER, wrap="word",
            relief="flat", borderwidth=0, padx=15, pady=15, highlightthickness=0
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        text_widget.insert(1.0, info_text.get(lang, info_text["en"]))
        text_widget.config(state="disabled")

        close_btn = RoundedButton(popup, pt(self.lang.get(), "close"), popup.destroy,
                                 PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
        close_btn.pack(pady=10)

    def _show_smith_chart(self):
        """Open Smith Chart in popup window."""
        if not self.design:
            messagebox.showwarning(self._t("error"), pt(self.lang.get(), "design_first"))
            return

        try:
            popup = tk.Toplevel(self)
            popup.title(pt(self.lang.get(), "smith_title") + " - " + antenna_type_label(self.antenna_type.get(), self.lang.get()))
            popup.geometry("800x800")
            popup.configure(bg=BG)


            # Title
            title_label = ttk.Label(popup, text=pt(self.lang.get(), "smith_heading"), style="PanelTitle.TLabel")
            title_label.pack(anchor="w", padx=10, pady=(10, 5))

            # Canvas for Smith Chart
            canvas = tk.Canvas(
                popup, width=750, height=380, bg=PANEL_BG, highlightthickness=0,
                relief="flat", borderwidth=0
            )
            canvas.pack(padx=10, pady=(5, 5))

            # Button frame
            btn_frame = ttk.Frame(popup, style="Panel.TFrame")
            btn_frame.pack(fill="x", padx=10, pady=(5, 10))

            close_btn = RoundedButton(btn_frame, pt(self.lang.get(), "close"), popup.destroy,
                                     PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
            close_btn.pack()

            # Chart parameters
            center = (375, 190)
            radius = 160

            # Draw grid
            draw_smith_chart_grid(canvas, center, radius, grid_color=AMBER_DIM, line_width=1)

            # Plot antenna impedance
            feedpoint_z = coax_side_impedance(self.design)  # as seen on the coax
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
                              text=pt(self.lang.get(), "smith_canvas"), fill=FG,
                              font=("Helvetica", 10, "bold"))

            info_text = (
                f"Z = {feedpoint_z:.1f}Ω | "
                f"SWR = {swr_data['swr']}:1 | "
                f"Γ = {swr_data['gamma_magnitude']:.3f}"
            )
            canvas.create_text(center[0], 15, text=info_text, fill=AMBER,
                              font=("Helvetica", 9))

            # Info panel below chart
            info_frame = ttk.Frame(popup, style="Panel.TFrame")
            info_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

            info_text_widget = tk.Text(
                info_frame, height=12, bg=PANEL_BG, fg=FG, font=("Helvetica", 8),
                relief="flat", borderwidth=0, padx=10, pady=10, wrap="word", highlightthickness=0
            )
            info_text_widget.pack(fill="both", expand=True)

            explanation = pt(self.lang.get(), "smith_expl")
            info_text_widget.insert(1.0, explanation)
            info_text_widget.config(state="disabled")

            # Close button
            close_btn = RoundedButton(popup, pt(self.lang.get(), "close"), popup.destroy,
                                     PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
            close_btn.pack(pady=(0, 10))

        except Exception as e:
            messagebox.showerror(self._t("error"), f"{pt(self.lang.get(), 'smith_error')}: {str(e)}")

    def _show_final_briefing(self):
        """Show comprehensive final briefing with all design parameters and build instructions."""
        if not self.design:
            messagebox.showwarning(self._t("error"), pt(self.lang.get(), "design_first"))
            return

        try:

            lang = self.lang.get()
            units = self.units.get()

            popup = tk.Toplevel(self)
            popup.title(pt(self.lang.get(), "brief_title"))
            popup.geometry("1000x900")
            popup.configure(bg=BG)

            # Title
            title_label = ttk.Label(popup, text=pt(self.lang.get(), "brief_heading"),
                                   style="PanelTitle.TLabel")
            title_label.pack(anchor="w", padx=10, pady=(10, 5))

            # Main text area with scrollbar
            text_frame = ttk.Frame(popup, style="Panel.TFrame")
            text_frame.pack(fill="both", expand=True, padx=10, pady=5)

            text_widget = tk.Text(
                text_frame, bg=PANEL_BG, fg=FG, font=FONT_COURIER, wrap="word",
                relief="flat", borderwidth=0, padx=15, pady=15, highlightthickness=0
            )
            text_widget.pack(side="left", fill="both", expand=True)

            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            scrollbar.pack(side="right", fill="y")
            text_widget.config(yscrollcommand=scrollbar.set)

            # Build briefing content
            antenna_label = antenna_type_label(self.antenna_type.get(), lang)
            band = self.band.get()
            custom_freq = self.custom_freq_entry.get() if hasattr(self, 'custom_freq_entry') else ""
            freq_mhz = self.design.design_freq_mhz
            wire_type = self.antenna_wire.get()
            cable_type = self.feed_cable.get()

            # Get design data
            gain_info = calculate_gain_description(self.design)

            # Bilingual labels
            if lang == "en":
                title_text = "FINAL BRIEFING - HAM ANTENNA DESIGNER"
                config_label = "DESIGN CONFIGURATION:"
                antenna_type_label_txt = "Antenna Type:"
                band_label_txt = "Band:"
                freq_label_txt = "Frequency:"
                wire_label_txt = "Antenna Wire:"
                cable_label_txt = "Feed Cable:"
                units_label_txt = "Units:"
                lang_label_txt = "Language:"
                spec_label = "ANTENNA SPECIFICATIONS:"
                elec_label = "Electrical Characteristics:"
                feedpoint_label = "Feedpoint Impedance:"
                gain_label = "Antenna Gain:"
                fb_label = "Front-to-Back:"
                toa_label = "Take-off Angle:"
                matching_label = "Matching Analysis (50Ω line):"
                swr_label = "SWR:"
                rl_label = "Return Loss:"
                pr_label = "Power Reflected:"
                pt_label = "Power Transmitted:"
                cable_label_txt2 = "Cable Loss Estimate (30m/98ft):"
                loss_at_label = "Loss at"
                balun_label = "Balun/Unun Recommendation:"
                type_label = "Type:"
                ratio_label = "Ratio:"
                location_label = "Location:"
                build_label = "BUILD INSTRUCTIONS:"
                checklist_label = "CONSTRUCTION CHECKLIST:"
                materials_label = "MATERIALS & TOOLS:"
                assembly_label = "ASSEMBLY STEPS:"
                safety_label = "SAFETY NOTES:"
            else:  # Dutch
                title_text = "FINAAL BRIEFING - HAM ANTENNE ONTWERPER"
                config_label = "ONTWERP CONFIGURATIE:"
                antenna_type_label_txt = "Antennetype:"
                band_label_txt = "Band:"
                freq_label_txt = "Frequentie:"
                wire_label_txt = "Antennedraad:"
                cable_label_txt = "Voedingskabel:"
                units_label_txt = "Eenheden:"
                lang_label_txt = "Taal:"
                spec_label = "ANTENNE SPECIFICATIES:"
                elec_label = "Elektrische Karakteristieken:"
                feedpoint_label = "Voedingspunt Impedantie:"
                gain_label = "Antenneversterking:"
                fb_label = "Voor-naar-Achter:"
                toa_label = "Afstraalhoek:"
                matching_label = "Aanpassing Analyse (50Ω lijn):"
                swr_label = "SWR:"
                rl_label = "Return Loss:"
                pr_label = "Gereflecteerd Vermogen:"
                pt_label = "Doorgegeven Vermogen:"
                cable_label_txt2 = "Kabelverlieschatting (30m/98ft):"
                loss_at_label = "Verlies bij"
                balun_label = "Balun/Unun Aanbeveling:"
                type_label = "Type:"
                ratio_label = "Verhouding:"
                location_label = "Locatie:"
                build_label = "BOUW INSTRUCTIES:"
                checklist_label = "CONSTRUCTIE CHECKLIST:"
                materials_label = "MATERIALEN & GEREEDSCHAP:"
                assembly_label = "MONTAGE STAPPEN:"
                safety_label = "VEILIGHEIDSNOTEN:"

            briefing = (
                f"{'='*90}\n"
                f"{title_text}\n"
                f"{'='*90}\n\n"
            )

            briefing += (
                f"{config_label}\n"
                f"{'-'*90}\n"
                f"{antenna_type_label_txt:20s} {antenna_label}\n"
                f"{band_label_txt:20s} {band}\n"
                f"{freq_label_txt:20s} {freq_mhz} MHz"
            )

            if custom_freq:
                briefing += f" (custom: {custom_freq} MHz)"
            briefing += "\n"

            briefing += (
                f"\n{wire_label_txt:20s} {wire_type}\n"
                f"{cable_label_txt:20s} {cable_type}\n"
                f"{units_label_txt:20s} {units.upper()}\n"
                f"{lang_label_txt:20s} {'English' if lang == 'en' else 'Nederlands'}\n\n"
            )

            # Antenna schema ASCII art
            briefing += (
                f"{pt(lang, 'brief_schema')}\n"
                f"{'-'*90}\n"
            )

            if "vertical" in self.design.antenna_type.lower():
                briefing += (
                    f"         {pt(lang, 'sch_radial')}\n"
                    "    -----┼-----\n"
                    "   |     |     |\n"
                    f"   |   {pt(lang, 'sch_mast')}    |\n"
                    "   |     |     |\n"
                    f"    -----⊗----- {pt(lang, 'sch_feedpoint')}\n"
                    "   |     |     |\n"
                    f"  {pt(lang, 'sch_radials_gp')}\n"
                )
            elif "dipole" in self.design.antenna_type.lower():
                briefing += (
                    f"      {pt(lang, 'sch_leg_a'):15s}{pt(lang, 'sch_leg_b')}\n"
                    "    =========== ⊗ ===========\n"
                    f"    {pt(lang, 'sch_elem1'):14s}{pt(lang, 'sch_elem2')}\n"
                    "                  |\n"
                    f"              {pt(lang, 'sch_feedpoint')}\n"
                    "                  |\n"
                    f"              {pt(lang, 'sch_feed_cable')}\n"
                )
            elif "efhw" in self.design.antenna_type.lower():
                briefing += (
                    f"  {pt(lang, 'sch_end_high_z')}\n"
                    "         |\n"
                    f"      ======= {pt(lang, 'sch_element')}\n"
                    "         |\n"
                    "      Unun 9:1\n"
                    "         |\n"
                    f"      {pt(lang, 'sch_feedpoint_50')}\n"
                    "         |\n"
                    f"      {pt(lang, 'sch_feed_cable')}\n"
                )
            else:
                briefing += (
                    f"   {pt(lang, 'sch_structure')}\n"
                    "         |\n"
                    f"      {pt(lang, 'sch_feedpoint')} ⊗\n"
                    "         |\n"
                    f"      {pt(lang, 'sch_feed_cable')}\n"
                )

            briefing += "\n"

            # Design parameters
            briefing += (
                f"\n{spec_label}\n"
                f"{'-'*90}\n"
            )

            # Element lengths
            for elem in self.design.elements:
                if units == "ft":
                    length = elem.length_ft
                    unit_str = "ft"
                else:
                    length = elem.length_m
                    unit_str = "m"

                briefing += f"  {elem.name:25s}: {length:10.2f} {unit_str}\n"

            briefing += (
                f"\n{elec_label}\n"
                f"  {feedpoint_label:25s} {self.design.feedpoint_impedance_ohms:.1f} Ohms\n"
                f"  {gain_label:25s} {gain_info['gain_dbi']:.2f} dBi\n"
                f"  {fb_label:25s} {gain_info['f_b_ratio_db']:.1f} dB\n"
                f"  {toa_label:25s} {gain_info['takeoff_angle_deg']}°"
                f"  ({pt(lang, 'rad_at', h=gain_info['height_m'], g=pt(lang, 'ground_' + gain_info['ground']))})\n"
            )

            # SWR info
            swr_data = impedance_to_swr_table(coax_side_impedance(self.design), z0=50)

            briefing += (
                f"\n{matching_label}\n"
                f"  {swr_label:25s} {swr_data['swr']}:1\n"
                f"  {rl_label:25s} {_rl(swr_data['return_loss_db'])}\n"
                f"  {pr_label:25s} {swr_data['power_reflected_percent']}%\n"
                f"  {pt_label:25s} {swr_data['power_transmitted_percent']}%\n"
            )

            # Cable loss estimate
            cable_loss_30m = calculate_cable_loss(cable_type, freq_mhz, 30 * 3.28084)

            briefing += (
                f"\n{cable_label_txt2}\n"
                f"  {loss_at_label} {freq_mhz} MHz: {cable_loss_30m} dB (~{100 * (10**(-cable_loss_30m/10)):.0f}W from 100W TX)\n"
            )

            # Balun info
            if self.design.balun:
                briefing += (
                    f"\n{balun_label}\n"
                    f"  {type_label:20s} {self.design.balun.get('type', 'N/A')}\n"
                    f"  {ratio_label:20s} {self.design.balun.get('ratio', 'N/A')}\n"
                    f"  {location_label:20s} {self.design.balun.get('where', 'Feedpoint')}\n"
            )

            # Build instructions
            briefing += (
                f"\n{'='*90}\n"
                f"{build_label}\n"
                f"{'='*90}\n\n"
            )

            # Get build advice - add with consistent formatting
            build_notes_text = build_advice(self.design, units=units, lang=lang)
            briefing += build_notes_text + "\n"

            if lang == "en":
                materials_list = (
                    f"  [ ] Wire: {wire_type}\n"
                    f"  [ ] Coaxial cable: {cable_type}\n"
                    "  [ ] Tape measure or ruler\n"
                    "  [ ] Cutting tool (wire cutter)\n"
                    "  [ ] Soldering iron (if needed)\n"
                    "  [ ] SWR meter or antenna analyzer\n"
                )
                assembly_list = (
                    "  [ ] Cut all wire elements to calculated lengths (±1%)\n"
                    "  [ ] Prepare element supports/insulators\n"
                    "  [ ] Assemble antenna structure\n"
                    "  [ ] Install feedpoint connector\n"
                    "  [ ] Mount balun/unun (if required)\n"
                    "  [ ] Connect feed cable\n"
                    "  [ ] Test continuity with multimeter\n"
                    "  [ ] Install antenna at operating height\n"
                    "  [ ] Measure SWR at multiple frequencies\n"
                    "  [ ] Document performance baseline\n"
                    "  [ ] Make tuning adjustments if needed\n"
                )
                safety_list = (
                    "  • Ensure antenna is clear of power lines\n"
                    "  • Ground antenna mast properly\n"
                    "  • Never transmit without proper grounding\n"
                    "  • Check RF safety compliance (SAR limits)\n"
                    "  • Inspect regularly for weather damage\n"
                )
            else:  # Dutch
                materials_list = (
                    f"  [ ] Draad: {wire_type}\n"
                    f"  [ ] Coaxiale kabel: {cable_type}\n"
                    "  [ ] Meetlint of liniaal\n"
                    "  [ ] Snijgereedschap (draadknipper)\n"
                    "  [ ] Soldeerbout (indien nodig)\n"
                    "  [ ] SWR-meter of antenne-analyzer\n"
                )
                assembly_list = (
                    "  [ ] Snij alle draadelementen op berekende lengtes (±1%)\n"
                    "  [ ] Bereid element-ondersteuningen/isolatoren voor\n"
                    "  [ ] Monteer antennestructuur\n"
                    "  [ ] Installeer voedingspunt-connector\n"
                    "  [ ] Monteer balun/unun (indien vereist)\n"
                    "  [ ] Verbind voedingskabel\n"
                    "  [ ] Test continuïteit met multimeter\n"
                    "  [ ] Installeer antenne op werkingshoogte\n"
                    "  [ ] Meet SWR op meerdere frequenties\n"
                    "  [ ] Leg de uitgangsprestaties vast\n"
                    "  [ ] Maak afstemmingsaanpassingen indien nodig\n"
                )
                safety_list = (
                    "  • Zorg dat antenne vrij is van stroomlijnen\n"
                    "  • Aard de antennemast correct\n"
                    "  • Zend nooit zonder juiste aarding\n"
                    "  • Controleer RF-veiligheidsnormen (SAR-limieten)\n"
                    "  • Controleer regelmatig op weerschade\n"
                )

            briefing += (
                f"\n{'='*90}\n"
                f"{checklist_label}\n"
                f"{'='*90}\n\n"
                f"{materials_label}\n"
                f"{materials_list}\n"
                f"{assembly_label}\n"
                f"{assembly_list}\n"
                f"{safety_label}\n"
                f"{safety_list}\n"
                f"{'='*90}\n"
            )

            if lang == "en":
                briefing += (
                    "Design generated by HAM Antenna Designer v2.2\n"
                    "Date: 2026-06-29\n"
                    f"{'='*90}\n"
                )
            else:
                briefing += (
                    "Ontwerp gegenereerd door HAM Antenne Ontwerper v2.2\n"
                    "Datum: 2026-06-29\n"
                    f"{'='*90}\n"
                )

            text_widget.insert(1.0, briefing)
            text_widget.config(state="disabled")

            # Button frame
            btn_frame = ttk.Frame(popup, style="Panel.TFrame")
            btn_frame.pack(fill="x", padx=10, pady=(5, 10))

            # Export button
            def export_briefing():
                path = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[(pt(self.lang.get(), "txt_files"), "*.txt"), (pt(self.lang.get(), "all_files"), "*.*")]
                )
                if path:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(text_widget.get(1.0, tk.END))
                    messagebox.showinfo(self._t("window_title"),
                                       pt(self.lang.get(), "brief_exported", path=path))

            export_btn = RoundedButton(btn_frame, pt(self.lang.get(), "brief_export"), export_briefing,
                                      PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
            export_btn.pack(side="left", padx=5)

            # Close button
            close_btn = RoundedButton(btn_frame, pt(self.lang.get(), "close"), popup.destroy,
                                     PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
            close_btn.pack(side="right", padx=5)

        except Exception as e:
            messagebox.showerror(self._t("error"), f"{pt(self.lang.get(), 'brief_error')}: {str(e)}")

    def _show_matching_networks(self):
        """Open Matching Network Calculator in popup window."""
        if not self.design:
            messagebox.showwarning(self._t("error"), pt(self.lang.get(), "design_first"))
            return

        try:
            freq_mhz = float(self.design.design_freq_mhz) if self.design else 14.0
            antenna_z = float(self.design.feedpoint_impedance_ohms)

            popup = tk.Toplevel(self)
            popup.title(pt(self.lang.get(), "match_title"))
            popup.geometry("900x850")
            popup.configure(bg=BG)

            # Title
            title_label = ttk.Label(popup, text=pt(self.lang.get(), "match_heading"), style="PanelTitle.TLabel")
            title_label.pack(anchor="w", padx=10, pady=(10, 5))

            # Input frame
            input_frame = ttk.Frame(popup, style="Panel.TFrame")
            input_frame.pack(fill="x", padx=10, pady=5)

            # Source impedance
            ttk.Label(input_frame, text=pt(self.lang.get(), "match_source"), style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=3)
            source_var = tk.StringVar(value="50")
            source_entry = ttk.Entry(input_frame, textvariable=source_var, width=10)
            source_entry.grid(row=0, column=1, sticky="w", padx=5, pady=3)

            # Load impedance (auto-filled from antenna design)
            ttk.Label(input_frame, text=pt(self.lang.get(), "match_load"), style="Panel.TLabel").grid(row=1, column=0, sticky="w", padx=5, pady=3)
            load_var = tk.StringVar(value=f"{antenna_z:g}")
            load_entry = ttk.Entry(input_frame, textvariable=load_var, width=16)
            load_entry.grid(row=1, column=1, sticky="w", padx=5, pady=3)

            # Frequency
            ttk.Label(input_frame, text=pt(self.lang.get(), "freq_mhz"), style="Panel.TLabel").grid(row=2, column=0, sticky="w", padx=5, pady=3)
            freq_var = tk.StringVar(value=str(freq_mhz))
            freq_entry = ttk.Entry(input_frame, textvariable=freq_var, width=10)
            freq_entry.grid(row=2, column=1, sticky="w", padx=5, pady=3)

            # Calculate button
            def calculate_networks():
                try:
                    source = float(source_var.get().replace(",", "."))
                    load = parse_impedance(load_var.get())
                    freq = float(freq_var.get().replace(",", "."))

                    if source <= 0 or load.real <= 0 or freq <= 0:
                        raise ValueError(pt(self.lang.get(), "values_positive"))

                    swr_before = calculate_swr_from_impedance(load, source)
                    networks = suggest_matching_network(source, load, freq)

                    info_text.config(state="normal")
                    info_text.delete(1.0, tk.END)

                    L = self.lang.get()
                    result = (
                        f"{pt(L, 'm_header')}\n"
                        f"{'='*60}\n"
                        f"{pt(L, 'm_source', v=f'{source:g}')}\n"
                        f"{pt(L, 'm_load', v=format_impedance(load))}\n"
                        f"{pt(L, 'm_freq', v=freq)}\n"
                        f"{pt(L, 'm_swr_before', v=swr_before)}\n"
                    )
                    if not networks or swr_before <= 1.0:
                        result += f"\n{pt(L, 'm_matched')}\n"

                    comp_label = {("series", "L"): "series_inductor", ("series", "C"): "series_capacitor",
                                  ("shunt", "L"): "shunt_inductor", ("shunt", "C"): "shunt_capacitor"}
                    char_key = {"L": "char_l", "Pi": "char_pi", "T": "char_t"}

                    for i, net in enumerate(networks, 1):
                        result += f"\n{pt(L, 'm_option', i=i, name=pt(L, 'net_' + net['name']))}\n"
                        result += f"{'-'*60}\n"
                        result += f"{pt(L, 'm_q', v=net['quality_factor'])}\n"
                        if 'r_virtual_ohm' in net:
                            result += f"{pt(L, 'm_rv', v=net['r_virtual_ohm'])}\n"
                        result += f"\n{pt(L, 'm_components')}\n"
                        for n, comp in enumerate(net['components'], 1):
                            label = pt(L, comp_label[(comp['position'], comp['kind'])])
                            result += (f"  {n}. {label:26s} {comp['display']:>10s}   "
                                       f"(E12 {comp['e12']:>8s})   X = {comp['reactance_ohm']:+.1f} Ω\n")
                        result += (f"  {pt(L, 'm_check', z=format_impedance(net['zin']), swr=net['swr'], swr12=net['swr_e12'])}\n")

                        result += f"\n{pt(L, 'm_characteristics')}\n"
                        for line in pt(L, char_key[net['type']]):
                            result += f"  • {line}\n"

                    result += f"\n{'='*60}\n" + pt(L, 'm_notes')

                    info_text.insert(1.0, result)
                    info_text.config(state="disabled")

                except Exception as e:
                    info_text.config(state="normal")
                    info_text.delete(1.0, tk.END)
                    info_text.insert(1.0, f"{pt(self.lang.get(), 'error_prefix')}: {str(e)}")
                    info_text.config(state="disabled")

            calc_btn = RoundedButton(input_frame, pt(self.lang.get(), "calculate"), calculate_networks,
                                    PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
            calc_btn.grid(row=3, column=0, columnspan=2, pady=10)

            # Results panel
            info_text = tk.Text(
                popup, height=30, bg=PANEL_BG, fg=FG, font=FONT_COURIER,
                relief="flat", borderwidth=0, padx=15, pady=15, highlightthickness=0
            )
            info_text.pack(fill="both", expand=True, padx=10, pady=5)

            # Close button
            close_btn = RoundedButton(popup, pt(self.lang.get(), "close"), popup.destroy,
                                     PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
            close_btn.pack(pady=10)

            # Auto-calculate on open
            calculate_networks()

        except Exception as e:
            messagebox.showerror(self._t("error"), f"{pt(self.lang.get(), 'match_error')}: {str(e)}")

    def _show_cable_loss(self):
        """Open Cable Loss Calculator in popup window."""
        try:

            freq_mhz = float(self.design.design_freq_mhz) if self.design else 14.0

            # Auto-fill from design
            cable_type = self.feed_cable.get()
            antenna_z = coax_side_impedance(self.design)  # after the balun/unun

            def antenna_swr(cable):
                # SWR against the line's OWN impedance (450/600 ohm for ladder line)
                return impedance_to_swr_table(antenna_z, z0=cable_impedance(cable))['swr']

            swr_value = antenna_swr(cable_type)

            popup = tk.Toplevel(self)
            popup.title(pt(self.lang.get(), "cable_title"))
            popup.geometry("800x700")
            popup.configure(bg=BG)

            # Title
            title_label = ttk.Label(popup, text=pt(self.lang.get(), "cable_heading"), style="PanelTitle.TLabel")
            title_label.pack(anchor="w", padx=10, pady=(10, 5))

            # Input frame
            input_frame = ttk.Frame(popup, style="Panel.TFrame")
            input_frame.pack(fill="x", padx=10, pady=5)

            # Frequency (auto-filled from design)
            ttk.Label(input_frame, text=pt(self.lang.get(), "freq_mhz"), style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=3)
            freq_var = tk.StringVar(value=str(freq_mhz))
            freq_entry = ttk.Entry(input_frame, textvariable=freq_var, width=10)
            freq_entry.grid(row=0, column=1, sticky="w", padx=5, pady=3)

            # Distance
            ttk.Label(input_frame, text=pt(self.lang.get(), "cable_len"), style="Panel.TLabel").grid(row=1, column=0, sticky="w", padx=5, pady=3)
            dist_var = tk.StringVar(value="30")
            dist_entry = ttk.Entry(input_frame, textvariable=dist_var, width=10)
            dist_entry.grid(row=1, column=1, sticky="w", padx=5, pady=3)

            # Cable type (auto-filled from design)
            ttk.Label(input_frame, text=pt(self.lang.get(), "cable_type"), style="Panel.TLabel").grid(row=2, column=0, sticky="w", padx=5, pady=3)
            cable_var = tk.StringVar(value=cable_type)
            cable_combo = ttk.Combobox(input_frame, textvariable=cable_var,
                                       values=get_all_cable_types(), width=30, state="readonly")
            cable_combo.grid(row=2, column=1, sticky="w", padx=5, pady=3)

            # SWR (auto-filled from design)
            ttk.Label(input_frame, text=pt(self.lang.get(), "antenna_swr"), style="Panel.TLabel").grid(row=3, column=0, sticky="w", padx=5, pady=3)
            swr_var = tk.StringVar(value=str(swr_value))
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

                    # Power budget (100 W TX): matched loss + extra loss from
                    # the SWR on the line (ARRL), tuner/TX matched to the line.
                    power_budget = power_budget_summary(100, cable, freq, distance_m, 2.15, swr)
                    cable_loss = power_budget['cable_loss_db']
                    swr_loss_db = power_budget['swr_loss_db']
                    total_loss = power_budget['total_loss_db']

                    # Update info panel
                    info_text.config(state="normal")
                    info_text.delete(1.0, tk.END)

                    L = self.lang.get()
                    efficiency = power_budget['efficiency_percent']
                    result_text = (
                        f"{pt(L, 'c_freq', v=freq)}\n"
                        f"{pt(L, 'c_cable', cable=cable, m=distance_m, ft=distance_ft)}\n"
                        f"{pt(L, 'c_swr', v=swr, z0=cable_impedance(cable))}\n\n"
                        f"{pt(L, 'c_losses')}\n"
                        f"  {pt(L, 'c_cable_loss', v=cable_loss)}\n"
                        f"  {pt(L, 'c_swr_loss', v=swr_loss_db)}\n"
                        f"  {pt(L, 'c_total_loss', v=total_loss)}\n\n"
                        f"{pt(L, 'c_budget')}\n"
                        f"  {pt(L, 'c_power_ant', v=power_budget['power_at_antenna_watts'])}\n"
                        f"  {pt(L, 'c_efficiency', v=efficiency)}\n"
                        f"  {pt(L, 'c_eirp', v=power_budget['eirp_watts'])}\n\n"
                        f"{pt(L, 'c_note')}\n"
                    )
                    info_text.insert(1.0, result_text)
                    info_text.config(state="disabled")

                except Exception as e:
                    info_text.config(state="normal")
                    info_text.delete(1.0, tk.END)
                    info_text.insert(1.0, f"{pt(self.lang.get(), 'error_prefix')}: {str(e)}")
                    info_text.config(state="disabled")

            calc_btn = RoundedButton(input_frame, pt(self.lang.get(), "calculate"), calculate_loss,
                                    PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
            calc_btn.grid(row=4, column=0, columnspan=2, pady=10)

            # Results panel
            info_text = tk.Text(
                popup, height=20, bg=PANEL_BG, fg=FG, font=FONT_COURIER,
                relief="flat", borderwidth=0, padx=15, pady=15, highlightthickness=0
            )
            info_text.pack(fill="both", expand=True, padx=10, pady=5)

            # Close button
            close_btn = RoundedButton(popup, pt(self.lang.get(), "close"), popup.destroy,
                                     PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
            close_btn.pack(pady=10)

            def on_cable_change(event=None):
                swr_var.set(str(antenna_swr(cable_var.get())))
                calculate_loss()

            cable_combo.bind("<<ComboboxSelected>>", on_cable_change)

            # Auto-calculate on open
            calculate_loss()

        except Exception as e:
            messagebox.showerror(self._t("error"), f"{pt(self.lang.get(), 'cable_error')}: {str(e)}")

    def _show_radiation_pattern(self):
        """Radiation pattern popup: azimuth and elevation cuts computed from
        the design's geometry, at a chosen height over a chosen ground."""
        if not self.design:
            messagebox.showwarning(self._t("error"), pt(self.lang.get(), "design_first"))
            return

        try:
            design = self.design
            lang = self.lang.get()

            popup = tk.Toplevel(self)
            popup.title(pt(lang, "rad_title") + " - " + antenna_type_label(design.antenna_type, lang))
            popup.geometry("820x860")
            popup.configure(bg=BG)

            ttk.Label(popup, text=pt(lang, "rad_heading"), style="PanelTitle.TLabel").pack(
                anchor="w", padx=10, pady=(10, 5))

            input_frame = ttk.Frame(popup, style="Panel.TFrame")
            input_frame.pack(fill="x", padx=10, pady=5)
            ttk.Label(input_frame, text=pt(lang, "rad_height"), style="Panel.TLabel").grid(
                row=0, column=0, sticky="w", padx=5, pady=3)
            height_var = tk.StringVar(value=f"{default_height(design):g}")
            height_entry = ttk.Entry(input_frame, textvariable=height_var, width=8)
            height_entry.grid(row=0, column=1, sticky="w", padx=5, pady=3)
            ttk.Label(input_frame, text=pt(lang, "rad_ground"), style="Panel.TLabel").grid(
                row=0, column=2, sticky="w", padx=(15, 5), pady=3)
            ground_keys = ["average", "perfect", "free"]
            ground_labels = [pt(lang, "ground_" + g) for g in ground_keys]
            ground_var = tk.StringVar(value=pt(lang, "ground_" + default_ground(design)))
            ground_combo = ttk.Combobox(input_frame, textvariable=ground_var, values=ground_labels,
                                        state="readonly", width=18)
            ground_combo.grid(row=0, column=3, sticky="w", padx=5, pady=3)

            plots = tk.Frame(popup, bg=BG)
            plots.pack(padx=10, pady=5)
            cw, ch = 390, 390
            az_canvas = tk.Canvas(plots, width=cw, height=ch, bg=PANEL_BG, highlightthickness=0)
            az_canvas.grid(row=0, column=0, padx=(0, 5))
            el_canvas = tk.Canvas(plots, width=cw, height=ch, bg=PANEL_BG, highlightthickness=0)
            el_canvas.grid(row=0, column=1, padx=(5, 0))

            info_label = ttk.Label(popup, text="", style="Panel.TLabel", justify="left")
            info_label.pack(anchor="w", padx=14, pady=(5, 5))

            def redraw(event=None):
                try:
                    h = float(height_var.get().replace(",", "."))
                except ValueError:
                    h = default_height(design)
                    height_var.set(f"{h:g}")
                ground = ground_keys[ground_labels.index(ground_var.get())]
                p = compute_pattern(design, max(0.0, h), ground)

                az_canvas.delete("all")
                el_canvas.delete("all")
                az_title = (pt(lang, "rad_az_title_free") if ground == "free"
                            else pt(lang, "rad_az_title", el=p["azimuth_elevation_deg"]))
                az_canvas.create_text(cw / 2, 14, text=az_title, fill=FG, font=("Helvetica", 9, "bold"))
                draw_db_polar(az_canvas, (cw / 2, ch / 2 + 12), 150,
                              list(enumerate(p["azimuth_cut"])), mode="azimuth",
                              line_color=AMBER, grid_color="#3a3a3a", text_color=AMBER_DIM)
                el_canvas.create_text(cw / 2, 14, text=pt(lang, "rad_el_title"), fill=FG,
                                      font=("Helvetica", 9, "bold"))
                over_ground = ground != "free"
                el_center = (cw / 2, ch - 70) if over_ground else (cw / 2, ch / 2 + 12)
                draw_db_polar(el_canvas, el_center, 165 if over_ground else 150,
                              list(zip(p["elevation_angles"], p["elevation_cut"])), mode="elevation",
                              line_color=AMBER, grid_color="#3a3a3a", text_color=AMBER_DIM)
                if over_ground:
                    el_canvas.create_text(el_center[0] + 150, el_center[1] + 18, text=pt(lang, "rad_front"),
                                          fill=AMBER_DIM, font=("Helvetica", 8))
                    el_canvas.create_text(el_center[0] - 150, el_center[1] + 18, text=pt(lang, "rad_back"),
                                          fill=AMBER_DIM, font=("Helvetica", 8))

                toa = f"{p['takeoff_angle_deg']}°" if p["takeoff_angle_deg"] is not None else pt(lang, "rad_toa_none")
                fb = f"{p['f_b_ratio_db']:.1f} dB" if p["f_b_ratio_db"] >= 1.0 else "-"
                bw = f"{p['beamwidth_deg']}°" if p["beamwidth_deg"] else pt(lang, "rad_omni")
                info_label.config(text=pt(
                    lang, "rad_info", g=p["gain_dbi"], gd=p["gain_dbd"], toa=toa, fb=fb, bw=bw,
                    pol=pt(lang, "rad_pol_" + p["polarization"][0])))

            height_entry.bind("<Return>", redraw)
            height_entry.bind("<FocusOut>", redraw)
            ground_combo.bind("<<ComboboxSelected>>", redraw)
            RoundedButton(input_frame, pt(lang, "calculate"), redraw, PANEL_BG, AMBER, AMBER_DIM,
                          font=("Helvetica", 8, "bold")).grid(row=0, column=4, padx=(15, 5))

            explanation_text = tk.Text(
                popup, height=9, bg=PANEL_BG, fg=FG, font=("Helvetica", 8),
                relief="flat", borderwidth=0, padx=10, pady=5, wrap="word", highlightthickness=0
            )
            explanation_text.pack(fill="both", expand=True, padx=10)
            explanation_text.insert(1.0, pt(lang, "rad_expl"))
            explanation_text.config(state="disabled")

            RoundedButton(popup, pt(lang, "close"), popup.destroy, PANEL_BG, AMBER, AMBER_DIM,
                          font=("Helvetica", 8, "bold")).pack(pady=(5, 10))
            redraw()

        except Exception as e:
            messagebox.showerror(self._t("error"), f"{pt(self.lang.get(), 'rad_error')}: {str(e)}")

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

Afstraalhoek:
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
        popup.title(pt(lang, "rad_expl_title"))
        popup.geometry("700x800")
        popup.configure(bg=BG)

        text_widget = tk.Text(
            popup, bg=PANEL_BG, fg=FG, font=FONT_COURIER, wrap="word",
            relief="flat", borderwidth=0, padx=15, pady=15, highlightthickness=0
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        text_widget.insert(1.0, info_text.get(lang, info_text["en"]))
        text_widget.config(state="disabled")

        close_btn = RoundedButton(popup, pt(self.lang.get(), "close"), popup.destroy,
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
        popup.title(pt(lang, "swr_expl_title"))
        popup.geometry("700x800")
        popup.configure(bg=BG)

        text_widget = tk.Text(
            popup, bg=PANEL_BG, fg=FG, font=FONT_COURIER, wrap="word",
            relief="flat", borderwidth=0, padx=15, pady=15, highlightthickness=0
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        text_widget.insert(1.0, info_text.get(lang, info_text["en"]))
        text_widget.config(state="disabled")

        close_btn = RoundedButton(popup, pt(self.lang.get(), "close"), popup.destroy,
                                 PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
        close_btn.pack(pady=10)

    def _show_sweep_window(self):
        """Open SWR Sweep in popup window."""
        if not self.design:
            messagebox.showwarning(self._t("error"), pt(self.lang.get(), "design_first"))
            return

        try:
            antenna_type = self.antenna_type.get()
            band = self.band.get()
            lang = self.lang.get()
            if band not in BANDS_MHZ:
                messagebox.showwarning(self._t("error"), pt(lang, "sweep_unavailable"))
                return

            # Sweep the antenna AS DESIGNED (incl. a custom frequency and the
            # wire factor) across the band.
            band_lo, band_hi = BANDS_MHZ[band]
            sweep = sweep_design(self.design, band_lo, band_hi)
            if "not_applicable" in sweep:
                messagebox.showinfo(pt(lang, "sweep_title"), pt(lang, "sweep_na_" + sweep["not_applicable"]))
                return

            popup = tk.Toplevel(self)
            popup.title(pt(lang, "sweep_title") + " - " + antenna_type_label(antenna_type, lang))
            popup.geometry("850x750")
            popup.configure(bg=BG)

            title_label = ttk.Label(popup, text=pt(lang, "sweep_heading"), style="PanelTitle.TLabel")
            title_label.pack(anchor="w", padx=10, pady=(10, 5))

            canvas_w, canvas_h = 800, 380
            canvas = tk.Canvas(popup, width=canvas_w, height=canvas_h, bg=PANEL_BG,
                               highlightthickness=0, relief="flat", borderwidth=0)
            canvas.pack(padx=10, pady=(5, 5))

            freqs = sweep["frequencies"]
            swrs = sweep["swr_values"]
            left, right, top, bottom = 55, 20, 20, 45
            plot_w = canvas_w - left - right
            plot_h = canvas_h - top - bottom
            freq_min, freq_max = freqs[0], freqs[-1]
            swr_top = 5.0

            def fx(f):
                return left + (f - freq_min) / (freq_max - freq_min) * plot_w

            def sy(v):
                return top + (swr_top - min(max(v, 1.0), swr_top)) / (swr_top - 1.0) * plot_h

            # SWR grid 1..5
            for v in (1, 1.5, 2, 3, 4, 5):
                y = sy(v)
                canvas.create_line(left, y, left + plot_w, y, fill=AMBER_DIM, width=1,
                                   dash=(4, 2) if v == 2 else (1, 3))
                canvas.create_text(left - 6, y, text=f"{v:g}", fill=FG, font=("Helvetica", 8), anchor="e")
            # Frequency ticks
            span = freq_max - freq_min
            raw = span / 6
            mag = 10 ** math.floor(math.log10(raw))
            tick = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
            f_tick = math.ceil(freq_min / tick) * tick
            while f_tick <= freq_max + 1e-9:
                x = fx(f_tick)
                canvas.create_line(x, top + plot_h, x, top + plot_h + 4, fill=AMBER)
                canvas.create_text(x, top + plot_h + 14, text=f"{f_tick:.4g}", fill=FG, font=("Helvetica", 8))
                f_tick += tick
            # Band edges
            for f_edge in sweep["band_edges"]:
                if freq_min <= f_edge <= freq_max:
                    x = fx(f_edge)
                    canvas.create_line(x, top, x, top + plot_h, fill="#5a8fd8", width=1, dash=(5, 3))
            # Axes
            canvas.create_line(left, top + plot_h, left + plot_w, top + plot_h, fill=AMBER, width=2)
            canvas.create_line(left, top, left, top + plot_h, fill=AMBER, width=2)
            canvas.create_text(left + plot_w / 2, canvas_h - 10, text=pt(lang, "sweep_axis"),
                               fill=FG, font=("Helvetica", 9))
            canvas.create_text(16, top + plot_h / 2, text="SWR", fill=FG, font=("Helvetica", 9), angle=90)

            # SWR curve
            pts = []
            for f, v in zip(freqs, swrs):
                pts += [fx(f), sy(v)]
            canvas.create_line(*pts, fill=AMBER, width=2, smooth=False)

            # Resonance (design frequency)
            res_freq = sweep["resonance_freq"]
            res_x, res_y = fx(res_freq), sy(sweep["min_swr"])
            canvas.create_oval(res_x - 4, res_y - 4, res_x + 4, res_y + 4, fill=AMBER, outline=AMBER)

            info_frame = ttk.Frame(popup, style="Panel.TFrame")
            info_frame.pack(fill="both", expand=True, padx=10, pady=(5, 0))

            bw = sweep["bandwidth_2"]
            bw_text = (pt(lang, "sweep_bw", lo=bw[0], hi=bw[1], khz=(bw[1] - bw[0]) * 1000)
                       if bw else pt(lang, "sweep_bw_none"))
            info_text = pt(lang, "sweep_info", res=res_freq, swr=sweep["min_swr"], bw=bw_text, q=sweep["q"])
            info_label = ttk.Label(info_frame, text=info_text, style="Panel.TLabel")
            info_label.pack(anchor="w", padx=10, pady=(5, 5))

            # Explanation text
            explanation_text = tk.Text(
                info_frame, height=8, bg=PANEL_BG, fg=FG, font=("Helvetica", 8),
                relief="flat", borderwidth=0, padx=10, pady=5, wrap="word", highlightthickness=0
            )
            explanation_text.pack(fill="both", expand=True)

            explanation = pt(lang, "sweep_expl")
            explanation_text.insert(1.0, explanation)
            explanation_text.config(state="disabled")

            # Close button
            close_btn = RoundedButton(popup, pt(self.lang.get(), "close"), popup.destroy,
                                     PANEL_BG, AMBER, AMBER_DIM, font=("Helvetica", 8, "bold"))
            close_btn.pack(pady=(5, 10))

        except Exception as e:
            messagebox.showerror(self._t("error"), f"{pt(self.lang.get(), 'sweep_error')}: {str(e)}")

    def _show_balun_help(self):
        """Show balun/unun construction guide popup."""
        lang = self.lang.get()

        help_text = {
            "en": """BALUN/UNUN CONSTRUCTION GUIDE

The ratio on a balun/unun is its IMPEDANCE ratio. A transformer changes
impedance by the SQUARE of its turns ratio:
    Z_antenna = Z_coax x (turns ratio)^2
    4:1 -> 2:1 turns    9:1 -> 3:1 turns    49:1 -> 7:1 turns    64:1 -> 8:1 turns

1:1 CURRENT BALUN / CHOKE  (dipoles, beams, quads, verticals)
------------------------------------------------------------
Stops RF current on the outside of the coax shield (common mode).
Build:  10-12 turns of RG-58/RG-316 (or 8 turns RG-213) through an
        FT240-31 (best below 10 MHz) or FT240-43 (3-30 MHz) toroid.
        Coax centre to one antenna leg, shield to the other leg.
Tip:    a voltage (transformer) 1:1 balun does NOT stop common-mode
        current -- use a current balun.

4:1 CURRENT BALUN  (50 -> 200 ohm: off-centre-fed dipole)
------------------------------------------------------------
Guanella type: two bifilar windings of ~10 turns, each on its own
FT240-31/43 core; inputs in parallel, outputs in series.

LOOPS  (~100-120 ohm: full-wave loop, delta loop)
------------------------------------------------------------
Either accept SWR ~2:1 with a 1:1 current balun, or add a quarter-wave
of 75-ohm coax (length = 0.25 x velocity factor x wavelength) between
the loop and the 50-ohm feed line: 75^2 / 112 = 50 ohm.

9:1 UNUN  (50 -> 450 ohm: random wire, long-wire receive)
------------------------------------------------------------
Trifilar winding, 9 turns of three wires on an FT140-43 or FT240-43.
Not for a half-wave end-fed: that antenna is ~2450 ohm (see 49:1).

49:1 UNUN  (50 -> ~2450 ohm: EFHW, half-wave vertical)
------------------------------------------------------------
Turns 1:7 -- e.g. 2 primary turns (coax side) and 14 secondary turns
(antenna side), the primary turns overlapping the start of the secondary.
Core: FT140-43 for ~100 W SSB, two stacked FT240-43 for more power.
A 100-150 pF capacitor (rated >= 1 kV) across the coax connector
improves the match on 10-15 m.

64:1 UNUN  (50 -> ~3200 ohm: end-fed full wave, very high impedance)
------------------------------------------------------------
Turns 1:8 -- e.g. 2 : 16 turns on an FT240-43.

LOOP-ON-GROUND RECEIVE  (~450 -> 50 ohm)
------------------------------------------------------------
Step-down transformer 9:1 = 3:1 turns, e.g. 9 turns loop side and
3 turns coax side on a #73-mix binocular core.

MATERIALS
------------------------------------------------------------
31 mix:  chokes 1.8-10 MHz        43 mix: 3-30 MHz transformers/chokes
61 mix:  VHF                      73 mix: receive transformers (LW/MW/HF)
VHF/UHF: a sleeve (bazooka) balun or ferrite beads on the coax

CONSTRUCTION TIPS
------------------------------------------------------------
- Enamelled copper wire of 1-1.5 mm for 100 W transformers
- Spread the windings evenly; keep coax-side and antenna-side apart
- Check the core temperature after a few minutes of full power
- Weatherproof the box, leave a drain hole at the bottom
- Verify with an antenna analyzer on a dummy load of the target impedance""",

            "nl": """BALUN/UNUN CONSTRUCTIEGIDS

De verhouding op een balun/unun is de IMPEDANTIEverhouding. Een transformator
verandert de impedantie met het KWADRAAT van de windingsverhouding:
    Z_antenne = Z_coax x (windingsverhouding)^2
    4:1 -> 2:1 windingen   9:1 -> 3:1   49:1 -> 7:1   64:1 -> 8:1

1:1 STROOMBALUN / CHOKE  (dipolen, beams, quads, verticals)
------------------------------------------------------------
Stopt HF-stroom op de buitenkant van het coaxscherm (common mode).
Bouw:   10-12 windingen RG-58/RG-316 (of 8 windingen RG-213) door een
        FT240-31 (best onder 10 MHz) of FT240-43 (3-30 MHz) toroide.
        Coaxkern naar de ene antennehelft, scherm naar de andere.
Tip:    een spannings- (transformator-) 1:1 balun stopt GEEN common-mode
        stroom -- gebruik een stroombalun.

4:1 STROOMBALUN  (50 -> 200 ohm: uit het midden gevoede dipool)
------------------------------------------------------------
Guanella-type: twee bifilaire wikkelingen van ~10 windingen, elk op een
eigen FT240-31/43-kern; ingangen parallel, uitgangen in serie.

LOOPS  (~100-120 ohm: full-wave loop, delta loop)
------------------------------------------------------------
Accepteer SWR ~2:1 met een 1:1 stroombalun, of zet een kwartgolf
75-ohm coax (lengte = 0,25 x verkortingsfactor x golflengte) tussen de
loop en de 50-ohm voedingslijn: 75^2 / 112 = 50 ohm.

9:1 UNUN  (50 -> 450 ohm: random wire, longwire-ontvangst)
------------------------------------------------------------
Trifilaire wikkeling, 9 windingen van drie draden op een FT140-43 of FT240-43.
Niet voor een halvegolf end-fed: die is ~2450 ohm (zie 49:1).

49:1 UNUN  (50 -> ~2450 ohm: EFHW, halvegolf verticaal)
------------------------------------------------------------
Windingen 1:7 -- bijv. 2 primaire windingen (coaxkant) en 14 secundaire
(antennekant), de primaire over het begin van de secundaire gelegd.
Kern: FT140-43 voor ~100 W SSB, twee gestapelde FT240-43 voor meer vermogen.
Een condensator van 100-150 pF (>= 1 kV) over de coaxconnector
verbetert de aanpassing op 10-15 m.

64:1 UNUN  (50 -> ~3200 ohm: end-fed hele golf, zeer hoge impedantie)
------------------------------------------------------------
Windingen 1:8 -- bijv. 2 : 16 windingen op een FT240-43.

LOOP-ON-GROUND ONTVANGST  (~450 -> 50 ohm)
------------------------------------------------------------
Step-down transformator 9:1 = 3:1 windingen, bijv. 9 windingen aan de
loopkant en 3 aan de coaxkant op een binoculaire kern van #73-materiaal.

MATERIAAL
------------------------------------------------------------
31-mix:  chokes 1,8-10 MHz        43-mix: 3-30 MHz transformatoren/chokes
61-mix:  VHF                      73-mix: ontvangsttransformatoren (LG/MG/KG)
VHF/UHF: een mantel- (bazooka-) balun of ferrietkralen om de coax

CONSTRUCTIETIPS
------------------------------------------------------------
- Geëmailleerd koperdraad van 1-1,5 mm voor 100 W-transformatoren
- Verdeel de windingen gelijkmatig; houd coax- en antennekant uit elkaar
- Controleer de kerntemperatuur na een paar minuten vol vermogen
- Maak de behuizing waterdicht, met een afwateringsgaatje onderin
- Controleer met een antenne-analyzer op een dummy load van de doelimpedantie"""
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



def _lang_from_argv(argv) -> str | None:
    """--lang nl | --lang=en → taalcode, anders None (eigen voorkeur)."""
    for i, arg in enumerate(argv):
        if arg.startswith("--lang="):
            return arg.split("=", 1)[1].strip().lower() or None
        if arg == "--lang" and i + 1 < len(argv):
            return argv[i + 1].strip().lower()
    return None


if __name__ == "__main__":
    import sys
    app = AntennaDesignerApp(lang=_lang_from_argv(sys.argv[1:]))
    app.mainloop()
