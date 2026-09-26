"""Fault tests for assembly release integrity; no CAD mutation or rerouting."""
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from jlcpcb_package import check_reference_sets, physical, validate_plot_inventory, EXTENSIONS, check_drills


class AssemblyPackageTests(unittest.TestCase):
    def test_drill_quantization(self):
        check_drills([(12.0009, -20, 0.1)], [(12, -20, 0.1)])

    def test_mirrored_shifted_resized_and_duplicated_drills(self):
        expected = [(12, -20, 0.1)]
        for actual in [[(12, 20, .1)], [(12.01, -20, .1)], [(12, -20, .2)], expected*2, []]:
            with self.assertRaises(ValueError): check_drills(expected, actual)

    def test_grouped_bom_matches_placements(self):
        check_reference_sets([{'Designator': 'R1,R2'}, {'Designator': 'U1'}],
                             [{'Designator': r} for r in ['U1', 'R2', 'R1']])

    def test_missing_or_unexpected_placement(self):
        for actual in ['R1', 'R1,R2,U1']:
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                check_reference_sets([{'Designator': 'R1,R2'}], [{'Designator': r} for r in actual.split(',')])

    def test_duplicate_ref_rejected_on_either_side(self):
        for bom, cpl in [('R1,R1', 'R1'), ('R1', 'R1,R1')]:
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                check_reference_sets([{'Designator': bom}], [{'Designator': r} for r in cpl.split(',')])

    def test_only_holes_and_bare_testpads_excluded(self):
        for ref in ['H1', 'H80', 'TP4']: self.assertFalse(physical(ref))
        for ref in ['J1', 'JP1', 'U20', 'F80']: self.assertTrue(physical(ref))

    def plots(self, root):
        for extension in EXTENSIONS: (root / ('test.' + extension)).write_text('placeholder')
        for i, span in enumerate(['NonPlated,1,8,NPTH', 'Plated,1,8,PTH', 'Plated,1,2,Blind', 'Plated,7,8,Blind']):
            (root / f'{i}.drl').write_text(f'METRIC\n; #@! TF.FileFunction,{span}\n')

    def test_complete_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.plots(root); validate_plot_inventory(root)

    def test_missing_inner_layer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.plots(root); (root / 'test.g6').unlink()
            with self.assertRaisesRegex(ValueError, 'Missing manufacturing'): validate_plot_inventory(root)

    def test_merged_drills_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.plots(root); (root / '3.drl').unlink()
            with self.assertRaisesRegex(ValueError, 'separate'): validate_plot_inventory(root)

    def test_wrong_blind_span_or_units(self):
        for wrong in ['METRIC\n; #@! TF.FileFunction,Plated,2,7,Blind', 'INCH\n; #@! TF.FileFunction,Plated,7,8,Blind']:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); self.plots(root); (root / '3.drl').write_text(wrong)
                with self.assertRaises(ValueError): validate_plot_inventory(root)


if __name__ == '__main__': unittest.main()
