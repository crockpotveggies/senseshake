"""Capture M10 timing evidence; UBX-21035062 R03, sections 3.18.2/4.9.25.

No UTC is inferred from message arrival. Offline correlation uses measured bounds.
"""
from dataclasses import dataclass, field
import time
from .sensors import MAXM10S, UBXParser, Reading
from .fifo import Drain

# key, encoded width, required RAM value. No receiver flash writes.
TIMING_KEYS = (
    (0x10720001, 1, 1), (0x10720002, 1, 0),  # I2C UBX on, NMEA off
    (0x2091017d, 1, 1), (0x2091005b, 1, 1),  # TIM-TP, NAV-TIMEUTC
    (0x20050023, 1, 0), (0x20050030, 1, 1),  # period/us length
    (0x40050002, 4, 1_000_000), (0x40050003, 4, 1_000_000),
    (0x40050004, 4, 100_000), (0x40050005, 4, 100_000),
    (0x10050007, 1, 1), (0x10050008, 1, 1), (0x10050009, 1, 1),
    (0x1005000a, 1, 1), (0x1005000b, 1, 1), (0x2005000c, 1, 0),
    (0x30050001, 2, 0), (0x40050006, 4, 0),  # delays bounded in bench policy
)


def configuration_evidence():
    entries = [(0x30210001, 2, 1000), (0x30210002, 2, 1), (0x20910006, 1, 1), *TIMING_KEYS]
    return {f'{key:08x}': value for key, _, value in entries}


@dataclass
class TimingDrain(Drain):
    events: list = field(default_factory=list)


class TimedGNSS(MAXM10S):
    KEYS = MAXM10S.KEYS + tuple((key, width) for key, width, _ in TIMING_KEYS)

    def __init__(self, bus, sleep=time.sleep, clock_ns=None):
        super().__init__(bus, sleep)
        self.clock_ns = clock_ns or (lambda: time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW))
        self.partial_since = None
        self.announce = False

    def configuration_values(self, cfg):
        if cfg['period_ns'] != 1_000_000_000: raise ValueError('UTC capture requires 1 Hz GNSS')
        return super().configuration_values(cfg) + tuple(value for _, _, value in TIMING_KEYS)

    def configure(self, cfg):
        result = super().configure(cfg)
        # Discard configuration-era queued data. A persistent stream is bounded.
        for _ in range(16):
            self.poll()
            count = self.bus.exchange(0x42, b'\xfd', 2)
            if count == b'\0\0': break
        else: raise OSError('GNSS startup backlog did not drain')
        self.parser, self.partial_since, self.last_tow = UBXParser(), None, None
        self.announce = True
        return result

    def read(self):
        readings, events = [], []
        if self.announce:
            events.append(dict(code='gnss_timing_config', effective=configuration_evidence(),
                               read_start_ns=self.clock_ns(), read_end_ns=self.clock_ns()))
            self.announce = False
        # Up to 2048 bytes and 32 packets per service; IPC remains bounded.
        for _ in range(8):
            before = self.clock_ns()
            start = before if self.partial_since is None else self.partial_since
            packets = self.poll()
            after = self.clock_ns()
            self.partial_since = start if self.parser.buffer else None
            for cls, ident, payload in packets:
                if len(events) >= 32: raise OSError('GNSS timing packet bound')
                if (cls, ident) in ((0x0d, 1), (1, 0x21)):
                    if len(payload) != (16 if cls == 0x0d else 20): raise OSError('GNSS timing length')
                    events.append(dict(code='gnss_tim_tp' if cls == 0x0d else 'gnss_timeutc',
                                       payload_hex=payload.hex(), read_start_ns=start, read_end_ns=after))
                elif (cls, ident) == (1, 7):
                    if len(payload) != 92: raise OSError('GNSS NAV-PVT length')
                    tow = int.from_bytes(payload[:4], 'little')
                    if tow != self.last_tow:
                        if len(readings) >= 8: raise OSError('GNSS navigation backlog')
                        readings.append(Reading(dict(nav_pvt=payload), acquisition_ns=after))
                        self.last_tow = tow
            if not packets: break
        return TimingDrain(readings, events)

    def close(self): self.bus.close()
