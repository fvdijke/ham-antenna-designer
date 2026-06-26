"""Shared English/Dutch text strings for CLI output and printed templates.

Only display text is translated. Formulas, units math, and data keys
(band names, internal dict keys) stay in English/standard form.
"""

ROLE_LABELS = {
    "radiator": {"en": "Radiator", "nl": "Stralend element"},
    "radial": {"en": "Radials", "nl": "Radialen"},
    "counterpoise": {"en": "Counterpoise", "nl": "Counterpoise"},
}

SUMMARY_LABELS = {
    "en": {
        "freq": "Design frequency",
        "impedance": "Feedpoint impedance",
        "ohms": "ohms",
        "balun": "Balun/unun",
        "each": "each",
    },
    "nl": {
        "freq": "Ontwerpfrequentie",
        "impedance": "Voedingspunt impedantie",
        "ohms": "ohm",
        "balun": "Balun/unun",
        "each": "elk",
    },
}

BALUN_WHERE = {
    "en": "at the feedpoint, on the coax just before it connects to the base of the vertical element",
    "nl": "bij het voedingspunt, op de coax net voordat deze de voet van het mastelement bereikt",
}

BALUN_WHY = {
    "en": "suppresses common-mode current on the coax shield; a quarter-wave vertical with ground-mounted radials is fed directly, so no impedance-transforming unun is needed",
    "nl": "onderdrukt common-mode stroom op het coax-scherm; een kwartgolf verticaal met grondradialen wordt direct gevoed, dus is er geen impedantie-transformerende unun nodig",
}

BALUN_WHERE_DIPOLE = {
    "en": "at the center feedpoint, between the coax and the two dipole legs",
    "nl": "bij het middenvoedingspunt, tussen de coax en de twee dipoolbenen",
}

BALUN_WHY_DIPOLE = {
    "en": "converts the unbalanced coax feed to the balanced dipole and suppresses common-mode current/RF-in-the-shack",
    "nl": "zet de ongebalanceerde coaxvoeding om naar de gebalanceerde dipool en onderdrukt common-mode stroom/RF-in-de-shack",
}

BALUN_WHERE_EFHW = {
    "en": "at the feedpoint, where the unun box connects to the high-impedance end of the wire",
    "nl": "bij het voedingspunt, waar de unun-behuizing verbinding maakt met het hoge-impedantie-einde van de draad",
}

BALUN_WHY_EFHW = {
    "en": "transforms the high impedance (roughly 2000-4500 ohms) at the end-fed point down to ~50 ohms for the coax/radio",
    "nl": "transformeert de hoge impedantie (ongeveer 2000-4500 ohm) op het end-fed punt omlaag naar ~50 ohm voor de coax/radio",
}

DRAWING = {
    "en": {
        "element_label": "Element: {length}",
        "radial_label": "Radial x{count}: {length} each",
        "counterpoise_label": "Counterpoise: {length}",
        "feedpoint_label": "Feedpoint: ~{ohms} ohms, {balun_type} ({balun_ratio})",
        "band_label": "{band} band -- design freq {freq} MHz",
    },
    "nl": {
        "element_label": "Element: {length}",
        "radial_label": "Radiaal x{count}: {length} elk",
        "counterpoise_label": "Counterpoise: {length}",
        "feedpoint_label": "Voedingspunt: ~{ohms} ohm, {balun_type} ({balun_ratio})",
        "band_label": "{band} band -- ontwerpfreq {freq} MHz",
    },
}

TILE_PDF = {
    "nl": {
        "title": "{label} ({band}) -- afdruksjabloon op echte schaal",
        "instructions": "Print op 100% schaal (geen 'aanpassen aan pagina'), knip af tot de overlapstrook en plak de pagina's aaneen met de uitlijnmarkeringen.",
        "element_label": "Element: {length}",
        "cut_count_note": "Knip {count}x van dit sjabloon (gelijke lengte elementen).",
        "tile_label": "Tegel rij {row}/{rows}, kolom {col}/{cols} -- lijn overlapstrook uit met buurtegel",
        "other_elements_note": "Overige elementen niet op schaal afgedrukt -- meet ze met een rolmaat (zie bouwnotities): {detail}",
        "saved": "Sjabloon van {tiles} pagina('s) op echte schaal opgeslagen in {path}",
        "print_hint": "Print op 100% schaal (geen 'aanpassen aan pagina'), knip bij tot de uitlijnmarkering en plak de tegels aan elkaar.",
    },
    "en": {
        "title": "{label} ({band}) -- true-to-scale print template",
        "instructions": "Print at 100% scale (no 'fit to page'), trim to the overlap strip, and tape pages together using the alignment marks.",
        "element_label": "Element: {length}",
        "cut_count_note": "Cut {count}x from this template (equal-length elements).",
        "tile_label": "Tile row {row}/{rows}, col {col}/{cols} -- align overlap strip with neighbor",
        "other_elements_note": "Other elements not printed to scale -- measure with a tape measure (see build notes): {detail}",
        "saved": "Saved {tiles}-page true-to-scale template to {path}",
        "print_hint": "Print at 100% scale (no 'fit to page'), trim to the overlap strip, and tape tiles together.",
    },
}

BUILD_NOTES_DIPOLE = {
    "en": {
        "title": "Build notes -- {band} half-wave dipole",
        "step1": "1. Cut two legs, each {length} long. Connect both to the center insulator/feedpoint,\n   one to each side of the balun.",
        "step2": "2. Mount horizontally (or as an inverted-V / sloper if space is tight) -- height above ground\n   matters more for radiation pattern than exact straightness.",
        "step3": "3. Feedpoint: connect coax through the balun to the center insulator. Expect ~{ohms} ohms\n   feedpoint impedance in free space -- height and nearby objects will shift this somewhat.",
        "step4": "4. Balun: use {balun_type} ({balun_ratio}) at the center feedpoint -- {balun_why}.",
        "step5": "5. End insulators: use proper egg/dogbone insulators at each leg end, not just knots in the wire,\n   to avoid the wire stretching or breaking under wind load.",
    },
    "nl": {
        "title": "Bouwnotities -- {band} halve-golf dipool",
        "step1": "1. Knip twee benen van elk {length} lang. Verbind beide met de middenisolator/het voedingspunt,\n   elk aan een kant van de balun.",
        "step2": "2. Monteer horizontaal (of als inverted-V / sloper bij weinig ruimte) -- de hoogte boven de grond\n   is belangrijker voor het stralingspatroon dan exacte rechtheid.",
        "step3": "3. Voedingspunt: verbind de coax via de balun met de middenisolator. Verwacht ~{ohms} ohm\n   voedingspuntimpedantie in de vrije ruimte -- hoogte en nabije objecten wijken hier iets van af.",
        "step4": "4. Balun: gebruik {balun_type} ({balun_ratio}) bij het middenvoedingspunt -- {balun_why}.",
        "step5": "5. Eindisolatoren: gebruik echte eier-/dogbone-isolatoren aan elk beneinde, niet alleen knopen in de draad,\n   om rek of breuk onder windbelasting te voorkomen.",
    },
}

BUILD_NOTES_EFHW = {
    "en": {
        "title": "Build notes -- {band} end-fed half-wave (EFHW)",
        "step1": "1. Cut the radiator wire to {length}. This is the full radiating element, fed at one end.",
        "step2": "2. Cut a counterpoise wire to {length_cp} and connect it to the unun's ground lug --\n   this is not a resonant radial system, just a return path for the unun.",
        "step3": "3. Feedpoint: connect the high-impedance end of the radiator and the counterpoise to the unun.\n   Expect ~{ohms} ohms at this point before the unun transforms it down to ~50 ohms.",
        "step4": "4. Unun: use a {balun_type} ({balun_ratio}) at the feedpoint -- {balun_why}.",
        "step5": "5. Routing: keep the counterpoise away from the radiator run (don't let them run parallel close together) --\n   and route the radiator away from metal structures, which detune it.",
    },
    "nl": {
        "title": "Bouwnotities -- {band} end-fed halve golf (EFHW)",
        "step1": "1. Knip de stralende draad af op {length}. Dit is het volledige stralende element, gevoed aan een einde.",
        "step2": "2. Knip een counterpoise-draad af op {length_cp} en verbind deze met de aardlip van de unun --\n   dit is geen resonant radialensysteem, slechts een retourpad voor de unun.",
        "step3": "3. Voedingspunt: verbind het hoge-impedantie-einde van de straler en de counterpoise met de unun.\n   Verwacht ~{ohms} ohm op dit punt voordat de unun dit omlaag transformeert naar ~50 ohm.",
        "step4": "4. Unun: gebruik een {balun_type} ({balun_ratio}) bij het voedingspunt -- {balun_why}.",
        "step5": "5. Routering: houd de counterpoise weg van de stralende draad (laat ze niet dicht parallel lopen) --\n   en houd de straler weg van metalen constructies, die hem ontstemmen.",
    },
}

CHOKE_SPEC = {
    "en": "{turns_toroid} turns of RG-58/RG-8X on a FT240-43 toroid (or {turns_pipe} turns on a {pipe_size} inch PVC pipe)",
    "nl": "{turns_toroid} wikkelingen RG-58/RG-8X op een FT240-43 toroide (of {turns_pipe} wikkelingen op een PVC-buis van {pipe_size} inch)",
}

BUILD_NOTES = {
    "en": {
        "title": "Build notes -- {band} ground-mounted quarter-wave vertical",
        "step1": "1. Element: cut a single length of wire or tubing to {length}.\n   Mount it vertically, insulated from the ground (a PVC mast or insulated base works).",
        "step2": (
            "2. Radials: lay out {count} radials, each {length} long,\n"
            "   spread evenly around the base (this design assumes equal angular spacing).\n"
            "   They can lie on the ground or be buried a few cm deep -- elevated radials work too,\n"
            "   but then 2-4 elevated radials resonant at this band's quarter-wave is the more common\n"
            "   approach rather than many ground-laid ones."
        ),
        "step3": (
            "3. Feedpoint: connect the coax center conductor to the base of the vertical element,\n"
            "   and the coax shield / radials to a common ground point. Expect ~{ohms} ohms\n"
            "   feedpoint impedance under ideal conditions -- real-world radial count/soil will shift this some."
        ),
        "step4": (
            "4. Common-mode choke: wind {choke},\n"
            "   placed right at the feedpoint before the coax run back to the radio.\n"
            "   ({balun_type}, {balun_ratio} -- {balun_why}.)"
        ),
        "step5": (
            "5. Weatherproofing: seal the feedpoint connections (self-amalgamating tape over\n"
            "   coax connectors) before the first rain -- this is the #1 cause of intermittent SWR issues."
        ),
    },
    "nl": {
        "title": "Bouwnotities -- {band} grondgemonteerde kwartgolf verticaal",
        "step1": "1. Mastelement: zaag/knip een stuk draad of buis af op {length}.\n   Monteer verticaal, geisoleerd van de grond (een PVC mast of geisoleerde voet werkt goed).",
        "step2": (
            "2. Radialen: leg {count} radialen aan, elk {length} lang,\n"
            "   gelijk verdeeld rond de voet (dit ontwerp gaat uit van gelijke hoekverdeling).\n"
            "   Ze kunnen op de grond liggen of een paar cm diep begraven worden -- verhoogde radialen\n"
            "   werken ook, maar dan zijn 2-4 verhoogde radialen op kwartgolflengte gangbaarder\n"
            "   dan veel radialen op de grond."
        ),
        "step3": (
            "3. Voedingspunt: verbind de kern van de coax met de voet van het mastelement,\n"
            "   en het coax-scherm / de radialen met een gemeenschappelijk aardpunt. Verwacht ~{ohms} ohm\n"
            "   voedingspuntimpedantie onder ideale omstandigheden -- het aantal radialen/de bodem in de praktijk wijkt hier iets van af."
        ),
        "step4": (
            "4. Common-mode choke: wikkel {choke},\n"
            "   direct bij het voedingspunt, voor de coax-loop terug naar de radio.\n"
            "   ({balun_type}, {balun_ratio} -- {balun_why}.)"
        ),
        "step5": (
            "5. Weerbestendig maken: dicht de voedingspuntverbindingen af (zelfvulkaniserende tape over\n"
            "   coaxconnectoren) voor de eerste regen -- dit is oorzaak #1 van wisselende SWR-problemen."
        ),
    },
}
