"""Audit all 158 ordinary TE0712-03-81I36-A I/Os against vendor page 6.

The module/ground CSVs are schematic transcriptions, not generated CAD netlists.
The separate breakout CSV is the carrier interface contract. Dedicated clocks,
Ethernet PHY pairs and GTP lanes must remain disconnected on this carrier.
"""
from collections import Counter
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[2]
CARRIER = {'JM1': 'J80', 'JM2': 'J81', 'JM3': 'J82'}
HOST = {('JM2', 11): 'FPGA_UART_RX', ('JM2', 13): 'FPGA_UART_TX',
        ('JM2', 14): 'FPGA_RESET_N'}
AUX = {('JM2', 16): ('FPGA_AUX0', '1'), ('JM2', 15): ('FPGA_AUX1', '3'),
       ('JM2', 17): ('FPGA_AUX2', '5')}
CONTROL = {
 'JM1': {1:'FPGA_VIN',3:'FPGA_VIN',5:'FPGA_VIN',7:'FPGA_NOSEQ',9:'FPGA_3V3',
         11:'FPGA_3V3',13:'FPGA_VIN',14:'FPGA_3V3',15:'FPGA_VIN',28:'FPGA_EN1',
         30:'FPGA_PGOOD',32:'FPGA_MODE',89:'FPGA_JTAGEN'},
 'JM2': {1:'FPGA_3V3',2:'FPGA_VIN',3:'FPGA_3V3',4:'FPGA_VIN',6:'FPGA_VIN',
         7:'FPGA_3V3',8:'FPGA_VIN',9:'FPGA_3V3',10:'FPGA_3V3',12:'FPGA_3V3',
         18:'FPGA_CONFIG_RESET_N',91:'FPGA_3V3',93:'JTAG_TMS',95:'JTAG_TDI',
         97:'JTAG_TDO',99:'JTAG_TCK'}, 'JM3': {}}


def records(name):
    with (ROOT / 'docs' / name).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def pad(module, number):
    return CARRIER[module], str(number + 1 if number % 2 else number - 1)


def check(pins):
    module = records('trenz-gpio-module.csv')
    breakout = records('trenz-gpio-breakout.csv')
    grounds = records('trenz-ground-module.csv')
    assert len(module) == len(breakout) == 158
    assert Counter(int(r['bank']) for r in module) == {13:30,14:30,15:50,16:48}
    by_key = {(r['module_connector'], int(r['module_pin'])): r for r in breakout}
    assert len(by_key) == 158, 'Duplicated module GPIO'
    expected = {}; external = {}; seen_nets = set()
    for r in module:
        k = r['module_connector'], int(r['module_pin'])
        b = by_key[k]
        assert b['signal'] == r['signal'] and b['bank'] == r['bank'], k
        cp = pad(*k)
        assert cp == (b['carrier_ref'], b['carrier_pad']), ('Mating parity', k)
        net = HOST.get(k, AUX[k][0] if k in AUX else 'FPGA_' + r['signal'])
        assert b['net'] == net and pins[cp] == net, (k, net, pins.get(cp))
        assert net not in seen_nets, ('Aliased GPIO', net)
        seen_nets.add(net); expected[k] = net
        if k in HOST:
            assert b['breakout_ref'] == 'host' and not b['breakout_pad']
            continue
        if k in AUX:
            ep = ('J85', AUX[k][1])
        else:
            ep = b['breakout_ref'], b['breakout_pad']
            assert ep[0] == {13:'J86',14:'J87',15:'J88',16:'J89'}[int(r['bank'])]
        assert ep == (b['breakout_ref'], b['breakout_pad'])
        assert ep not in external and pins[ep] == net, (ep, net)
        external[ep] = net
        # Direct pass-through has precisely one module and one breakout endpoint.
        assert {p for p,n in pins.items() if n == net} == {cp, ep}, ('Unexpected GPIO stub', net)
    assert len(external) == 155
    for r in grounds:
        k = r['module_connector'], int(r['module_pin'])
        assert k not in expected, ('GPIO grounded', k)
        expected[k] = 'GND'
    for m, assignments in CONTROL.items():
        for n, net in assignments.items():
            assert (m,n) not in expected
            expected[m,n] = net
    degree = Counter(pins.values())
    for m, count in [('JM1',100),('JM2',100),('JM3',60)]:
        for n in range(1,count+1):
            key = pad(m,n); net = pins[key]
            if (m,n) in expected:
                assert net == expected[m,n], (m,n,net,expected[m,n])
            else:
                assert net and degree[net] == 1, ('Reserved/dedicated pin connected',m,n,net)
        assert pins[CARRIER[m],str(count+1)] == 'GND'
    # All non-signal expansion contacts are returns, except pin 2 (reference OUT).
    for ref,count in [('J86',40),('J87',40),('J88',60),('J89',60)]:
        for n in range(1,count+2):
            ep = ref,str(n)
            assert pins[ep] == external.get(ep,'FPGA_3V3' if n == 2 else 'GND'), ep
    for n in ('2','4','6'):
        assert pins['J85',n] == 'GND'
    return {'module_gpio_checks':158, 'module_contact_checks':260,
            'exposed_gpio':155, 'added_gpio':152, 'gpio_voltage_v':3.3}
