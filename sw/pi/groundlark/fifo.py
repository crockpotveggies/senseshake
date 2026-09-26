"""LSM6DSO uncompressed FIFO with per-slot hardware timestamps (AN5192 §9).

SPI failures, parity errors, slot gaps and overrun discard the affected drain.
The host-clock mapping is an estimate; sensor/filter latency is not qualified.
"""
from dataclasses import dataclass
import struct
import time
from .sensors import LSM6DSO, Reading


class FifoFault(OSError):
    pass


@dataclass
class Drain:
    readings: list


class Slots:
    """At most one incomplete slot; tags are paired by counter, never position."""
    def __init__(self, bdr):
        self.bdr, self.counter, self.fields = bdr, None, {}
        self.emitted = False

    def feed(self, word):
        if len(word) != 7 or word[0].bit_count() % 2: raise FifoFault("FIFO tag parity/length")
        kind, counter = word[0] >> 3, (word[0] >> 1) & 3
        if kind not in (1, 2, 4): raise FifoFault("unexpected FIFO tag/configuration")
        if self.counter is not None and counter != self.counter:
            if not self.emitted or counter != (self.counter + 1) % 4:
                raise FifoFault("FIFO incomplete/missing time slot")
            self.fields, self.emitted = {}, False
        self.counter = counter
        if self.emitted or kind in self.fields: raise FifoFault("FIFO duplicate sensor tag")
        if kind == 4:
            if word[5:] != bytes([0, self.bdr * 17]): raise FifoFault("FIFO batch-rate changed")
            value = int.from_bytes(word[1:5], "little")
        else: value = struct.unpack("<3h", word[1:])
        self.fields[kind] = value
        if set(self.fields) != {1, 2, 4}: return None
        self.emitted = True
        return self.fields[4], dict(angular_rate=self.fields[1], acceleration=self.fields[2])


class LSM6DSOFIFO(LSM6DSO):
    def __init__(self, bus, sleep=time.sleep, clock_ns=None):
        super().__init__(bus, sleep)
        self.clock_ns = clock_ns or (lambda: time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW))
        self.last = -1

    def configure(self, cfg):
        effective = super().configure(cfg)
        bdr = self.PERIODS[cfg['period_ns']]
        # Watermark one full slot; timestamp every slot; no compression/temp.
        settings = {7: 3, 8: 0, 9: bdr * 17, 0x19: 0x20, 0x0d: 0x18, 0x0a: 0x46}
        self.write(0x0a, 0)
        for reg, value in settings.items(): self.write(reg, value)
        for reg, value in settings.items():
            if self.reg(reg)[0] != value: raise OSError('FIFO configuration readback mismatch')
        combined = dict(zip(effective['register_config'][::2], effective['register_config'][1::2]))
        combined.update(settings)
        self.bdr, self.slots = bdr, Slots(bdr)
        self.period_ticks = cfg['period_ns'] / 25_000
        self.last, self.last_tick = -1, None
        effective['register_config'] = b''.join(bytes([r, v]) for r, v in sorted(combined.items()))
        return effective

    def reset_fifo(self):
        self.write(0x0a, 0)
        self.slots = Slots(self.bdr)
        self.last_tick = None  # A flushed interval is already reported as unknown loss.
        self.write(0x0a, 0x46)

    def read(self):
        try:
            status = self.reg(0x3a, 2)
            if status[1] & 0x48: raise FifoFault('FIFO overrun; physical loss unknown')
            count = status[0] | ((status[1] & 3) << 8)
            # Bound work and IPC. Reject backlog rather than return silently stale data.
            if count > 96: raise FifoFault('FIFO backlog exceeds 32-slot service bound')
            complete = []
            for _ in range(count):
                sample = self.slots.feed(self.reg(0x78, 7))
                if sample is not None: complete.append(sample)
            if self.reg(0x3b)[0] & 0x48: raise FifoFault('FIFO overrun during drain')
            if not complete: return Drain([])
            # Map FIFO device time to RAW using a bracketed live timestamp read.
            before = self.clock_ns()
            tick = int.from_bytes(self.reg(0x40, 4), 'little')
            after = self.clock_ns()
            host = (before + after) // 2
            readings = []
            last, last_tick = self.last, self.last_tick
            for sample_tick, raw in complete:
                age = (tick - sample_tick) & 0xffffffff
                if age > 80_000: raise FifoFault('FIFO timestamp reset/future/stale')
                if last_tick is not None:
                    interval = (sample_tick - last_tick) & 0xffffffff
                    # A two-bit tag counter alone cannot detect four missing slots.
                    # Broad tolerance covers nominal oscillator error, not loss.
                    if not .5 * self.period_ticks <= interval <= 1.5 * self.period_ticks:
                        raise FifoFault('FIFO timestamp cadence/gap')
                acquired = host - age * 25_000
                if acquired <= last: raise FifoFault('FIFO host clock mapping moved backwards')
                quality = 3 if any(v in (-32768, 32767) for vector in raw.values() for v in vector) else 1
                readings.append(Reading(raw, quality, acquired))
                last, last_tick = acquired, sample_tick
            self.last, self.last_tick = last, last_tick
            return Drain(readings)
        except (OSError, ValueError) as error:
            self.reset_fifo()
            raise FifoFault(str(error)) from error

    def close(self):
        try: self.write(0x0d, 0); self.write(0x0a, 0)
        finally: self.bus.close()
