"""English/Dutch text for the analysis popups (Smith chart, matching networks,
cable loss, radiation pattern, SWR sweep, final briefing).

Kept separate from UI_TEXT in gui.py so the main-window strings stay readable.
Use: pt(lang, key, **fmt) — falls back to English for a missing key.
"""

POPUP_TEXT = {
    "en": {
        # ── common ───────────────────────────────────────────────────────────
        "close": "Close",
        "calculate": "Calculate",
        "design_first": "Design an antenna first",
        "error_prefix": "Error",
        # ── Smith chart ──────────────────────────────────────────────────────
        "smith_expl_title": "Smith Chart Explanation",
        "smith_title": "Smith Chart",
        "smith_heading": "Smith Chart (50Ω) - Impedance Visualization",
        "smith_canvas": "Smith Chart (50Ω)",
        "smith_expl": (
            "SMITH CHART EXPLANATION:\n\n"
            "• Center point = 50Ω (perfect match, SWR 1:1)\n"
            "• Your antenna point (AMBER) = your impedance\n"
            "• Distance from center = mismatch severity\n"
            "• SWR circle (dashed line) = constant SWR\n"
            "• Circles = resistance curves\n"
            "• Arcs = reactance curves\n\n"
            "INTERPRETATION:\n"
            "• Closer to center = better match (lower SWR)\n"
            "• Right side = higher impedance\n"
            "• Left side = lower impedance\n"
        ),
        "smith_error": "Smith Chart error",
        # ── final briefing ───────────────────────────────────────────────────
        "brief_title": "Final Briefing - Complete Design Summary",
        "brief_heading": "FINAL BRIEFING - Design Summary & Build Instructions",
        "brief_schema": "ANTENNA SCHEMA (Simplified):",
        "brief_export": "Export as TXT",
        "brief_exported": "Briefing exported to:\n{path}",
        "brief_error": "Briefing error",
        "txt_files": "Text files",
        "all_files": "All files",
        "sch_radial": "Radial",
        "sch_mast": "Mast",
        "sch_feedpoint": "Feedpoint",
        "sch_radials_gp": "Radials (ground plane)",
        "sch_leg_a": "Leg A",
        "sch_leg_b": "Leg B",
        "sch_elem1": "(Element 1)",
        "sch_elem2": "(Element 2)",
        "sch_feed_cable": "Feed cable",
        "sch_end_high_z": "End (high impedance)",
        "sch_element": "Element",
        "sch_feedpoint_50": "Feedpoint (50 Ohms)",
        "sch_structure": "Antenna Structure",
        # ── matching networks ────────────────────────────────────────────────
        "match_title": "Impedance Matching Network Calculator",
        "match_heading": "Matching Network Design",
        "match_source": "Source (Ohms):",
        "match_load": "Load/antenna (R or R+jX, ohm):",
        "freq_mhz": "Frequency (MHz):",
        "values_positive": "All values must be positive",
        "m_header": "IMPEDANCE MATCHING NETWORK DESIGN",
        "m_source": "Source impedance: {v} Ohms",
        "m_load": "Load impedance: {v}",
        "m_freq": "Frequency: {v} MHz",
        "m_swr_before": "SWR (before matching): {v}:1",
        "m_option": "OPTION {i}: {name}",
        "m_topology": "Topology: {v}",
        "m_q": "Loaded Q: {v}",
        "m_rv": "Virtual resistance: {v} ohm",
        "m_check": "Check: Zin = {z} -> SWR {swr}:1  (with the E12 values: SWR {swr12}:1)",
        "m_matched": "The load already equals the source impedance -- no network needed.",
        "net_L_lowpass": "L-network, low-pass (series L, shunt C)",
        "net_L_highpass": "L-network, high-pass (series C, shunt L)",
        "net_L_other": "L-network (cancels the load reactance)",
        "net_Pi": "Pi-network, low-pass (C-L-C)",
        "net_T": "T-network, high-pass (C-L-C, the usual tuner)",
        "m_description": "Description: {v}",
        "m_components": "Components (from the source/transmitter side to the antenna):",
        "series_inductor": "Series Inductor",
        "shunt_capacitor": "Shunt Capacitor",
        "shunt_inductor": "Shunt Inductor",
        "series_capacitor": "Series Capacitor",
        "shunt_inductor_1": "Shunt Inductor 1",
        "shunt_inductor_2": "Shunt Inductor 2",
        "shunt_capacitor_1": "Shunt Capacitor 1",
        "shunt_capacitor_2": "Shunt Capacitor 2",
        "z_mid": "Impedance (midpoint)",
        "m_characteristics": "Characteristics:",
        "char_l": ("Simplest design (2 components), lowest loss",
                   "Q is fixed by the impedance ratio -- the lowest Q (widest bandwidth) possible"),
        "char_t": ("3 components; Q can be chosen freely (always above the L-network Q)",
                   "High-pass: does not suppress harmonics",
                   "The common amateur tuner: two variable capacitors and a (roller) coil"),
        "char_pi": ("3 components; Q can be chosen freely (always above the L-network Q)",
                    "Low-pass: suppresses harmonics",
                    "The classic valve PA output network (variable C's allow adjustment)"),
        "m_notes": (
            "NOTES:\n"
            "  • Values are exact for this load at this frequency; the check line proves the match\n"
            "  • The E12 SWR shows how critical the values are -- trim with variable parts\n"
            "  • Higher Q = narrower bandwidth, higher circulating current and more loss\n"
            "  • Components must handle the RF voltage and current at your power level\n"
            "  • Load R+jX: enter the measured antenna impedance (e.g. 36-j20) for a real match\n"
        ),
        "match_error": "Matching network error",
        # Topology/description phrases from matching_networks.py (English source)
        "phr": {},
        # ── cable loss ───────────────────────────────────────────────────────
        "cable_title": "Transmission Line Loss Calculator",
        "cable_heading": "Transmission Line Loss Analysis",
        "cable_len": "Cable length (meters):",
        "cable_type": "Cable type:",
        "antenna_swr": "Antenna SWR:",
        "c_freq": "Frequency: {v} MHz",
        "c_cable": "Cable: {cable} ({m}m = {ft:.0f}ft)",
        "c_swr": "Antenna SWR: {v}:1 (on the {z0:g} ohm line)",
        "c_losses": "LOSSES:",
        "c_cable_loss": "Cable loss (matched): {v:.2f} dB",
        "c_swr_loss": "Extra loss from SWR on the line: {v:.2f} dB",
        "c_total_loss": "Total loss: {v:.2f} dB",
        "c_budget": "POWER BUDGET (100W TX):",
        "c_power_ant": "Power at antenna: {v:.1f}W",
        "c_efficiency": "Efficiency: {v:.1f}%",
        "c_eirp": "EIRP: {v:.2f}W",
        "c_note": ("Assumes the transmitter (or a tuner in the shack) is matched to the line input:\n"
                   "reflected power is not lost, it only makes extra passes through the lossy cable.\n"
                   "Cable loss from typical datasheet values; SWR is taken against the cable's own impedance."),
        "cable_error": "Cable Loss error",
        # ── radiation pattern ────────────────────────────────────────────────
        "rad_title": "Radiation Pattern",
        "rad_heading": "Radiation Pattern (computed from the antenna geometry)",
        "rad_height": "Height (m):",
        "rad_ground": "Ground:",
        "ground_average": "Average ground",
        "ground_perfect": "Perfect ground",
        "ground_free": "Free space",
        "rad_at": "at {h:g} m, {g}",
        "rad_az_title": "Azimuth - top view, at {el}° elevation",
        "rad_az_title_free": "Azimuth - top view, horizontal plane",
        "rad_el_title": "Elevation - side view, through the main lobe",
        "rad_front": "front",
        "rad_back": "back",
        "rad_toa_none": "- (free space)",
        "rad_omni": "omnidirectional",
        "rad_pol_h": "horizontal",
        "rad_pol_v": "vertical",
        "rad_info": ("Gain: {g:.1f} dBi ({gd:+.1f} dBd)   •   Take-off angle: {toa}   •   F/B: {fb}\n"
                     "-3 dB beamwidth: {bw}   •   Polarisation: {pol}"),
        "rad_expl": (
            "RADIATION PATTERN EXPLANATION:\n\n"
            "• Computed from the wire geometry and its standing-wave currents; beam element currents\n"
            "  from mutual impedances. The scale is in dB: outer ring = maximum, rings at -3/-6/-10/-20 dB\n"
            "• Height = the lowest point / feedpoint above the ground; the ground reflection shapes the\n"
            "  elevation pattern (low dipoles radiate mostly upward = NVIS; higher = lower take-off angle)\n"
            "• Over real ground a vertical loses its lowest angles; a horizontal antenna needs height\n"
            "• Gain = directivity incl. ground reflection, excluding ground and wire losses\n"
            "  (real verticals typically lose another 1-3 dB in the ground)\n"
            "• Take-off angle = elevation of maximum radiation: low (<20°) for DX, high for short range\n\n"
            "USE: choose height and orientation -- azimuth 0° = broadside / beam direction"
        ),
        "rad_error": "Pattern error",
        "rad_expl_title": "Radiation Pattern Explanation",
        "swr_expl_title": "SWR & Impedance Matching Explanation",
        # ── SWR sweep ────────────────────────────────────────────────────────
        "sweep_title": "SWR Sweep",
        "sweep_heading": "SWR Sweep Analysis - Frequency Response",
        "sweep_axis": "Frequency (MHz)",
        "sweep_unavailable": "Sweep data unavailable",
        "sweep_info": "Resonance: {res} MHz (SWR {swr}:1)  •  SWR ≤ 2: {bw}  •  Q ≈ {q}",
        "sweep_bw": "{lo:.3f}-{hi:.3f} MHz ({khz:.0f} kHz)",
        "sweep_bw_none": "nowhere (a matching network is needed)",
        "sweep_na_broadband": ("Broadband receive antenna: there is no single resonance, "
                               "so there is no SWR curve to show."),
        "sweep_na_tuner": ("This antenna is fed through open-wire line and a tuner: its SWR depends "
                           "on the tuner setting, not on a single resonance."),
        "sweep_expl": (
            "SWR SWEEP EXPLANATION:\n\n"
            "• The curve is the SWR of the antenna as built (dimensions fixed at the design\n"
            "  frequency), seen on 50-ohm coax behind its balun/unun\n"
            "• Model: a resonant circuit whose Q follows from the wire thickness (2 mm);\n"
            "  real height, ground and surroundings shift the dip -- trim the wire to place it\n"
            "• Longer wire moves the dip down, shorter moves it up (about the same percentage)\n"
            "• Dot = resonance (design frequency); blue dashed lines = band edges;\n"
            "  amber dashed line = SWR 2:1, the usual limit without a tuner\n\n"
            "USE: see whether the whole band fits under 2:1 or where a tuner is needed"
        ),
        "sweep_error": "Sweep error",
    },
    "nl": {
        # ── algemeen ─────────────────────────────────────────────────────────
        "close": "Sluiten",
        "calculate": "Berekenen",
        "design_first": "Ontwerp eerst een antenne",
        "error_prefix": "Fout",
        # ── Smith-diagram ────────────────────────────────────────────────────
        "smith_expl_title": "Uitleg Smith-diagram",
        "smith_title": "Smith-diagram",
        "smith_heading": "Smith-diagram (50Ω) - impedantieweergave",
        "smith_canvas": "Smith-diagram (50Ω)",
        "smith_expl": (
            "UITLEG SMITH-DIAGRAM:\n\n"
            "• Middelpunt = 50Ω (perfecte aanpassing, SWR 1:1)\n"
            "• Jouw antennepunt (AMBER) = jouw impedantie\n"
            "• Afstand tot het midden = mate van mismatch\n"
            "• SWR-cirkel (stippellijn) = constante SWR\n"
            "• Cirkels = weerstandscurven\n"
            "• Bogen = reactantiecurven\n\n"
            "INTERPRETATIE:\n"
            "• Dichter bij het midden = betere aanpassing (lagere SWR)\n"
            "• Rechterkant = hogere impedantie\n"
            "• Linkerkant = lagere impedantie\n"
        ),
        "smith_error": "Fout in Smith-diagram",
        # ── eindoverzicht ────────────────────────────────────────────────────
        "brief_title": "Eindoverzicht - volledige ontwerpsamenvatting",
        "brief_heading": "EINDOVERZICHT - ontwerpsamenvatting en bouwinstructies",
        "brief_schema": "ANTENNESCHEMA (vereenvoudigd):",
        "brief_export": "Exporteren als TXT",
        "brief_exported": "Overzicht geëxporteerd naar:\n{path}",
        "brief_error": "Fout in eindoverzicht",
        "txt_files": "Tekstbestanden",
        "all_files": "Alle bestanden",
        "sch_radial": "Radiaal",
        "sch_mast": "Mast",
        "sch_feedpoint": "Voedingspunt",
        "sch_radials_gp": "Radialen (grondvlak)",
        "sch_leg_a": "Been A",
        "sch_leg_b": "Been B",
        "sch_elem1": "(Element 1)",
        "sch_elem2": "(Element 2)",
        "sch_feed_cable": "Voedingskabel",
        "sch_end_high_z": "Uiteinde (hoge impedantie)",
        "sch_element": "Element",
        "sch_feedpoint_50": "Voedingspunt (50 ohm)",
        "sch_structure": "Antenneconstructie",
        # ── aanpassingsnetwerken ─────────────────────────────────────────────
        "match_title": "Calculator impedantie-aanpassingsnetwerk",
        "match_heading": "Ontwerp aanpassingsnetwerk",
        "match_source": "Bron (ohm):",
        "match_load": "Belasting/antenne (R of R+jX, ohm):",
        "freq_mhz": "Frequentie (MHz):",
        "values_positive": "Alle waarden moeten positief zijn",
        "m_header": "ONTWERP IMPEDANTIE-AANPASSINGSNETWERK",
        "m_source": "Bronimpedantie: {v} ohm",
        "m_load": "Belastingsimpedantie: {v}",
        "m_freq": "Frequentie: {v} MHz",
        "m_swr_before": "SWR (vóór aanpassing): {v}:1",
        "m_option": "OPTIE {i}: {name}",
        "m_topology": "Topologie: {v}",
        "m_q": "Belaste Q: {v}",
        "m_rv": "Virtuele weerstand: {v} ohm",
        "m_check": "Controle: Zin = {z} -> SWR {swr}:1  (met de E12-waarden: SWR {swr12}:1)",
        "m_matched": "De belasting is al gelijk aan de bronimpedantie -- geen netwerk nodig.",
        "net_L_lowpass": "L-netwerk, laagdoorlaat (L in serie, C naar massa)",
        "net_L_highpass": "L-netwerk, hoogdoorlaat (C in serie, L naar massa)",
        "net_L_other": "L-netwerk (compenseert de reactantie van de belasting)",
        "net_Pi": "Pi-netwerk, laagdoorlaat (C-L-C)",
        "net_T": "T-netwerk, hoogdoorlaat (C-L-C, de gangbare tuner)",
        "m_description": "Beschrijving: {v}",
        "m_components": "Componenten (van de bron/zenderkant naar de antenne):",
        "series_inductor": "Spoel in serie",
        "shunt_capacitor": "Condensator naar massa",
        "shunt_inductor": "Spoel naar massa",
        "series_capacitor": "Condensator in serie",
        "shunt_inductor_1": "Spoel naar massa 1",
        "shunt_inductor_2": "Spoel naar massa 2",
        "shunt_capacitor_1": "Condensator naar massa 1",
        "shunt_capacitor_2": "Condensator naar massa 2",
        "z_mid": "Impedantie (middenpunt)",
        "m_characteristics": "Eigenschappen:",
        "char_l": ("Eenvoudigste ontwerp (2 componenten), laagste verlies",
                   "Q ligt vast door de impedantieverhouding -- de laagst mogelijke Q (breedste bandbreedte)"),
        "char_t": ("3 componenten; Q vrij te kiezen (altijd boven de Q van het L-netwerk)",
                   "Hoogdoorlaat: onderdrukt geen harmonischen",
                   "De gangbare amateurtuner: twee variabele condensatoren en een (rol)spoel"),
        "char_pi": ("3 componenten; Q vrij te kiezen (altijd boven de Q van het L-netwerk)",
                    "Laagdoorlaat: onderdrukt harmonischen",
                    "Het klassieke uitgangsnetwerk van buizen-PA's (variabele C's om bij te regelen)"),
        "m_notes": (
            "OPMERKINGEN:\n"
            "  • De waarden zijn exact voor deze belasting op deze frequentie; de controleregel bewijst de aanpassing\n"
            "  • De E12-SWR laat zien hoe kritisch de waarden zijn -- regel bij met variabele onderdelen\n"
            "  • Hogere Q = smallere bandbreedte, hogere circulerende stroom en meer verlies\n"
            "  • Onderdelen moeten de HF-spanning en -stroom bij jouw vermogen aankunnen\n"
            "  • Belasting R+jX: vul de gemeten antenne-impedantie in (bijv. 36-j20) voor een echte aanpassing\n"
        ),
        "match_error": "Fout in aanpassingsnetwerk",
        # Vertaling van de Engelse topologie-/beschrijvingsteksten uit matching_networks.py
        "phr": {
            "Series L, Shunt C": "L in serie, C naar massa",
            "Shunt L, Series C": "L naar massa, C in serie",
            "Shunt L, Series C, Shunt L": "L naar massa, C in serie, L naar massa",
            "Shunt C, Series L, Shunt C": "C naar massa, L in serie, C naar massa",
            "Inductor": "Spoel",
            "Capacitor": "Condensator",
            "in series": "in serie",
            "to ground": "naar massa",
        },
        # ── kabelverlies ─────────────────────────────────────────────────────
        "cable_title": "Calculator kabelverlies",
        "cable_heading": "Analyse kabelverlies",
        "cable_len": "Kabellengte (meter):",
        "cable_type": "Kabeltype:",
        "antenna_swr": "SWR antenne:",
        "c_freq": "Frequentie: {v} MHz",
        "c_cable": "Kabel: {cable} ({m}m = {ft:.0f}ft)",
        "c_swr": "SWR antenne: {v}:1 (op de {z0:g} ohm-lijn)",
        "c_losses": "VERLIEZEN:",
        "c_cable_loss": "Kabelverlies (aangepast): {v:.2f} dB",
        "c_swr_loss": "Extra verlies door SWR op de kabel: {v:.2f} dB",
        "c_total_loss": "Totaal verlies: {v:.2f} dB",
        "c_budget": "VERMOGENSBUDGET (100W zender):",
        "c_power_ant": "Vermogen bij de antenne: {v:.1f}W",
        "c_efficiency": "Rendement: {v:.1f}%",
        "c_eirp": "EIRP: {v:.2f}W",
        "c_note": ("Aanname: de zender (of een tuner in de shack) is aangepast aan de kabelingang:\n"
                   "gereflecteerd vermogen gaat niet verloren, het doorloopt de verliesgevende kabel alleen extra keren.\n"
                   "Kabelverlies uit typische datasheetwaarden; SWR t.o.v. de eigen impedantie van de kabel."),
        "cable_error": "Fout in kabelverlies",
        # ── stralingspatroon ─────────────────────────────────────────────────
        "rad_title": "Stralingspatroon",
        "rad_heading": "Stralingspatroon (berekend uit de antennegeometrie)",
        "rad_height": "Hoogte (m):",
        "rad_ground": "Bodem:",
        "ground_average": "Gemiddelde bodem",
        "ground_perfect": "Perfecte bodem",
        "ground_free": "Vrije ruimte",
        "rad_at": "op {h:g} m, {g}",
        "rad_az_title": "Azimut - bovenaanzicht, op {el}° elevatie",
        "rad_az_title_free": "Azimut - bovenaanzicht, horizontaal vlak",
        "rad_el_title": "Elevatie - zijaanzicht, door de hoofdlob",
        "rad_front": "voor",
        "rad_back": "achter",
        "rad_toa_none": "- (vrije ruimte)",
        "rad_omni": "rondom",
        "rad_pol_h": "horizontaal",
        "rad_pol_v": "verticaal",
        "rad_info": ("Versterking: {g:.1f} dBi ({gd:+.1f} dBd)   •   Afstraalhoek: {toa}   •   V/A: {fb}\n"
                     "-3 dB-bundelbreedte: {bw}   •   Polarisatie: {pol}"),
        "rad_expl": (
            "UITLEG STRALINGSPATROON:\n\n"
            "• Berekend uit de draadgeometrie en de staandegolfstromen; elementstromen van beams\n"
            "  uit de wederzijdse impedanties. Schaal in dB: buitenste ring = maximum, ringen op -3/-6/-10/-20 dB\n"
            "• Hoogte = laagste punt / voedingspunt boven de bodem; de bodemreflectie vormt het\n"
            "  elevatiepatroon (lage dipolen stralen vooral omhoog = NVIS; hoger = lagere afstraalhoek)\n"
            "• Boven echte bodem verliest een verticaal de laagste hoeken; een horizontale antenne heeft hoogte nodig\n"
            "• Versterking = richtingsfactor incl. bodemreflectie, zonder bodem- en draadverliezen\n"
            "  (echte verticals verliezen doorgaans nog 1-3 dB in de bodem)\n"
            "• Afstraalhoek = elevatie van de maximale straling: laag (<20°) voor DX, hoog voor korte afstand\n\n"
            "GEBRUIK: kies hoogte en richting -- azimut 0° = dwars op de draad / bundelrichting"
        ),
        "rad_error": "Fout in stralingspatroon",
        "rad_expl_title": "Uitleg stralingspatroon",
        "swr_expl_title": "Uitleg SWR en impedantie-aanpassing",
        # ── SWR-sweep ────────────────────────────────────────────────────────
        "sweep_title": "SWR-sweep",
        "sweep_heading": "SWR-sweep - frequentieverloop",
        "sweep_axis": "Frequentie (MHz)",
        "sweep_unavailable": "Geen sweepgegevens beschikbaar",
        "sweep_info": "Resonantie: {res} MHz (SWR {swr}:1)  •  SWR ≤ 2: {bw}  •  Q ≈ {q}",
        "sweep_bw": "{lo:.3f}-{hi:.3f} MHz ({khz:.0f} kHz)",
        "sweep_bw_none": "nergens (er is een aanpasnetwerk nodig)",
        "sweep_na_broadband": ("Breedband-ontvangstantenne: er is geen enkele resonantie, "
                               "dus er is geen SWR-curve te tonen."),
        "sweep_na_tuner": ("Deze antenne wordt via open lijn en een tuner gevoed: de SWR hangt af "
                           "van de tunerinstelling, niet van een enkele resonantie."),
        "sweep_expl": (
            "UITLEG SWR-SWEEP:\n\n"
            "• De curve is de SWR van de antenne zoals gebouwd (afmetingen vast op de\n"
            "  ontwerpfrequentie), gezien op 50 ohm coax achter de balun/unun\n"
            "• Model: een resonantiekring waarvan de Q volgt uit de draaddikte (2 mm);\n"
            "  echte hoogte, bodem en omgeving verschuiven de dip -- knip de draad bij om hem te plaatsen\n"
            "• Langere draad schuift de dip omlaag, kortere omhoog (ongeveer hetzelfde percentage)\n"
            "• Punt = resonantie (ontwerpfrequentie); blauwe stippellijnen = bandgrenzen;\n"
            "  amber stippellijn = SWR 2:1, de gebruikelijke grens zonder tuner\n\n"
            "GEBRUIK: zie of de hele band onder 2:1 past of waar een tuner nodig is"
        ),
        "sweep_error": "Fout in SWR-sweep",
    },
}


def pt(lang: str, key: str, **fmt):
    """Popup text in the requested language (English fallback)."""
    table = POPUP_TEXT.get(lang, POPUP_TEXT["en"])
    value = table.get(key, POPUP_TEXT["en"].get(key, key))
    return value.format(**fmt) if fmt and isinstance(value, str) else value


def translate_phrases(lang: str, text: str) -> str:
    """Translate the English topology/description phrases of matching_networks.py.
    Longest phrases first, so combined topologies win over single words."""
    phr = POPUP_TEXT.get(lang, {}).get("phr") or {}
    for src in sorted(phr, key=len, reverse=True):
        text = text.replace(src, phr[src])
    return text
