"""Fail closed on missing/stale FPGA implementation evidence.

--record accepts a completed Vivado output directory; default checks committed
reports and exact RTL/XDC/build hashes. It does not rerun Vivado or program hardware.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'sw/fpga/verification'
SOURCES=('sw/fpga/rtl/t1_link.sv','sw/fpga/t1.xdc','sw/fpga/build.tcl')
REPORTS=('timing.rpt','cdc.rpt','drc.rpt','utilization.rpt')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(timing,cdc,drc):
    for category in ('no_clock','constant_clock','unconstrained_internal_endpoints',
                     'multiple_clock','loops','latch_loops'):
        values=re.findall(r'checking '+category+r' \((\d+)\)',timing)
        if not values or any(int(v) for v in values):raise ValueError(f'Timing coverage: {category}')
    row=re.search(r'^\s*WNS\(ns\).*\n\s*[- ]+\n([^\n]+)',timing,re.M)
    if row is None:raise ValueError('Missing timing summary')
    fields=row[1].split()
    if len(fields)!=12:raise ValueError('Incomplete timing summary')
    setup,hold,pulse=(float(fields[i]) for i in (0,4,8))
    if not all(math.isfinite(v) and v>=0 for v in (setup,hold,pulse)):raise ValueError('Timing slack')
    if any(float(fields[i])!=0 for i in (1,2,5,6,9,10)):raise ValueError('Failing timing endpoints')
    if any(int(fields[i])<=0 for i in (3,7,11)):raise ValueError('Missing timed endpoints')
    if 'All user specified timing constraints are met.' not in timing:raise ValueError('Timing failed')
    if 'CDC Report' not in cdc or re.search(r'CDC-\d+\s+(Critical|Warning)',cdc):raise ValueError('CDC review')
    findings=re.findall(r'Checks found:\s*(\d+)',drc)
    if not findings or any(int(v) for v in findings):raise ValueError('FPGA DRC')
    return dict(setup_slack_ns=setup,hold_slack_ns=hold,pulse_width_slack_ns=pulse)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record',type=Path)
    args=parser.parse_args()
    directory=args.record or FOLDER
    metrics=validate(*( (directory/name).read_text() for name in REPORTS[:3]))
    if args.record:
        bit=directory/'t1-link.bit'
        if bit.stat().st_size<1_000_000:raise ValueError('Missing/truncated 200T bitstream')
        tool=re.search(r'Tool Version : (.+)',(directory/'timing.rpt').read_text())
        for name in REPORTS:
            (FOLDER/name).write_text((directory/name).read_text(),encoding='utf8',newline='\n')
        record=dict(tool=tool[1].strip(),part='xc7a200tfbg484-1',clock_mhz=50,**metrics,
                    bitstream_generated=True,bitstream_sha256=sha(bit),
                    source_sha256={name:sha(ROOT/name) for name in SOURCES},
                    report_sha256={name:sha(FOLDER/name) for name in REPORTS},
                    limits=['Asynchronous input-to-first-stage and reset exceptions are intentional; board timing is not measured',
                            'Reserved DQ2/DQ3 optimized out; unused pins remain undriven',
                            'No physical Pi/Linux/JTAG qualification; reports are digital implementation evidence only'])
        (FOLDER/'result.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8',newline='\n')
    else:
        record=json.loads((FOLDER/'result.json').read_text())
        if record['source_sha256']!={name:sha(ROOT/name) for name in SOURCES}:raise ValueError('Stale FPGA source evidence')
        if record['report_sha256']!={name:sha(FOLDER/name) for name in REPORTS}:raise ValueError('Changed FPGA reports')
        if any(record.get(key)!=value for key,value in metrics.items()):raise ValueError('Incorrect recorded timing')
    print('PASS FPGA implementation evidence:',metrics)


if __name__=='__main__':main()
