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
    BANDS_MHZ, CABLES, SHAPE_FAMILIES, STANDALONE_TYPES,
    antenna_type_for, antenna_type_label, wave_fractions_for,
)
from drawing import draw_antenna
from format_text import format_summary
from i18n import SHAPE_FAMILY_LABELS, WAVE_FRACTION_LABELS
from registry import REGISTRY, design as design_antenna
from settings import load_settings, save_settings
from widgets import LogoCanvas, RoundedButton, RoundedPanel
from canvas_view import show_drawing

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
FONT_COMBO = ("Helvetica", 9)
FONT_COURIER = ("Courier New", 11)


def _band_display(band: str) -> str:
    low, high = BANDS_MHZ[band]
    return f"{band} ({low:g}-{high:g} MHz)"


_BAND_DISPLAY_TO_KEY = {_band_display(b): b for b in BANDS_MHZ}

UI_TEXT = {
    "en": {
        "window_title": "HAM Antenna Designer",
        "antenna_type": "Antenna",
        "wave": "Wave",
        "band": "Band",
        "units": "Units",
        "language": "Language",
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
    },
    "nl": {
        "window_title": "HAM Antenne Ontwerper",
        "antenna_type": "Antenne",
        "wave": "Golf",
        "band": "Band",
        "units": "Eenheden",
        "language": "Taal",
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
            font=FONT_COMBO,
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
        self.option_add("*TCombobox*Listbox.font", FONT_COMBO)
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

        self.cable_label = ttk.Label(controls, text=self._t("feed_cable"), style="Panel.TLabel")
        self.cable_label.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="w")
        cable_combo = ttk.Combobox(controls, textvariable=self.feed_cable, values=list(CABLES), state="readonly", width=20)
        cable_combo.grid(row=3, column=1, padx=10, pady=(0, 10), sticky="w")
        cable_combo.bind("<<ComboboxSelected>>", lambda e: self._update_cable_label())
        self.cable_vf_label = ttk.Label(controls, text="", style="Panel.TLabel")
        self.cable_vf_label.grid(row=3, column=2, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        self.custom_freq_label = ttk.Label(controls, text=self._t("custom_freq"), style="Panel.TLabel")
        self.custom_freq_label.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="w")
        self.custom_freq = tk.StringVar(value="")
        custom_freq_entry = ttk.Entry(controls, textvariable=self.custom_freq, width=10)
        custom_freq_entry.grid(row=4, column=1, padx=10, pady=(0, 10), sticky="w")
        custom_freq_entry.bind("<KeyRelease>", lambda e: self._calculate())
        self.custom_freq_hint = ttk.Label(controls, text=self._t("custom_freq_hint"), style="Panel.TLabel")
        self.custom_freq_hint.grid(row=4, column=2, columnspan=2, padx=10, pady=(0, 10), sticky="w")

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

        # Build advice panel.
        advice_border, advice_frame = self._make_panel(self)
        advice_border.pack(fill="both", expand=True, padx=14, pady=8)
        self.advice_title = ttk.Label(advice_frame, text=self._t("advice"), style="PanelTitle.TLabel")
        self.advice_title.pack(anchor="w", padx=12, pady=(12, 0))
        self.advice_text = tk.Text(
            advice_frame, bg=PANEL_BG, fg=FG, insertbackground=AMBER,
            font=FONT_COURIER, relief="flat", borderwidth=0, wrap="word", padx=12, pady=12,
            highlightthickness=0,
        )
        self.advice_text.pack(fill="both", expand=True, padx=12, pady=12)

        self._update_cable_label()

    def _update_cable_label(self):
        cable = CABLES[self.feed_cable.get()]
        self.cable_vf_label.config(
            text=self._t("vf_label").format(vf=cable["velocity_factor"], notes=cable["notes"])
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

    def _set_text_with_hanging_indent(self, text_widget, content):
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

    def _calculate(self):
        lang = self.lang.get()
        units = self.units.get()
        band = self.band.get()
        antenna_type = self.antenna_type.get()
        freq_mhz = self._parse_custom_freq()

        self.design = design_antenna(antenna_type, band, lang=lang, freq_mhz=freq_mhz)

        self._set_text_with_hanging_indent(self.results_text, format_summary(self.design, units=units, lang=lang))
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



if __name__ == "__main__":
    app = AntennaDesignerApp()
    app.mainloop()
