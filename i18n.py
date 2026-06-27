"""Shared English/Dutch text strings for CLI output and printed templates.

Only display text is translated. Formulas, units math, and data keys
(band names, internal dict keys) stay in English/standard form.
"""

ROLE_LABELS = {
    "radiator": {"en": "Radiator", "nl": "Stralend element"},
    "radial": {"en": "Radials", "nl": "Radialen"},
    "counterpoise": {"en": "Counterpoise", "nl": "Counterpoise"},
    "matching_stub": {"en": "Matching stub", "nl": "Matching stub"},
    "leg_short": {"en": "Short leg", "nl": "Kort been"},
    "leg_long": {"en": "Long leg", "nl": "Lang been"},
    "reflector": {"en": "Reflector", "nl": "Reflector"},
    "director": {"en": "Director", "nl": "Director"},
    "driven_loop": {"en": "Driven loop", "nl": "Gevoede loop"},
    "reflector_loop": {"en": "Reflector loop", "nl": "Reflector-loop"},
    "disc": {"en": "Disc", "nl": "Disc"},
}

SUMMARY_LABELS = {
    "en": {
        "freq": "Design frequency",
        "impedance": "Feedpoint impedance",
        "ohms": "ohms",
        "balun": "Matching",
        "each": "each",
    },
    "nl": {
        "freq": "Ontwerpfrequentie",
        "impedance": "Voedingspunt impedantie",
        "ohms": "ohm",
        "balun": "Aanpassing",
        "each": "elk",
    },
}

BALUN_TYPE_LABELS = {
    "current_choke_1_1": {"en": "1:1 current choke", "nl": "1:1 stroomchoke"},
    "current_balun_1_1": {"en": "1:1 current balun", "nl": "1:1 stroombalun"},
    "unun_49_1": {"en": "49:1 unun", "nl": "49:1 unun"},
    "current_balun_4_1": {"en": "4:1 current balun", "nl": "4:1 stroombalun"},
    "tap_point_match": {"en": "Tap-point match (no balun)", "nl": "Aftakpunt-aanpassing (geen balun)"},
    "base_loading_coil": {"en": "Base loading coil", "nl": "Spoel aan de voet"},
    "balanced_tuner": {"en": "Balanced tuner (open-wire feed)", "nl": "Gebalanceerde tuner (open-wire voeding)"},
    "unun_9_1": {"en": "9:1 unun", "nl": "9:1 unun"},
    "direct_coax_feed": {"en": "Direct 50-ohm coax feed (no balun)", "nl": "Direct 50-ohm coax-voeding (geen balun)"},
    "stepup_transformer_5_2": {
        "en": "Step-up transformer (5:2 turns, ~6:1 impedance)",
        "nl": "Step-up transformer (5:2 wikkelingen, ~6:1 impedantie)",
    },
}

BALUN_WHERE = {
    "en": "at the feedpoint, on the coax just before it connects to the base of the vertical element",
    "nl": "bij het voedingspunt, op de coax net voordat deze de voet van het mastelement bereikt",
}

BALUN_WHY = {
    "en": "suppresses common-mode current on the coax shield; a quarter-wave vertical with ground-mounted radials is fed directly, so no impedance-transforming unun is needed",
    "nl": "onderdrukt common-mode stroom op het coax-scherm; een quarter-wave verticaal met grondradialen wordt direct gevoed, dus is er geen impedantie-transformerende unun nodig",
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

BALUN_WHERE_LOOP = {
    "en": "at the feedpoint, where the coax connects to a break in the wire at the midpoint of one side",
    "nl": "bij het voedingspunt, waar de coax verbinding maakt met een onderbreking in de draad op het midden van een zijde",
}

BALUN_WHY_LOOP = {
    "en": "converts the unbalanced coax feed to the balanced loop; the ~100 ohm loop impedance against 50 ohm coax gives a roughly 2:1 SWR, which most radios tolerate without an external tuner",
    "nl": "zet de ongebalanceerde coaxvoeding om naar de gebalanceerde loop; de ~100 ohm loopimpedantie tegenover 50 ohm coax geeft een SWR van ongeveer 2:1, wat de meeste radio's zonder externe tuner verdragen",
}

BALUN_WHERE_OCFD = {
    "en": "at the feedpoint, 1/3 of the way along the wire from the short end",
    "nl": "bij het voedingspunt, op 1/3 van de draad gerekend vanaf het korte einde",
}

BALUN_WHY_OCFD = {
    "en": "transforms the ~200 ohm off-center feedpoint impedance down to ~50 ohms and converts unbalanced coax to the balanced wire",
    "nl": "transformeert de ~200 ohm impedantie van het asymmetrische voedingspunt omlaag naar ~50 ohm en zet ongebalanceerde coax om naar de gebalanceerde draad",
}

BALUN_WHERE_FIVE_EIGHTHS = {
    "en": "at the base, in series between the element and the coax feedpoint",
    "nl": "bij de voet, in serie tussen het element en het coax-voedingspunt",
}

BALUN_WHY_FIVE_EIGHTHS = {
    "en": "the 5/8-wave element is not naturally resonant; the coil cancels its reactance so the feedpoint presents a low, mostly resistive impedance to the coax",
    "nl": "het 5/8-wave element is niet vanzelf resonant; de spoel heft de reactantie op zodat het voedingspunt een lage, vrijwel resistieve impedantie aan de coax biedt",
}

BALUN_WHERE_EDZ = {
    "en": "at the center feedpoint, where the open-wire/ladder line connects before running to a balanced tuner",
    "nl": "bij het middenvoedingspunt, waar de open-wire/ladderlijn aansluit voordat deze naar een gebalanceerde tuner loopt",
}

BALUN_WHY_EDZ = {
    "en": "feedpoint impedance is high and varies considerably with height (commonly several hundred ohms), so a balanced tuner -- not a fixed-ratio coax balun -- is the practical match",
    "nl": "de voedingspuntimpedantie is hoog en varieert sterk met de hoogte (vaak enkele honderden ohm), dus een gebalanceerde tuner -- geen vaste-ratio coaxbalun -- is de praktische aanpassing",
}

BALUN_WHERE_YAGI = {
    "en": "at the driven element's center feedpoint",
    "nl": "bij het middenvoedingspunt van het gevoede element",
}

BALUN_WHY_YAGI = {
    "en": "converts the unbalanced coax feed to the balanced driven element and suppresses common-mode current, same as on a plain dipole",
    "nl": "zet de ongebalanceerde coaxvoeding om naar het gebalanceerde gevoede element en onderdrukt common-mode stroom, net als bij een gewone dipool",
}

BALUN_WHERE_QUAD = {
    "en": "at the feedpoint, where the coax connects to a break in the driven loop",
    "nl": "bij het voedingspunt, waar de coax verbinding maakt met een onderbreking in de gevoede loop",
}

BALUN_WHY_QUAD = {
    "en": "suppresses common-mode current; with the spacing used here the driven loop's impedance is already close to 50 ohms, so no impedance transformation is needed",
    "nl": "onderdrukt common-mode stroom; met de hier gebruikte afstand ligt de impedantie van de gevoede loop al dicht bij 50 ohm, dus is geen impedantietransformatie nodig",
}

JPOLE_BALUN_WHERE = {
    "en": "at the tap point on the matching stub, about {fraction} of the way up from the shorted bottom",
    "nl": "op het aftakpunt op de aanpasstub, ongeveer {fraction} omhoog vanaf de kortgesloten onderkant",
}

JPOLE_BALUN_WHY = {
    "en": "the tap position itself transforms the impedance to 50 ohms, so the antenna can be fed directly with coax",
    "nl": "de positie van het aftakpunt transformeert de impedantie zelf naar 50 ohm, waardoor de antenne direct met coax gevoed kan worden",
}

BALUN_WHERE_MOXON = {
    "en": "at the feedpoint gap in the center of the driven element",
    "nl": "bij de voedingsspleet in het midden van het gevoede element",
}

BALUN_WHY_MOXON = {
    "en": "converts the unbalanced coax feed to the balanced driven element; the Moxon's geometry already gives a feedpoint impedance close to 50 ohms",
    "nl": "zet de ongebalanceerde coaxvoeding om naar het gebalanceerde gevoede element; de geometrie van de Moxon geeft al een voedingspuntimpedantie dicht bij 50 ohm",
}

BALUN_WHERE_LONGWIRE = {
    "en": "at the feedpoint, where the high-impedance end of the wire and the counterpoise connect to the unun",
    "nl": "bij het voedingspunt, waar het hoge-impedantie-einde van de draad en de counterpoise op de unun aansluiten",
}

BALUN_WHY_LONGWIRE = {
    "en": "transforms the long wire's high end-fed impedance (commonly 500-1000 ohms) down toward 50 ohms for the receiver -- a measurable, often 12+ dB, improvement over a bare wire into a receiver input",
    "nl": "transformeert de hoge end-fed impedantie van de longwire (doorgaans 500-1000 ohm) omlaag richting 50 ohm voor de ontvanger -- een merkbare, vaak 12+ dB, verbetering tegenover een blote draad direct op de ontvangeringang",
}

BALUN_WHERE_DISCONE = {
    "en": "at the apex, where the coax center conductor connects to the disc and the shield connects to the cone",
    "nl": "bij de apex, waar de coax-kern verbinding maakt met de disc en het scherm met de cone",
}

BALUN_WHY_DISCONE = {
    "en": "the disc/cone geometry itself presents a low, fairly constant impedance across a very wide bandwidth, so no balun or matching network is needed -- this is what makes the discone genuinely broadband",
    "nl": "de disc/cone-geometrie geeft zelf al een lage, redelijk constante impedantie over een zeer breed bereik, dus is geen balun of aanpasnetwerk nodig -- dit maakt de discone echt breedband",
}

BALUN_WHERE_GROUND_LOOP = {
    "en": "at the feedpoint gap, where the loop's two ends connect to the step-up transformer",
    "nl": "bij de voedingsspleet, waar de twee uiteinden van de loop op de step-up transformer aansluiten",
}

BALUN_WHY_GROUND_LOOP = {
    "en": "a loop lying on the ground has a very low impedance that varies a lot with frequency and ground conditions; the step-up transformer brings it into a usable range for the receiver's 50/75 ohm input",
    "nl": "een loop die op de grond ligt heeft een zeer lage impedantie die sterk varieert met frequentie en bodemgesteldheid; de step-up transformer brengt dit naar een bruikbaar bereik voor de 50/75 ohm ingang van de ontvanger",
}

DRAWING = {
    "en": {
        "element_label": "Element: {length}",
        "radial_label": "Radial x{count}: {length} each, {angle:.0f} deg apart",
        "radial_each_label": "R{index}: {length}",
        "counterpoise_label": "Counterpoise x{count}: {length}",
        "loop_side_label": "Side: {length} (x{count})",
        "spacing_label": "Spacing: {length}",
        "boom_label": "Boom: {length}",
        "reflector_label": "Reflector: {length}",
        "director_label": "Director: {length}",
        "disc_label": "Disc: {length}",
        "cone_label": "Cone: {length}",
        "feedpoint_label": "Feedpoint: ~{ohms} ohms, {balun_type} ({balun_ratio})",
        "band_label": "{band} band -- design freq {freq} MHz",
    },
    "nl": {
        "element_label": "Element: {length}",
        "radial_label": "Radiaal x{count}: {length} elk, {angle:.0f} graden uit elkaar",
        "radial_each_label": "R{index}: {length}",
        "counterpoise_label": "Counterpoise x{count}: {length}",
        "loop_side_label": "Zijde: {length} (x{count})",
        "spacing_label": "Afstand: {length}",
        "boom_label": "Boom: {length}",
        "disc_label": "Disc: {length}",
        "cone_label": "Cone: {length}",
        "reflector_label": "Reflector: {length}",
        "director_label": "Director: {length}",
        "feedpoint_label": "Voedingspunt: ~{ohms} ohm, {balun_type} ({balun_ratio})",
        "band_label": "{band} band -- ontwerpfreq {freq} MHz",
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
        "title": "Bouwnotities -- {band} half-wave dipool",
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
        "title": "Bouwnotities -- {band} end-fed half-wave (EFHW)",
        "step1": "1. Knip de stralende draad af op {length}. Dit is het volledige stralende element, gevoed aan een einde.",
        "step2": "2. Knip een counterpoise-draad af op {length_cp} en verbind deze met de aardlip van de unun --\n   dit is geen resonant radialensysteem, slechts een retourpad voor de unun.",
        "step3": "3. Voedingspunt: verbind het hoge-impedantie-einde van de straler en de counterpoise met de unun.\n   Verwacht ~{ohms} ohm op dit punt voordat de unun dit omlaag transformeert naar ~50 ohm.",
        "step4": "4. Unun: gebruik een {balun_type} ({balun_ratio}) bij het voedingspunt -- {balun_why}.",
        "step5": "5. Routering: houd de counterpoise weg van de stralende draad (laat ze niet dicht parallel lopen) --\n   en houd de straler weg van metalen constructies, die hem ontstemmen.",
    },
}

BUILD_NOTES_LOOP = {
    "en": {
        "title": "Build notes -- {band} full-wave horizontal loop",
        "step1": "1. Cut ONE continuous wire to the total length {length}. Mark fold points at each quarter\n   ({side_length} apart) -- these become the four corners of the loop.",
        "step2": "2. Hang the wire as a square (or circle/triangle -- shape barely matters, only total length does)\n   between 4 supports at a consistent height. Keep it under light tension; sag shifts resonance.",
        "step3": "3. Feedpoint: break the wire at the midpoint of one side and connect the coax there\n   (through the balun). Expect ~{ohms} ohms feedpoint impedance.",
        "step4": "4. Balun: use {balun_type} ({balun_ratio}) at the feedpoint -- {balun_why}.",
        "step5": "5. This antenna is quieter (lower noise pickup) than a dipole at the same height, and works\n   reasonably on multiple bands with a tuner -- a good all-rounder if you have the space for the perimeter.",
    },
    "nl": {
        "title": "Bouwnotities -- {band} full-wave horizontale loop",
        "step1": "1. Knip EEN doorlopende draad af op de totale lengte {length}. Markeer vouwpunten bij elk kwart\n   ({side_length} uit elkaar) -- dit worden de vier hoeken van de loop.",
        "step2": "2. Hang de draad op als vierkant (of cirkel/driehoek -- de vorm maakt weinig uit, alleen de totale lengte telt)\n   tussen 4 steunpunten op gelijke hoogte. Houd licht onder spanning; doorzakken verschuift de resonantie.",
        "step3": "3. Voedingspunt: onderbreek de draad op het midden van een zijde en verbind daar de coax\n   (via de balun). Verwacht ~{ohms} ohm voedingspuntimpedantie.",
        "step4": "4. Balun: gebruik {balun_type} ({balun_ratio}) bij het voedingspunt -- {balun_why}.",
        "step5": "5. Deze antenne is stiller (minder ruisontvangst) dan een dipool op dezelfde hoogte, en werkt\n   redelijk op meerdere banden met een tuner -- een goede allrounder als je de ruimte voor de omtrek hebt.",
    },
}

BUILD_NOTES_INVERTED_V = {
    "en": {
        "title": "Build notes -- {band} inverted-V dipole",
        "step1": "1. Cut two legs, each {length} long, same as a flat dipole.",
        "step2": "2. Mount with the apex (feedpoint) high on a single mast, legs sloping down at roughly\n   30 degrees to side supports or ground anchors -- needs only one tall support, not two.",
        "step3": "3. Feedpoint: connect coax through the balun at the apex. Expect ~{ohms} ohms feedpoint\n   impedance -- a bit lower than a flat dipole's 73 ohms because of the bent geometry.",
        "step4": "4. Balun: use {balun_type} ({balun_ratio}) at the apex -- {balun_why}.",
        "step5": "5. Keep the leg ends at least a few meters off the ground and away from metal objects,\n   which detune the antenna and can present a shock/RF burn hazard at the high-voltage tips.",
    },
    "nl": {
        "title": "Bouwnotities -- {band} inverted-V dipool",
        "step1": "1. Knip twee benen van elk {length} lang, net als bij een vlakke dipool.",
        "step2": "2. Monteer met de top (voedingspunt) hoog aan een enkele mast, benen onder ongeveer\n   30 graden naar zij-ankers of grondankers -- vereist maar één hoge steun, geen twee.",
        "step3": "3. Voedingspunt: verbind de coax via de balun bij de top. Verwacht ~{ohms} ohm voedingspuntimpedantie\n   -- iets lager dan de 73 ohm van een vlakke dipool door de gebogen geometrie.",
        "step4": "4. Balun: gebruik {balun_type} ({balun_ratio}) bij de top -- {balun_why}.",
        "step5": "5. Houd de beneindes minstens een paar meter van de grond en weg van metalen objecten,\n   die de antenne ontstemmen en bij de hoogspanningstips een schok-/RF-brandgevaar kunnen geven.",
    },
}

BUILD_NOTES_OCFD = {
    "en": {
        "title": "Build notes -- {band} off-center-fed dipole (Windom)",
        "step1": "1. Cut the short leg to {length_short} and the long leg to {length_long} -- this 1:2 split\n   is what gives the off-center feed its characteristic ~200 ohm impedance.",
        "step2": "2. Mount horizontally (or as an inverted-V) like a regular dipole -- the asymmetry is only\n   in the feedpoint location, not the mounting style.",
        "step3": "3. Feedpoint: connect coax through the 4:1 balun at the 1/3 point. Expect ~{ohms} ohms\n   feedpoint impedance before the balun transforms it down to ~50 ohms.",
        "step4": "4. Balun: use {balun_type} ({balun_ratio}) at the feedpoint -- {balun_why}.",
        "step5": "5. This antenna is popular for rough multiband coverage with a tuner -- don't expect a\n   flat 1:1 SWR on every band, that's normal for this design.",
    },
    "nl": {
        "title": "Bouwnotities -- {band} asymmetrisch gevoede dipool (Windom)",
        "step1": "1. Knip het korte been op {length_short} en het lange been op {length_long} -- deze 1:2-verdeling\n   geeft de asymmetrische voeding zijn karakteristieke impedantie van ~200 ohm.",
        "step2": "2. Monteer horizontaal (of als inverted-V) zoals een gewone dipool -- de asymmetrie zit\n   alleen in de positie van het voedingspunt, niet in de montagestijl.",
        "step3": "3. Voedingspunt: verbind de coax via de 4:1 balun op het 1/3-punt. Verwacht ~{ohms} ohm\n   voedingspuntimpedantie voordat de balun dit omlaag transformeert naar ~50 ohm.",
        "step4": "4. Balun: gebruik {balun_type} ({balun_ratio}) bij het voedingspunt -- {balun_why}.",
        "step5": "5. Deze antenne is populair voor ruwe multiband-dekking met een tuner -- verwacht geen\n   vlakke 1:1 SWR op elke band, dat is normaal voor dit ontwerp.",
    },
}

BUILD_NOTES_JPOLE = {
    "en": {
        "title": "Build notes -- {band} J-pole",
        "step1": "1. Cut the radiator to {length} and the stub to {length_stub}, mounted parallel\n   about 2.5 cm (1 inch) apart.",
        "step2": "2. Join radiator and stub at the BOTTOM with a solid bridge/short -- this is what makes\n   it a \"J\" shape (the stub is shorted, the radiator is open at the bottom).",
        "step3": "3. Feedpoint: connect coax center conductor and shield across the stub, tapped {tap_length}\n   up from the shorted bottom. Expect ~{ohms} ohms at this tap point.",
        "step4": "4. Matching: {balun_type} -- {balun_why}. Slide the tap point up/down a little while\n   watching SWR to fine-tune; this is the normal way to dial in a J-pole.",
        "step5": "5. No radials or ground plane needed -- mount on a non-conductive mast (PVC/fiberglass),\n   as high and clear of metal/structures as practical for best VHF/UHF range.",
    },
    "nl": {
        "title": "Bouwnotities -- {band} J-pole",
        "step1": "1. Knip de straler op {length} en de stub op {length_stub}, parallel gemonteerd\n   op ongeveer 2,5 cm afstand van elkaar.",
        "step2": "2. Verbind straler en stub ONDERAAN met een stevige brug/kortsluiting -- dit geeft\n   de \"J\"-vorm (de stub is kortgesloten, de straler is onderaan open).",
        "step3": "3. Voedingspunt: verbind coax-kern en -scherm over de stub, afgetakt op {tap_length}\n   vanaf de kortgesloten onderkant. Verwacht ~{ohms} ohm op dit aftakpunt.",
        "step4": "4. Aanpassing: {balun_type} -- {balun_why}. Schuif het aftakpunt iets op/neer terwijl je\n   de SWR observeert om fijn af te stemmen; dit is de normale manier om een J-pole af te stemmen.",
        "step5": "5. Geen radialen of grondvlak nodig -- monteer op een niet-geleidende mast (PVC/glasvezel),\n   zo hoog en vrij van metaal/constructies als praktisch voor het beste VHF/UHF-bereik.",
    },
}

BUILD_NOTES_FIVE_EIGHTHS = {
    "en": {
        "title": "Build notes -- {band} 5/8-wave gain vertical",
        "step1": "1. Cut the element to {length} -- noticeably longer than a quarter-wave vertical\n   for the same band, which is where the extra gain comes from.",
        "step2": "2. Lay out {count} radials, each {length_radial} long, same as a quarter-wave vertical's ground plane.",
        "step3": "3. Feedpoint: the element alone does NOT present a clean 50 ohm match -- it's reactive.\n   Expect ~{ohms} ohms only AFTER the loading coil is correctly sized and installed.",
        "step4": "4. Matching: {balun_type} -- {balun_why}. This coil's exact inductance depends on your\n   element diameter and material; use an antenna analyzer to trim turns for minimum SWR\n   rather than relying on a fixed turn count.",
        "step5": "5. This is the most finicky antenna in this list to get right -- budget time for SWR\n   sweeping and coil adjustment, it won't be a cut-once-done antenna like the others.",
    },
    "nl": {
        "title": "Bouwnotities -- {band} 5/8-wave gain-verticaal",
        "step1": "1. Knip het element op {length} -- merkbaar langer dan een quarter-wave verticaal\n   voor dezelfde band, daar komt de extra winst vandaan.",
        "step2": "2. Leg {count} radialen aan, elk {length_radial} lang, net als het grondvlak van een quarter-wave verticaal.",
        "step3": "3. Voedingspunt: het element alleen geeft GEEN schone 50 ohm match -- het is reactief.\n   Verwacht ~{ohms} ohm pas NA correcte dimensionering en installatie van de spoel.",
        "step4": "4. Aanpassing: {balun_type} -- {balun_why}. De exacte inductantie van deze spoel hangt af\n   van je elementdiameter en materiaal; gebruik een antenne-analyzer om wikkelingen te trimmen\n   voor minimale SWR in plaats van te vertrouwen op een vast aantal wikkelingen.",
        "step5": "5. Dit is de lastigste antenne in deze lijst om goed te krijgen -- reserveer tijd voor\n   SWR-metingen en spoelafstelling, het is geen eenmalig-knippen-klaar antenne zoals de rest.",
    },
}

BUILD_NOTES_EDZ = {
    "en": {
        "title": "Build notes -- {band} extended double Zepp (EDZ)",
        "step1": "1. Cut two legs, each {length} long -- noticeably longer than a half-wave dipole's legs\n   for the same band; this extra length is what produces the gain.",
        "step2": "2. Mount horizontally like a dipole, as high and as straight as your supports allow --\n   this antenna rewards height more than most.",
        "step3": "3. Feedpoint: connect open-wire/ladder line at the center, running to a balanced tuner\n   (not direct coax). Expect roughly ~{ohms} ohms, but treat this as a rough number --\n   it shifts a lot with height and surroundings.",
        "step4": "4. Matching: {balun_type} -- {balun_why}.",
        "step5": "5. Don't substitute coax feed without a 4:1+ balun and expect a clean match -- this\n   antenna's whole design assumes a balanced feedline and a tuner doing the final matching.",
    },
    "nl": {
        "title": "Bouwnotities -- {band} extended double Zepp (EDZ)",
        "step1": "1. Knip twee benen van elk {length} lang -- merkbaar langer dan de benen van een half-wave\n   dipool voor dezelfde band; deze extra lengte levert de winst.",
        "step2": "2. Monteer horizontaal zoals een dipool, zo hoog en recht als je steunpunten toelaten --\n   deze antenne beloont hoogte meer dan de meeste andere.",
        "step3": "3. Voedingspunt: verbind open-wire/ladderlijn in het midden, lopend naar een gebalanceerde\n   tuner (niet direct coax). Verwacht ruwweg ~{ohms} ohm, maar zie dit als een ruw getal --\n   het verschuift sterk met hoogte en omgeving.",
        "step4": "4. Aanpassing: {balun_type} -- {balun_why}.",
        "step5": "5. Vervang de voeding niet door coax zonder 4:1+ balun en verwacht een schone match --\n   het hele ontwerp van deze antenne gaat uit van een gebalanceerde voedingslijn met een tuner\n   die de uiteindelijke aanpassing doet.",
    },
}

BUILD_NOTES_DELTA_LOOP = {
    "en": {
        "title": "Build notes -- {band} vertical delta loop",
        "step1": "1. Cut ONE continuous wire to the total length {length}. Mark fold points at each third\n   ({side_length} apart) -- these become the three corners of the triangle.",
        "step2": "2. Hang as a triangle between 3 supports, oriented vertically (one side along the\n   ground/low, apex high) -- vertical orientation is what gives the low-angle DX pattern.",
        "step3": "3. Feedpoint: break the wire at the midpoint of the bottom side and connect the coax there\n   (through the balun). Expect ~{ohms} ohms feedpoint impedance.",
        "step4": "4. Balun: use {balun_type} ({balun_ratio}) at the feedpoint -- {balun_why}.",
        "step5": "5. Like the horizontal loop, this is quieter than a dipole, but the vertical orientation\n   favors DX over local/NVIS contacts -- pick orientation based on what you want to work.",
    },
    "nl": {
        "title": "Bouwnotities -- {band} verticale delta-loop",
        "step1": "1. Knip EEN doorlopende draad af op de totale lengte {length}. Markeer vouwpunten bij elk derde\n   ({side_length} uit elkaar) -- dit worden de drie hoeken van de driehoek.",
        "step2": "2. Hang als een driehoek tussen 3 steunpunten, verticaal georienteerd (een zijde laag/bij\n   de grond, top hoog) -- de verticale orientatie geeft het lage-hoek DX-patroon.",
        "step3": "3. Voedingspunt: onderbreek de draad op het midden van de onderste zijde en verbind daar\n   de coax (via de balun). Verwacht ~{ohms} ohm voedingspuntimpedantie.",
        "step4": "4. Balun: gebruik {balun_type} ({balun_ratio}) bij het voedingspunt -- {balun_why}.",
        "step5": "5. Net als de horizontale loop is deze stiller dan een dipool, maar de verticale orientatie\n   bevoordeelt DX over lokale/NVIS-verbindingen -- kies de orientatie op basis van wat je wilt werken.",
    },
}

BUILD_NOTES_YAGI = {
    "en": {
        "title": "Build notes -- {band} 3-element Yagi",
        "warning": "NOTE: these are published beginner rule-of-thumb dimensions, not an NEC-optimized\n   design. Treat this as a starting point to build and tune, not a final answer.",
        "step1": "1. Cut the driven element to {length_driven}, reflector to {length_reflector},\n   and director to {length_director}. All three mount perpendicular to the boom.",
        "step2": "2. Build a boom of at least {length_boom} long. Mount the reflector at one end, the\n   driven element {length_reflector_spacing} from the reflector, and the director\n   {length_director_spacing} beyond the driven element.",
        "step3": "3. Feedpoint: connect coax through the balun at the driven element's center.\n   Expect ~{ohms} ohms feedpoint impedance, lower than a plain dipole's 73 ohms.",
        "step4": "4. Balun: use {balun_type} ({balun_ratio}) at the driven element -- {balun_why}.",
        "step5": "5. The reflector and director are NOT fed -- they're parasitic elements, mounted\n   insulated from the boom (or with insulating standoffs) and left open at the ends.\n   Use an antenna analyzer to fine-tune spacing/lengths for best SWR and front-to-back ratio.",
    },
    "nl": {
        "title": "Bouwnotities -- {band} 3-elements Yagi",
        "warning": "LET OP: dit zijn gepubliceerde vuistregel-afmetingen voor beginners, geen\n   NEC-geoptimaliseerd ontwerp. Zie dit als startpunt om te bouwen en af te stemmen, niet als eindantwoord.",
        "step1": "1. Knip het gevoede element op {length_driven}, de reflector op {length_reflector},\n   en de director op {length_director}. Alle drie monteren loodrecht op de boom.",
        "step2": "2. Bouw een boom van minstens {length_boom} lang. Monteer de reflector aan een einde, het\n   gevoede element {length_reflector_spacing} van de reflector, en de director\n   {length_director_spacing} voorbij het gevoede element.",
        "step3": "3. Voedingspunt: verbind de coax via de balun op het midden van het gevoede element.\n   Verwacht ~{ohms} ohm voedingspuntimpedantie, lager dan de 73 ohm van een gewone dipool.",
        "step4": "4. Balun: gebruik {balun_type} ({balun_ratio}) bij het gevoede element -- {balun_why}.",
        "step5": "5. Reflector en director worden NIET gevoed -- het zijn parasitaire elementen, geisoleerd\n   van de boom gemonteerd (of met isolerende afstandhouders) en open aan de uiteinden.\n   Gebruik een antenne-analyzer om afstand/lengtes fijn af te stemmen voor beste SWR en voor-achterverhouding.",
    },
}

BUILD_NOTES_QUAD = {
    "en": {
        "title": "Build notes -- {band} 2-element cubical quad",
        "warning": "NOTE: these are published beginner rule-of-thumb dimensions, not an NEC-optimized\n   design. Treat this as a starting point to build and tune, not a final answer.",
        "step1": "1. Cut a driven loop wire to {length_driven} total circumference (side = {length_driven_side})\n   and a reflector loop wire to {length_reflector} total (side = {length_reflector_side}).",
        "step2": "2. Build a spreader frame (fiberglass/wood) for each loop, square, supported from a\n   center boom {length_spacing} long separating driven and reflector.",
        "step3": "3. Feedpoint: break the driven loop at its center-bottom and connect coax there\n   (through the balun). Expect ~{ohms} ohms -- the spacing here is chosen to land close\n   to 50 ohms directly.",
        "step4": "4. Balun: use {balun_type} ({balun_ratio}) at the feedpoint -- {balun_why}.",
        "step5": "5. The reflector loop is NOT fed -- left as a closed loop, slightly larger than the\n   driven loop. Quads are quieter and often outperform a Yagi of similar boom length on\n   the lower HF bands.",
    },
    "nl": {
        "title": "Bouwnotities -- {band} 2-elements kubieke quad",
        "warning": "LET OP: dit zijn gepubliceerde vuistregel-afmetingen voor beginners, geen\n   NEC-geoptimaliseerd ontwerp. Zie dit als startpunt om te bouwen en af te stemmen, niet als eindantwoord.",
        "step1": "1. Knip een gevoede-loopdraad af op {length_driven} totale omtrek (zijde = {length_driven_side})\n   en een reflector-loopdraad op {length_reflector} totaal (zijde = {length_reflector_side}).",
        "step2": "2. Bouw een spreader-frame (glasvezel/hout) voor elke loop, vierkant, gedragen door een\n   middenboom van {length_spacing} lang die gevoede loop en reflector scheidt.",
        "step3": "3. Voedingspunt: onderbreek de gevoede loop onderaan in het midden en verbind daar de\n   coax (via de balun). Verwacht ~{ohms} ohm -- de afstand hier is gekozen om dicht bij\n   50 ohm direct uit te komen.",
        "step4": "4. Balun: gebruik {balun_type} ({balun_ratio}) bij het voedingspunt -- {balun_why}.",
        "step5": "5. De reflector-loop wordt NIET gevoed -- blijft een gesloten loop, iets groter dan de\n   gevoede loop. Quads zijn stiller en presteren vaak beter dan een Yagi met vergelijkbare\n   boomlengte op de lagere HF-banden.",
    },
}

BUILD_NOTES_MOXON = {
    "en": {
        "title": "Build notes -- {band} Moxon rectangle",
        "warning": "NOTE: based on the published Cebik (W4RNL) regression-equation method, assuming a\n   {wire_diameter} mm wire/tubing diameter. If your actual wire gauge differs significantly,\n   dimensions will shift slightly -- this is the one place this calculator depends on an assumption.",
        "step1": "1. Cut the driven element wire to {length_driven} total (a {length_a} straight run with a\n   {length_b} tail bent back at each end) and the reflector to {length_reflector} total\n   (same {length_a} straight run, {length_d} tails).",
        "step2": "2. Mount both elements on a single flat frame (spreader), driven element in front,\n   reflector behind, with a {length_c} gap between the driven tail tips and the reflector tail tips.",
        "step3": "3. Feedpoint: connect coax through the balun at the gap in the center of the driven element\n   (NOT the reflector). Expect ~{ohms} ohms -- the Moxon shape is specifically designed to land near 50 ohms.",
        "step4": "4. Balun: use {balun_type} ({balun_ratio}) at the feedpoint -- {balun_why}.",
        "step5": "5. The compact, lightweight Moxon rectangle is popular for portable/field use -- decent\n   gain and front-to-back ratio in a much smaller footprint than a 2-element Yagi or quad.",
    },
    "nl": {
        "title": "Bouwnotities -- {band} Moxon-rechthoek",
        "warning": "LET OP: gebaseerd op de gepubliceerde Cebik (W4RNL) regressievergelijking-methode, uitgaande\n   van een draad-/buisdiameter van {wire_diameter} mm. Bij een sterk afwijkende draaddikte\n   verschuiven de afmetingen iets -- dit is de enige plek waar deze calculator van een aanname uitgaat.",
        "step1": "1. Knip de draad voor het gevoede element op {length_driven} totaal (een rechte loop van\n   {length_a} met aan elk einde een teruggebogen staart van {length_b}) en de reflector op\n   {length_reflector} totaal (zelfde rechte loop van {length_a}, staarten van {length_d}).",
        "step2": "2. Monteer beide elementen op een enkel vlak frame (spreader), gevoede element voor,\n   reflector achter, met een tussenruimte van {length_c} tussen de staartpunten.",
        "step3": "3. Voedingspunt: verbind de coax via de balun bij de spleet in het midden van het gevoede\n   element (NIET de reflector). Verwacht ~{ohms} ohm -- de Moxon-vorm is specifiek ontworpen\n   om dicht bij 50 ohm uit te komen.",
        "step4": "4. Balun: gebruik {balun_type} ({balun_ratio}) bij het voedingspunt -- {balun_why}.",
        "step5": "5. De compacte, lichte Moxon-rechthoek is populair voor portable/veldgebruik -- behoorlijke\n   winst en voor-achterverhouding in een veel kleinere footprint dan een 2-elements Yagi of quad.",
    },
}

BUILD_NOTES_LONGWIRE = {
    "en": {
        "title": "Build notes -- {band} long-wire receive antenna (SWL)",
        "warning": "NOTE: this is a receive-only, intentionally non-resonant design -- there is no single\n   \"correct\" length like a transmit antenna. {length} is a practical MINIMUM (a quarter-wave\n   floor at the band's low edge); longer is generally better for low-frequency sensitivity.\n   If {length} is impractical for your location (common on LW/MW), use what space allows --\n   a shorter wire still works, just with reduced low-end response.",
        "step1": "1. Run a wire at least {length} long, as high and as clear of buildings/power lines as practical.\n   Straight is ideal but not required -- a bent or sloping run still works for receive.",
        "step2": "2. Run a counterpoise/ground wire of about {length_cp} from the unun's ground lug, or use\n   a real ground rod/cold-water-pipe ground if available -- either gives the unun a return path.",
        "step3": "3. Feedpoint: connect the wire's far (high-impedance) end and the counterpoise to the unun.\n   Expect roughly ~{ohms} ohms at this point before the unun transforms it down for the receiver.",
        "step4": "4. Unun: use a {balun_type} ({balun_ratio}) at the feedpoint -- {balun_why}.",
        "step5": "5. Keep the wire away from noisy sources (switching power supplies, LED drivers, routers) --\n   for a receive antenna, noise pickup matters as much as signal pickup.",
    },
    "nl": {
        "title": "Bouwnotities -- {band} longwire receive-antenne (SWL)",
        "warning": "LET OP: dit is een receive-only, expres niet-resonant ontwerp -- er is geen \"juiste\"\n   lengte zoals bij een transmit-antenne. {length} is een praktisch MINIMUM (een quarter-wave\n   bodemwaarde op de onderkant van de band); langer is over het algemeen beter voor lage-frequentie\n   gevoeligheid. Is {length} onpraktisch voor je locatie (gebruikelijk op LW/MW), gebruik dan wat\n   de ruimte toelaat -- een kortere draad werkt nog steeds, alleen met minder respons onderin.",
        "step1": "1. Span een draad van minstens {length} lang, zo hoog en zo vrij van gebouwen/stroomkabels als praktisch.\n   Recht is ideaal maar niet vereist -- een gebogen of hellende loop werkt ook voor ontvangst.",
        "step2": "2. Span een counterpoise/aarddraad van ongeveer {length_cp} vanaf de aardlip van de unun, of gebruik\n   een echte aardpin/koudwaterleiding-aarde als die beschikbaar is -- beide geven de unun een retourpad.",
        "step3": "3. Voedingspunt: verbind het verre (hoge-impedantie) einde van de draad en de counterpoise met de unun.\n   Verwacht ruwweg ~{ohms} ohm op dit punt voordat de unun dit omlaag transformeert voor de ontvanger.",
        "step4": "4. Unun: gebruik een {balun_type} ({balun_ratio}) bij het voedingspunt -- {balun_why}.",
        "step5": "5. Houd de draad weg van ruisbronnen (schakelende voedingen, LED-drivers, routers) -- bij een\n   receive-antenne telt ruisontvangst net zo zwaar als signaalontvangst.",
    },
}

BUILD_NOTES_DISCONE = {
    "en": {
        "title": "Build notes -- {band} discone receive antenna",
        "warning": "NOTE: published rule-of-thumb dimensions ({skirt_count} skirt wires at {cone_angle} degrees\n   below horizontal from the apex), not an NEC-optimized design -- a solid starting point for\n   a genuinely wideband VHF/UHF receive antenna.",
        "step1": "1. Cut the cone (vertical) element to {length_cone} and the disc to {length_disc} diameter --\n   the cone sets the low-frequency cutoff, the disc's size is derived from it.",
        "step2": "2. Build the disc as a small flat ring or {skirt_count} short spokes at the top, and the cone\n   skirt as {skirt_count} wires/rods running from the apex down and outward at about\n   {cone_angle} degrees below horizontal to the cone's rim.",
        "step3": "3. Feedpoint: connect the coax center conductor to the disc and the shield to the cone apex,\n   right at the narrow gap between them. Expect ~{ohms} ohms across a very wide bandwidth.",
        "step4": "4. Matching: {balun_type} -- {balun_why}.",
        "step5": "5. Mount as high and as clear of nearby structures as practical -- discones are popular\n   scanner/SDR antennas precisely because one antenna covers VHF and UHF without retuning.",
    },
    "nl": {
        "title": "Bouwnotities -- {band} discone receive-antenne",
        "warning": "LET OP: gepubliceerde vuistregel-afmetingen ({skirt_count} skirt-draden op {cone_angle} graden\n   onder de horizon vanaf de apex), geen NEC-geoptimaliseerd ontwerp -- een solide startpunt voor\n   een echt breedband VHF/UHF receive-antenne.",
        "step1": "1. Knip het cone-element (verticaal) op {length_cone} en de disc op {length_disc} diameter --\n   de cone bepaalt de onderste frequentiegrens, de afmeting van de disc volgt daaruit.",
        "step2": "2. Bouw de disc als een kleine vlakke ring of {skirt_count} korte spaken aan de top, en de cone-skirt\n   als {skirt_count} draden/staven die vanaf de apex naar beneden en naar buiten lopen onder ongeveer\n   {cone_angle} graden ten opzichte van de horizon, tot aan de rand van de cone.",
        "step3": "3. Voedingspunt: verbind de coax-kern met de disc en het scherm met de apex van de cone,\n   precies op de smalle tussenruimte daartussen. Verwacht ~{ohms} ohm over een zeer breed bereik.",
        "step4": "4. Aanpassing: {balun_type} -- {balun_why}.",
        "step5": "5. Monteer zo hoog en zo vrij van nabije constructies als praktisch -- discones zijn populaire\n   scanner/SDR-antennes precies omdat een antenne zowel VHF als UHF dekt zonder herafstemmen.",
    },
}

BUILD_NOTES_GROUND_LOOP = {
    "en": {
        "title": "Build notes -- {band} loop-on-ground receive antenna (LoG)",
        "warning": "NOTE: receive-only, untuned, and intentionally laid flat on the ground -- this is a\n   noise-canceling DX antenna, not a transmit design. Published field reports cite a 120 ft\n   loop performing well at MW and a 250 ft loop performing better but with a higher noise floor;\n   {length} is this calculator's quarter-wave-floor reference for your selected band.",
        "step1": "1. Lay ONE continuous wire on the ground (not elevated) in a loop of total length {length}\n   ({side_length} per side if run as a square). Avoid running it directly over buried metal\n   (pipes, rebar) if you can -- it detunes/distorts the pattern.",
        "step2": "2. Leave a small gap where the loop's two ends come close together but don't touch --\n   this is the feedpoint.",
        "step3": "3. Feedpoint: connect both loop ends across the step-up transformer's low-impedance\n   (loop-side) winding. Expect roughly ~{ohms} ohms here, varying a lot with ground and frequency.",
        "step4": "4. Transformer: use a {balun_type} -- {balun_why}. Wind it on a ferrite binocular/toroid\n   core (a common choice is Fair-Rite #73 mix) with the receiver-side winding going to coax.",
        "step5": "5. This antenna trades some signal strength for a much better signal-to-noise ratio than\n   a vertical or longwire at the same location -- it shines specifically where local electrical\n   noise (not weak signal) is your limiting factor.",
    },
    "nl": {
        "title": "Bouwnotities -- {band} loop-on-ground receive-antenne (LoG)",
        "warning": "LET OP: receive-only, ongetuned, en expres plat op de grond gelegd -- dit is een\n   ruisonderdrukkende DX-antenne, geen transmit-ontwerp. Gepubliceerde veldrapporten noemen een\n   loop van 120 ft die goed presteert op MW en een loop van 250 ft die beter presteert maar met\n   een hogere ruisvloer; {length} is de quarter-wave-bodemwaarde van deze calculator voor je band.",
        "step1": "1. Leg EEN doorlopende draad op de grond (niet verhoogd) in een loop van totale lengte {length}\n   ({side_length} per zijde als vierkant aangelegd). Vermijd waar mogelijk direct over begraven\n   metaal (leidingen, wapeningsstaal) -- dat ontstemt/vervormt het patroon.",
        "step2": "2. Laat een kleine tussenruimte waar de twee uiteinden van de loop dicht bij elkaar komen\n   maar elkaar niet raken -- dit is het voedingspunt.",
        "step3": "3. Voedingspunt: verbind beide loop-uiteinden met de laagohmige (loop-kant) wikkeling van\n   de step-up transformer. Verwacht hier ruwweg ~{ohms} ohm, sterk variërend met bodem en frequentie.",
        "step4": "4. Transformer: gebruik een {balun_type} -- {balun_why}. Wikkel hem op een ferriet\n   binocular/toroide kern (Fair-Rite #73 mix is een gangbare keuze), met de ontvanger-kant naar de coax.",
        "step5": "5. Deze antenne ruilt wat signaalsterkte in voor een veel betere signaal-ruisverhouding dan\n   een verticaal of longwire op dezelfde locatie -- hij blinkt specifiek uit waar lokale elektrische\n   ruis (niet zwak signaal) je beperkende factor is.",
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
        "title": "Bouwnotities -- {band} grondgemonteerde quarter-wave verticaal",
        "step1": "1. Mastelement: zaag/knip een stuk draad of buis af op {length}.\n   Monteer verticaal, geisoleerd van de grond (een PVC mast of geisoleerde voet werkt goed).",
        "step2": (
            "2. Radialen: leg {count} radialen aan, elk {length} lang,\n"
            "   gelijk verdeeld rond de voet (dit ontwerp gaat uit van gelijke hoekverdeling).\n"
            "   Ze kunnen op de grond liggen of een paar cm diep begraven worden -- verhoogde radialen\n"
            "   werken ook, maar dan zijn 2-4 verhoogde radialen op quarter-wave lengte gangbaarder\n"
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
