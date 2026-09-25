"""Add bounded UTC estimates to a copy of a completed timing capture."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'sw/pi'), str(ROOT/'sw/interfaces/python')]
from senseshake.cli import load_json
from senseshake.utc import correlate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recording', type=Path)
    parser.add_argument('--policy', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): parser.error('report already exists')
    if args.report.resolve() == args.output.resolve(): parser.error('output and report must be different files')
    try:
        report = correlate(args.recording, args.output, load_json(args.policy))
        with args.report.open('x', encoding='utf-8') as stream: json.dump(report, stream, indent=2, allow_nan=False)
    except (ValueError, OSError, KeyError, TypeError) as error: parser.exit(1, f'UTC correlation: {error}\n')
    print(f"Correlated {report['samples_correlated']} samples; {report['samples_unlabelled']} remain unlabelled ({report['scope']})")


if __name__ == '__main__': main()
