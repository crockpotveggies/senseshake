import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from geophone_checks import PINS, verify


class GeophoneCircuitTests(unittest.TestCase):
    def test_rejects_missing_or_reversed_terminal(self):
        orientation={f'U{i}':(0,False) for i in range(11,15)}
        self.assertEqual(verify(PINS,orientation),len(PINS))
        for key in PINS:
            wrong=dict(PINS);wrong[key]='WRONG'
            with self.assertRaises(ValueError): verify(wrong,orientation)

    def test_rejects_any_rotated_or_flipped_imu(self):
        for i in range(11,15):
            for pose in ((90,False),(180,False),(0,True)):
                axes={f'U{j}':(0,False) for j in range(11,15)};axes[f'U{i}']=pose
                with self.assertRaises(ValueError):verify(PINS,axes)
