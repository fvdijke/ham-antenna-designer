"""Reference checks for the calculation engine (run: python -m unittest discover tests).

Reference values: ARRL Antenna Book rules of thumb (468/f, 234/f, 1005/f),
L.B. Cebik's Moxon equations, Kraus (mutual impedance, dipole directivity)
and the ARRL additional-loss-due-to-SWR formula.
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import calculators  # noqa: E402,F401
import data_store as ds  # noqa: E402
import freq_sweep as fs  # noqa: E402
import matching_networks as mn  # noqa: E402
import radiation_pattern as rp  # noqa: E402
import transmissionline_loss as tl  # noqa: E402
from models import METERS_PER_FOOT  # noqa: E402
from registry import REGISTRY, design  # noqa: E402
from swr_calc import calculate_swr  # noqa: E402


def ft_to_m(ft):
    return ft * METERS_PER_FOOT


class Lengths(unittest.TestCase):
    def test_dipole_bare_wire_is_468_over_f(self):
        d = design("dipole_half_wave", "20m")
        total = sum(e.length_m for e in d.elements)
        self.assertAlmostEqual(total, ft_to_m(468 / d.design_freq_mhz), delta=0.005)

    def test_insulation_only_shortens_relative_to_bare(self):
        self.assertEqual(ds.wire_length_factor("Bare copper wire"), 1.0)
        pvc = ds.wire_length_factor("PVC installation wire")
        self.assertTrue(0.96 < pvc < 0.98)
        bare = design("dipole_half_wave", "40m")
        ins = design("dipole_half_wave", "40m", wire_vf=pvc)
        self.assertAlmostEqual(ins.elements[0].length_m / bare.elements[0].length_m, pvc, delta=0.001)

    def test_quarter_wave_vertical(self):
        d = design("vertical_quarter_wave", "40m")
        self.assertAlmostEqual(d.elements[0].length_m, ft_to_m(234 / d.design_freq_mhz), delta=0.005)

    def test_beam_spacings_are_free_space(self):
        for vf in (1.0, 0.97):
            y = design("yagi_3_element", "20m", wire_vf=vf)
            lam = 299.792458 / y.design_freq_mhz
            self.assertAlmostEqual(y.extra["reflector_spacing_m"] / lam, 0.2, delta=0.003)
            self.assertAlmostEqual(y.extra["director_spacing_m"] / lam, 0.15, delta=0.003)
            q = design("quad_2_element", "20m", wire_vf=vf)
            self.assertAlmostEqual(q.extra["spacing_m"] / lam, 0.15, delta=0.003)

    def test_moxon_matches_cebik_and_keeps_gap(self):
        m = design("moxon_2_element", "20m")
        ex = m.extra
        # MoxGen, 14.175 MHz, 2 mm wire: A ~ 7.71 m, E = B + C + D
        self.assertAlmostEqual(ex["a_m"], 7.71, delta=0.03)
        self.assertAlmostEqual(ex["e_m"], ex["b_m"] + ex["c_m"] + ex["d_m"], delta=0.002)
        pvc = design("moxon_2_element", "20m", wire_vf=0.97)
        self.assertEqual(pvc.extra["c_m"], ex["c_m"])  # air gap is not a wire dimension
        self.assertLess(pvc.extra["a_m"], ex["a_m"])

    def test_end_fed_counterpoise_is_short(self):
        for t in ("efhw", "vertical_half_wave", "vertical_full_wave"):
            d = design(t, "40m")
            lam = 299.792458 / d.design_freq_mhz
            cp = d.elements_with_role("counterpoise")[0].length_m
            self.assertAlmostEqual(cp / lam, 0.05, delta=0.002, msg=t)

    def test_receive_antennas_stay_buildable(self):
        for band in ("LW", "MW", "KW", "20m"):
            lw = design("longwire_receive", band)
            self.assertTrue(10 <= lw.elements[0].length_m <= 50, band)
            log = design("ground_loop_receive", band)
            self.assertTrue(20 <= log.elements[0].length_m <= 60, band)

    def test_discone_geometry(self):
        d = design("discone_receive", "VHF")
        low = ds.low_frequency("VHF")
        cone = d.elements_with_role("radiator")[0].length_m
        self.assertAlmostEqual(cone, 75 / low, delta=0.01)  # free-space quarter wave slant
        self.assertAlmostEqual(d.extra["cone_height_m"], cone * math.cos(math.radians(30)), delta=0.01)
        disc = d.elements_with_role("disc")[0].length_m
        self.assertAlmostEqual(disc, 0.7 * d.extra["cone_base_m"], delta=0.01)


class Bands(unittest.TestCase):
    def tearDown(self):
        ds.set_region("1")

    def test_region_1_is_default(self):
        self.assertEqual(ds.current_region(), "1")
        self.assertEqual(ds.BANDS_MHZ["40m"], (7.0, 7.2))
        self.assertEqual(ds.BANDS_MHZ["80m"], (3.5, 3.8))

    def test_region_switch_updates_in_place(self):
        bands = ds.BANDS_MHZ
        ds.set_region("2")
        self.assertIs(bands, ds.BANDS_MHZ)
        self.assertEqual(bands["40m"], (7.0, 7.3))
        self.assertEqual(ds.design_frequency("40m"), 7.15)

    def test_60m_and_broad_ranges(self):
        self.assertIn("60m", ds.BANDS_MHZ)
        self.assertNotIn("KW", ds.bands_for("dipole_half_wave"))
        self.assertIn("KW", ds.bands_for("longwire_receive"))


class CableLoss(unittest.TestCase):
    def test_model_hits_both_reference_points(self):
        for name, cable in ds.CABLES.items():
            l10, l100 = cable["loss_db_100m"]
            self.assertAlmostEqual(tl.matched_loss_db_per_100m(name, 10), l10, delta=0.01, msg=name)
            self.assertAlmostEqual(tl.matched_loss_db_per_100m(name, 100), l100, delta=0.01, msg=name)
            self.assertLess(tl.matched_loss_db_per_100m(name, 3.5), l10, msg=name)

    def test_arrl_swr_loss(self):
        # ARRL Antenna Book chart: 3 dB matched loss at SWR 10 -> ~7 dB total
        self.assertAlmostEqual(tl.total_line_loss_db(3.0, 10.0), 7.0, delta=0.1)
        self.assertEqual(tl.total_line_loss_db(1.0, 1.0), 1.0)

    def test_power_budget_consistent(self):
        b = tl.power_budget_summary(100, "RG-213/U", 14.175, 30, 2.15, 2.0)
        self.assertAlmostEqual(b["total_loss_db"], b["cable_loss_db"] + b["swr_loss_db"], delta=0.011)
        self.assertAlmostEqual(b["power_at_antenna_watts"], 100 * 10 ** (-b["total_loss_db"] / 10), delta=0.3)


class Swr(unittest.TestCase):
    def test_coax_sees_the_impedance_behind_the_unun(self):
        from swr_calc import coax_side_impedance
        self.assertAlmostEqual(coax_side_impedance(design("efhw", "40m")), 50.0)
        self.assertAlmostEqual(coax_side_impedance(design("off_center_fed_dipole", "40m")), 50.0)
        self.assertAlmostEqual(coax_side_impedance(design("dipole_half_wave", "40m")), 73.0)
        self.assertAlmostEqual(coax_side_impedance(design("j_pole", "2m")), 50.0)

    def test_reactance_counts(self):
        self.assertEqual(calculate_swr(50), 1.0)
        self.assertAlmostEqual(calculate_swr(complex(50, 50)), 2.62, delta=0.01)
        self.assertEqual(calculate_swr(100), 2.0)


class Matching(unittest.TestCase):
    LOADS = [200, 12, complex(73, 42), complex(36, -20), 2450, complex(50, 50), complex(1000, -900)]

    def test_every_network_matches(self):
        for zl in self.LOADS:
            for f in (1.85, 14.175, 145.0):
                nets = mn.suggest_matching_network(50, zl, f)
                self.assertGreaterEqual(len(nets), 3)
                for n in nets:
                    self.assertAlmostEqual(abs(n["zin"] - 50), 0, delta=1e-6, msg=(zl, f, n["name"]))

    def test_pi_and_t_honour_q(self):
        n = mn.calculate_pi_network(50, 200, 14.0, q_target=5)
        self.assertAlmostEqual(n["quality_factor"], 5, delta=0.05)
        n = mn.calculate_t_network(50, 200, 14.0, q_target=5)
        self.assertAlmostEqual(n["quality_factor"], 5, delta=0.05)

    def test_formatting_and_parsing(self):
        self.assertEqual(mn.format_capacitance(1e-9), "1 nF")
        self.assertEqual(mn.format_inductance(0.33e-6), "330 nH")
        self.assertAlmostEqual(mn.nearest_e12(9.6), 10.0)
        self.assertEqual(mn.parse_impedance("36-j20"), complex(36, -20))
        self.assertEqual(mn.parse_impedance("73 + 42j"), complex(73, 42))
        self.assertEqual(mn.parse_impedance("2450,5"), complex(2450.5, 0))


class Sweep(unittest.TestCase):
    def test_resonance_and_bandwidth(self):
        d = design("dipole_half_wave", "20m")
        s = fs.sweep_design(d, *ds.BANDS_MHZ["20m"])
        self.assertAlmostEqual(s["resonance_freq"], d.design_freq_mhz, delta=1e-6)
        self.assertAlmostEqual(s["min_swr"], 1.46, delta=0.01)
        lo, hi = s["bandwidth_2"]
        rel = (hi - lo) / d.design_freq_mhz
        self.assertTrue(0.03 < rel < 0.07)  # measured wire dipoles: ~4-6 %
        self.assertGreater(s["swr_values"][0], s["min_swr"])

    def test_end_fed_is_matched_by_its_unun(self):
        d = design("efhw", "40m")
        s = fs.sweep_design(d, *ds.BANDS_MHZ["40m"])
        self.assertAlmostEqual(s["min_swr"], 1.0, delta=0.01)

    def test_not_applicable(self):
        self.assertEqual(fs.sweep_design(design("discone_receive", "VHF"), 30, 300)["not_applicable"], "broadband")
        self.assertEqual(fs.sweep_design(design("extended_double_zepp", "20m"), 14, 14.35)["not_applicable"], "tuner")


class Patterns(unittest.TestCase):
    def test_mutual_impedance_kraus(self):
        lam = 20.0
        z = rp.mutual_impedance(0.1 * lam, lam)
        self.assertAlmostEqual(z.real, 67.4, delta=1.0)
        z = rp.mutual_impedance(0.5 * lam, lam)
        self.assertAlmostEqual(z.real, -12.5, delta=1.0)
        self.assertAlmostEqual(z.imag, -29.9, delta=1.0)

    def test_dipole_free_space(self):
        p = rp.compute_pattern(design("dipole_half_wave", "20m"), 10, "free")
        self.assertAlmostEqual(p["gain_dbi"], 2.15, delta=0.1)
        # figure-8: broadside (0 deg) strong, off the wire ends (90 deg) deep null
        self.assertLess(p["azimuth_cut"][90], p["azimuth_cut"][0] - 20)

    def test_quarter_wave_over_perfect_ground(self):
        p = rp.compute_pattern(design("vertical_quarter_wave", "20m"), 0, "perfect")
        self.assertAlmostEqual(p["gain_dbi"], 5.15, delta=0.15)

    def test_real_ground_raises_vertical_takeoff(self):
        p = rp.compute_pattern(design("vertical_quarter_wave", "40m"), 0, "average")
        self.assertTrue(15 <= p["takeoff_angle_deg"] <= 35)

    def test_low_dipole_is_nvis(self):
        p = rp.compute_pattern(design("dipole_half_wave", "80m"), 10, "average")
        self.assertGreater(p["takeoff_angle_deg"], 60)

    def test_beams_are_directional(self):
        for t, fb in (("yagi_3_element", 12), ("moxon_2_element", 15), ("quad_2_element", 8)):
            p = rp.compute_pattern(design(t, "20m"), 10, "free")
            self.assertGreater(p["f_b_ratio_db"], fb, t)
            self.assertGreater(p["gain_dbi"], 5.0, t)

    def test_every_type_has_a_pattern(self):
        for t in REGISTRY:
            band = "VHF" if t == "discone_receive" else ("MW" if t in ("longwire_receive", "ground_loop_receive") else "20m")
            p = rp.compute_pattern(design(t, band))
            self.assertTrue(-5 < p["gain_dbi"] < 20, t)


if __name__ == "__main__":
    unittest.main()
