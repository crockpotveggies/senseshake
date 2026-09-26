"""Run the bounded bring-up RTL test using the portable Icarus installation."""
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='groundlark-rtl-') as tmp:
    executable=Path(tmp)/'link.vvp'
    subprocess.run(['iverilog','-g2012','-Wall','-s','tb_link','-o',str(executable),
                    str(ROOT/'rtl/daqhat_01_link.sv'),str(ROOT/'tests/tb_link.sv')],check=True,timeout=60)
    subprocess.run(['vvp',str(executable)],check=True,timeout=60)
    import sys
    subprocess.run([sys.executable,str(ROOT/'cosim.py')],check=True,timeout=240)
