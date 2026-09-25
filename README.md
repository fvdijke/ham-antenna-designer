# HAM Antenna Designer

<img width="1465" height="1203" alt="HAM Antenna Designer-1" src="https://github.com/user-attachments/assets/e99a0ce6-fe18-4785-8c71-5a798d008be6" />


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

<img width="1023" height="829" alt="HAM Antenna Designer-2" src="https://github.com/user-attachments/assets/032b215c-b35d-4bff-8425-a43580f48c36" />

## Bands

All HAM bands 160m-70cm (including 60m), with the band edges of IARU
Region 1 (Europe/Africa/Middle East, default) or Region 2 (the Americas),
plus the license-free/utility bands CB (11m Citizens Band), Air (VHF
aviation voice), Marine (VHF maritime mobile) and PMR446. The broadcast/SWL
ranges LW, MW, KW (general shortwave), VHF and UHF are offered for the
receive antennas only -- a single design frequency in the middle of e.g.
1.6-30 MHz means nothing for a resonant transmit antenna.

## Features

### Analysis tools

- **SWR & Impedance Matching**
  - SWR (complex impedance, as seen on the coax behind the balun/unun) with
    Smith Chart visualization
  - SWR sweep of the antenna as built: a resonance model whose Q follows from
    the wire thickness, showing where the band fits under 2:1
  - Matching network designer for a real or complex load (enter e.g. 36-j20):
    every L-network solution plus a low-pass Pi and a high-pass T, each
    verified by recomputing Zin, with E12 standard values and the SWR they give

- **Radiation Pattern**
  - Computed from the antenna geometry: standing-wave currents on the wires,
    Yagi/quad element currents from mutual impedances, ground reflection with
    real-ground Fresnel coefficients
  - Azimuth and elevation plots at a chosen height over average ground,
    perfect ground or free space; gain (dBi/dBd), take-off angle, F/B,
    -3 dB beamwidth

- **Transmission Line Loss Calculator**
  - All 44 cables with typical datasheet loss (fitted k1*sqrt(f) + k2*f)
  - Extra loss from SWR on the line (ARRL formula), SWR taken against the
    cable's own impedance (ladder line 450/600 ohm)
  - Power budget: power at the antenna, efficiency, EIRP
  
- **Final Briefing Report**
  - Complete design summary with antenna schema (ASCII art)
  - Step-by-step build instructions
  - Construction checklist with materials & safety notes
  - Bilingual (English/Dutch)
  - Export to TXT file

- **GUI** (`gui.py`) -- dark background, amber accents, rounded panels,
  matches the HAMIOS look. Antenna type / band / units / language pickers,
  antenna wire and feed-cable selectors with 22 wire types and 44 cable
  types, IARU region choice, live dynamic calculation, build notes, SVG
  export, and comprehensive analysis tools.
- **Antenna Wire Selection** -- 22 wire types (bare copper, Litz, PVC,
  Silicone, PTFE, DX-Wire, Copperweld, CAT5/6, etc.). The rules of thumb
  (468/f, 234/f, 1005/f, ...) are for bare wire and already contain the end
  effect, so insulation is applied only RELATIVE to bare wire
  (factor = VF / 0.98: PVC ~0.97, PTFE ~0.99). Beam spacings stay free-space
  values; only wire dimensions are corrected.
- **Feed Cable Selection** -- 44 cable types including RG-series, LMR-series,
  Heliax, and ladder line, with velocity factor, impedance and loss data.
- **Dynamic Calculations** -- real-time antenna recalculation as you change
  antenna type, band, wire type, cable type, frequency, or units. No manual
  "Calculate" button needed.
- **In-app drawing viewer** -- a schematic of the antenna with the
  radiator, counterpoise/radials, parasitic elements, feed line (coax or
  ladder line) to the shack, the balun/unun/choke AT the feedpoint, masts,
  ropes, insulators and the ground point, each in its own colour and line
  style. **2D/3D** (cabinet front or top view / isometric) and **Day/Night**
  (technical drawing on paper / electronics schematic) toggles; the choice is
  remembered. All text sits in labelled callouts beside the drawing or next
  to its dimension line -- a layout check keeps text off the drawing.
- **Balun/Unun Construction Guide** -- 1:1 current balun, 4:1 Guanella,
  loop matching, 9:1, 49:1 and 64:1 ununs and the loop-on-ground
  transformer, with turns ratios (impedance ratio = turns ratio squared),
  cores and material selection. Available in English and Dutch.
- **SVG export** -- the same schematic as a light situation sketch (lawn,
  masts, copper wire, blue counterpoise, black coax to a little shack), for
  printing and sharing.
- **CLI** -- `antenna_calc.py`, `build_notes.py`, `drawing.py` all run
  standalone with `<antenna_type> <band> --units --lang`.
- **EN/NL** -- full bilingual support including wire names and balun guide.
  Dutch build notes use authentic HAM jargon (wave, choke, balun, unun, SWR
  stay English, as real Dutch hams say them) instead of literal textbook
  translation.
- **Settings persistence** -- language, units and IARU region are remembered
  across runs.
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
- `schematic.py` -- ONE world model per antenna (roles: radiator,
  counterpoise, feed line, balun, ground, supports) and the page layout for
  2D and 3D, including collision-free label placement.
  `schematic_render.py` -- the night/day/print themes, painted through one
  painter interface onto a Tk canvas (`canvas_view.py`) or into SVG
  (`drawing.py`).
- `build_notes.py` / `format_text.py` -- per-type build advice and summary
  text, dispatched by antenna type.
- `tests/` -- reference checks against ARRL/Cebik/Kraus values
  (`python -m unittest discover tests`).
- `i18n.py` -- all EN/NL strings.
- `gui.py` / `widgets.py` -- the Tkinter app and its custom rounded-panel /
  rounded-button canvas widgets (ttk's native theming silently drops colors
  on macOS, so buttons/panels are hand-drawn instead).
