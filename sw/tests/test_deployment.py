import ctypes as c
import importlib.util
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from groundlark.linux_io import RisingEdges, GPIOEventRequest

ROOT = Path(__file__).resolve().parents[2]


class DeploymentTests(unittest.TestCase):
    def test_spi_binding_refuses_wrong_device_before_mutations(self):
        spec = importlib.util.spec_from_file_location('bind_spi', ROOT/'sw/pi/deploy/bind_spi.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(5):
                folder = root/'devices'/f'spi0.{i}'/'of_node'
                folder.mkdir(parents=True)
                (folder/'compatible').write_bytes(b'groundlark,' + (b'lsm6dso-userspace' if i < 4 else b'scl3300-userspace') + b'\0')
            self.assertEqual(len(module.inventory(root)), 5)
            (root/'devices/spi0.3/of_node/compatible').write_bytes(b'unrelated\0')
            with self.assertRaises(ValueError): module.inventory(root)

    @unittest.skipUnless(shutil.which('dtc') and shutil.which('fdtoverlay'), 'device-tree compiler/merger in portable lab')
    def test_compiled_overlay_merges_five_selects_without_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            base = folder/'base.dts'
            base.write_text('''/dts-v1/;
/ { compatible="brcm,bcm2711";
    gpio: gpio { gpio-controller; #gpio-cells=<2>;
      spi0_cs_pins: spi0_cs_pins { brcm,pins=<8 7>; brcm,function=<1>; }; };
    spi0: spi { #address-cells=<1>; #size-cells=<0>; cs-gpios=<&gpio 8 1>,<&gpio 7 1>; status="disabled";
      spidev@0 { compatible="spidev"; reg=<0>; };
      spidev@1 { compatible="spidev"; reg=<1>; }; };
    i2c1: i2c { status="disabled"; };
};''')
            def run(*args): return subprocess.check_output(args, text=True).strip()
            run('dtc', '-@', '-I', 'dts', '-O', 'dtb', '-o', str(folder/'base.dtb'), str(base))
            run('dtc', '-@', '-I', 'dts', '-O', 'dtb', '-o', str(folder/'overlay.dtbo'), str(ROOT/'sw/pi/deploy/groundlark-daqhat-01-overlay.dts'))
            run('fdtoverlay', '-i', str(folder/'base.dtb'), '-o', str(folder/'merged.dtb'), str(folder/'overlay.dtbo'))
            merged = str(folder/'merged.dtb')
            self.assertEqual(set(run('fdtget','-l',merged,'/spi').split()), {f'spidev@{i}' for i in range(5)})
            cs = [int(v) for v in run('fdtget','-t','u',merged,'/spi','cs-gpios').split()]
            self.assertEqual(cs[1::3], [8, 7, 5, 6, 13])
            self.assertEqual(cs[2::3], [1]*5)
            self.assertEqual(run('fdtget',merged,'/i2c','status'), 'okay')
            self.assertEqual(run('fdtget','-t','u',merged,'/i2c','clock-frequency'), '100000')
            for i in range(5):
                self.assertEqual(run('fdtget','-t','u',merged,f'/spi/spidev@{i}','reg'), str(i))
                self.assertEqual(run('fdtget',merged,f'/spi/spidev@{i}','compatible'),
                                 'groundlark,' + ('lsm6dso-userspace' if i < 4 else 'scl3300-userspace'))

    @unittest.skipUnless(shutil.which('dtc') and shutil.which('fdtoverlay'), 'device-tree tools in portable lab')
    def test_fpga_overlay_preserves_interrupt_and_requests_cs_timing(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            base=folder/'base.dts'
            base.write_text('''/dts-v1/;
/ { compatible="brcm,bcm2711";
 gpio: gpio { gpio-controller; #gpio-cells=<2>;
   spi6_cs_pins: spi6_cs_pins { brcm,pins=<18 27>; brcm,function=<1>; }; };
 spi6: spi { #address-cells=<1>; #size-cells=<0>; cs-gpios=<&gpio 18 1>,<&gpio 27 1>; status="disabled";
   spidev@0 { compatible="spidev"; reg=<0>; };
   spidev@1 { compatible="spidev"; reg=<1>; status="okay"; }; };
};''')
            def run(*args):return subprocess.check_output(args,text=True).strip()
            run('dtc','-@','-I','dts','-O','dtb','-o',str(folder/'base.dtb'),str(base))
            run('dtc','-@','-I','dts','-O','dtb','-o',str(folder/'link.dtbo'),str(ROOT/'sw/pi/deploy/groundlark-fpga-overlay.dts'))
            run('fdtoverlay','-i',str(folder/'base.dtb'),'-o',str(folder/'merged.dtb'),str(folder/'link.dtbo'))
            merged=str(folder/'merged.dtb')
            self.assertEqual(run('fdtget','-t','u',merged,'/gpio/spi6_cs_pins','brcm,pins'),'18')
            self.assertEqual(run('fdtget',merged,'/spi/spidev@1','status'),'disabled')
            cs=[int(v) for v in run('fdtget','-t','u',merged,'/spi','cs-gpios').split()]
            self.assertEqual(cs[1::3],[18])
            self.assertEqual(run('fdtget',merged,'/spi/spidev@0','compatible'),'groundlark,fpga-userspace')
            for prop in ('setup','hold','inactive'):
                self.assertEqual(run('fdtget','-t','u',merged,'/spi/spidev@0',f'spi-cs-{prop}-delay-ns'),'1000')
            self.assertEqual(run('fdtget','-t','u',merged,'/spi/spidev@0','spi-max-frequency'),'1000000')

    def test_gpio_edge_records_and_bounds(self):
        edges = RisingEdges.__new__(RisingEdges); edges.fd = 9
        with patch('groundlark.linux_io.os.read', return_value=struct.pack('=QI4x',123456789,1)) as read:
            self.assertEqual(edges.read(), [123456789])
            read.assert_called_once_with(9, 1024)
        with patch('groundlark.linux_io.os.read', side_effect=BlockingIOError): self.assertFalse(edges.poll())
        for data in (b'x', b'', struct.pack('=QI4x',1,2)):
            with patch('groundlark.linux_io.os.read', return_value=data):
                with self.assertRaises(OSError): edges.read()

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux GPIO request ABI')
    def test_gpio_request_uses_input_rising_edge_and_closes_chip(self):
        self.assertEqual(c.sizeof(GPIOEventRequest),48)
        def fake(fd, command, data, mutate):
            self.assertEqual(command,0xc030b404)
            request = GPIOEventRequest.from_buffer_copy(data)
            self.assertEqual((request.offset, request.handleflags, request.eventflags),(27,1,1))
            request.fd=18; data[:]=bytes(request)
        with patch('groundlark.linux_io.os.open',return_value=17), patch('groundlark.linux_io.ioctl',fake), \
             patch('groundlark.linux_io.os.close') as close, patch('fcntl.fcntl'):
            edge=RisingEdges('/dev/gpiochip0',27)
            close.assert_called_once_with(17)
            edge.close()
            self.assertEqual(close.call_args.args,(18,))


if __name__ == '__main__': unittest.main()
