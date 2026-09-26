"""Live bounded receiver; malformed peers cannot reset session history."""
from collections import Counter, deque
from google.protobuf.message import DecodeError
from groundlark_contract.framing import Decoder
from .messages import Envelope


class Receiver:
    def __init__(self, sessions, partial_timeout_ns=1_000_000_000, board=None, forbidden_devices=()):
        self.sessions, self.decoder = sessions, Decoder()
        if partial_timeout_ns <= 0: raise ValueError("partial-frame deadline")
        self.board, self.forbidden_devices = board, frozenset(forbidden_devices)
        self.partial_timeout = partial_timeout_ns
        self.partial_started = None
        self.errors = Counter()

    def disconnect(self, device=None):
        self.decoder.reset()
        self.partial_started = None
        self.sessions.disconnect(device)
        self.errors["disconnect"] += 1

    def feed(self, data, arrived):
        if len(data) > 4096: raise ValueError("transport chunk limit")
        if self.partial_started is not None and arrived - self.partial_started >= self.partial_timeout:
            self.decoder.reset()
            self.decoder.discarding = True
            self.errors["partial_timeout"] += 1
            self.partial_started = None
        before = self.decoder.errors
        for raw in self.decoder.feed(data):
            try:
                message = Envelope().FromString(raw)
                if message.device_id in self.forbidden_devices: raise ValueError("reserved local producer identity")
                if self.board is not None and message.WhichOneof("body") == "identity" and message.identity.board != self.board:
                    raise ValueError("wrong board on transport")
                self.sessions.accept(message)
            except (DecodeError, ValueError):
                self.errors["invalid_message"] += 1
            else: yield message
        self.errors["corrupt_frame"] += self.decoder.errors - before
        if self.decoder.buffer or self.decoder.discarding:
            if self.partial_started is None or 0 in data: self.partial_started = arrived
        else: self.partial_started = None


class Outbox:
    """Drop newest data on overflow; carry loss into the next accepted batch.

    Control messages must be drained, never silently dropped. Keys are bounded
    by the producer's fixed sensor inventory; no arbitrary network key growth.
    """
    def __init__(self, keys, capacity=64):
        if not 1 <= capacity <= 4096 or not 1 <= len(keys) <= 32: raise ValueError("queue bounds")
        self.queue = deque()
        self.capacity = capacity
        self.pending = {key: 0 for key in keys}
        self.dropped_samples = 0

    def put(self, message, arrived):
        kind = message.WhichOneof("body")
        key = (message.device_id, message.boot_id, message.batch.sensor_id) if kind == "batch" else None
        if key is not None and key not in self.pending: raise ValueError("unknown queue producer")
        if len(self.queue) == self.capacity:
            if kind != "batch": raise BufferError("control backpressure; drain before control")
            b = message.batch
            previous = self.pending[key]
            self.pending[key] = None if previous is None or not b.HasField("dropped_before") else previous + b.dropped_before + len(b.samples)
            self.dropped_samples += len(b.samples)
            return False
        copy = type(message)()
        copy.CopyFrom(message)
        if key is not None:
            pending = self.pending[key]
            if pending is None: copy.batch.ClearField("dropped_before")
            elif copy.batch.HasField("dropped_before"): copy.batch.dropped_before += pending
            self.pending[key] = 0
        self.queue.append((copy, arrived))
        return True

    def pop(self):
        return self.queue.popleft()
