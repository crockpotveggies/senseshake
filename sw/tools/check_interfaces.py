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
BUF = os.environ.get("SENSESHAKE_BUF", "buf")


def run(*args, **kwargs):
    return subprocess.run(list(args), cwd=INTERFACES, check=True, **kwargs)


def main():
    BUILD.mkdir(exist_ok=True)
    run(BUF, "format", "--diff", "--exit-code")
    run(BUF, "lint")
    run(BUF, "build", "--exclude-source-info", "-o", str(BUILD / "schema.binpb"))
    run(BUF, "breaking", "--against", "baseline.binpb")
    # Prove that the compatibility gate catches a real incompatible wire change.
    with tempfile.TemporaryDirectory(dir=BUILD) as tmp:
        folder = Path(tmp)
        shutil.copytree(INTERFACES / "proto", folder / "proto")
        shutil.copy2(INTERFACES / "buf.yaml", folder / "buf.yaml")
        path = folder / "proto/senseshake/sensor/v1/sensor.proto"
        path.write_text(path.read_text().replace("fixed64 boot_id = 3;", "string boot_id = 3;"))
        rejected = subprocess.run([BUF, "breaking", str(folder), "--against", str(INTERFACES / "baseline.binpb")],
                                  capture_output=True, text=True)
        assert rejected.returncode != 0 and "boot_id" in rejected.stdout + rejected.stderr, rejected
    env = dict(os.environ, PYTHONPATH=str(INTERFACES / "python"),
               SENSESHAKE_DESCRIPTOR=str(BUILD / "schema.binpb"))
    run(sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "sw/tests"), "-p", "test_*.py", "-v", env=env)
    (BUILD / "verification.json").write_text(json.dumps({
        "status": "passed", "buf": run(BUF, "--version", capture_output=True, text=True).stdout.strip(),
        "breaking_baseline": "sw/interfaces/baseline.binpb", "incompatible_change_rejected": True,
        "scope": "Schema, semantics and framing; not sensor drivers, USB enumeration or firmware emulation"
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
