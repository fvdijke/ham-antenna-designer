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
        "match_load": "Load/Antenna (Ohms):",
        "freq_mhz": "Frequency (MHz):",
        "values_positive": "All values must be positive",
        "m_header": "IMPEDANCE MATCHING NETWORK DESIGN",
        "m_source": "Source impedance: {v} Ohms",
        "m_load": "Load impedance: {v} Ohms",
        "m_freq": "Frequency: {v} MHz",
        "m_swr_before": "SWR (before matching): {v}:1",
        "m_option": "OPTION {i}: {name}",
        "m_topology": "Topology: {v}",
        "m_q": "Quality Factor (Q): {v}",
        "m_description": "Description: {v}",
        "m_components": "Component Values:",
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
        "char_l": ("Simplest design (2 components)", "Narrowest bandwidth (high Q)",
                   "Good for single-frequency matching"),
        "char_t": ("Moderate complexity (3 components)", "Medium bandwidth (lower Q than L-network)",
                   "Better impedance transformation"),
        "char_pi": ("Moderate complexity (3 components)", "Good filtering properties",
                    "Variable capacitors allow adjustment", "Popular in amateur radio tuners"),
        "m_notes": (
            "NOTES:\n"
            "  • Use standard component values nearest calculated values\n"
            "  • All inductors should be wound on appropriate cores\n"
            "  • Capacitors must handle expected power levels\n"
            "  • L-networks have narrowest bandwidth\n"
            "  • T/Pi networks provide better bandwidth\n"
            "  • After matching, antenna SWR should approach 1:1\n"
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
        "c_swr": "Antenna SWR: {v}:1",
        "c_losses": "LOSSES:",
        "c_cable_loss": "Cable loss: {v:.2f} dB",
        "c_swr_loss": "SWR loss: {v:.2f} dB",
        "c_total_loss": "Total loss: {v:.2f} dB",
        "c_budget": "POWER BUDGET (100W TX):",
        "c_power_ant": "Power at antenna: {v:.1f}W",
        "c_efficiency": "Efficiency: {v:.1f}%",
        "c_eirp": "EIRP: {v:.2f}W",
        "cable_error": "Cable Loss error",
        # ── radiation pattern ────────────────────────────────────────────────
        "rad_title": "Radiation Pattern",
        "rad_heading": "Azimuth Radiation Pattern (Horizontal Plane)",
        "rad_canvas": "Azimuth Pattern (Top View)",
        "rad_info": "Gain: {g:.1f} dBi  •  F/B Ratio: {fb:.1f} dB  •  Take-off: {toa:.0f}°",
        "rad_expl": (
            "RADIATION PATTERN EXPLANATION:\n\n"
            "• Pattern shows antenna directivity (top view/azimuth)\n"
            "• Wider lobes = radiation in that direction\n"
            "• Dipole: Omnidirectional (donut shaped)\n"
            "• Yagi: Directional with main lobe + side lobes\n"
            "• Vertical: Omnidirectional for skywave\n"
            "• F/B Ratio: How much better forward than backward\n"
            "• Gain (dBi): Power amplification vs isotropic source\n\n"
            "USE: Understand antenna directivity and coverage area"
        ),
        "rad_error": "Pattern error",
        "rad_expl_title": "Radiation Pattern Explanation",
        "swr_expl_title": "SWR & Impedance Matching Explanation",
        # ── SWR sweep ────────────────────────────────────────────────────────
        "sweep_title": "SWR Sweep",
        "sweep_heading": "SWR Sweep Analysis - Frequency Response",
        "sweep_axis": "Frequency (MHz)",
        "sweep_unavailable": "Sweep data unavailable",
        "sweep_info": ("Resonance: {res} MHz (SWR {swr}:1)  •  "
                       "Bandwidth (SWR ≤1.5): {lo}-{hi} MHz ({bw:.1f} MHz)"),
        "sweep_expl": (
            "SWR SWEEP EXPLANATION:\n\n"
            "• V-shaped curve shows SWR across the band\n"
            "• Lowest point = resonance frequency (best match)\n"
            "• Wider curve base = broader usable bandwidth\n"
            "• SWR ≤1.5:1 = acceptable for most operations\n"
            "• Marked point (AMBER) = resonance with minimum SWR\n"
            "• Bandwidth shows frequency range for SWR ≤1.5:1\n\n"
            "USE: Find best frequency for operation or antenna tuner needs"
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
        "match_load": "Belasting/antenne (ohm):",
        "freq_mhz": "Frequentie (MHz):",
        "values_positive": "Alle waarden moeten positief zijn",
        "m_header": "ONTWERP IMPEDANTIE-AANPASSINGSNETWERK",
        "m_source": "Bronimpedantie: {v} ohm",
        "m_load": "Belastingsimpedantie: {v} ohm",
        "m_freq": "Frequentie: {v} MHz",
        "m_swr_before": "SWR (vóór aanpassing): {v}:1",
        "m_option": "OPTIE {i}: {name}",
        "m_topology": "Topologie: {v}",
        "m_q": "Kwaliteitsfactor (Q): {v}",
        "m_description": "Beschrijving: {v}",
        "m_components": "Componentwaarden:",
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
        "char_l": ("Eenvoudigste ontwerp (2 componenten)", "Smalste bandbreedte (hoge Q)",
                   "Geschikt voor aanpassing op één frequentie"),
        "char_t": ("Gemiddelde complexiteit (3 componenten)",
                   "Gemiddelde bandbreedte (lagere Q dan L-netwerk)",
                   "Betere impedantietransformatie"),
        "char_pi": ("Gemiddelde complexiteit (3 componenten)", "Goede filtereigenschappen",
                    "Variabele condensatoren maken bijregelen mogelijk",
                    "Veel gebruikt in tuners voor zendamateurs"),
        "m_notes": (
            "OPMERKINGEN:\n"
            "  • Gebruik standaardwaarden die het dichtst bij de berekende waarden liggen\n"
            "  • Wikkel alle spoelen op een geschikte kern\n"
            "  • Condensatoren moeten het verwachte vermogen aankunnen\n"
            "  • L-netwerken hebben de smalste bandbreedte\n"
            "  • T-/Pi-netwerken geven meer bandbreedte\n"
            "  • Na aanpassing hoort de antenne-SWR richting 1:1 te gaan\n"
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
        "c_swr": "SWR antenne: {v}:1",
        "c_losses": "VERLIEZEN:",
        "c_cable_loss": "Kabelverlies: {v:.2f} dB",
        "c_swr_loss": "SWR-verlies: {v:.2f} dB",
        "c_total_loss": "Totaal verlies: {v:.2f} dB",
        "c_budget": "VERMOGENSBUDGET (100W zender):",
        "c_power_ant": "Vermogen bij de antenne: {v:.1f}W",
        "c_efficiency": "Rendement: {v:.1f}%",
        "c_eirp": "EIRP: {v:.2f}W",
        "cable_error": "Fout in kabelverlies",
        # ── stralingspatroon ─────────────────────────────────────────────────
        "rad_title": "Stralingspatroon",
        "rad_heading": "Azimut-stralingspatroon (horizontaal vlak)",
        "rad_canvas": "Azimutpatroon (bovenaanzicht)",
        "rad_info": "Versterking: {g:.1f} dBi  •  V/A-verhouding: {fb:.1f} dB  •  Afstraalhoek: {toa:.0f}°",
        "rad_expl": (
            "UITLEG STRALINGSPATROON:\n\n"
            "• Het patroon toont de richtwerking van de antenne (bovenaanzicht/azimut)\n"
            "• Bredere lobben = meer straling in die richting\n"
            "• Dipool: rondom stralend (donutvorm)\n"
            "• Yagi: gericht, met hoofdlob en zijlobben\n"
            "• Verticaal: rondom stralend voor ruimtegolf\n"
            "• V/A-verhouding: hoeveel sterker naar voren dan naar achteren\n"
            "• Versterking (dBi): vermogenswinst t.o.v. een isotrope straler\n\n"
            "GEBRUIK: inzicht in richtwerking en dekkingsgebied"
        ),
        "rad_error": "Fout in stralingspatroon",
        "rad_expl_title": "Uitleg stralingspatroon",
        "swr_expl_title": "Uitleg SWR en impedantie-aanpassing",
        # ── SWR-sweep ────────────────────────────────────────────────────────
        "sweep_title": "SWR-sweep",
        "sweep_heading": "SWR-sweep - frequentieverloop",
        "sweep_axis": "Frequentie (MHz)",
        "sweep_unavailable": "Geen sweepgegevens beschikbaar",
        "sweep_info": ("Resonantie: {res} MHz (SWR {swr}:1)  •  "
                       "Bandbreedte (SWR ≤1,5): {lo}-{hi} MHz ({bw:.1f} MHz)"),
        "sweep_expl": (
            "UITLEG SWR-SWEEP:\n\n"
            "• De V-vormige curve toont de SWR over de band\n"
            "• Laagste punt = resonantiefrequentie (beste aanpassing)\n"
            "• Bredere voet van de curve = grotere bruikbare bandbreedte\n"
            "• SWR ≤1,5:1 = acceptabel voor de meeste verbindingen\n"
            "• Gemarkeerd punt (AMBER) = resonantie met minimale SWR\n"
            "• De bandbreedte is het frequentiebereik met SWR ≤1,5:1\n\n"
            "GEBRUIK: vind de beste werkfrequentie, of zie of een tuner nodig is"
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
