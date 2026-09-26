"""Offline schema checks and portable contract tests; output only in sw/build/."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
INTERFACES = ROOT / "sw/interfaces"
BUILD = ROOT / "sw/build"
BUF = os.environ.get("GROUNDLARK_BUF", "buf")


def run(*args, **kwargs):
    return subprocess.run(list(args), cwd=INTERFACES, check=True, **kwargs)


def main():
    BUILD.mkdir(exist_ok=True)
    run(BUF, "format", "--diff", "--exit-code")
    run(BUF, "lint")
    run(BUF, "build", "--exclude-source-info", "-o", str(BUILD / "schema.binpb"))
    baseline = INTERFACES / 'baseline.binpb'
    run(BUF, "breaking", "--against", str(baseline))
    # Prove that the compatibility gate catches a real incompatible wire change.
    with tempfile.TemporaryDirectory(dir=BUILD) as tmp:
        folder = Path(tmp)
        shutil.copytree(INTERFACES / "proto", folder / "proto")
        shutil.copy2(INTERFACES / "buf.yaml", folder / "buf.yaml")
        path = folder / "proto/groundlark/sensor/v1/sensor.proto"
        path.write_text(path.read_text().replace("fixed64 boot_id = 3;", "string boot_id = 3;"))
        rejected = subprocess.run([BUF, "breaking", str(folder), "--against", str(baseline)],
                                  capture_output=True, text=True)
        assert rejected.returncode != 0 and "boot_id" in rejected.stdout + rejected.stderr, rejected
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(INTERFACES / "python"), str(ROOT / "sw/pi")]),
               GROUNDLARK_DESCRIPTOR=str(BUILD / "schema.binpb"))
    run(sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "sw/tests"), "-p", "test_*.py", "-v", env=env)
    # Run the public application entry point and retain one bounded review artifact.
    demo = BUILD / "demo.ssrec"
    if demo.exists(): demo.unlink()
    cli = str(ROOT / "sw/tools/sensor.py")
    simulated = run(sys.executable, cli, "simulate", "--remote", "--seconds", "2",
                    "--faults", str(ROOT / "sw/tests/fixtures/acquisition_faults.json"),
                    "--scenario", str(ROOT / "sw/pi/profiles/stimulus-demo.json"),
                    "--output", str(demo), env=env, capture_output=True, text=True)
    replayed = run(sys.executable, cli, "replay", str(demo), env=env, capture_output=True, text=True)
    assert json.loads(simulated.stdout) == json.loads(replayed.stdout)
    (BUILD / "demo-summary.json").write_text(replayed.stdout)
    signal_capture = BUILD / "hat-signals.ssrec"
    signal_report = signal_capture.with_suffix(".json")
    for path in (signal_capture, signal_report):
        if path.exists(): path.unlink()
    run(sys.executable, str(ROOT / "sw/tools/check_hat_signals.py"), "--output", str(signal_capture),
        env=env, capture_output=True, text=True)
    (BUILD / "verification.json").write_text(json.dumps({
        "status": "passed", "buf": run(BUF, "--version", capture_output=True, text=True).stdout.strip(),
        "breaking_baseline": "sw/interfaces/baseline.binpb", "incompatible_change_rejected": True,
        "application_demo": json.loads(replayed.stdout),
        "hat_signals": json.loads(signal_report.read_text()),
        "scope": "Schemas, software acquisition/replay, modeled sensor buses and injected faults; not physical buses, USB enumeration or MCU emulation"
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
