"""Immutable, explicit affine SI calibration in package axes; raw is retained."""
import hashlib
import json
import math
from groundlark_contract.validation import require, validate

VECTORS = {"acceleration_m_s2": "acceleration", "angular_rate_rad_s": "angular_rate",
           "angle_rad": "angle", "magnetic_t": "counts"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def configuration_hash(configuration):
    return hashlib.sha256(configuration.SerializeToString(deterministic=True)).hexdigest()


class Calibrations:
    def __init__(self, records=()):
        self.records = {}
        for record in records:
            self.add(record)

    def add(self, record):
        require(len(self.records) < 16, "calibration capacity exhausted")
        data = canonical(record)
        require(len(data) <= 2048, "calibration too large")
        require(set(record) == {"sensor_id", "configuration_sha256", "provenance", "fields"}, "calibration keys")
        require(1 <= record["sensor_id"] <= 8 and record["sensor_id"] != 6, "calibration sensor")
        require(isinstance(record["provenance"], str) and 0 < len(record["provenance"]) <= 256, "calibration provenance")
        require(len(record["configuration_sha256"]) == 64 and all(c in "0123456789abcdef" for c in record["configuration_sha256"]), "configuration digest")
        require(1 <= len(record["fields"]) <= 3, "calibration fields")
        for name, coefficients in record["fields"].items():
            require(name in VECTORS or name in ("temperature_k", "pressure_pa"), "unknown calibration field")
            require(set(coefficients) == {"scale", "offset"}, "calibration coefficient keys")
            count = 3 if name in VECTORS else 1
            for key in ("scale", "offset"):
                values = coefficients[key]
                require(isinstance(values, list) and len(values) == count and all(type(v) in (int, float) and math.isfinite(v) for v in values), "calibration coefficient shape")
        ident = "cal-" + hashlib.sha256(data).hexdigest()[:28]
        self.records[ident] = json.loads(data)
        return ident

    def verify(self, ident, sensor, cfg):
        r = self.records.get(ident)
        require(r is not None and r["sensor_id"] == sensor and r["configuration_sha256"] == configuration_hash(cfg), "calibration/configuration mismatch")
        return r

    def apply(self, message, ident, cfg):
        record = self.verify(ident, message.batch.sensor_id, cfg)
        copy = type(message)()
        copy.CopyFrom(message)
        for sample in copy.batch.samples:
            if sample.quality not in (1, 3): continue
            raw = getattr(sample, sample.WhichOneof("raw"))
            for name, c in record["fields"].items():
                if name in VECTORS:
                    source = VECTORS[name]
                    require(source in raw.DESCRIPTOR.fields_by_name and raw.HasField(source), "raw calibration input missing")
                    for i, axis in enumerate(("x", "y", "z")):
                        setattr(getattr(sample.calibrated, name), axis, getattr(getattr(raw, source), axis) * c["scale"][i] + c["offset"][i])
                else:
                    if name == "pressure_pa":
                        require(sample.WhichOneof("raw") == "pressure", "pressure input missing")
                        value = int.from_bytes(raw.response[:2], "big") & 0x3fff
                    else:
                        require("temperature" in raw.DESCRIPTOR.fields_by_name and raw.HasField("temperature"), "temperature input missing")
                        value = raw.temperature
                    setattr(sample.calibrated, name, value * c["scale"][0] + c["offset"][0])
            copy.batch.calibration_id = ident
        return validate(copy)
