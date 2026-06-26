"""Shared English/Dutch text strings for CLI output and printed templates.

Only display text is translated. Formulas, units math, and data keys
(band names, internal dict keys) stay in English/standard form.
"""

CALC_OUTPUT = {
    "en": {
        "heading": "Ground-mounted quarter-wave vertical -- {band} band",
        "freq": "  Design frequency:      {freq} MHz (band midpoint)",
        "element": "  Element length:        {length}",
        "radials": "  Radials:               {count} x {length} each",
        "impedance": "  Feedpoint impedance:   ~{ohms} ohms",
        "balun": "  Balun/choke:           {type} ({ratio}) -- {where}",
    },
    "nl": {
        "heading": "Grondgemonteerde kwartgolf verticaal -- {band} band",
        "freq": "  Ontwerpfrequentie:     {freq} MHz (midden van de band)",
        "element": "  Lengte mastelement:    {length}",
        "radials": "  Radialen:              {count} x {length} elk",
        "impedance": "  Voedingspunt impedantie: ~{ohms} ohm",
        "balun": "  Balun/choke:           {type} ({ratio}) -- {where}",
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

DRAWING = {
    "en": {
        "element_label": "Element: {length}",
        "radial_label": "Radial x{count}: {length} each",
        "feedpoint_label": "Feedpoint: ~{ohms} ohms, {balun_type} ({balun_ratio})",
        "band_label": "{band} band -- design freq {freq} MHz",
    },
    "nl": {
        "element_label": "Mastelement: {length}",
        "radial_label": "Radiaal x{count}: {length} elk",
        "feedpoint_label": "Voedingspunt: ~{ohms} ohm, {balun_type} ({balun_ratio})",
        "band_label": "{band} band -- ontwerpfreq {freq} MHz",
    },
}

TILE_PDF = {
    "nl": {
        "title": "{band}-band verticale mast -- afdruksjabloon op echte schaal",
        "instructions": "Print op 100% schaal (geen 'aanpassen aan pagina'), knip af tot de overlapstrook en plak de pagina's aaneen met de uitlijnmarkeringen.",
        "element_label": "Mastelement: {length}",
        "tile_label": "Tegel rij {row}/{rows}, kolom {col}/{cols} -- lijn overlapstrook uit met buurtegel",
        "radial_note": "Radialen ({count} x {length}) niet op schaal afgedrukt -- meet ze met een rolmaat (zie bouwnotities).",
        "saved": "Sjabloon van {tiles} pagina('s) op echte schaal opgeslagen in {path}",
        "print_hint": "Print op 100% schaal (geen 'aanpassen aan pagina'), knip bij tot de uitlijnmarkering en plak de tegels aan elkaar.",
    },
    "en": {
        "title": "{band} band vertical mast -- true-to-scale print template",
        "instructions": "Print at 100% scale (no 'fit to page'), trim to the overlap strip, and tape pages together using the alignment marks.",
        "element_label": "Mast element: {length}",
        "tile_label": "Tile row {row}/{rows}, col {col}/{cols} -- align overlap strip with neighbor",
        "radial_note": "Radials ({count} x {length}) not printed to scale -- measure with a tape measure (see build notes).",
        "saved": "Saved {tiles}-page true-to-scale template to {path}",
        "print_hint": "Print at 100% scale (no 'fit to page'), trim to the overlap strip, and tape tiles together.",
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
