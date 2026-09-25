"""End-to-end Pi driver signals and negative controls for the signal oracle."""
from copy import deepcopy
from io import BytesIO
from unittest.mock import patch
import unittest

from senseshake.hat_signals import PROFILE, run_bench, check_recording
from senseshake.recording import Reader, Writer
from senseshake.sensors import LSM6DSO, SCL3300, MAXM10S


def altered(data, edit):
    """Re-encode valid CRCs, so failures come from signal validity, not framing."""
    reader = Reader(BytesIO(data))
    stream = BytesIO()
    writer = Writer(stream, reader.metadata)
    for arrived, message in reader:
        if isinstance(message, dict):
            fields = {k: v for k, v in message.items() if k not in ("code", "detail")}
            writer.event(message["code"], message["detail"], arrived, **fields)
        else:
            edit(message)
            writer.message(message, arrived)
    return stream.getvalue()


class HatSignalsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.report = run_bench()

    def assert_check_fails(self, data, name):
        report = check_recording(data)
        self.assertFalse(report["passed"])
        self.assertFalse(next(c for c in report["checks"] if c["name"] == name)["passed"])

    def test_known_signal_runs_through_all_production_hat_drivers(self):
        # Spy on real methods rather than replacing them with model adapters.
        counts = dict(imu=0, tilt=0, gnss=0)
        def spy(original, key):
            def read(driver):
                counts[key] += 1
                return original(driver)
            return read
        with patch.object(LSM6DSO, "read", spy(LSM6DSO.read, "imu")), \
             patch.object(SCL3300, "read", spy(SCL3300.read, "tilt")), \
             patch.object(MAXM10S, "read", spy(MAXM10S.read, "gnss")):
            data, report = run_bench()
        self.assertTrue(report["passed"], report)
        self.assertEqual(counts, dict(imu=832, tilt=200, gnss=8))
        self.assertEqual(data, self.data)
        self.assertEqual(len(report["checks"]), 10)

    def test_consistent_but_wrong_rocking_motion_is_rejected(self):
        profile = deepcopy(PROFILE)
        profile["initial"]["orientation_deg"] = [0, 0, 0]
        with patch("senseshake.hat_signals.PROFILE", profile):
            data, _ = run_bench()
        self.assert_check_fails(data, "Known roll waveform")

    def test_wrong_gain_fails_even_with_valid_framing(self):
        def edit(m):
            if m.WhichOneof("body") == "batch" and m.batch.sensor_id <= 4:
                for s in m.batch.samples:
                    s.imu.acceleration.x *= 2
        self.assert_check_fails(altered(self.data, edit), "IMU frequency, gain & phase")

    def test_wrong_frequency_fails(self):
        profile = deepcopy(PROFILE)
        profile["initial"]["acceleration_m_s2"][0]["frequency_hz"] = 3
        with patch("senseshake.hat_signals.PROFILE", profile):
            data, _ = run_bench()
        self.assert_check_fails(data, "IMU frequency, gain & phase")

    def test_inverted_signal_phase_fails(self):
        def edit(m):
            if m.WhichOneof("body") == "batch" and m.batch.sensor_id <= 4:
                for s in m.batch.samples:
                    s.imu.acceleration.x *= -1
        self.assert_check_fails(altered(self.data, edit), "IMU frequency, gain & phase")

    def test_stuck_sensor_breaks_coherence(self):
        def edit(m):
            if m.WhichOneof("body") == "batch" and m.batch.sensor_id == 3:
                for s in m.batch.samples:
                    s.imu.acceleration.x = 0
        self.assert_check_fails(altered(self.data, edit), "Four-IMU coherence")

    def test_gyro_scale_error_breaks_integrated_roll(self):
        def edit(m):
            if m.WhichOneof("body") == "batch" and m.batch.sensor_id <= 4:
                for s in m.batch.samples:
                    s.imu.angular_rate.x = round(s.imu.angular_rate.x * .9)
        self.assert_check_fails(altered(self.data, edit), "Gyro / gravity consistency")

    def test_gravity_scale_error_fails(self):
        def edit(m):
            if m.WhichOneof("body") == "batch" and m.batch.sensor_id <= 4:
                for s in m.batch.samples:
                    s.imu.acceleration.z = round(s.imu.acceleration.z * .99)
        self.assert_check_fails(altered(self.data, edit), "Gravity magnitude")

    def test_tilt_sign_error_fails(self):
        def edit(m):
            if m.WhichOneof("body") == "batch" and m.batch.sensor_id == 5:
                for s in m.batch.samples:
                    s.tilt.angle.y *= -1
        self.assert_check_fails(altered(self.data, edit), "Inclinometer consistency")

    def test_gnss_velocity_unit_error_fails(self):
        import struct
        def edit(m):
            if m.WhichOneof("body") == "batch" and m.batch.sensor_id == 6:
                for s in m.batch.samples:
                    data = bytearray(s.gnss.nav_pvt)
                    struct.pack_into("<iii", data, 48, 1, 2, 0)
                    s.gnss.nav_pvt = bytes(data)
        self.assert_check_fails(altered(self.data, edit), "GNSS motion & units")

    def test_zero_tilt_vector_fails_without_crashing(self):
        def edit(m):
            if m.WhichOneof("body") == "batch" and m.batch.sensor_id == 5:
                for s in m.batch.samples:
                    s.tilt.acceleration.x = s.tilt.acceleration.y = s.tilt.acceleration.z = 0
        self.assert_check_fails(altered(self.data, edit), "Inclinometer consistency")

    def test_timestamp_shift_fails(self):
        def edit(m):
            if m.WhichOneof("body") == "batch":
                for s in m.batch.samples:
                    s.time.acquisition_ns += 2_000_000
        self.assert_check_fails(altered(self.data, edit), "Timing & continuity")

    def test_missing_sample_cannot_be_a_pass(self):
        def edit(m):
            if m.WhichOneof("body") == "batch" and m.batch.sensor_id == 1:
                s = m.batch.samples[0]
                if s.sequence == 1:
                    s.ClearField("imu")
                    s.quality = 2
        self.assert_check_fails(altered(self.data, edit), "Inventory & quality")


if __name__ == "__main__":
    unittest.main()
