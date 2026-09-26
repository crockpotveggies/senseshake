"""A BOM-only correction must not silently reuse tampered placement/artwork."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from jlcpcb_bom_overlay import verify_base_files, export_overlay
from jlcpcb_package import sha


class OverlayIntegrityTests(unittest.TestCase):
    def test_modified_base_cpl_bom_artwork_or_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            names=['manifest.json','BOM-review.csv','CPL-review.csv','DAQHAT-01-Gerbers-REVIEW.zip']
            for name in names: (base/name).write_text('original')
            (base/'SHA256SUMS.txt').write_text(''.join(f'{sha(base/name)}  {name}\n' for name in names))
            verify_base_files(base)
            for name in names:
                (base/name).write_text('altered')
                with self.subTest(name=name), self.assertRaisesRegex(ValueError,'checksum mismatch'):
                    verify_base_files(base)
                (base/name).write_text('original')

    def test_existing_overlay_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'new output directory'):
                export_overlay(Path(tmp)/'missing-base',Path(tmp))

    def test_changed_design_input_rejected_before_overlay_is_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'base';base.mkdir()
            design=root/'board-input';design.write_text('validated CAD')
            manifest={'source_sha256':{'board-input':sha(design)}}
            (base/'manifest.json').write_text(json.dumps(manifest))
            for name in ('BOM-review.csv','CPL-review.csv','DAQHAT-01-Gerbers-REVIEW.zip'):
                (base/name).write_text('unchanged archive fixture')
            files=sorted(base.iterdir())
            (base/'SHA256SUMS.txt').write_text(''.join(f'{sha(path)}  {path.name}\n' for path in files))
            design.write_text('different CAD')
            with patch('jlcpcb_bom_overlay.ROOT',root),patch('jlcpcb_bom_overlay.REGISTRY',root/'parts.json'):
                with self.assertRaisesRegex(ValueError,'Stale base-package design input'):
                    export_overlay(base,root/'output')
            self.assertFalse((root/'output').exists())
