"""Production Python client talking to real RTL pins, with deterministic faults.

Icarus only supplies electrical bit transactions: it does not implement or mock
the packet contract. Runs on the portable Linux lab; no physical bus claim.
"""
from pathlib import Path
import random
import select
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'pi'))
from senseshake.fpga_link import Packets,encode,MAX_FRAME


class RTL:
    def __init__(self,program):
        self.process=subprocess.Popen(['vvp',str(program)],stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
        self.low,self.high,self.phase=500,500,0
        self.transactions=0

    def command(self,op,data=b'',partial=0):
        line=f'{op} {len(data)} {self.low} {self.high} {self.phase} {partial} '
        self.process.stdin.write(line+' '.join(f'{v:02x}' for v in data)+'\n')
        self.process.stdin.flush()
        if not select.select([self.process.stdout],[],[],10)[0]:raise TimeoutError('RTL peer stalled')
        response=self.process.stdout.readline().strip()
        if not response.startswith('RX'):raise RuntimeError(f'RTL failure: {response}')
        return bytes.fromhex(response[3:])

    def transfer(self,data,mode=0,hz=1_000_000):
        assert mode==0 and hz<=1_000_000
        self.transactions+=1
        result=self.command(1,data)
        assert len(result)==len(data)
        return result

    def reset(self):self.command(0)

    def close(self):
        self.process.stdin.close()
        try:self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill();self.process.wait()
        self.process.stdout.close()


def main():
    with tempfile.TemporaryDirectory(prefix='senseshake-cosim-') as tmp:
        executable=Path(tmp)/'host.vvp'
        subprocess.run(['iverilog','-g2012','-Wall','-s','tb_host','-o',str(executable),
                        str(ROOT/'rtl/t1_link.sv'),str(ROOT/'tests/tb_host.sv')],check=True,timeout=30)
        peer=RTL(executable)
        try:
            client=Packets(peer,sleep=lambda _:None,clock=lambda:0)
            rng=random.Random(0x53534650)
            peer.reset()
            # Every payload length; phases sweep the entire 20 ns fabric period.
            for size in range(193):
                peer.low=500+(size%3)*137;peer.high=500+(size%5)*83;peer.phase=size%20
                payload=rng.randbytes(size)
                seq=(65500+size)&65535
                assert client.exchange(payload,seq)==payload,(size,seq)
            peer.low=peer.high=500
            cases=0
            def rejected(data,error,partial=0):
                nonlocal cases
                peer.reset();peer.command(1,data,partial)
                status=peer.transfer(bytes(9))
                assert status[1:]==b'SSFP\x01\x00\x01'+bytes([error]),status.hex()
                cases+=1
            # Independently corrupt every bit of a valid frame (including CRC).
            frame=encode(b'fault-pattern',0xFFFF)
            for bit in range(len(frame)*8):
                bad=bytearray(frame);bad[bit//8]^=1<<(bit%8)
                rejected(b'\x01'+bad,2 if bit//8 in range(6) or bit//8 in (8,9) else 3)
            for partial in range(8):rejected(b'',4,partial)
            for count in (0,1,205,207):rejected(b'\x02'+bytes(count),4)
            for count in (0,1,2,3):rejected(b'\x03'+bytes(count),6)
            for count in (207,1022,1023,1098):rejected(b'\x01'+bytes(count),1)
            for command in range(4,256):rejected(bytes([command]),7)
            # Reset while CS is asserted must discard its tail, including ACK.
            for data in (b'\x01'+frame[:8],b'\x02'+bytes(10),b'\x03\xff'):
                peer.reset();peer.transfer(b'\x01'+frame)
                peer.command(3,data)
                assert client.status()==1,'reset tail created a spurious sticky error'
                assert client.exchange(b'after reset',0)==b'after reset'
                cases+=1
            print(f'PASS co-simulation: 193 payload sizes, sequence wrap, 20 clock phases; {cases} fault/reset cases; {peer.transactions} host transactions')
        finally:peer.close()


if __name__=='__main__':main()
