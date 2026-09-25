"""ADS122C04 polling driver for the T1 Racotech input.

TI SBAS751B: AIN0-AIN1, internal reference, normal 330 SPS, PGA64.
Counter plus inverted data detect repeat, skipped and corrupt conversions.
No FIFO or sample clock timestamp is fabricated; loss and latency stay unknown.
"""
import time
from .sensors import Reading, NotReady

SETTINGS = dict(sensor_id=9, enabled=True, period_ns=3_030_303,
                geophone_gain=64, geophone_reference_v=2.048)


class ADS122C04:
    loss_unknown = True
    REGISTERS = (0x0c, 0x88, 0x50, 0x00)

    def __init__(self, bus, sleep=time.sleep, clock=time.monotonic):
        self.bus, self.sleep, self.clock = bus, sleep, clock
        self.counter = self.last_read = None
        self.integrity = False

    def exchange(self, command, count=0):
        data = self.bus.exchange(0x40, command, count)
        if len(data) != count: raise OSError('short geophone ADC response')
        return data

    def register(self, index):
        data = self.exchange(bytes([0x20 | index << 2]), 2 if self.integrity else 1)
        if self.integrity and data[0] ^ data[1] != 255:
            raise OSError('geophone register integrity')
        return data[0]

    def configure(self, cfg):
        if any(cfg.get(k) != v for k, v in SETTINGS.items()):
            raise ValueError('geophone requires 330 SPS / PGA64 / internal reference profile')
        self.exchange(b'\x06')
        self.integrity = False
        self.sleep(.001)
        if any(self.register(i) != 0 for i in range(4)):
            raise OSError('geophone reset register mismatch')
        for i in (0, 1, 3, 2):
            self.exchange(bytes([0x40 | i << 2, self.REGISTERS[i]]))
        self.integrity = True
        if tuple(self.register(i) & (0x7f if i == 2 else 0xff) for i in range(4)) != self.REGISTERS:
            raise OSError('geophone configuration readback mismatch')
        self.counter = self.last_read = None
        self.sleep(.3)  # Mid-supply RC settling; not a sensor mechanical settling claim.
        self.exchange(b'\x08')
        self.sleep(.004)
        return dict(cfg)

    def read(self):
        if not self.register(2) & 0x80: raise NotReady('geophone conversion not ready')
        data = self.exchange(b'\x10', 8)
        if any(a ^ b != 255 for a, b in zip(data[:4], data[4:])):
            raise OSError('geophone conversion integrity')
        counter = data[0]
        now = self.clock()
        old, elapsed = self.counter, None if self.last_read is None else now - self.last_read
        self.counter, self.last_read = counter, now
        if elapsed is not None and (elapsed < 0 or elapsed >= .7):
            raise OSError('geophone counter interval ambiguous')
        if old is not None:
            delta = (counter - old) & 255
            if delta == 0: raise NotReady('duplicate geophone conversion')
            if delta != 1: raise OSError('geophone conversion gap; loss unknown')
        count = int.from_bytes(data[1:4], 'big', signed=True)
        return Reading(dict(counts=count, conversion_counter=counter),
                       3 if count in (-8388608, 8388607) else 1)

    def close(self): self.bus.close()
