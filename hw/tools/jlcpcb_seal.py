"""Hash and bundle a reviewed package. Does not remove manufacturing holds."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from jlcpcb_package import ROOT, sha, write_json


def seal(out):
    manifest = json.loads((out / 'manifest.json').read_text())
    for source, expected in manifest['source_sha256'].items():
        if sha(ROOT / source) != expected: raise ValueError(f'Stale source: {source}')
    for required in ['README.md', 'DAQHAT-01-assembly-review.pdf', 'review/independent-check.json']:
        if not (out / required).is_file(): raise ValueError(f'Missing review file: {required}')
    manifest['exporter_sha256'] = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted((ROOT / 'hw/tools').glob('jlcpcb_*.py'))}
    write_json(out / 'manifest.json', manifest)
    bundle = out / 'DAQHAT-01-JLCPCB-REVIEW.zip'
    checksum = out / 'SHA256SUMS.txt'
    bundle_hash = out / (bundle.name + '.sha256')
    files = sorted(p for p in out.rglob('*') if p.is_file() and p not in [bundle, checksum, bundle_hash])
    checksum.write_text(''.join(f'{sha(p)}  {p.relative_to(out).as_posix()}\n' for p in files), encoding='utf-8', newline='\n')
    with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in files + [checksum]: archive.write(path, path.relative_to(out).as_posix())
    with zipfile.ZipFile(bundle) as archive:
        if archive.testzip(): raise ValueError('ZIP CRC failed')
        for path in files:
            data = archive.read(path.relative_to(out).as_posix())
            if hashlib.sha256(data).hexdigest() != sha(path): raise ValueError('Archive content mismatch')
    bundle_hash.write_text(f'{sha(bundle)}  {bundle.name}\n', encoding='utf-8', newline='\n')
    print(f'Packed {len(files)+1} files, {bundle.stat().st_size} bytes. Status remains REVIEW ONLY.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package',type=Path)
    seal(parser.parse_args().package.resolve())
