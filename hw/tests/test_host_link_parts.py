"""BOM faults independent of physical net connectivity."""
import copy
import csv
import json
from pathlib import Path
import sys
import unittest
import pcbnew

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'hw/tools'))
from host_link_checks import verify_parts


class HostLinkPartsTests(unittest.TestCase):
    def setUp(self):
        folder=ROOT/'hw/boards/shakesense-trenz-hat'
        self.board=pcbnew.LoadBoard(str(folder/'shakesense-trenz-hat.kicad_pcb'))
        self.spec=json.loads((ROOT/'hw/layout-trenz.json').read_text())['shakesense-trenz-hat']
        with (folder/'bom.csv').open(newline='',encoding='utf8') as stream:self.bom=list(csv.DictReader(stream))

    def test_complete_parts_fixture(self):
        self.assertEqual(verify_parts(self.spec,self.bom,self.board),32)

    def test_wrong_supervisor_variant(self):
        row=next(p for p in self.spec['parts'] if p['ref']=='U104')
        row['mpn']='TLV810EA30DBZR'  # Same land pattern, opposite reset polarity.
        with self.assertRaises(AssertionError):verify_parts(self.spec,self.bom,self.board)

    def test_missing_bypass_or_wrong_resistor_decade(self):
        for ref,field,value in [('C103','DNP','True'),('R107','Value','1k'),('U106','Footprint','SOT-23')]:
            with self.subTest(ref=ref):
                bom=copy.deepcopy(self.bom)
                next(p for p in bom if p['Reference']==ref)[field]=value
                with self.assertRaises(AssertionError):verify_parts(self.spec,bom,self.board)

    def test_board_value_drift(self):
        f=next(f for f in self.board.GetFootprints() if f.GetReference()=='R100')
        f.SetValue('0')
        with self.assertRaises(AssertionError):verify_parts(self.spec,self.bom,self.board)

    def test_duplicate_bom_reference(self):
        self.bom.append(self.bom[-1].copy())
        with self.assertRaises(AssertionError):verify_parts(self.spec,self.bom,self.board)


if __name__=='__main__':unittest.main()
