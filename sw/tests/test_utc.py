"""Independent calendar/wire fixtures and faults through capture/record/replay."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from senseshake.utc import intervals, correlate, tim_tp, timeutc, policy_check
from senseshake.gnss_timing import TimedGNSS, configuration_evidence
from senseshake.sensors import ubx_packet
from senseshake.simulation import defaults
from senseshake.recording import Reader, Writer
from senseshake.runtime import Acquisition, Channel
from senseshake.session import Sessions
from senseshake import messages
from senseshake.cli import replay

S = 1_000_000_000
BASE = int(datetime(2026, 9, 24, 12, tzinfo=timezone.utc).timestamp())


def tp(second, flags=3, qerr=-1501):
    epoch = int(datetime(1980, 1, 6, tzinfo=timezone.utc).timestamp())
    week, tow = divmod(second - epoch, 7*24*3600)
    return struct.pack('<IIiHBB', tow*1000, 0, qerr, week, flags, 0x30)


def nav(second, valid=0x37):
    d = datetime.fromtimestamp(second, timezone.utc)
    return struct.pack('<IIiH6B', 123000, 25, 0, d.year, d.month, d.day, d.hour, d.minute, d.second, valid)


def policy(digest='a'*64):
    return dict(version=1, recording_sha256=digest, scope='modeled', evidence='independent synthetic timing fixture',
                transport_max_ns=100_000_000, edge_error_ns=1000, pulse_error_ns=1000,
                capture_age_max_ns=200_000_000, clock_rate_ppm=100, sample_error_ns={'1':25000, '6':1000})


def fixture():
    events = [(0, dict(code='gnss_timing_config', effective=configuration_evidence()))]
    for second in range(1, 8):
        t = second*S
        events.append((t+1_000_000, dict(code='pps_edge', monotonic_ns=t+5000, estimated_raw_ns=t,
                        mapping_monotonic_ns=t+1_005_000, mapping_bracket_ns=200)))
        if second < 7:
            for offset, code, payload in [(250_000_000, 'gnss_timeutc', nav(BASE+second-1)),
                                         (260_000_000, 'gnss_tim_tp', tp(BASE+second))]:
                events.append((t+offset+1000, dict(code=code, read_start_ns=t+offset-1000,
                              read_end_ns=t+offset, payload_hex=payload.hex())))
    return events


class ConfigBus:
    def __init__(self, bad=False): self.data, self.writes, self.bad = b'', [], bad
    def exchange(self, address, write, count):
        if count:
            if write == b'\xfd': return len(self.data).to_bytes(2, 'big')
            result, self.data = self.data[:count], self.data[count:]
            return result
        self.writes.append(write)
        if write[3] == 0x8a:
            self.fields = write[10:-2]
            self.data += ubx_packet(5, 1, b'\x06\x8a')
        else:
            fields = self.fields[:-1] + bytes([self.fields[-1] ^ self.bad])
            self.data += ubx_packet(6, 0x8b, b'\x01\0\0\0' + fields)
        return b''
    def close(self): pass


class UTCTests(unittest.TestCase):
    def test_calendar_and_signed_quantization_error(self):
        self.assertEqual(tim_tp(tp(BASE)), (BASE*S, 2, 3))
        self.assertEqual(timeutc(nav(BASE)), (BASE*S, 25, 3))
        for flags in (0, 1, 2, 0x13, 0x23, 0x43):
            with self.assertRaises(ValueError): tim_tp(tp(BASE, flags))
        for valid in (0, 0x33, 7, 0xf7):
            with self.assertRaises(ValueError): timeutc(nav(BASE, valid))

    def test_noninteger_pulse_unknown_standard_and_malformed(self):
        for offset, value in ((0, 1), (4, 1), (15, 0xf0)):
            value_bytes = bytearray(tp(BASE)); value_bytes[offset] = value
            with self.assertRaises(ValueError): tim_tp(bytes(value_bytes))
        for data in (b'', bytes(15), bytes(17)):
            with self.assertRaises(ValueError): tim_tp(data)
        payload=bytearray(nav(BASE));payload[4:8]=(100_000_001).to_bytes(4,'little')
        with self.assertRaises(ValueError):timeutc(bytes(payload))

    def test_configuration_wire_keys_ack_and_full_readback(self):
        bus = ConfigBus()
        driver = TimedGNSS(bus, sleep=lambda _:None, clock_ns=lambda:0)
        self.assertEqual(driver.configure(defaults(legacy_gnss=True)[5]), defaults(legacy_gnss=True)[5])
        written = bus.writes[0]
        for independent_hex in ('7d01912001', '5b00912001', '0200054040420f00',
                                '0c00052000', '0b00051001', '3000052001'):
            self.assertIn(bytes.fromhex(independent_hex), written)
        with self.assertRaises(OSError): TimedGNSS(ConfigBus(True), sleep=lambda _:None).configure(defaults(legacy_gnss=True)[5])
        with self.assertRaises(ValueError): driver.configure(dict(defaults(legacy_gnss=True)[5], period_ns=2*S))

    def test_driver_captures_fragmented_packets_and_corruption(self):
        bus = ConfigBus(); now = [0]
        driver = TimedGNSS(bus, sleep=lambda _:None, clock_ns=lambda:now[0])
        driver.configure(defaults(legacy_gnss=True)[5]); driver.read()
        packet = ubx_packet(0x0d, 1, tp(BASE))
        now[0] = 100; bus.data = packet[:9]
        self.assertFalse(driver.read().events)
        now[0] = 200; bus.data = packet[9:]
        event = driver.read().events[0]
        self.assertEqual((event['read_start_ns'], event['read_end_ns']), (100,200))
        self.assertEqual(event['payload_hex'], tp(BASE).hex())
        bus.data = packet[:-1] + bytes([packet[-1] ^ 1])
        with self.assertRaises(OSError): driver.read()

    def test_runtime_records_real_timing_driver_events_and_nav(self):
        bus, clock = ConfigBus(), [0]
        driver = TimedGNSS(bus, sleep=lambda _:None, clock_ns=lambda:clock[0])
        driver.buffered, driver.ready = True, lambda:False
        stream = io.BytesIO()
        app = Acquisition(Writer(stream, {'format':'senseshake-acquisition-v1'}), Sessions(),
                          [Channel('pi',1,defaults(legacy_gnss=True)[5],driver)])
        app.start(0); clock[0] = S
        payload = bytearray(92); payload[:4] = (1000).to_bytes(4,'little')
        bus.data = ubx_packet(1,7,payload) + ubx_packet(0x0d,1,tp(BASE)) + ubx_packet(1,0x21,nav(BASE-1))
        app.tick(lambda:clock[0]); app.finish(S+1)
        stream.seek(0); records = list(Reader(stream))
        self.assertEqual([x['code'] for _,x in records if isinstance(x,dict)],
                         ['gnss_timing_config','gnss_tim_tp','gnss_timeutc','acquisition_summary'])
        self.assertEqual(sum(m.WhichOneof('body')=='batch' for _,m in records if not isinstance(m,dict)),1)

    def test_consecutive_pulses_and_missing_startup_evidence(self):
        spans, _ = intervals(fixture(), policy())
        self.assertEqual(len(spans),4)
        self.assertEqual(spans[0]['raw_start_ns'],3*S)
        self.assertEqual(spans[0]['utc_start_ns'],(BASE+2)*S)
        with self.assertRaises(ValueError): intervals(fixture()[1:],policy())

    def test_duplicate_or_backward_pps_rejected(self):
        events = fixture(); events.insert(2,events[1])
        with self.assertRaises(ValueError): intervals(events,policy())

    def test_duplicate_message_not_silently_deduplicated(self):
        events=fixture(); row=next(x for x in events if x[1]['code']=='gnss_tim_tp' and 3*S<x[0]<4*S)
        events.insert(events.index(row),deepcopy(row))
        spans, counts=intervals(events,policy())
        self.assertFalse(any(x['raw_start_ns']<=4*S<=x['raw_end_ns'] for x in spans))
        self.assertGreater(counts['ambiguous_or_missing_pair'],0)

    def test_late_transport_and_edge_crossing_are_not_next_second(self):
        for mode in ('near_previous','crossing','near_next'):
            events=fixture()
            for position, (_,event) in enumerate(events):
                if event['code']=='gnss_tim_tp' and 3*S<event['read_end_ns']<4*S:
                    if mode=='near_previous': event.update(read_start_ns=3*S+1,read_end_ns=3*S+50_000_000)
                    elif mode=='crossing': event['read_start_ns']=3*S-1
                    else:
                        event.update(read_start_ns=4*S-1100,read_end_ns=4*S-1)
                        events[position]=(4*S,event)
            spans, counts=intervals(events,policy())
            self.assertGreater(counts.get('ambiguous_transport',0),0)
            self.assertFalse(any(x['raw_start_ns']<=4*S<=x['raw_end_ns'] for x in spans))

    def test_missing_pulse_and_loss_of_lock_leave_gap(self):
        for fault in ('missing','unlocked','reset','stale'):
            events=fixture()
            if fault=='missing': events=[x for x in events if not (x[1]['code']=='pps_edge' and x[1]['estimated_raw_ns']==4*S)]
            elif fault=='reset': events.append((4*S,dict(code='timing_fault')))
            else:
                for _, event in events:
                    if fault=='unlocked' and event['code']=='gnss_tim_tp' and 3*S<event['read_end_ns']<4*S:
                        event['payload_hex']=tp(BASE+3,0x23).hex()
                    if fault=='stale' and event['code']=='pps_edge' and event['estimated_raw_ns']==4*S:
                        event['mapping_monotonic_ns']+=S
            spans,_=intervals(events,policy())
            self.assertFalse(any(x['raw_start_ns']<4*S<x['raw_end_ns'] or x['raw_start_ns']==4*S for x in spans))

    def test_midnight_and_leap_second_are_explicitly_unlabelled(self):
        midnight=int(datetime(2027,1,1,tzinfo=timezone.utc).timestamp())
        events=fixture()
        for _,event in events:
            if event['code']=='gnss_tim_tp': event['payload_hex']=tp(midnight).hex()
            elif event['code']=='gnss_timeutc': event['payload_hex']=nav(midnight-1).hex()
        self.assertEqual(intervals(events,policy())[0],[])
        payload=bytearray(nav(midnight-1));payload[18]=60
        with self.assertRaisesRegex(ValueError,'leap second'):timeutc(bytes(payload))

    def test_week_rollover_and_day_guard_reacquisition(self):
        sunday=int(datetime(2026,9,27,tzinfo=timezone.utc).timestamp())
        self.assertEqual(tim_tp(tp(sunday))[0]-tim_tp(tp(sunday-1))[0],S)
        self.assertEqual(tim_tp(tp(sunday+10))[0],(sunday+10)*S)
        events=fixture()
        for _,event in events:
            if event['code'] in ('gnss_tim_tp','gnss_timeutc'):
                n=event['read_end_ns']//S
                event['payload_hex']=(tp(sunday+10+n) if event['code']=='gnss_tim_tp' else nav(sunday+9+n)).hex()
        self.assertEqual(len(intervals(events,policy())[0]),4)

    def test_policy_wrong_recording_scope_and_missing_bounds(self):
        for key,value in [('recording_sha256','b'*64),('edge_error_ns',0),('sample_error_ns',{}),('scope','bench')]:
            bad=policy();bad[key]=value
            with self.assertRaises(ValueError):policy_check(bad,'a'*64,'modeled-timing')

    def test_clock_drift_outside_declared_envelope_rejected(self):
        events=[]
        for arrival,event in fixture():
            event=deepcopy(event)
            for key in ('monotonic_ns','estimated_raw_ns','mapping_monotonic_ns','read_start_ns','read_end_ns'):
                if key in event:event[key]=event[key]*1001//1000
            events.append((arrival*1001//1000,event))
        spans,counts=intervals(events,policy())
        self.assertEqual(spans,[])
        self.assertGreater(counts.get('pulse_or_utc_discontinuity',0),0)

    def test_correlated_copy_preserves_raw_and_replays_with_unknown_edges(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source.ssrec';output=root/'utc.ssrec'
            with source.open('wb') as stream:
                writer=Writer(stream,dict(format='senseshake-acquisition-v1',source='modeled-timing',utc_capture='m10-tim-tp-v1'))
                writer.message(messages.identity('pi',1,1,[1]),0)
                writer.message(messages.configuration('pi',1,defaults()[:1]),0)
                raw=dict(acceleration=(1,2,3),angular_rate=(4,5,6))
                data=[(a,e) for a,e in fixture()]
                for sequence,at in enumerate((S//2,3*S+S//2,7*S+S//2)):
                    data.append((at,messages.batch('pi',1,1,sequence,at,raw)))
                for at,item in sorted(data,key=lambda x:x[0]):
                    if isinstance(item,dict):writer.record(2,json.dumps(item).encode(),at)
                    else:writer.message(item,at)
                writer.event('acquisition_summary','complete',8*S)
            digest=hashlib.sha256(source.read_bytes()).hexdigest()
            report=correlate(source,output,policy(digest))
            self.assertEqual(report['samples_correlated'],1)
            self.assertEqual(report['samples_unlabelled'],2)
            self.assertTrue(replay(output)['completed'])
            with output.open('rb') as stream:
                batches=[m for _,m in Reader(stream) if not isinstance(m,dict) and m.WhichOneof('body')=='batch']
            stamp=batches[1].batch.samples[0].time
            self.assertEqual(stamp.acquisition_ns,3*S+S//2)
            self.assertEqual(stamp.utc_unix_ns,(BASE+2)*S+S//2)
            self.assertGreater(stamp.utc_uncertainty_ns,25000)
            self.assertEqual(batches[1].batch.samples[0].imu.acceleration.z,3)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),digest)
            with self.assertRaises(FileExistsError):correlate(source,output,policy(digest))
            policy_file=root/'policy.json';policy_file.write_text(json.dumps(policy(digest)))
            entry=Path(__file__).resolve().parents[1]/'tools/correlate_utc.py'
            completed=subprocess.run([sys.executable,str(entry),str(source),'--policy',str(policy_file),
                                      '--output',str(root/'cli.ssrec'),'--report',str(root/'cli.json')],capture_output=True,text=True)
            self.assertEqual(completed.returncode,0,completed.stderr)
            self.assertEqual(json.loads((root/'cli.json').read_text())['samples_correlated'],1)
            self.assertEqual((root/'cli.ssrec').read_bytes(),output.read_bytes())


if __name__=='__main__':unittest.main()
