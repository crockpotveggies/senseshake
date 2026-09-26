"""Analyze a stationary HAT recording or compare FPGA off/idle/active runs."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'sw/pi'), str(ROOT/'sw/interfaces/python')]
from groundlark.measurements import analyze, compare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recording', type=Path)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = analyze(args.recording)
    if args.baseline: result['comparison'] = compare(analyze(args.baseline), result)
    rendered = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.output:
        with args.output.open('x', encoding='utf-8') as stream: stream.write(rendered)
    else: print(rendered)


if __name__ == '__main__': main()
