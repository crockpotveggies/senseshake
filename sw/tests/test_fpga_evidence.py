"""Prove the report gate rejects missing coverage and real failures."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'fpga'))
from verify_reports import validate


class FPGATimingGateTests(unittest.TestCase):
    def setUp(self):
        self.timing='\n'.join(f'checking {c} (0)' for c in (
            'no_clock','constant_clock','unconstrained_internal_endpoints','multiple_clock','loops','latch_loops'))
        self.timing+='\n WNS(ns) header\n ------- ------\n 1.0 0 0 42 0.1 0 0 42 9.5 0 0 42\nAll user specified timing constraints are met.'
        self.cdc='CDC Report\nCDC-3 Info 1'
        self.drc='Checks found: 0'

    def test_positive_report(self):
        self.assertEqual(validate(self.timing,self.cdc,self.drc)['setup_slack_ns'],1)

    def test_missing_or_unconstrained_endpoints(self):
        for timing in ('',self.timing.replace('unconstrained_internal_endpoints (0)','unconstrained_internal_endpoints (1)'),
                       self.timing.replace('0 0 42','0 0 0')):
            with self.assertRaises(ValueError):validate(timing,self.cdc,self.drc)

    def test_negative_or_nonfinite_slack(self):
        for value in ('-0.01','nan','-inf','inf'):
            with self.assertRaises(ValueError):validate(self.timing.replace('1.0',value),self.cdc,self.drc)

    def test_cdc_or_drc_findings(self):
        for cdc,drc in [('',self.drc),(self.cdc+'\nCDC-1 Critical 1',self.drc),
                        (self.cdc,''),(self.cdc,'Checks found: 1')]:
            with self.assertRaises(ValueError):validate(self.timing,cdc,drc)


if __name__=='__main__':unittest.main()
