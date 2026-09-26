"""Pin the contract baseline and verify recording and wire compatibility."""
import hashlib
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory
from groundlark_contract.schema import envelope_type
from groundlark.cli import replay
from groundlark.measurements import analyze
from groundlark.recording import Reader, Writer, is_acquisition_metadata
from groundlark.workbench import Workbench

ROOT = Path(__file__).resolve().parents[2]


class ContractBaselineTests(unittest.TestCase):
    def test_frozen_baseline(self):
        data = (ROOT / 'sw/interfaces/baseline.binpb').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         'baea8814b3b28a3e990e3b9ece794895d30718dcf3f5fc86a3fde9a1bd90440f')
        baseline = descriptor_pb2.FileDescriptorSet.FromString(data)
        board = next(e for f in baseline.file for e in f.enum_type if e.name == 'Board')
        value = next(v for v in board.value if v.name == 'BOARD_DAQHAT_01')
        self.assertEqual(value.number, 1)

    def test_baseline_and_current_envelopes_cross_decode_identically(self):
        pool = descriptor_pool.DescriptorPool()
        baseline = descriptor_pb2.FileDescriptorSet.FromString((ROOT / 'sw/interfaces/baseline.binpb').read_bytes())
        for file in baseline.file: pool.Add(file)
        old_type = message_factory.GetMessageClass(pool.FindMessageTypeByName('groundlark.sensor.v1.Envelope'))
        old = old_type(version=1, device_id='original-device', boot_id=0xffffffffffffffff)
        old.status.code = 1
        wire = old.SerializeToString(deterministic=True)
        new = envelope_type().FromString(wire)
        self.assertEqual(new.SerializeToString(deterministic=True), wire)
        self.assertEqual(old_type.FromString(new.SerializeToString()), old)

    def test_recording_in_cli_workbench_and_measurements(self):
        engine = Workbench(); engine.running = True; engine.advance(100)
        reader = Reader(BytesIO(engine.finish()))
        metadata = dict(reader.metadata, format='groundlark-acquisition-v1')
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
            path = Path(tmp) / 'capture.ssrec'; path.write_bytes(data)
            self.assertTrue(replay(path))
            self.assertTrue(analyze(path)['completed'])

    def test_unknown_format_is_still_rejected(self):
        self.assertTrue(is_acquisition_metadata({'format': 'groundlark-acquisition-v1'}))
        for metadata in [None, [], {}, {'format': []}, {'format': 'unknown-v1'}]:
            self.assertFalse(is_acquisition_metadata(metadata))
