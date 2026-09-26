import io
import struct
import unittest
from collections import deque
from groundlark.fifo import Slots, LSM6DSOFIFO, FifoFault, Drain
from groundlark.sensors import Reading
from groundlark.simulation import defaults
from groundlark.runtime import Acquisition, Channel
from groundlark.recording import Writer, Reader
from groundlark.session import Sessions


def word(kind, counter, payload):
    tag = (kind << 3) | (counter << 1)
    return bytes([tag | (tag.bit_count() % 2)]) + payload


def slot(counter, timestamp, sample=1):
    return [word(4, counter, struct.pack('<IBB', timestamp, 0, 0x22)),
            word(1, counter, struct.pack('<3h', sample, -2, 3)),
            word(2, counter, struct.pack('<3h', 4, 5, 16384))]


class Bus:
    def __init__(self):
        self.regs = {15: 0x6c}
        self.words, self.tick, self.overrun = deque(), 4000, 0
    def transfer(self, data, **kwargs):
        address = data[0] & 127
        if data[0] & 128:
            if address == 0x78: result = self.words.popleft()
            elif address == 0x3a: result = bytes([len(self.words) & 255, self.overrun | len(self.words) >> 8])
            elif address == 0x3b: result = bytes([self.overrun])
            elif address == 0x40: result = self.tick.to_bytes(4, 'little')
            else: result = bytes([self.regs.get(address, 0)])
            return b'\0' + result
        self.regs[address] = 0 if address == 0x12 and data[1] == 1 else data[1]
        if address == 0xa and data[1] == 0: self.words.clear(); self.overrun = 0
        return bytes(len(data))
    def close(self): pass


class FifoTests(unittest.TestCase):
    def driver(self):
        bus = Bus()
        driver = LSM6DSOFIFO(bus, sleep=lambda _: None, clock_ns=lambda: 1_000_000_000)
        cfg = driver.configure(defaults()[0])
        self.assertEqual(dict(zip(cfg['register_config'][::2], cfg['register_config'][1::2]))[0xa], 0x46)
        return bus, driver

    def test_independent_tag_vectors_signed_axes_and_chunk_boundary(self):
        parser = Slots(2)
        # Timestamp tag 0x21, gyro 0x09, accel 0x11: even tag parity, slot zero.
        self.assertIsNone(parser.feed(bytes.fromhex('21 10000000 00 22')))
        self.assertIsNone(parser.feed(bytes.fromhex('09 0080 ffff ff7f')))
        tick, raw = parser.feed(bytes.fromhex('11 0100 0200 0300'))
        self.assertEqual(tick, 16)
        self.assertEqual(raw['angular_rate'], (-32768, -1, 32767))
        self.assertEqual(raw['acceleration'], (1, 2, 3))

    def test_counter_wrap_and_arbitrary_tag_order(self):
        parser = Slots(2)
        for i in range(12):
            words = slot(i % 4, 100 + i * 1538)
            for record in (words[2], words[0], words[1]): result = parser.feed(record)
            self.assertEqual(result[0], 100 + i * 1538)

    def test_parity_unknown_tags_duplicates_missing_and_changed_bdr(self):
        bad_cases = [bytes.fromhex('20 10000000 00 22'), word(5, 0, bytes(6)),
                     word(4, 0, struct.pack('<IBB', 1, 0, 0x33))]
        for value in bad_cases:
            with self.assertRaises(FifoFault): Slots(2).feed(value)
        for mode in ('duplicate', 'incomplete', 'gap'):
            parser = Slots(2)
            for value in slot(0, 10)[:1 if mode != 'gap' else 3]: parser.feed(value)
            with self.assertRaises(FifoFault): parser.feed(slot(2 if mode == 'gap' else 1 if mode == 'incomplete' else 0, 20)[0])

    def test_driver_preserves_all_backlog_and_hardware_time_intervals(self):
        bus, driver = self.driver()
        bus.words.extend(slot(0, 1000) + slot(1, 2538))
        result = driver.read().readings
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1].acquisition_ns - result[0].acquisition_ns, 38_450_000)
        self.assertEqual(result[0].acquisition_ns, 925_000_000)
        self.assertNotIn('temperature', result[0].raw)  # Never invent same-slot temperature.
        self.assertEqual(driver.read(), Drain([]))

    def test_timestamp_wrap_stale_reset_and_overrun(self):
        bus, driver = self.driver()
        bus.tick = 10
        bus.words.extend(slot(0, 0xfffffff0))
        self.assertEqual(driver.read().readings[0].acquisition_ns, 999_350_000)
        for mode in ('future', 'overrun', 'backlog', 'parity'):
            bus, driver = self.driver()
            bus.words.extend(slot(0, 5000 if mode == 'future' else 1000))
            if mode == 'overrun': bus.overrun = 0x08
            if mode == 'backlog': bus.words.extend(slot(0, 1000) * 33)
            if mode == 'parity': bus.words[0] = bytes([bus.words[0][0] ^ 1]) + bus.words[0][1:]
            with self.assertRaises(FifoFault): driver.read()
            self.assertFalse(bus.words)

    def test_four_missing_slots_cannot_hide_behind_counter_wrap(self):
        bus, driver = self.driver()
        bus.tick = 12_000
        bus.words.extend(slot(0, 1000) + slot(1, 8690))
        with self.assertRaisesRegex(FifoFault, 'cadence/gap'): driver.read()
        # After an explicitly reported flush, a later valid slot can recover.
        bus.words.extend(slot(2, 10_228))
        self.assertEqual(len(driver.read().readings), 1)

    def test_driver_runtime_recording_with_delayed_service(self):
        bus = Bus()
        driver = LSM6DSOFIFO(bus, sleep=lambda _: None, clock_ns=lambda: 1_000_000_000)
        driver.buffered = True
        driver.ready = lambda: False
        stream = io.BytesIO()
        app = Acquisition(Writer(stream, {'format':'groundlark-acquisition-v1'}), Sessions(),
                          [Channel('pi', 1, defaults()[0], driver)])
        app.start(0)
        bus.words.extend(slot(0, 1000) + slot(1, 2538))
        app.tick(lambda: 1_000_000_000)
        app.finish(1_000_000_001)
        stream.seek(0)
        samples = [s for _, m in Reader(stream) if not isinstance(m, dict)
                   and m.WhichOneof('body') == 'batch' for s in m.batch.samples]
        self.assertEqual([s.sequence for s in samples], [0, 1])
        self.assertEqual([s.time.acquisition_ns for s in samples], [925_000_000, 963_450_000])
        self.assertEqual(samples[1].imu.acceleration.z, 16384)

    def test_runtime_backlog_not_lost_to_scheduler_slots_and_overrun_marked(self):
        class Adapter:
            buffered = True
            def configure(self, cfg): return cfg
            def ready(self): return False
            def read(self):
                if self.failed: raise FifoFault('overrun')
                return Drain([Reading(dict(acceleration=(0, 0, 1), angular_rate=(0, 0, 0)), 1, t)
                              for t in (100, 200, 300)])
            failed = False
        stream, adapter = io.BytesIO(), Adapter()
        channel = Channel('pi', 1, defaults()[0], adapter)
        app = Acquisition(Writer(stream, {'format':'groundlark-acquisition-v1'}), Sessions(), [channel])
        app.start(0)
        app.tick(lambda: 1000)
        adapter.failed = True
        app.tick(lambda: 30_000_000)
        app.finish(30_000_001)
        stream.seek(0)
        items = [x for _, x in Reader(stream) if not isinstance(x, dict)]
        samples = [s for m in items if m.WhichOneof('body') == 'batch' for s in m.batch.samples]
        self.assertEqual([s.sequence for s in samples], [0, 1, 2, 3])
        self.assertEqual([s.time.acquisition_ns for s in samples[:3]], [100, 200, 300])
        self.assertEqual(samples[-1].quality, 2)
        self.assertTrue(any(m.WhichOneof('body') == 'status' and m.status.code == 4 for m in items))
        self.assertTrue(all(not m.batch.HasField('dropped_before') for m in items if m.WhichOneof('body') == 'batch'))


if __name__ == '__main__': unittest.main()
