"""Bounded passive interface and DC input-budget checks; not FPGA simulation."""
from pathlib import Path
import subprocess,re,json,itertools
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'hw/simulation/trenz';OUT.mkdir(exist_ok=True)
results=[]
def run(name,body):
    path=OUT/(name+'.cir');path.write_text('ShakeSense Trenz support check: '+name+'\n'+body+'\n.end\n')
    r=subprocess.run(['ngspice','-b',str(path)],capture_output=True,text=True);log=r.stdout+r.stderr;(OUT/(name+'.log')).write_text(log)
    assert r.returncode==0,log
    return {k:float(v) for k,v in re.findall(r'^([a-z][a-z0-9_]*)\s*=\s*([-+0-9.eE]+)',log,re.M)}
for vin,load in itertools.product([3.267,3.333],[.1,1.5,3.0]):
    # 15 milliohms is a design budget for fuse+PCB, NOT extracted resistance.
    m=run(f'dc_{vin}_{load}',f'Vsource src 0 {vin}\nRpath src module 0.015\nIload module 0 {load}\nCbulk module 0 26.4u\n.tran 1u 100u\n.measure tran vmodule FIND v(module) AT=99u')
    assert 3.201<=m['vmodule']<=3.399,m
    results.append(dict(case=f'dc_{vin}_{load}',measured=m,pass_check=True))
# Negative case: excessive wiring resistance must be recognized as unsafe.
m=run('reject_long_power_lead','Vsource src 0 3.267\nRpath src module 0.10\nIload module 0 3\n.tran 1u 100u\n.measure tran vmodule FIND v(module) AT=99u')
assert m['vmodule']<3.201;results.append(dict(case='reject_long_power_lead',measured=m,undervoltage_detected=True))
for cap in [25,100,200]:
    m=run(f'uart_{cap}pf',f'Vdrive src 0 PULSE(0 3.201 100n 5n 5n 500n 1u)\nRdriver src driver 25\nRseries driver rx 47\nCload rx 0 {cap}p\n.tran .5n 900n\n.measure tran rise TRIG v(rx) VAL=0.9603 RISE=1 TARG v(rx) VAL=2.2407 RISE=1\n.measure tran sample FIND v(rx) AT=350n')
    assert m['rise']<50e-9 and m['sample']>2.31,m
    results.append(dict(case=f'uart_{cap}pf',measured=m,pass_check=True))
(OUT/'results.json').write_text(json.dumps({'cases':results,'scope':'6 DC budget checks, 1 expected undervoltage detection, 3 lumped UART RC checks; not regulator stability, silicon, FPGA firmware or signal-integrity signoff'},indent=2));print('PASS:',len(results),'bounded support-circuit cases')
