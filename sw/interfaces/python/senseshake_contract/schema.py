"""Load the descriptor built by Buf; generated output stays in sw/build/."""
import os
from pathlib import Path
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

DEFAULT = Path(__file__).resolve().parents[3] / "build/schema.binpb"


def envelope_type(path=None):
    files = descriptor_pb2.FileDescriptorSet.FromString(
        Path(path or os.environ.get("SENSESHAKE_DESCRIPTOR", DEFAULT)).read_bytes())
    pool = descriptor_pool.DescriptorPool()
    for file in files.file:
        pool.Add(file)
    return message_factory.GetMessageClass(
        pool.FindMessageTypeByName("senseshake.sensor.v1.Envelope"))
