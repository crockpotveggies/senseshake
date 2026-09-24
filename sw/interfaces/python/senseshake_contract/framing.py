"""Bounded COBS + CRC-32/ISO-HDLC framing for USB CDC and recordings."""
import struct
import zlib

MAX_PAYLOAD = 1024
MAX_ENCODED = 1033  # 1028 decoded bytes + floor(1028 / 254) + 1.


def cobs_encode(data):
    out = bytearray([0])
    start, code = 0, 1
    for byte in data:
        if byte == 0:
            out[start] = code
            start = len(out)
            out.append(0)
            code = 1
        else:
            out.append(byte)
            code += 1
            if code == 255:
                out[start] = code
                start = len(out)
                out.append(0)
                code = 1
    out[start] = code
    return bytes(out)


def cobs_decode(data):
    out = bytearray()
    index = 0
    while index < len(data):
        code = data[index]
        index += 1
        end = index + code - 1
        if code == 0 or end > len(data):
            raise ValueError("invalid COBS block")
        block = data[index:end]
        if 0 in block:
            raise ValueError("zero inside COBS block")
        out.extend(block)
        index = end
        if code < 255 and index < len(data):
            out.append(0)
    return bytes(out)


def encode(payload):
    if not 1 <= len(payload) <= MAX_PAYLOAD:
        raise ValueError("payload length must be 1..1024")
    return cobs_encode(payload + struct.pack("<I", zlib.crc32(payload))) + b"\0"


def decode(frame):
    if not 1 <= len(frame) <= MAX_ENCODED:
        raise ValueError("encoded frame exceeds bound")
    raw = cobs_decode(frame)
    if not 5 <= len(raw) <= MAX_PAYLOAD + 4:
        raise ValueError("decoded frame exceeds bound")
    payload, crc = raw[:-4], raw[-4:]
    if struct.unpack("<I", crc)[0] != zlib.crc32(payload):
        raise ValueError("CRC mismatch")
    return payload


class Decoder:
    """feed yields payloads, never queues them; overflow discards to delimiter.

    Call reset on disconnect. Exhaust the iterator before feeding another chunk.
    The application must supply its own bounded dispatch queue and timeout.
    """
    def __init__(self):
        self.errors = 0
        self.reset()

    def reset(self):
        self.buffer = bytearray()
        self.discarding = False

    def feed(self, data):
        for byte in data:
            if byte == 0:
                if not self.discarding and self.buffer:
                    try:
                        payload = decode(self.buffer)
                    except ValueError:
                        self.errors += 1
                    else:
                        yield payload
                self.reset()
            elif not self.discarding:
                if len(self.buffer) == MAX_ENCODED:
                    self.errors += 1
                    self.buffer.clear()
                    self.discarding = True
                else:
                    self.buffer.append(byte)
