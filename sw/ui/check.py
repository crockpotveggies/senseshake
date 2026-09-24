"""Framework smoke check: real HTTP page construction and static model delivery.

Run in the locked UI environment. Browser interaction checks are documented
separately; this check deliberately does not claim to exercise WebGL.
"""
from pathlib import Path
import html
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import urlopen


def main():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen([sys.executable, str(Path(__file__).with_name("main.py")), "--port", str(port)],
                                   stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 30
            while True:
                try:
                    with urlopen(f"http://127.0.0.1:{port}/", timeout=3) as response:
                        page = html.unescape(response.read().decode())
                    break
                except URLError:
                    if time.monotonic() >= deadline or process.poll() is not None:
                        log.seek(0)
                        raise RuntimeError(log.read().decode(errors="replace"))
                    time.sleep(.1)
            for text in ("ShakeSense", "STIMULUS LAB", "Finish &amp; save", "Pose &amp; vibration"):
                # NiceGUI encodes element text as JSON instead of HTML entities.
                assert text.replace("&amp;", "&") in page, text
            with urlopen(f"http://127.0.0.1:{port}/board-assets/t1.glb", timeout=10) as response:
                assert response.read(4) == b"glTF"
            print("PASS workbench HTTP page and KiCad GLB delivery")
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    main()
