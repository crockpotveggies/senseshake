"""Image-build-only download, pinned and verified before execution."""
import hashlib
from pathlib import Path
import urllib.request

VERSION = "1.73.0"
SHA256 = "8f2986298ad08f0cc1bf999b9797b7c383adf32d7edf0f73d6f1e1a701baeac1"
payload = urllib.request.urlopen(
    f"https://github.com/bufbuild/buf/releases/download/v{VERSION}/buf-Linux-x86_64", timeout=120).read()
assert hashlib.sha256(payload).hexdigest() == SHA256, "Buf checksum mismatch"
target = Path("/usr/local/bin/buf")
target.write_bytes(payload)
target.chmod(0o755)
