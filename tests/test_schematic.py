"""Every antenna schematic, in every view: no text on top of the drawing.

Checks the computed layout: callout cards stay outside the drawing area and
apart from each other, dimension labels touch no wire, feed line, symbol or
other label, and everything lies on the page.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import calculators  # noqa: E402,F401
from drawing import draw_antenna  # noqa: E402
from registry import REGISTRY, design  # noqa: E402
from schematic import _rects_overlap, _seg_hits_rect, build_model, layout  # noqa: E402
from schematic_render import THEMES, MeasureOnly  # noqa: E402


def _band(t):
    if t == "discone_receive":
        return "VHF"
    if t in ("longwire_receive", "ground_loop_receive"):
        return "MW"
    return "20m"


class SchematicLayout(unittest.TestCase):
    def _layouts(self):
        for t in REGISTRY:
            d = design(t, _band(t))
            for lang in ("en", "nl"):
                for theme in ("night", "day", "print"):
                    m = MeasureOnly(THEMES[theme])
                    for view in ("2d", "3d"):
                        yield (t, lang, theme, view), layout(d, build_model(d, lang=lang), view,
                                                             m.measure, m.line_h, lang)

    def test_no_text_on_the_drawing(self):
        for key, L in self._layouts():
            segs = []
            for q, _ in L.wires:
                segs += list(zip(q, q[1:]))
            if L.feedline:
                segs += list(zip(L.feedline[0], L.feedline[0][1:]))
            symbols = [(x - 23, y - 15, x + 23, y + 15) for x, y, *_ in L.boxes]
            cards = [c["rect"] for c in L.callouts]
            for i, r in enumerate(cards):
                self.assertFalse(_rects_overlap(r, L.geo), (key, "card over drawing"))
                for r2 in cards[i + 1:]:
                    self.assertFalse(_rects_overlap(r, r2), (key, "cards overlap"))
                self.assertTrue(0 <= r[0] and r[2] <= L.width and r[3] <= L.height, (key, "card off page"))
            labels = [dm["rect"] for dm in L.dims]
            for i, r in enumerate(labels):
                for a, b in segs:
                    self.assertFalse(_seg_hits_rect(a, b, r), (key, "dimension label on a wire", L.dims[i]["label"]))
                for sr in symbols:
                    self.assertFalse(_rects_overlap(r, sr), (key, "dimension label on a symbol"))
                for r2 in labels[i + 1:]:
                    self.assertFalse(_rects_overlap(r, r2), (key, "dimension labels overlap"))

    def test_roles_are_distinct(self):
        d = design("efhw", "40m")
        L = next(L for k, L in self._layouts() if k == ("efhw", "nl", "night", "2d"))
        roles = {r for _, r in L.wires}
        self.assertTrue({"radiator", "counterpoise", "support"} <= roles)
        self.assertEqual(L.feedline[1], "coax")
        self.assertEqual(len(L.boxes), 1)
        self.assertEqual(len(L.earths), 1)
        self.assertIsNotNone(d)

    def test_svg_export(self):
        svg = draw_antenna(design("dipole_half_wave", "40m"), lang="nl").tostring()
        self.assertTrue(svg.startswith("<svg") and svg.endswith("</svg>"))
        self.assertIn("Voedingslijn", svg)


if __name__ == "__main__":
    unittest.main()
