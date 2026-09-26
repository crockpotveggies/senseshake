"""Create/check a physical bench report, or hash its evidence attachments."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'sw/pi'))
from groundlark.bench import template, evaluate, evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    for name in ('init', 'check', 'evidence'):
        sub = subs.add_parser(name)
        sub.add_argument('report', type=Path)
        if name == 'evidence': sub.add_argument('file', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            with args.report.open('x', encoding='utf-8') as stream: json.dump(template(), stream, indent=2)
            print('Created unmeasured report: ' + str(args.report)); return
        if args.command == 'evidence': result = evidence(args.file, args.report.parent)
        else:
            if args.report.stat().st_size > 65536: raise ValueError('report exceeds 64 KiB')
            result = evaluate(json.loads(args.report.read_text(encoding='utf-8')), args.report.parent)
        print(json.dumps(result, indent=2, allow_nan=False))
        if args.command == 'check' and result['status'] != 'pass': raise SystemExit(2)
    except (OSError, ValueError, KeyError, TypeError) as error: parser.exit(1, f'Bench report: {error}\n')


if __name__ == '__main__': main()
