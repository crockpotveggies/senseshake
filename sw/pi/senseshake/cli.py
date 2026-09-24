"""The same acquisition, validation and recording path for sim and Linux."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import time
from .calibration import Calibrations, canonical
from .messages import configuration
from .recording import Reader, Writer
from .runtime import Acquisition, Channel
from .session import Sessions
from .simulation import Simulated, defaults
from .stimulus import Scenario


def load_json(path, limit=16384):
    with open(path, "rb") as stream: data = stream.read(limit + 1)
    if len(data) > limit: raise ValueError("JSON input byte limit")
    return json.loads(data, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def replay(path):
    counts, digest = Counter(), hashlib.sha256()
    completed = False
    with open(path, "rb") as stream:
        reader = Reader(stream)
        if not isinstance(reader.metadata, dict) or reader.metadata.get("format") != "senseshake-acquisition-v1":
            raise ValueError("recording application metadata")
        calibrations = Calibrations(reader.metadata.get("calibrations", []))
        sessions = Sessions(calibrations)
        for arrived, item in reader:
            completed = isinstance(item, dict) and item.get("code") == "acquisition_summary"
            if isinstance(item, dict):
                counts["events"] += 1
                if item.get("code") == "usb_disconnected" and item.get("device") is not None:
                    sessions.disconnect(item["device"])
            else:
                kind = sessions.accept(item)
                counts[kind] += 1
                digest.update(item.SerializeToString(deterministic=True))
                if kind == "batch":
                    for sample in item.batch.samples:
                        counts["samples"] += 1
                        counts[{1: "valid", 2: "missing", 3: "saturated", 4: "fault"}[sample.quality]] += 1
    return dict(counts, completed=completed, message_sha256=digest.hexdigest())


def export_scenario(recording, output):
    """Recover scheduled and interactive changes from a validated recording."""
    replay(recording)
    with open(recording, "rb") as stream:
        reader = Reader(stream)
        if reader.metadata.get("stimulus_model") != "ideal-v1": raise ValueError("recording has no supported stimulus model")
        document = Scenario(reader.metadata["scenario"]).export()
        pending, applied = document["events"][:], []
        for arrived, item in reader:
            if not isinstance(item, dict) or item.get("code") != "stimulus_change": continue
            event = {"at_ns": item["at_ns"], "set": item["set"]}
            if type(event["at_ns"]) is not int or not 0 <= event["at_ns"] <= arrived:
                raise ValueError("invalid recorded control time")
            if event in pending: pending.remove(event)
            applied.append(event)
            if len(applied) > 256: raise ValueError("recorded control limit")
        document["events"] = sorted(applied + pending, key=lambda e: e["at_ns"])
        document = Scenario(document).export()
    with open(output, "x", encoding="utf-8") as stream:
        stream.write(json.dumps(document, indent=2, allow_nan=False) + "\n")
    return dict(scenario=str(output), events=len(document["events"]), seed=reader.metadata["seed"], remote=reader.metadata["remote"])


def run(args):
    simulated = args.command == "simulate"
    faults = load_json(args.faults) if getattr(args, "faults", None) else []
    records = load_json(args.calibrations) if args.calibrations else []
    calibrations = Calibrations(records)
    ids = {}
    for ident, record in calibrations.records.items():
        if record["sensor_id"] in ids: raise ValueError("one active calibration per sensor")
        ids[record["sensor_id"]] = ident
    if not 0 < args.seconds <= 3600 or not 1 <= args.drain_every <= 10000: raise ValueError("run bounds")
    settings = defaults()
    channels, enable, usb = [], None, None
    if simulated:
        # Human-readable JSON may exceed its bounded canonical representation.
        scenario = Scenario(load_json(args.scenario, 65536) if args.scenario else None)
        current = 0
        clock = lambda: current
        for cfg in settings:
            channels.append(Channel("sim-pi", 1, cfg, Simulated(cfg["sensor_id"], args.seed, faults, scenario, clock)))
        if args.remote:
            for cfg in defaults(True):
                channels.append(Channel("sim-head", 2, cfg, Simulated(cfg["sensor_id"], args.seed, faults, scenario, clock)))
    else:
        if not sys.platform.startswith("linux"): raise ValueError("live acquisition requires Linux")
        from .live import Factory, USB
        from .linux_io import SensorEnable
        from .worker import Worker
        from .transport import Receiver
        profile = load_json(args.profile)
        if set(profile) != {"device_id", "spi", "i2c", "sensor_enable"} or len(profile["spi"]) != 5:
            raise ValueError("live profile requires five explicit SPI paths and sensor OE")
        if len(set(profile["spi"])) != 5: raise ValueError("each sensor needs a separate chip select")
        boot = secrets.randbits(64) or 1
        # Validate all identity/configuration fields before opening devices.
        configuration(profile["device_id"], boot, settings)
        for cfg in settings:
            sid = cfg["sensor_id"]
            path = profile["spi"][sid - 1] if sid <= 5 else profile["i2c"]
            channels.append(Channel(profile["device_id"], boot, cfg, Worker(Factory(sid, path), cfg)))
        clock = lambda: time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
    sessions = Sessions(calibrations)
    metadata = dict(format="senseshake-acquisition-v1", source="simulation" if simulated else "linux-polling",
                    calibrations=list(calibrations.records.values()), timing="poll completion; uncertainty unknown")
    if simulated: metadata.update(seed=args.seed, faults=faults, remote=args.remote, stimulus_model="ideal-v1", scenario=scenario.export())
    else: metadata["profile"] = profile
    try:
        # Exclusive create prevents accidentally replacing a prior recording.
        with open(args.output, "xb") as stream:
            writer = Writer(stream, metadata, max_bytes=args.max_mib * 1024 * 1024)
            app = Acquisition(writer, sessions, channels, args.queue, ids)
            if not simulated:
                enable = SensorEnable(**profile["sensor_enable"])
                enable.enabled(True)
                if args.usb:
                    # Independent USB session state prevents peers replacing local identities.
                    usb = USB(args.usb, Receiver(Sessions(calibrations), board=2, forbidden_devices=[profile["device_id"]]))
            start = clock()
            app.start(start)
            end, tick = clock() + int(args.seconds * 1e9), 0
            while clock() < end:
                if simulated:
                    for change in scenario.advance(current):
                        app.event("stimulus_change", "simulation controls changed", current, **change)
                app.tick(clock)
                if usb:
                    app.drain()
                    usb.poll(clock(), lambda m, t: app.emit(m, t), app.event)
                tick += 1
                if tick % args.drain_every == 0: app.drain()
                if simulated: current += 1_000_000
                else: time.sleep(.001)
            app.finish(clock())
    finally:
        # Close every independent resource even if one worker cannot be reaped.
        errors = []
        for obj in [usb, *[c.adapter for c in channels], enable]:
            if obj is not None:
                try: obj.close()
                except Exception as error: errors.append(error)
        if errors: raise errors[0]
    return replay(args.output)


def main(argv=None):
    parser = argparse.ArgumentParser(description="ShakeSense sensor acquisition (no FPGA required)")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("simulate", "live"):
        p = commands.add_parser(name)
        p.add_argument("--output", type=Path, required=True)
        p.add_argument("--seconds", type=float, default=2)
        p.add_argument("--queue", type=int, default=64)
        p.add_argument("--drain-every", type=int, default=1)
        p.add_argument("--max-mib", type=int, default=64)
        p.add_argument("--calibrations", type=Path)
        if name == "simulate":
            p.add_argument("--seed", type=int, default=1)
            p.add_argument("--faults", type=Path)
            p.add_argument("--scenario", type=Path, help="versioned SI stimulus scenario JSON")
            p.add_argument("--remote", action="store_true")
        else:
            p.add_argument("--profile", type=Path, required=True)
            p.add_argument("--usb")
    p = commands.add_parser("replay")
    p.add_argument("recording", type=Path)
    p = commands.add_parser("export-scenario", help="recover controls for another deterministic simulation")
    p.add_argument("recording", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "replay": result = replay(args.recording)
        elif args.command == "export-scenario": result = export_scenario(args.recording, args.output)
        else: result = run(args)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f"senseshake: {error}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__": main()
