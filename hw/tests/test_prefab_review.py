import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from prefab_review import response, separation, analog_review
from assembly_fit import review


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

    def test_harness_review_does_not_claim_full_fit(self):
        placements={'J86':(17,22,0,'back'),'J87':(17,39,180,'back'),
                    'J88':(57,20,0,'back'),'J89':(57,37,180,'back')}
        result=review(placements)
        self.assertGreater(result['minimum_pi_port_margin_mm'],2)
        self.assertEqual(result['omitted_support_xy_mm'],[61.5,52.5])
        self.assertIn('flex_local_clearance',{r['code'] for r in result['findings']})
        placements['J86']=(17,22,180,'back')
        with self.assertRaises(AssertionError):review(placements)
