"""Independent wire vectors and invalid semantic examples for sensor v1."""
import json
from pathlib import Path
import unittest
import zlib

from google.protobuf.message import DecodeError
from senseshake_contract import framing as f
from senseshake_contract.schema import envelope_type
from senseshake_contract.validation import validate

Envelope = envelope_type()
FIXTURE = json.loads((Path(__file__).parent / "fixtures/magnetic_boundary.json").read_text())


def magnetic():
    return Envelope.FromString(bytes.fromhex(FIXTURE["wire_hex"]))


class ContractTests(unittest.TestCase):
    def test_independent_producer_vector(self):
        message = validate(magnetic())
        self.assertEqual(message.device_id, FIXTURE["device_id"])
        self.assertEqual(message.boot_id, int(FIXTURE["boot_id"]))
        sample = message.batch.samples[0]
        self.assertEqual(sample.sequence, FIXTURE["sequence"])
        self.assertEqual(sample.time.acquisition_ns, FIXTURE["acquisition_ns"])
        self.assertEqual([sample.magnetic.counts.x, sample.magnetic.counts.y, sample.magnetic.counts.z], FIXTURE["counts"])
        self.assertEqual(message.SerializeToString(deterministic=True).hex(), FIXTURE["wire_hex"])

    def test_zero_is_present_but_absence_is_invalid(self):
        for field in ("sequence", "time.acquisition_ns", "magnetic.counts.y"):
            message = magnetic()
            node = message.batch.samples[0]
            names = field.split(".")
            for name in names[:-1]: node = getattr(node, name)
            node.ClearField(names[-1])
            with self.subTest(field=field), self.assertRaises(ValueError): validate(message)

    def test_raw_precision_outside_24_bit(self):
        for value in (-8388609, 8388608):
            message = magnetic()
            message.batch.samples[0].magnetic.counts.x = value
            with self.subTest(value=value), self.assertRaises(ValueError): validate(message)

    def test_missing_has_no_fake_zero_measurement(self):
        message = magnetic()
        sample = message.batch.samples[0]
        sample.quality = 2
        with self.assertRaises(ValueError): validate(message)
        sample.ClearField("magnetic")
        validate(message)

    def test_clock_domain_and_utc_uncertainty(self):
        message = magnetic()
        sample = message.batch.samples[0]
        sample.time.domain = 1
        with self.assertRaises(ValueError): validate(message)
        sample.time.domain = 2
        sample.time.utc_unix_ns = 0
        with self.assertRaises(ValueError): validate(message)
        sample.time.utc_uncertainty_ns = 1000000
        validate(message)

    def test_batch_order_and_bound(self):
        message = magnetic()
        sample = message.batch.samples.add()
        sample.CopyFrom(message.batch.samples[0])
        with self.assertRaises(ValueError): validate(message)
        sample.sequence = 1
        with self.assertRaises(ValueError): validate(message)
        sample.time.acquisition_ns = 100
        validate(message)
        for i in range(2, 5):
            next_sample = message.batch.samples.add()
            next_sample.CopyFrom(sample)
            next_sample.sequence = i
            next_sample.time.acquisition_ns = i * 100
        with self.assertRaises(ValueError): validate(message)

    def test_drop_count_cannot_exceed_first_sequence(self):
        message = magnetic()
        message.batch.dropped_before = 1
        with self.assertRaises(ValueError): validate(message)
        message.batch.samples[0].sequence = 4
        message.batch.dropped_before = 4
        validate(message)

    def test_unknown_loss_is_distinct_from_no_loss(self):
        message = validate(magnetic())
        self.assertFalse(message.batch.HasField("dropped_before"))
        message.batch.dropped_before = 0
        decoded = validate(Envelope.FromString(message.SerializeToString()))
        self.assertTrue(decoded.batch.HasField("dropped_before"))
        self.assertEqual(decoded.batch.dropped_before, 0)

    def test_calibration_identity_and_nonfinite_values(self):
        message = magnetic()
        c = message.batch.samples[0].calibrated.magnetic_t
        c.x, c.y, c.z = 0, 1e-9, -1e-9
        with self.assertRaises(ValueError): validate(message)
        message.batch.calibration_id = "rm3100-installation-1"
        validate(message)
        for value in (float("nan"), float("inf"), -float("inf")):
            c.x = value
            with self.subTest(value=value), self.assertRaises(ValueError): validate(message)

    def test_wrong_raw_kind(self):
        message = magnetic()
        message.batch.sensor_id = 1
        message.batch.samples[0].time.domain = 1
        with self.assertRaises(ValueError): validate(message)

    def test_identity_and_configuration(self):
        message = Envelope(version=1, device_id="pi-1", boot_id=1)
        message.identity.board = 1
        message.identity.firmware_version = "0.1-dev"
        message.identity.sensors.extend([1, 2, 3, 4, 5, 6])
        validate(message)
        message.identity.sensors.append(7)
        with self.assertRaises(ValueError): validate(message)
        message.configuration.revision = 1
        sensor = message.configuration.sensors.add(sensor_id=7, enabled=True, period_ns=100000000)
        sensor.cycle_count_x = sensor.cycle_count_y = sensor.cycle_count_z = 200
        sensor.register_config = bytes.fromhex("04200820")
        validate(message)
        sensor.register_config = bytes.fromhex("08200420")
        with self.assertRaises(ValueError): validate(message)

    def test_configuration_requires_interpretation_settings(self):
        message = Envelope(version=1, device_id="pi-1", boot_id=1)
        message.configuration.revision = 1
        sensor = message.configuration.sensors.add(sensor_id=1, enabled=True, period_ns=10000000)
        with self.assertRaises(ValueError): validate(message)
        sensor.acceleration_range_g, sensor.angular_rate_range_dps = 4, 500
        validate(message)
        sensor.acceleration_range_g = 3
        with self.assertRaises(ValueError): validate(message)
        sensor.acceleration_range_g = 4
        sensor.tilt_mode = 1
        with self.assertRaises(ValueError): validate(message)

    def test_status_bounds_and_unknown_values(self):
        message = Envelope(version=1, device_id="head-1", boot_id=1)
        message.status.code = 3
        message.status.detail = "I2C timeout"
        validate(message)
        message.status.detail = "x" * 97
        with self.assertRaises(ValueError): validate(message)
        message.status.detail = ""
        message.status.code = 99
        with self.assertRaises(ValueError): validate(message)

    def test_all_sensor_payloads(self):
        for sensor_id in range(1, 9):
            message = Envelope(version=1, device_id="device-1", boot_id=1)
            message.batch.sensor_id = sensor_id
            message.batch.configuration_revision = 1
            s = message.batch.samples.add(sequence=0, quality=1)
            s.time.domain = 1 if sensor_id <= 6 else 2
            s.time.acquisition_ns = 0
            if sensor_id <= 4:
                for v in (s.imu.acceleration, s.imu.angular_rate): v.x, v.y, v.z = -32768, 0, 32767
            elif sensor_id == 5:
                s.tilt.angle.x, s.tilt.angle.y, s.tilt.angle.z = -32768, 0, 32767
                s.tilt.device_status = 0
            elif sensor_id == 6: s.gnss.nav_pvt = bytes(92)
            elif sensor_id == 7: s.magnetic.counts.x, s.magnetic.counts.y, s.magnetic.counts.z = -8388608, 0, 8388607
            else: s.pressure.response = bytes.fromhex("06668000")
            with self.subTest(sensor_id=sensor_id): validate(message)

    def test_pressure_status_preserved_but_not_silently_valid(self):
        message = magnetic()
        message.batch.sensor_id = 8
        sample = message.batch.samples[0]
        sample.pressure.response = bytes.fromhex("c6668000")
        with self.assertRaises(ValueError): validate(message)
        sample.quality = 4
        validate(message)

    def test_unknown_additive_field_survives(self):
        # Field 100, varint 1: old consumers retain additive fields.
        wire = bytes.fromhex(FIXTURE["wire_hex"]) + bytes.fromhex("a00601")
        message = validate(Envelope.FromString(wire))
        self.assertIn(bytes.fromhex("a00601"), message.SerializeToString())

    def test_unknown_body_and_truncated_protobuf(self):
        message = magnetic()
        message.ClearField("batch")
        with self.assertRaises(ValueError): validate(message)
        with self.assertRaises(DecodeError): Envelope.FromString(bytes.fromhex("620508"))


class FramingTests(unittest.TestCase):
    def test_crc_reference(self):
        self.assertEqual(zlib.crc32(b"123456789"), 0xcbf43926)
        self.assertEqual(f.encode(b"123456789"), bytes.fromhex("0e3132333435363738392639f4cb00"))

    def test_cobs_independent_vectors(self):
        for raw, encoded in (("", "01"), ("00", "0101"), ("0000", "010101"),
                             ("11220033", "0311220233")):
            self.assertEqual(f.cobs_encode(bytes.fromhex(raw)).hex(), encoded)
            self.assertEqual(f.cobs_decode(bytes.fromhex(encoded)).hex(), raw)

    def test_every_split_and_concatenated_frames(self):
        raw = bytes.fromhex(FIXTURE["wire_hex"])
        wire = f.encode(raw)
        for cut in range(len(wire) + 1):
            d = f.Decoder()
            self.assertEqual(list(d.feed(wire[:cut])) + list(d.feed(wire[cut:])), [raw])
        self.assertEqual(list(f.Decoder().feed(wire * 3)), [raw] * 3)

    def test_corruption_and_recovery(self):
        good = f.encode(b"good")
        bad = bytearray(f.encode(b"bad"))
        bad[2] ^= 0x20
        decoder = f.Decoder()
        self.assertEqual(list(decoder.feed(bad + good)), [b"good"])
        self.assertEqual(decoder.errors, 1)

    def test_overflow_is_bounded_and_recovers_at_delimiter(self):
        decoder = f.Decoder()
        for _ in range(20):
            self.assertEqual(list(decoder.feed(b"a" * 10000)), [])
            self.assertLessEqual(len(decoder.buffer), f.MAX_ENCODED)
        self.assertTrue(decoder.discarding)
        self.assertEqual(list(decoder.feed(b"\0" + f.encode(b"recovered"))), [b"recovered"])
        self.assertEqual(decoder.errors, 1)

    def test_disconnect_discards_partial_frame(self):
        d = f.Decoder()
        list(d.feed(f.encode(b"old")[:3]))
        d.reset()
        self.assertEqual(list(d.feed(f.encode(b"new"))), [b"new"])

    def test_boundaries(self):
        for size in (1, 253, 254, 255, 1024):
            for byte in (0, 1, 255):
                raw = bytes([byte]) * size
                wire = f.encode(raw)
                self.assertLessEqual(len(wire), 1034)
                self.assertEqual(f.decode(wire[:-1]), raw)
        for raw in (b"", bytes(1025)):
            with self.assertRaises(ValueError): f.encode(raw)
        for malformed in (b"\0", b"\3x", b"\3\0x", b"\1", b"x" * 1034):
            with self.assertRaises(ValueError): f.decode(malformed)


if __name__ == "__main__":
    unittest.main()
