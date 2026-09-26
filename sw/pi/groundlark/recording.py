"""Length/CRC-protected, bounded streaming recordings with explicit arrival time."""
import json
import struct
import zlib
from groundlark_contract.framing import encode, decode
from .calibration import canonical
from .messages import Envelope
from google.protobuf.message import DecodeError

MAGIC = b"SSREC01\0"
ACQUISITION_FORMAT = 'groundlark-acquisition-v1'


def is_acquisition_metadata(metadata):
    return isinstance(metadata, dict) and metadata.get('format') == ACQUISITION_FORMAT


HEADER_LIMIT = 16384
RECORD_LIMIT = 2048
PREFIX = struct.Struct("<BQH")


class RecordingError(ValueError):
    pass


def parse_json(data):
    try:
        return json.loads(data, parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
    except (ValueError, UnicodeError, RecursionError) as error:
        raise RecordingError("invalid recording JSON") from error


def exact(stream, count):
    data = stream.read(count)
    if len(data) != count: raise RecordingError("truncated recording")
    return data


class Writer:
    def __init__(self, stream, metadata, max_bytes=64 * 1024 * 1024):
        if not 4096 <= max_bytes <= 1024 * 1024 * 1024: raise ValueError("recording limit")
        self.stream, self.limit, self.written = stream, max_bytes, 0
        data = canonical(metadata)
        if len(data) > HEADER_LIMIT: raise ValueError("recording metadata limit")
        header = MAGIC + struct.pack("<I", len(data)) + data
        self._write(header + struct.pack("<I", zlib.crc32(header)))
        self.last_arrival = -1

    def _write(self, data):
        if self.written + len(data) > self.limit: raise RecordingError("recording byte budget exhausted")
        if self.stream.write(data) != len(data): raise RecordingError("short recording write")
        self.written += len(data)

    def record(self, kind, payload, arrival_ns):
        if len(payload) > RECORD_LIMIT or kind not in (1, 2): raise ValueError("record bounds")
        if not self.last_arrival <= arrival_ns < 1 << 64: raise ValueError("arrival time regressed")
        data = PREFIX.pack(kind, arrival_ns, len(payload)) + payload
        self._write(data + struct.pack("<I", zlib.crc32(data)))
        self.last_arrival = arrival_ns

    def message(self, message, arrival_ns):
        self.record(1, encode(message.SerializeToString(deterministic=True)), arrival_ns)

    def event(self, code, detail, arrival_ns, **fields):
        self.record(2, canonical(dict(code=code, detail=str(detail)[:256], **fields)), arrival_ns)


class Reader:
    def __init__(self, stream):
        self.stream = stream
        header = exact(stream, 12)
        if header[:8] != MAGIC: raise RecordingError("unknown recording format")
        length = struct.unpack("<I", header[8:])[0]
        if length > HEADER_LIMIT: raise RecordingError("metadata exceeds bound")
        data = exact(stream, length)
        if zlib.crc32(header + data) != struct.unpack("<I", exact(stream, 4))[0]: raise RecordingError("metadata CRC")
        self.metadata = parse_json(data)

    def __iter__(self):
        previous = -1
        while True:
            first = self.stream.read(1)
            if not first: return
            prefix = first + exact(self.stream, PREFIX.size - 1)
            kind, arrived, length = PREFIX.unpack(prefix)
            if kind not in (1, 2) or length > RECORD_LIMIT or arrived < previous: raise RecordingError("record bounds/order")
            payload = exact(self.stream, length)
            if zlib.crc32(prefix + payload) != struct.unpack("<I", exact(self.stream, 4))[0]: raise RecordingError("record CRC")
            previous = arrived
            if kind == 1:
                if not payload.endswith(b"\0"): raise RecordingError("missing frame delimiter")
                try: message = Envelope().FromString(decode(payload[:-1]))
                except (DecodeError, ValueError) as error: raise RecordingError("invalid recorded message") from error
                yield arrived, message
            else:
                value = parse_json(payload)
                if not isinstance(value, dict): raise RecordingError("event must be an object")
                yield arrived, value
