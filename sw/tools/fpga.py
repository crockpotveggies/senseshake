"""Optional Pi 4 SPI/JTAG bring-up, with a process lock and independent disarm."""
import argparse
from contextlib import contextmanager
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pi'))
from senseshake.fpga_link import ModeControl,Packets


@contextmanager
def termination_cleanup():
    """Normal service termination unwinds the same isolation path as Ctrl-C."""
    def terminate(signum, frame):
        raise SystemExit(128+signum)
    previous=signal.signal(signal.SIGTERM,terminate)
    try:yield
    finally:signal.signal(signal.SIGTERM,previous)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('scan','program','status','loopback'))
    parser.add_argument('--gpiochip',required=True,help='Verified BCM2711 GPIO chip, e.g. /dev/gpiochip0')
    parser.add_argument('--bitstream',type=Path)
    parser.add_argument('--message',default='ShakeSense internal SPI link')
    args=parser.parse_args()
    if args.action=='program' and (args.bitstream is None or not args.bitstream.is_file()):
        parser.error('program requires an existing --bitstream .bit file')
    if len(args.message.encode())>192:parser.error('message exceeds 192 bytes')
    import fcntl
    from senseshake.fpga_linux import Arm,Owner
    from senseshake.linux_io import I2C,SPI
    # Root-owned directory prevents an unprivileged user supplying a lock symlink.
    lockdir=Path('/run/senseshake-fpga');lockdir.mkdir(mode=0o700,exist_ok=True)
    with (lockdir/'owner.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        arm=Arm(args.gpiochip);bus=None
        try:
            bus=I2C('/dev/i2c-1');owner=Owner(args.gpiochip)
            control=ModeControl(bus,owner,arm)
            mode='jtag' if args.action in ('scan','program') else 'spi'
            with control.active(mode):
                if mode=='jtag':
                    cfg=Path(__file__).resolve().parents[1]/'pi/deploy/t1-jtag.cfg'
                    command=['openocd','-f',str(cfg),'-c','init; scan_chain']
                    if args.action=='scan':command+=['-c','shutdown']
                    else:
                        # Copy to a generated safe path, avoiding Tcl path interpolation.
                        with tempfile.TemporaryDirectory(prefix='program-',dir=lockdir) as tmp:
                            bit=Path(tmp)/'image.bit';bit.write_bytes(args.bitstream.read_bytes())
                            subprocess.run(command+['-c',f'pld load 0 {bit}; shutdown'],check=True,timeout=180)
                        return
                    subprocess.run(command,check=True,timeout=30)
                else:
                    spi=SPI(owner.spi_path())
                    try:
                        packets=Packets(spi)
                        if args.action=='status':print({'status':packets.status(),'quad_supported':False})
                        else:
                            payload=args.message.encode();result=packets.exchange(payload,0)
                            if result!=payload:raise RuntimeError('FPGA loopback payload mismatch')
                            print(f'PASS SPI loopback: {len(result)} bytes, CRC and sequence verified')
                    finally:spi.close()
        finally:
            try:arm.close()
            finally:
                if bus is not None:bus.close()


if __name__=='__main__':
    with termination_cleanup():main()
