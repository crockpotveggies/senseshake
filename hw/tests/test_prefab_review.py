import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from prefab_review import response, separation, analog_review
from assembly_fit import review, EXPECTED, SPACER_BOXES, default_obstacles, cable_path, clearance


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

    def test_guided_four_ribbon_assembly_preserves_all_supports(self):
        placements={k:(*v,'back') for k,v in EXPECTED.items()}
        result=review(placements)
        self.assertEqual(result['slot_height_cases'],36)
        self.assertGreater(result['minimum_obstacle_margin_mm'],.15)
        self.assertGreater(result['guide_to_pi_port_margin_mm'],.3)
        self.assertGreater(result['ribbon_to_ribbon_margin_mm'],1.6)
        self.assertEqual(len(result['pi_supports_xy_mm']),4)
        self.assertIsNone(result['omitted_support_xy_mm'])
        self.assertEqual(result['findings'],[])
        self.assertIn('unmeasured',result['status'])

    def test_original_j87_position_reproduces_capacitor_collision(self):
        obstacles=default_obstacles({})
        old=cable_path('J87',17,39,-1.765)
        self.assertLess(clearance(old,20.5,obstacles['C95']),0)
        self.assertLess(clearance(old,20.5,obstacles['C96']),0)
        new=cable_path('J87',17,36,-1.765)
        self.assertGreater(clearance(new,20.5,obstacles['C96']),.8)

    def test_straight_fourth_spacer_cannot_replace_offset_part(self):
        placements={k:(*v,'back') for k,v in EXPECTED.items()}
        with self.assertRaisesRegex(AssertionError,'straight'):
            review(placements,spacer_boxes={'straight':(59.1,50.1,-28.779,63.9,54.9,-1.6)})

    def test_raised_lower_arm_and_untrimmed_tails_fail(self):
        placements={k:(*v,'back') for k,v in EXPECTED.items()}
        bad=dict(SPACER_BOXES);bad['lower_arm']=(31,50,-14,61.5,55,-9.8)
        with self.assertRaisesRegex(AssertionError,'lower_arm'):
            review(placements,spacer_boxes=bad)
        with self.assertRaisesRegex(AssertionError,'untrimmed'):
            review(placements,{'untrimmed':(16.5,50,-8,17.5,51,-1.6)})

    def test_reversed_connector_rejected(self):
        placements={k:(*v,'back') for k,v in EXPECTED.items()}
        placements['J86']=(17,22,180,'back')
        with self.assertRaises(AssertionError):review(placements)

    def test_original_power_terminal_tails_cross_left_return_bend(self):
        path=cable_path('J86',17,22,-1.765)
        old_tail=(5.7,15.78,-3.8,8.3,18.38,-1.6)
        new_tail=(3.4,15.78,-3.8,6,18.38,-1.6)
        self.assertLess(clearance(path,20.5,old_tail),0)
        self.assertGreater(clearance(path,20.5,new_tail),.24)

    def test_long_generic_stiffener_cannot_replace_short_custom_tip(self):
        from unittest.mock import patch
        shield_tail=(69.225,12.4,-3.8,70.725,13.9,-1.6)
        self.assertGreater(clearance(cable_path('J88',57,20,-1.765),30.5,shield_tail),.2)
        with patch('assembly_fit.STRAIGHT',6):
            self.assertLess(clearance(cable_path('J88',57,20,-1.765),30.5,shield_tail),0)
