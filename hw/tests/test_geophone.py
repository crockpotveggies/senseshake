import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from geophone_checks import PINS, verify


class GeophoneCircuitTests(unittest.TestCase):
    def test_removed_inclinometer_and_support_parts_cannot_return(self):
        orientation={f'U{i}':(0,False) for i in range(11,14)}
        for ref in ('U20','C20','C21','C22','C23','R20'):
            with self.subTest(ref=ref), self.assertRaisesRegex(ValueError,'removed inclinometer'):
                verify(PINS,{**orientation,ref:(0,False)})
        with self.assertRaisesRegex(ValueError,'removed inclinometer'):
            verify({**PINS,('J1','33'):'PI_TILT_CS'},orientation)

    def test_removed_fourth_imu_cannot_silently_return(self):
        orientation={f'U{i}':(0,False) for i in range(11,14)}
        for ref in ('U14','R14','C18','C19'):
            with self.assertRaisesRegex(ValueError,'removed fourth'):
                verify(PINS,{**orientation,ref:(0,False)})

    def test_rejects_missing_or_reversed_terminal(self):
        orientation={f'U{i}':(0,False) for i in range(11,14)}
        self.assertEqual(verify(PINS,orientation),len(PINS))
        for key in PINS:
            wrong=dict(PINS);wrong[key]='WRONG'
            with self.assertRaises(ValueError): verify(wrong,orientation)

    def test_rejects_any_rotated_or_flipped_imu(self):
        for i in range(11,14):
            for pose in ((90,False),(180,False),(0,True)):
                axes={f'U{j}':(0,False) for j in range(11,14)};axes[f'U{i}']=pose
                with self.assertRaises(ValueError):verify(PINS,axes)
