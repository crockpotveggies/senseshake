import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from prefab_review import response, separation, analog_review
from assembly_fit import review, PI_SUPPORTS, default_obstacles


class PrefabReviewTests(unittest.TestCase):
    def test_physical_limits_and_independent_spice_reference(self):
        self.assertEqual(response(0),0)
        self.assertAlmostEqual(abs(response(10))*.0001,.002299408,delta=2e-9)
        self.assertAlmostEqual(abs(response(4.5,coil=0,series=0)),23.4/1.4)
        self.assertAlmostEqual(abs(response(100,coil=0,series=0,damping=0,f0=0)),23.4)

    def test_full_corners_enclose_nominal_and_common_mode(self):
        result=analog_review()
        self.assertEqual(result['corner_count'],256)
        for row in result['response']:
            self.assertLess(row['minimum_v_per_m_s'],row['nominal_v_per_m_s'])
            self.assertGreater(row['maximum_v_per_m_s'],row['nominal_v_per_m_s'])
        self.assertGreater(result['minimum_full_scale_common_mode_margin_v'],1)
        self.assertAlmostEqual(result['nominal_actual_sps'],328.626444,places=5)
        self.assertFalse(result['digital_filter']['exact_alias_rejection_qualified'])

    def test_mechanical_overlap_is_not_clearance(self):
        module=[30,8,80,48]
        self.assertEqual(separation([40,20,50,30],module),0)
        self.assertEqual(separation([20,20,30,30],module),0)
        self.assertEqual(separation([10,20,21,30],module),9)

    def test_four_straight_supports(self):
        report=review({})
        self.assertEqual(report['external_ribbon_count'],0)
        self.assertFalse(report['custom_guide_required'])
        self.assertEqual(len(report['pi_supports_xy_mm']),4)
        self.assertGreater(min(report['support_to_pi_margin_mm'].values()),0)

    def test_missing_fourth_support_rejected(self):
        with self.assertRaisesRegex(AssertionError,'four'):
            review({},supports=PI_SUPPORTS[:3])

    def test_fourth_support_collision_rejected(self):
        obstacles=default_obstacles({})
        obstacles['new_part']=(60,51,-5,63,54,-1.6)
        with self.assertRaisesRegex(AssertionError,'support-to-HAT'):
            review({},obstacles)

    def test_tall_underside_part_collides_with_heatsink(self):
        obstacles=default_obstacles({})
        obstacles['new_part']=(25,22,-20,35,30,-1.6)
        with self.assertRaisesRegex(AssertionError,'HAT-to-Pi'):
            review({},obstacles)

    def test_old_external_connectors_rejected(self):
        with self.assertRaisesRegex(AssertionError,'External'):
            review({'J86':(17,22,0,'back')})
