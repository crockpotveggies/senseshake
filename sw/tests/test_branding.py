"""Branding migration must preserve old recordings and the frozen wire contract."""
import hashlib
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory
from groundlark_contract.compatibility import renamed_baseline
from groundlark_contract.schema import envelope_type
from groundlark.cli import replay
from groundlark.measurements import analyze
from groundlark.recording import Reader, Writer, is_acquisition_metadata
from groundlark.workbench import Workbench

ROOT = Path(__file__).resolve().parents[2]


class BrandingCompatibilityTests(unittest.TestCase):
    def test_frozen_baseline_and_namespace_only_projection(self):
        data = (ROOT / 'sw/interfaces/baseline.binpb').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         '7177780d921a4962fbbd7fa7035a745578a802c7d3e2272ca31c4f6f602e359b')
        old = descriptor_pb2.FileDescriptorSet.FromString(data)
        new = descriptor_pb2.FileDescriptorSet.FromString(renamed_baseline(data))
        # Only the board enum spelling changes; its numeric wire value stays 1.
        board = next(e for f in old.file for e in f.enum_type if e.name == 'Board')
        value = next(v for v in board.value if v.name == 'BOARD_T1')
        self.assertEqual(value.number, 1)
        value.name = 'BOARD_DAQHAT_01'
        # Both brands have ten characters, so exact byte replacement is an
        # independent oracle for the remaining descriptor namespace edits.
        self.assertEqual(new.SerializeToString(deterministic=True),
                         old.SerializeToString(deterministic=True).replace(b'senseshake', b'groundlark'))

    def test_old_and_new_envelopes_cross_decode_identically(self):
        pool = descriptor_pool.DescriptorPool()
        baseline = descriptor_pb2.FileDescriptorSet.FromString((ROOT / 'sw/interfaces/baseline.binpb').read_bytes())
        for file in baseline.file: pool.Add(file)
        old_type = message_factory.GetMessageClass(pool.FindMessageTypeByName('senseshake.sensor.v1.Envelope'))
        old = old_type(version=1, device_id='original-device', boot_id=0xffffffffffffffff)
        old.status.code = 1
        wire = old.SerializeToString(deterministic=True)
        new = envelope_type().FromString(wire)
        self.assertEqual(new.SerializeToString(deterministic=True), wire)
        self.assertEqual(old_type.FromString(new.SerializeToString()), old)

    def test_legacy_recording_in_cli_workbench_and_measurements(self):
        engine = Workbench(); engine.running = True; engine.advance(100)
        reader = Reader(BytesIO(engine.finish()))
        metadata = dict(reader.metadata, format='senseshake-acquisition-v1')
        stream = BytesIO(); writer = Writer(stream, metadata)
        for arrived, item in reader:
            if isinstance(item, dict):
                fields = dict(item)
                code, detail = fields.pop('code'), fields.pop('detail')
                writer.event(code, detail, arrived, **fields)
            else: writer.message(item, arrived)
        data = stream.getvalue()
        target = Workbench(); target.load_recording(data)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'legacy.ssrec'; path.write_bytes(data)
            self.assertTrue(replay(path))
            self.assertTrue(analyze(path)['completed'])

    def test_unknown_format_is_still_rejected(self):
        for metadata in [None, [], {}, {'format': []}, {'format': 'unknown-v1'}]:
            self.assertFalse(is_acquisition_metadata(metadata))
