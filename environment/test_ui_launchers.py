"""Exercise launcher boundaries without network, dependency installs or a server."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='groundlark ui ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.windows = os.name == 'nt'
        self.shell = shutil.which('powershell' if self.windows else 'sh')
        if not self.shell:
            self.skipTest('platform shell unavailable')
        self.launcher = self.root / ('ui.ps1' if self.windows else 'ui.sh')
        shutil.copyfile(ROOT / self.launcher.name, self.launcher)
        (self.root / 'sw/ui').mkdir(parents=True)
        self.log = self.root / 'calls.jsonl'
        mock = self.root / 'mock_uv.py'
        mock.write_text('''import json, os, sys
from pathlib import Path
with Path(os.environ['MOCK_UV_LOG']).open('a') as out:
    out.write(json.dumps({'args': sys.argv[1:], 'env': {
        key: os.environ.get(key) for key in
        ('UV_PROJECT_ENVIRONMENT', 'UV_CACHE_DIR', 'UV_PYTHON_INSTALL_DIR')}}) + '\\n')
sys.exit(int(os.environ.get('MOCK_UV_EXIT', '0')))
''', encoding='utf-8')
        bin_dir = self.root / 'bin'
        bin_dir.mkdir()
        if self.windows:
            fake = bin_dir / 'uv.cmd'
            fake.write_text(f'@"{sys.executable}" "{mock}" %*\n', encoding='utf-8')
        else:
            import shlex
            fake = bin_dir / 'uv'
            fake.write_text(f'#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(mock))} "$@"\n')
            fake.chmod(0o755)
        self.env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ['PATH'],
                        MOCK_UV_LOG=str(self.log), UV_CACHE_DIR='caller-cache')

    def run_launcher(self, *args, failure=0):
        command = [self.shell]
        if self.windows:
            command += ['-NoProfile', '-File']
        result = subprocess.run(command + [str(self.launcher), *args], cwd=ROOT,
                                env=dict(self.env, MOCK_UV_EXIT=str(failure)),
                                capture_output=True, text=True, timeout=30)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []
        return result, calls

    def test_spaces_working_directory_port_and_local_environment(self):
        result, calls = self.run_launcher('-Port' if self.windows else '--port', '8123')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(calls), 1)
        args = calls[0]['args']
        self.assertIn('--locked', args)
        self.assertEqual(Path(args[args.index('--project') + 1]), self.root / 'sw/ui')
        self.assertEqual(Path(args[args.index('python') + 1]), self.root / 'sw/ui/main.py')
        self.assertEqual(args[-2:], ['--port', '8123'])
        for value in calls[0]['env'].values():
            self.assertTrue(Path(value).is_relative_to(self.root / '.local'))

    def test_failed_sync_stops_before_checks_or_server(self):
        result, calls = self.run_launcher(*(['-Setup', '-Check'] if self.windows else ['--setup', '--check']), failure=37)
        self.assertEqual(result.returncode, 37, result.stderr)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['args'][0], 'sync')

    def test_failed_http_check_is_not_reported_as_success(self):
        result, calls = self.run_launcher('-Check' if self.windows else '--check', failure=29)
        self.assertEqual(result.returncode, 29, result.stderr)
        self.assertEqual(len(calls), 1)
        self.assertEqual(Path(calls[0]['args'][-1]), self.root / 'sw/ui/check.py')

    @unittest.skipUnless(os.name == 'nt', 'PowerShell process environment restoration')
    def test_restores_callers_environment_on_failure(self):
        command = "& '{}' -Check; $code=$LASTEXITCODE; Write-Output $env:UV_CACHE_DIR; exit $code".format(
            str(self.launcher).replace("'", "''"))
        result = subprocess.run([self.shell, '-NoProfile', '-Command', command],
                                env=dict(self.env, MOCK_UV_EXIT='29'), capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 29, result.stderr)
        self.assertIn('caller-cache', result.stdout)


if __name__ == '__main__':
    unittest.main()
