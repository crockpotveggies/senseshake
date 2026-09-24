"""Fault injection for GPIO mapping: exercise known wiring hazards."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import gpio_audit as audit
import pcbnew

class GPIOFaultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        board = pcbnew.LoadBoard(str(audit.ROOT / 'hw/layout/trenz_hat/trenz_hat.kicad_pcb'))
        cls.original = {(f.GetReference(),p.GetNumber()):p.GetNetname()
                        for f in board.GetFootprints() for p in f.Pads() if p.GetNumber()}

    def setUp(self):
        self.pins = self.original.copy()

    def test_valid_compiled_circuit(self):
        self.assertEqual(audit.check(self.pins)['exposed_gpio'],155)

    def test_atomic_footprint_uuid_repair(self):
        from kicad_support import unique_ids
        b=pcbnew.BOARD()
        original=pcbnew.FootprintLoad(str(audit.ROOT/'hw/elec'),'TZ_FFC40')
        for ref in ('J86','J87'):
            f=pcbnew.FOOTPRINT(original)
            f.SetReference(ref);b.Add(f)
        ids=lambda:[q.m_Uuid.AsString() for f in b.GetFootprints() for q in f.Pads()]
        self.assertNotEqual(len(ids()),len(set(ids())))
        unique_ids(b)
        repaired=ids()
        self.assertEqual(len(repaired),len(set(repaired)))
        unique_ids(b)
        self.assertEqual(ids(),repaired)

    def test_save_preserves_project_rules(self):
        import json, tempfile
        from kicad_support import save_board
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'rules.kicad_pcb'
            project=path.with_suffix('.kicad_pro')
            content=json.dumps({'net_settings':{'classes':[{'name':'Default','clearance':0.15}]}}).encode()
            project.write_bytes(content)
            save_board(path,pcbnew.BOARD())
            self.assertEqual(project.read_bytes(),content)

    def test_old_grounded_gpio(self):
        self.pins['J80','32'] = 'GND'  # Module JM1.31, B16_L22_P.
        with self.assertRaises(AssertionError): audit.check(self.pins)

    def test_old_grounded_ethernet(self):
        self.pins['J80','11'] = 'GND'  # Module JM1.12, PHY ETH_RD_N.
        with self.assertRaises(AssertionError): audit.check(self.pins)

    def test_reversed_mating_parity(self):
        self.pins['J80','16'],self.pins['J80','17'] = self.pins['J80','17'],self.pins['J80','16']
        with self.assertRaises(AssertionError): audit.check(self.pins)

    def test_missing_breakout(self):
        self.pins['J88','4'] = 'UNCONNECTED'
        with self.assertRaises(AssertionError): audit.check(self.pins)

    def test_wrong_reference_voltage(self):
        self.pins['J89','2'] = 'PI_5V'
        with self.assertRaises(AssertionError): audit.check(self.pins)

    def test_unintended_shared_gpio(self):
        self.pins['EXTRA','1'] = self.pins['J88','4']
        with self.assertRaises(AssertionError): audit.check(self.pins)

if __name__ == '__main__': unittest.main()
