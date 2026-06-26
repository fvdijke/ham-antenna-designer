"""Tkinter GUI for the HAM Antenna Designer.

Visual style matches HAMIOS: dark background, amber (#FFB000) accents,
amber-bordered panels. Lets you pick a band, units, and language, see the
computed design + build advice, and export the scaled SVG drawing or the
true-to-scale mast print template (PDF).
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from antenna_calc import BANDS_MHZ, design_vertical
from build_notes import build_advice
from drawing import draw_vertical
from i18n import CALC_OUTPUT
from tile_pdf import tile_mast

BG = "#1a1a1a"
PANEL_BG = "#1f1f1f"
FG = "#e8e8e8"
AMBER = "#ffb000"
AMBER_DIM = "#8a6000"
FONT_TITLE = ("Helvetica", 13, "bold")
FONT_LABEL = ("Helvetica", 10)
FONT_MONO = ("Menlo", 10)

UI_TEXT = {
    "en": {
        "window_title": "HAM Antenna Designer",
        "band": "Band",
        "units": "Units",
        "language": "Language",
        "calculate": "Calculate",
        "export_svg": "Export SVG drawing...",
        "export_pdf": "Export mast print template (PDF)...",
        "results": "Design",
        "advice": "Build notes",
        "saved": "Saved to {path}",
        "error": "Error",
    },
    "nl": {
        "window_title": "HAM Antenne Ontwerper",
        "band": "Band",
        "units": "Eenheden",
        "language": "Taal",
        "calculate": "Berekenen",
        "export_svg": "SVG-tekening exporteren...",
        "export_pdf": "Mastsjabloon exporteren (PDF)...",
        "results": "Ontwerp",
        "advice": "Bouwnotities",
        "saved": "Opgeslagen naar {path}",
        "error": "Fout",
    },
}


class AntennaDesignerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.design = None
        self.lang = tk.StringVar(value="en")
        self.units = tk.StringVar(value="metric")
        self.band = tk.StringVar(value="20m")

        self._configure_style()
        self.title(UI_TEXT[self.lang.get()]["window_title"])
        self.configure(bg=BG)
        self.geometry("760x600")
        self.minsize(620, 480)

        self._build_layout()
        self._calculate()

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

    def _make_panel(self, parent) -> ttk.Frame:
        """An amber-bordered panel, matching the HAMIOS DraggablePanel look
        (amber 2px border) using a plain tk.Frame as the border carrier,
        since ttk frames can't render a colored border directly."""
        border = tk.Frame(parent, bg=AMBER, highlightthickness=0)
        inner = ttk.Frame(border, style="Panel.TFrame")
        inner.pack(fill="both", expand=True, padx=2, pady=2)
        return border, inner

    def _t(self, key):
        return UI_TEXT[self.lang.get()][key]

    def _build_layout(self):
        # Header.
        header = ttk.Frame(self)
        header.pack(fill="x", padx=12, pady=(12, 6))
        self.title_label = ttk.Label(header, text=self._t("window_title"), style="Title.TLabel")
        self.title_label.pack(side="left")

        # Controls panel (amber-bordered, like HAMIOS panels).
        controls_border, controls = self._make_panel(self)
        controls_border.pack(fill="x", padx=12, pady=6)

        self.band_label = ttk.Label(controls, text=self._t("band"), style="Panel.TLabel")
        self.band_label.grid(row=0, column=0, padx=8, pady=8, sticky="w")
        band_combo = ttk.Combobox(controls, textvariable=self.band, values=list(BANDS_MHZ), state="readonly", width=8)
        band_combo.grid(row=0, column=1, padx=8, pady=8, sticky="w")
        band_combo.bind("<<ComboboxSelected>>", lambda e: self._calculate())

        self.units_label = ttk.Label(controls, text=self._t("units"), style="Panel.TLabel")
        self.units_label.grid(row=0, column=2, padx=8, pady=8, sticky="w")
        for i, val in enumerate(["metric", "imperial"]):
            rb = ttk.Radiobutton(controls, text=val, value=val, variable=self.units, command=self._calculate)
            rb.grid(row=0, column=3 + i, padx=4, pady=8, sticky="w")

        self.lang_label = ttk.Label(controls, text=self._t("language"), style="Panel.TLabel")
        self.lang_label.grid(row=0, column=5, padx=8, pady=8, sticky="w")
        for i, val in enumerate(["en", "nl"]):
            rb = ttk.Radiobutton(controls, text=val.upper(), value=val, variable=self.lang, command=self._on_lang_change)
            rb.grid(row=0, column=6 + i, padx=4, pady=8, sticky="w")

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
            font=FONT_MONO, relief="flat", borderwidth=0, wrap="word",
        )
        self.advice_text.pack(fill="both", expand=True, padx=8, pady=8)

        # Footer / export buttons.
        footer = ttk.Frame(self)
        footer.pack(fill="x", padx=12, pady=(6, 12))
        self.calc_button = ttk.Button(footer, text=self._t("calculate"), command=self._calculate)
        self.calc_button.pack(side="left")
        self.svg_button = ttk.Button(footer, text=self._t("export_svg"), command=self._export_svg)
        self.svg_button.pack(side="left", padx=(8, 0))
        self.pdf_button = ttk.Button(footer, text=self._t("export_pdf"), command=self._export_pdf)
        self.pdf_button.pack(side="left", padx=(8, 0))

    def _on_lang_change(self):
        t = UI_TEXT[self.lang.get()]
        self.title(t["window_title"])
        self.title_label.config(text=t["window_title"])
        self.band_label.config(text=t["band"])
        self.units_label.config(text=t["units"])
        self.lang_label.config(text=t["language"])
        self.results_title.config(text=t["results"])
        self.advice_title.config(text=t["advice"])
        self.calc_button.config(text=t["calculate"])
        self.svg_button.config(text=t["export_svg"])
        self.pdf_button.config(text=t["export_pdf"])
        self._calculate()

    def _calculate(self):
        lang = self.lang.get()
        units = self.units.get()
        band = self.band.get()
        self.design = design_vertical(band, lang=lang)
        d = self.design

        def fmt(ft, m):
            return f"{m} m" if units == "metric" else f"{ft} ft"

        t = CALC_OUTPUT[lang]
        lines = [
            t["heading"].format(band=d.band),
            t["freq"].format(freq=d.design_freq_mhz),
            t["element"].format(length=fmt(d.element_length_ft, d.element_length_m)),
            t["radials"].format(count=d.radial_count, length=fmt(d.radial_length_ft, d.radial_length_m)),
            t["impedance"].format(ohms=d.feedpoint_impedance_ohms),
            t["balun"].format(type=d.balun["type"], ratio=d.balun["ratio"], where=d.balun["where"]),
        ]
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", "\n".join(lines))

        self.advice_text.delete("1.0", "end")
        self.advice_text.insert("1.0", build_advice(d, units=units, lang=lang))

    def _export_svg(self):
        if not self.design:
            return
        path = filedialog.asksaveasfilename(defaultextension=".svg", filetypes=[("SVG", "*.svg")])
        if not path:
            return
        dwg = draw_vertical(self.design, units=self.units.get(), lang=self.lang.get())
        dwg.saveas(path)
        messagebox.showinfo(self._t("window_title"), self._t("saved").format(path=path))

    def _export_pdf(self):
        if not self.design:
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        try:
            tile_mast(self.design, path, units=self.units.get(), lang=self.lang.get())
        except Exception as exc:  # surfacing to the user, not a recoverable case
            messagebox.showerror(self._t("error"), str(exc))
            return
        messagebox.showinfo(self._t("window_title"), self._t("saved").format(path=path))


if __name__ == "__main__":
    app = AntennaDesignerApp()
    app.mainloop()
