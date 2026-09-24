"""Deterministic device models, not electrical or instruction-set emulation."""
import struct
from .sensors import Reading, NotReady


class Simulated:
    def __init__(self, sensor, seed=1, faults=()):
        self.sensor, self.seed, self.index = sensor, seed, 0
        if len(faults) > 256: raise ValueError("fault fixture bound")
        self.faults = {}
        for f in faults:
            if set(f) != {"sensor", "sample", "action"} or f["sensor"] not in range(1, 9) or type(f["sample"]) is not int or not 0 <= f["sample"] <= 1_000_000:
                raise ValueError("fault fixture fields")
            if f["action"] not in ("timeout", "nack", "disconnect", "not_ready", "saturation", "short_read"):
                raise ValueError("unknown fault action")
            if f["sensor"] == sensor:
                if f["sample"] in self.faults: raise ValueError("duplicate fault")
                self.faults[f["sample"]] = f["action"]

    def configure(self, settings): return dict(settings)

    def read(self):
        i = self.index
        self.index += 1
        fault = self.faults.get(i)
        if fault == "not_ready": raise NotReady("simulated data not ready")
        if fault == "timeout": raise TimeoutError("simulated timeout")
        if fault in ("nack", "disconnect", "short_read"): raise OSError("simulated " + fault)
        n = (i * 17 + self.sensor * 101 + self.seed * 13) % 2001 - 1000
        quality = 3 if fault == "saturation" and self.sensor != 6 else 1
        if self.sensor <= 4:
            raw = dict(acceleration=(32767 if quality == 3 else n, -n, 16384), angular_rate=(n // 3, 0, -n // 3), temperature=0)
        elif self.sensor == 5:
            raw = dict(acceleration=(n, -n, 6000), angle=(n, -n, 0), temperature=-100, device_status=64 if quality == 3 else 0)
        elif self.sensor == 6:
            payload = bytearray(92)
            struct.pack_into("<I", payload, 0, (i * 1000) % 604800000)
            raw = dict(nav_pvt=bytes(payload))
        elif self.sensor == 7: raw = dict(counts=(8388607 if quality == 3 else n * 10, -n * 10, 50000))
        else: raw = dict(response=struct.pack(">HH", 16383 if quality == 3 else 8192 + n, 1024 << 5))
        return Reading(raw, quality)

    def close(self): pass


def defaults(remote=False):
    entries = [dict(sensor_id=i, enabled=True, period_ns=38_461_538, acceleration_range_g=2, angular_rate_range_dps=250) for i in range(1, 5)]
    entries += [dict(sensor_id=5, enabled=True, period_ns=40_000_000, tilt_mode=1),
                dict(sensor_id=6, enabled=True, period_ns=1_000_000_000)]
    if remote:
        return [dict(sensor_id=7, enabled=True, period_ns=100_000_000, cycle_count_x=200,
                     cycle_count_y=200, cycle_count_z=200),
                dict(sensor_id=8, enabled=True, period_ns=10_000_000, pressure_min_pa=-250,
                     pressure_max_pa=250, pressure_part_number="SIMULATED-DLVR")]
    return entries
