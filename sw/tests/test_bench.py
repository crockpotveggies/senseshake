from copy import deepcopy
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from senseshake.bench import template, evaluate, evidence, CHECKS


class BenchTests(unittest.TestCase):
    def test_empty_report_is_incomplete_not_pass(self):
        self.assertEqual(evaluate(template(),'.')['status'],'incomplete')

    def test_public_init_and_check_do_not_turn_blank_report_into_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            report=Path(directory)/'report.json'
            entry=Path(__file__).resolve().parents[1]/'tools/bench.py'
            init=subprocess.run([sys.executable,str(entry),'init',str(report)],capture_output=True,text=True)
            self.assertEqual(init.returncode,0,init.stderr)
            check=subprocess.run([sys.executable,str(entry),'check',str(report)],capture_output=True,text=True)
            self.assertEqual(check.returncode,2,check.stdout+check.stderr)
            repeat=subprocess.run([sys.executable,str(entry),'init',str(report)],capture_output=True,text=True)
            self.assertNotEqual(repeat.returncode,0)

    def test_limits_requirements_and_evidence_integrity(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); trace=root/'trace.txt';trace.write_text('synthetic evidence for validator test')
            report=template()
            for key in ('operator','date_utc','hardware_revision','board_serial','software_commit','pi_and_kernel','geophone_serial','fpga_image'):
                report[key]='test fixture'
            report['conditions']={key:'fixture' for key in report['conditions']}
            report['equipment']=['test fixture; no physical measurement']
            report['targets']={key:1 for key in report['targets']}
            for key,row in report['checks'].items():
                row['value']= True if row['unit']=='boolean' else 0
                row['evidence']=[evidence(trace,root)]
            report['checks']['module_min_v']['value']=3.24
            report['checks']['module_max_v']['value']=3.36
            for key,value in {'fpga_spi_clock_max':1_000_000,'fpga_sclk_high_min':500,
                              'fpga_sclk_low_min':500,'fpga_cs_setup_min':1000,
                              'fpga_cs_hold_min':1000,'fpga_cs_inactive_min':1000}.items():
                report['checks'][key]['value']=value
            self.assertEqual(evaluate(report,root)['status'],'pass')
            for key,value in [('module_min_v',3.19),('module_max_v',3.4),('hot_loop_resistance',.031),('power_sequence',False)]:
                bad=deepcopy(report);bad['checks'][key]['value']=value
                self.assertEqual(evaluate(bad,root)['status'],'fail')
            bad=deepcopy(report);bad['targets']['max_geophone_timing_error_ns']=None
            self.assertEqual(evaluate(bad,root)['status'],'incomplete')
            for key,value in [('fpga_spi_clock_max',1_000_001),('fpga_sclk_high_min',499),
                              ('fpga_sclk_low_min',499),('fpga_cs_setup_min',999),
                              ('fpga_cs_hold_min',999),('fpga_cs_inactive_min',999),
                              ('fpga_jtag_programming',False),('fpga_mode_handoff',False),
                              ('fpga_loopback_errors',1)]:
                bad=deepcopy(report);bad['checks'][key]['value']=value
                self.assertEqual(evaluate(bad,root)['status'],'fail',key)
                bad['checks'][key]['value']=None
                self.assertEqual(evaluate(bad,root)['status'],'incomplete',key)
            trace.write_text('changed')
            self.assertEqual(evaluate(report,root)['status'],'fail')

    def test_units_nonfinite_and_outside_evidence(self):
        report=template();report['checks']['module_min_v']['unit']='mV'
        with self.assertRaises(ValueError):evaluate(report,'.')
        report=template();report['checks']['module_min_v']['value']=float('nan')
        with self.assertRaises(ValueError):evaluate(report,'.')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'report').mkdir();outside=root/'outside';outside.write_text('x')
            with self.assertRaises(ValueError):evidence(outside,root/'report')

    def test_legacy_or_missing_fpga_inventory_cannot_qualify_current_board(self):
        report=template();report['version']=2
        with self.assertRaises(ValueError):evaluate(report,'.')
        report=template();del report['checks']['fpga_jtag_programming']
        with self.assertRaises(ValueError):evaluate(report,'.')


if __name__=='__main__':unittest.main()
