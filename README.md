# HAM Antenna Designer

Practical antenna design tool for HAM radio operators and shortwave listeners.
Pick an antenna type and a band, get element/radial/counterpoise lengths,
feedpoint impedance, balun/unun/choke advice, plain-language build notes, and
a schematic drawing -- in a dark/amber GUI styled after HAMIOS.

Every formula is a documented, sourced rule of thumb (ARRL-style references,
Cebik/W4RNL's published Moxon regression equations, Palomar Engineers' SWL
unun specs, etc.) -- never guessed. Drawings are schematic, **not to scale**,
but every element carries its calculated dimension.

## Antenna types

The GUI's "Antenna" picker shows a **shape** (Vertical, Horizontal
center-fed, Horizontal end-fed, Horizontal loop, or one of the standalone
designs below); shapes that come in more than one real, documented
wavelength fraction get a second **Wave** picker next to it. A shape with
only one fraction (e.g. EFHW) or a standalone design (Yagi, J-pole, ...)
skips the Wave picker entirely -- it only appears where there's an actual
choice to make.

**Vertical** -- quarter wave / half wave (vertical EFHW) / 5/8 wave (gain,
needs a loading coil) / full wave (very high impedance, 64:1 unun)

**Horizontal, center-fed** -- half wave (the classic dipole) / extended
1.25λ (EDZ, more gain, needs a balanced tuner)

**Horizontal, end-fed** -- half wave (EFHW)

**Horizontal loop** -- full wave

**Standalone designs** (own fixed electrical design, not a shape+fraction
combination): Inverted-V dipole, Off-center-fed dipole (Windom), J-pole
(VHF/UHF), Vertical delta loop, 3-element Yagi, 2-element cubical quad,
Moxon rectangle.

**Receive-only (SWL / scanner), also standalone:**
- Long-wire receive (LW/MW/KW, 9:1 unun)
- Discone receive (VHF/UHF wideband, no balun needed)
- Loop-on-ground receive (LoG -- noise-canceling LW/MW DX loop)

A full-wave center-fed dipole was deliberately left out: it's not a
mainstream, well-documented design (a true wavelength-long center feed sits
on a current null, giving an oddly high, poorly-characterized impedance) --
the EDZ and full-wave loop already cover "more wire, more gain" with
formulas that are actually sourced.

## Bands

All HAM bands 160m-70cm, plus broadcast/SWL bands LW, MW, KW (general
shortwave), VHF, and UHF, plus the license-free/utility bands CB (11m
Citizens Band), Air (VHF aviation voice), Marine (VHF maritime mobile),
and PMR446 -- each band dropdown shows its frequency range.

## Features

- **GUI** (`gui.py`) -- dark background, amber accents, rounded panels,
  matches the HAMIOS look. Antenna type / band / units / language pickers,
  antenna wire and feed-cable velocity-factor selectors with 22 wire types
  and 44 cable types, live dynamic calculation, build notes, SVG export, and
  an in-app schematic viewer.
- **Antenna Wire Selection** -- 22 wire types (bare copper, Litz, PVC, 
  Silicone, PTFE, DX-Wire, Copperweld, CAT5/6, etc.) with velocity factors
  (0.95-0.98). Wire VF is integrated into all antenna calculations to match
  electrical length to actual wire properties.
- **Feed Cable Selection** -- 44 cable types including RG-series, LMR-series,
  Heliax, and specialty cables with velocity factors (0.66-0.97). Displayed
  for reference during design.
- **Dynamic Calculations** -- real-time antenna recalculation as you change
  antenna type, band, wire type, cable type, frequency, or units. No manual
  "Calculate" button needed.
- **In-app drawing viewer** -- glowing amber schematic on a dark,
  blueprint-grid canvas (not to scale), with a HUD-style corner frame,
  ground-hatching symbols, and every element, the balun/unun/choke, the
  feedpoint, and total antenna length clearly marked. A **2D/3D toggle**
  in the viewer switches to an isometric 3D rendering of the same design
  (mast + radial fan in a circle, Yagi boom-and-elements in depth, etc.)
  for antenna types where a 3D view adds something a flat side-view can't.
- **Balun/Unun Construction Guide** -- comprehensive popup guide with 9
  transformer ratios (1:1, 2:1, 4:1, 9:1, 16:1, 49:1, 64:1), construction
  instructions, impedance matching formulas, and material selection by band.
  Available in English and Dutch.
- **SVG export** -- black-on-white version of the 2D schematic (graph-paper
  grid, rounded component boxes, matching corner frame), for printing/sharing.
- **CLI** -- `antenna_calc.py`, `build_notes.py`, `drawing.py` all run
  standalone with `<antenna_type> <band> --units --lang`.
- **EN/NL** -- full bilingual support including wire names and balun guide.
  Dutch build notes use authentic HAM jargon (wave, choke, balun, unun, SWR
  stay English, as real Dutch hams say them) instead of literal textbook
  translation.
- **Settings persistence** -- language and units are remembered across runs.
- **Custom frequency** -- an optional exact-MHz override next to the band
  picker, for designing at a specific spot in (or outside) the band instead
  of the band's midpoint.

## Running it

### Quick Start (Recommended)
**Windows:** Download and run the standalone executable
- Get **HAM_Antenna_Designer.exe** from [Latest Release](https://github.com/fvdijke/ham-antenna-designer/releases/latest)
- Double-click the `.exe` file -- no Python installation needed
- All dependencies are bundled; just run and go

### From Source (Python Required)
**Windows:**
- Double-click **"Start HAM Antenna Designer.bat"** (or `.ps1` for PowerShell)
- Or from command prompt:
  ```
  cd ham-antenna-designer
  python -m venv .venv && .venv\Scripts\activate.bat && pip install -r requirements.txt
  python gui.py
  ```

**macOS/Linux:**
```
cd ham-antenna-designer
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python3 gui.py
```
Or just double-click **"Start HAM Antenna Designer.command"** on macOS.

## Architecture

- `data/` -- bands, antenna wire types (with velocity factor), feed cables
  (with velocity factor), antenna type metadata
- `calculators/` -- one module per antenna type, self-registering via
  `registry.py`'s `@register` decorator. Add a type: write one calculator,
  nothing else needs to know it exists.
- `scene.py` -- geometry math (where every line/label goes) lives here ONCE,
  as a renderer-agnostic `Scene`. Consumed by both `drawing.py` (SVG) and
  `canvas_view.py` (in-app dark/amber viewer) -- no duplicated geometry.
- `build_notes.py` / `format_text.py` -- per-type build advice and summary
  text, dispatched by antenna type.
- `i18n.py` -- all EN/NL strings.
- `gui.py` / `widgets.py` -- the Tkinter app and its custom rounded-panel /
  rounded-button canvas widgets (ttk's native theming silently drops colors
  on macOS, so buttons/panels are hand-drawn instead).
