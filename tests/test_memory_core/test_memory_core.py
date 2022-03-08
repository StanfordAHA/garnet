import argparse
from lake.modules.reg_cr import Reg

import os
from memory_core.fake_pe_core import FakePECore
from memory_core.lookup_core import LookupCore
from peak_core.peak_core import PeakCore
from memory_core.intersect_core import IntersectCore
from memory_core.write_scanner_core import WriteScannerCore
from gemstone.common.util import compress_config_data
from memory_core.scanner_core import ScannerCore
from memory_core.reg_core import RegCore
from lake.utils.parse_clkwork_csv import generate_data_lists
from gemstone.common.testers import BasicTester
from cgra.util import create_cgra
from canal.util import IOSide
from memory_core.memory_core_magma import config_mem_tile
from archipelago import pnr
import lassen.asm as asm
import random as rand
import re
from memory_core.constraints import *
from memory_core.memtile_util import NetlistBuilder


def io_sides():
    return IOSide.North | IOSide.East | IOSide.South | IOSide.West


def make_memory_core():
    mem_core = "memtile"
    return mem_core


def make_scanner_core():
    scan_core = ScannerCore()
    return scan_core


class MemoryCoreTester(BasicTester):

    def configure(self, addr, data, feature=0):
        self.poke(self.clock, 0)
        self.poke(self.reset_port, 0)
        if(feature == 0):
            exec(f"self.poke(self._circuit.config.config_addr, addr)")
            exec(f"self.poke(self._circuit.config.config_data, data)")
            exec(f"self.poke(self._circuit.config.write, 1)")
            self.step(1)
            exec(f"self.poke(self._circuit.config.write, 0)")
            exec(f"self.poke(self._circuit.config.config_data, 0)")
        else:
            exec(f"self.poke(self._circuit.config_{feature}.config_addr, addr)")
            exec(f"self.poke(self._circuit.config_{feature}.config_data, data)")
            exec(f"self.poke(self._circuit.config_{feature}.write, 1)")
            self.step(1)
            exec(f"self.poke(self._circuit.config_{feature}.write, 0)")
            exec(f"self.poke(self._circuit.config_{feature}.config_data, 0)")


def basic_tb(config_path,
             stream_path,
             run_tb,
             in_file_name="input",
             out_file_name="output",
             cwd=None,
             trace=False):

    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2))

    netlist = {
        "e0": [("I0", "io2f_16"), ("m0", "data_in_0")],
        "e1": [("m0", "data_out_0"), ("I1", "f2io_16")]
    }
    bus = {"e0": 16, "e1": 16}

    placement, routing = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    # Regular Bootstrap
    MCore = make_memory_core()
    # Get configuration
    configs_mem = MCore.get_static_bitstream(config_path=config_path,
                                             in_file_name=in_file_name,
                                             out_file_name=out_file_name)

    config_final = []
    for (f1, f2) in configs_mem:
        config_final.append((f1, f2, 0))
    mem_x, mem_y = placement["m0"]
    memtile = interconnect.tile_circuits[(mem_x, mem_y)]
    mcore = memtile.core
    config_mem_tile(interconnect, config_data, config_final, mem_x, mem_y, mcore)

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    tester.zero_inputs()

    tester.poke(circuit.interface["stall"], 1)

    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    in_data, out_data, valids = generate_data_lists(csv_file_name=stream_path,
                                                    data_in_width=MCore.num_data_inputs(),
                                                    data_out_width=MCore.num_data_outputs())

    data_in_x, data_in_y = placement["I0"]
    data_in = f"glb2io_16_X{data_in_x:02X}_Y{data_in_y:02X}"
    data_out_x, data_out_y = placement["I1"]
    data_out = f"io2glb_16_X{data_out_x:02X}_Y{data_out_y:02X}"

    for i in range(len(out_data)):
        tester.poke(circuit.interface[data_in], in_data[0][i])
        tester.eval()
        tester.expect(circuit.interface[data_out], out_data[0][i])
        # toggle the clock
        tester.step(2)

    run_tb(tester, cwd=cwd, trace=trace, disable_ndarray=True)


# add more tests with this function by adding args
# @pytest.mark.parametrize("args", [lake_test_app_args("conv_3_3")])
# def test_lake_garnet(args, run_tb):
#     basic_tb(config_path=args[0],
#              stream_path=args[1],
#              in_file_name=args[2],
#              out_file_name=args[3],
#              run_tb=run_tb)


def scanner_test(trace, run_tb, cwd):

    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=[ScannerCore])

    netlist = {
        # Scanner to I/O
        "e0": [("s4", "data_out"), ("I0", "f2io_16")],
        "e1": [("s4", "valid_out"), ("i1", "f2io_1")],
        "e2": [("s4", "eos_out"), ("i2", "f2io_1")],
        "e3": [("i3", "io2f_1"), ("s4", "ready_in")],
        # Scanner to Mem
        "e4": [("m5", "data_out_0"), ("s4", "data_in")],
        "e5": [("m5", "valid_out_0"), ("s4", "valid_in")],
        "e6": [("s4", "addr_out"), ("m5", "addr_in_0")],
        "e7": [("s4", "ready_out"), ("m5", "ren_in_0")],
        "e8": [("i6", "io2f_1"), ("s4", "flush")],
        "e9": [("i6", "io2f_1"), ("m5", "flush")]
    }

    bus = {"e0": 16,
           "e1": 1,
           "e2": 1,
           "e3": 1,
           "e4": 16,
           "e5": 1,
           "e6": 16,
           "e7": 1,
           "e8": 1,
           "e9": 1
           }

    placement, routing = pnr(interconnect, (netlist, bus), cwd=cwd)
    config_data = interconnect.get_route_bitstream(routing)

    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    data_len = len(data)

    # Get configuration
    mem_x, mem_y = placement["m5"]
    mem_data = interconnect.configure_placement(mem_x, mem_y, {"config": ["mek", {"init": data}]})
    scan_x, scan_y = placement["s4"]
    scan_data = interconnect.configure_placement(scan_x, scan_y, data_len)
    config_data += scan_data
    config_data += mem_data
    skip_addr = interconnect.get_skip_addr()
    config_data = compress_config_data(config_data, skip_compression=skip_addr)

    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    tester.zero_inputs()

    tester.poke(circuit.interface["stall"], 1)

    flush_x, flush_y = placement["i6"]
    flush = f"glb2io_1_X{flush_x:02X}_Y{flush_y:02X}"

    for addr, index in config_data:
        tester.configure(addr, index)
        #  tester.config_read(addr)
        tester.eval()

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    # Now flush to synchronize everybody
    tester.poke(circuit.interface[flush], 1)
    tester.eval()
    tester.step(2)
    tester.poke(circuit.interface[flush], 0)
    tester.eval()

    data_out_x, data_out_y = placement["I0"]
    data_out = f"io2glb_16_X{data_out_x:02X}_Y{data_out_y:02X}"

    valid_x, valid_y = placement["i1"]
    valid = f"io2glb_1_X{valid_x:02X}_Y{valid_y:02X}"
    eos_x, eos_y = placement["i2"]
    eos = f"io2glb_1_X{eos_x:02X}_Y{eos_y:02X}"
    readyin_x, readyin_y = placement["i3"]
    readyin = f"glb2io_1_X{readyin_x:02X}_Y{readyin_y:02X}"

    val = 1
    for i in range(50):
        tester.poke(circuit.interface[readyin], (i > 25))
        tester.eval()
        # tester.expect(circuit.interface[data_out], out_data[0][i])
        # toggle the clock
        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)


def intersect_test(trace, run_tb, cwd):

    chip_size = 4
    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=[IntersectCore])

    netlist = {
        # Intersect to I/O
        "e0": [("j0", "coord_out"), ("I1", "f2io_16")],
        "e1": [("j0", "pos_out_0"), ("I2", "f2io_16")],
        "e2": [("j0", "pos_out_1"), ("I3", "f2io_16")],
        "e3": [("j0", "valid_out"), ("i4", "f2io_1")],
        "e4": [("j0", "eos_out"), ("i5", "f2io_1")],
        "e5": [("j0", "ready_out_0"), ("i6", "f2io_1")],
        "e6": [("j0", "ready_out_1"), ("i7", "f2io_1")],

        # I/O to Intersect
        "e7": [("i8", "io2f_1"), ("j0", "flush")],
        "e8": [("I9", "io2f_16"), ("j0", "coord_in_0")],
        "e9": [("I10", "io2f_16"), ("j0", "coord_in_1")],
        "e10": [("i11", "io2f_1"), ("j0", "valid_in_0")],
        "e11": [("i12", "io2f_1"), ("j0", "valid_in_1")],
        "e12": [("i13", "io2f_1"), ("j0", "eos_in_0")],
        "e13": [("i14", "io2f_1"), ("j0", "eos_in_1")],
        "e14": [("i15", "io2f_1"), ("j0", "ready_in")]
    }

    bus = {
        # Intersect to I/O
        "e0": 16,
        "e1": 16,
        "e2": 16,
        "e3": 1,
        "e4": 1,
        "e5": 1,
        "e6": 1,
        "e7": 1,

        # I/O to Intersect
        "e8": 16,
        "e9": 16,
        "e10": 1,
        "e11": 1,
        "e12": 1,
        "e13": 1,
        "e14": 1
    }

    placement, routing = pnr(interconnect, (netlist, bus), cwd=cwd)
    config_data = interconnect.get_route_bitstream(routing)

    # Get configuration
    isect_x, isect_y = placement["j0"]
    isect_data = interconnect.configure_placement(isect_x, isect_y, 5)
    config_data += isect_data

    config_data = compress_config_data(config_data)

    print("BITSTREAM START")
    for addr, config in config_data:
        print("{0:08X} {1:08X}".format(addr, config))
    print("BITSTREAM END")

    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    tester.zero_inputs()

    tester.poke(circuit.interface["stall"], 1)

    flush_x, flush_y = placement["i6"]
    flush = f"glb2io_1_X{flush_x:02X}_Y{flush_y:02X}"

    for addr, index in config_data:
        tester.configure(addr, index)
        #  tester.config_read(addr)
        tester.eval()

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    # Now flush to synchronize everybody
    tester.poke(circuit.interface[flush], 1)
    tester.eval()
    tester.step(2)
    tester.poke(circuit.interface[flush], 0)
    tester.eval()

    coord0_x, coord0_y = placement["I9"]
    coord0 = f"glb2io_16_X{coord0_x:02X}_Y{coord0_y:02X}"
    coord1_x, coord1_y = placement["I10"]
    coord1 = f"glb2io_16_X{coord1_x:02X}_Y{coord1_y:02X}"

    valid0_x, valid0_y = placement["i11"]
    valid0 = f"glb2io_1_X{valid0_x:02X}_Y{valid0_y:02X}"
    valid1_x, valid1_y = placement["i12"]
    valid1 = f"glb2io_1_X{valid1_x:02X}_Y{valid1_y:02X}"

    eos0_x, eos0_y = placement["i13"]
    eos0 = f"glb2io_1_X{eos0_x:02X}_Y{eos0_y:02X}"
    eos1_x, eos1_y = placement["i14"]
    eos1 = f"glb2io_1_X{eos1_x:02X}_Y{eos1_y:02X}"

    readyin_x, readyin_y = placement["i15"]
    readyin = f"glb2io_1_X{readyin_x:02X}_Y{readyin_y:02X}"

    c0 = [7, 1, 2, 7, 6, 10, 42]
    v0 = [0, 1, 1, 0, 1, 1, 0]
    e0 = [0, 0, 0, 0, 0, 1, 0]

    c1 = [3, 6, 7, 7, 8, 42]
    v1 = [1, 1, 0, 0, 1, 0]
    e1 = [0, 0, 0, 0, 1, 0]

    i0 = 0
    i1 = 0

    state = 0

    for i in range(50):
        tester.poke(circuit.interface[readyin], 1)
        tester.poke(circuit.interface[coord0], c0[i0])
        tester.poke(circuit.interface[coord1], c1[i1])
        tester.poke(circuit.interface[valid0], v0[i0])
        tester.poke(circuit.interface[valid1], v1[i1])
        tester.poke(circuit.interface[eos0], e0[i0])
        tester.poke(circuit.interface[eos1], e1[i1])
        tester.eval()

        # If both are valid (assuming FIFO is not full)
        # we should bump one of them pending the coordinate
        if v0[i0] == 1 and v1[i1] == 1:
            if state == 1:
                inc0 = 0
                inc1 = 0
                if c0[i0] <= c1[i1]:
                    inc0 = 1
                if c1[i1] <= c0[i0]:
                    inc1 = 1
                i0 += inc0
                i1 += inc1
            state = 1
        else:
            if v0[i0] == 0 and (i0 < len(v0) - 1):
                i0 += 1
            if v1[i1] == 0 and (i1 < len(v1) - 1):
                i1 += 1

        # tester.expect(circuit.interface[data_out], out_data[0][i])
        # toggle the clock
        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)


def scanner_intersect_test(trace, run_tb, cwd):

    chip_size = 4
    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=[ScannerCore, IntersectCore])

    netlist = {
        # Intersect to I/O
        "e0": [("j0", "coord_out"), ("I6", "f2io_16")],
        "e1": [("j0", "pos_out_0"), ("I7", "f2io_16")],
        "e2": [("j0", "pos_out_1"), ("I8", "f2io_16")],
        "e3": [("j0", "valid_out"), ("i9", "f2io_1")],
        "e4": [("j0", "eos_out"), ("i10", "f2io_1")],
        # Intersect to SCAN
        "e5": [("j0", "ready_out_0"), ("s1", "ready_in")],
        "e6": [("j0", "ready_out_1"), ("s2", "ready_in")],
        # Flush
        "e7": [("i11", "io2f_1"), ("m4", "flush")],
        "e8": [("i11", "io2f_1"), ("m3", "flush")],
        "e9": [("i11", "io2f_1"), ("s2", "flush")],
        "e10": [("i11", "io2f_1"), ("s1", "flush")],
        "e11": [("i11", "io2f_1"), ("j0", "flush")],
        # I/O to Intersect
        "e12": [("s1", "data_out"), ("j0", "coord_in_0")],
        "e13": [("s2", "data_out"), ("j0", "coord_in_1")],
        "e14": [("s1", "valid_out"), ("j0", "valid_in_0")],
        "e15": [("s2", "valid_out"), ("j0", "valid_in_1")],
        "e16": [("s1", "eos_out"), ("j0", "eos_in_0")],
        "e17": [("s2", "eos_out"), ("j0", "eos_in_1")],
        # This should technically be the only input I/O
        "e18": [("i12", "io2f_1"), ("j0", "ready_in")],
        # Mem to Scanner
        "e19": [("m3", "data_out_0"), ("s1", "data_in")],
        "e20": [("m4", "data_out_0"), ("s2", "data_in")],
        "e21": [("m3", "valid_out_0"), ("s1", "valid_in")],
        "e22": [("m4", "valid_out_0"), ("s2", "valid_in")],
        # Scanner to Mem
        "e23": [("s1", "addr_out"), ("m3", "addr_in_0")],
        "e24": [("s2", "addr_out"), ("m4", "addr_in_0")],
        "e25": [("s1", "ready_out"), ("m3", "ren_in_0")],
        "e26": [("s2", "ready_out"), ("m4", "ren_in_0")]
    }

    bus = {
        "e0": 16,
        "e1": 16,
        "e2": 16,
        "e3": 1,
        "e4": 1,
        "e5": 1,
        "e6": 1,
        "e7": 1,
        "e8": 1,
        "e9": 1,
        "e10": 1,
        "e11": 1,
        "e12": 16,
        "e13": 16,
        "e14": 1,
        "e15": 1,
        "e16": 1,
        "e17": 1,
        "e18": 1,
        "e19": 16,
        "e20": 16,
        "e21": 1,
        "e22": 1,
        "e23": 16,
        "e24": 16,
        "e25": 1,
        "e26": 1
    }

    placement, routing = pnr(interconnect, (netlist, bus), cwd=cwd)
    config_data = interconnect.get_route_bitstream(routing)

    data0 = [1, 2, 6, 10]
    data0_len = len(data0)
    data1 = [3, 6, 8, 0]
    # Need to provide 4 or else the machine doesn't work, so subtracting 1 here...
    data1_len = len(data1) - 1

    # Get configuration
    mem0_x, mem0_y = placement["m3"]
    mem0_data = interconnect.configure_placement(mem0_x, mem0_y, {"config": ["mek", {"init": data0}]})
    scan0_x, scan0_y = placement["s1"]
    scan0_data = interconnect.configure_placement(scan0_x, scan0_y, data0_len)
    mem1_x, mem1_y = placement["m4"]
    mem1_data = interconnect.configure_placement(mem1_x, mem1_y, {"config": ["mek", {"init": data1}]})
    scan0_x, scan0_y = placement["s2"]
    scan1_data = interconnect.configure_placement(scan0_x, scan0_y, data1_len)
    isect_x, isect_y = placement["j0"]
    isect_data = interconnect.configure_placement(isect_x, isect_y, 5)
    config_data += mem0_data
    config_data += scan0_data
    config_data += mem1_data
    config_data += scan1_data
    config_data += isect_data
    skip_addr = interconnect.get_skip_addr()
    config_data = compress_config_data(config_data, skip_compression=skip_addr)

    print("BITSTREAM START")
    for addr, config in config_data:
        print("{0:08X} {1:08X}".format(addr, config))
    print("BITSTREAM END")

    # Create tester and perform init routine...
    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    tester.zero_inputs()

    # Stall during config
    tester.poke(circuit.interface["stall"], 1)

    for addr, index in config_data:
        tester.configure(addr, index)
        #  tester.config_read(addr)
        tester.eval()

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    # Get flush handle and apply flush to start off app
    flush_x, flush_y = placement["i11"]
    flush = f"glb2io_1_X{flush_x:02X}_Y{flush_y:02X}"
    tester.poke(circuit.interface[flush], 1)
    tester.eval()
    tester.step(2)
    tester.poke(circuit.interface[flush], 0)
    tester.eval()

    # Just set final ready to always 1 for simplicity...
    readyin_x, readyin_y = placement["i12"]
    readyin = f"glb2io_1_X{readyin_x:02X}_Y{readyin_y:02X}"

    for i in range(50):
        tester.poke(circuit.interface[readyin], 1)
        tester.eval()
        # tester.expect(circuit.interface[data_out], out_data[0][i])
        # toggle the clock
        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)


def mem_scanner_intersect_test(trace, run_tb, cwd):

    chip_size = 4
    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=[ScannerCore, IntersectCore])

    netlist = {
        # Intersect to DATA MEM
        "e0": [("j0", "coord_out"), ("r15", "reg")],
        "e1": [("r15", "reg"), ("I6", "f2io_16")],
        "e2": [("j0", "pos_out_0"), ("m13", "addr_in_0")],
        "e3": [("j0", "pos_out_1"), ("m14", "addr_in_0")],
        "e4": [("j0", "valid_out"), ("m13", "ren_in_0"), ("m14", "ren_in_0")],
        "e5": [("j0", "eos_out"), ("r16", "reg")],
        "e6": [("r16", "reg"), ("i10", "f2io_1")],
        # Intersect to SCAN
        "e7": [("j0", "ready_out_0"), ("s1", "ready_in")],
        "e8": [("j0", "ready_out_1"), ("s2", "ready_in")],
        # Flush
        "e9": [("i11", "io2f_1"),
               ("j0", "flush"),
               ("s1", "flush"),
               ("s2", "flush"),
               ("m3", "flush"),
               ("m4", "flush"),
               ("m13", "flush"),
               ("m14", "flush")],
        # I/O to Intersect
        "e10": [("s1", "data_out"), ("j0", "coord_in_0")],
        "e11": [("s2", "data_out"), ("j0", "coord_in_1")],
        "e12": [("s1", "valid_out"), ("j0", "valid_in_0")],
        "e13": [("s2", "valid_out"), ("j0", "valid_in_1")],
        "e14": [("s1", "eos_out"), ("j0", "eos_in_0")],
        "e15": [("s2", "eos_out"), ("j0", "eos_in_1")],
        # This should technically be the only input I/O
        "e16": [("i12", "io2f_1"), ("j0", "ready_in")],
        # Mem to Scanner
        "e17": [("m3", "data_out_0"), ("s1", "data_in")],
        "e18": [("m4", "data_out_0"), ("s2", "data_in")],
        "e19": [("m3", "valid_out_0"), ("s1", "valid_in")],
        "e20": [("m4", "valid_out_0"), ("s2", "valid_in")],
        # Scanner to Mem
        "e21": [("s1", "addr_out"), ("m3", "addr_in_0")],
        "e22": [("s2", "addr_out"), ("m4", "addr_in_0")],
        "e23": [("s1", "ready_out"), ("m3", "ren_in_0")],
        "e24": [("s2", "ready_out"), ("m4", "ren_in_0")],
        # Data mem to IO (data, valid)
        "e25": [("m13", "data_out_0"), ("I17", "f2io_16")],
        "e26": [("m14", "data_out_0"), ("I18", "f2io_16")],
        "e27": [("m13", "valid_out_0"), ("i19", "f2io_1")],
        "e28": [("m14", "valid_out_0"), ("i20", "f2io_1")],

    }

    bus = {
        "e0": 16,
        "e1": 16,
        "e2": 16,
        "e3": 16,
        "e4": 1,
        "e5": 1,
        "e6": 1,
        "e7": 1,
        "e8": 1,
        "e9": 1,
        "e10": 16,
        "e11": 16,
        "e12": 1,
        "e13": 1,
        "e14": 1,
        "e15": 1,
        "e16": 1,
        "e17": 16,
        "e18": 16,
        "e19": 1,
        "e20": 1,
        "e21": 16,
        "e22": 16,
        "e23": 1,
        "e24": 1,
        "e25": 16,
        "e26": 16,
        "e27": 1,
        "e28": 1
    }

    placement, routing = pnr(interconnect, (netlist, bus), cwd=cwd)
    config_data = interconnect.get_route_bitstream(routing)

    data0 = [1, 2, 6, 10]
    data0_len = len(data0)
    data1 = [3, 6, 8, 0]
    # Need to provide 4 or else the machine doesn't work, so subtracting 1 here...
    data1_len = len(data1) - 1

    datad0 = [11, 12, 13, 14]
    datad1 = [15, 16, 17, 18]

    # Get configuration
    mem0_x, mem0_y = placement["m3"]
    mem0_data = interconnect.configure_placement(mem0_x, mem0_y, {"config": ["mek", {"init": data0}]})
    scan0_x, scan0_y = placement["s1"]
    scan0_data = interconnect.configure_placement(scan0_x, scan0_y, data0_len)
    mem1_x, mem1_y = placement["m4"]
    mem1_data = interconnect.configure_placement(mem1_x, mem1_y, {"config": ["mek", {"init": data1}]})
    scan0_x, scan0_y = placement["s2"]
    scan1_data = interconnect.configure_placement(scan0_x, scan0_y, data1_len)
    isect_x, isect_y = placement["j0"]
    isect_data = interconnect.configure_placement(isect_x, isect_y, 5)

    memd0_x, memd0_y = placement["m13"]
    memd0_data = interconnect.configure_placement(memd0_x, memd0_y, {"config": ["mek", {"init": datad0}]})
    memd1_x, memd1_y = placement["m14"]
    memd1_data = interconnect.configure_placement(memd1_x, memd1_y, {"config": ["mek", {"init": datad1}]})

    config_data += mem0_data
    config_data += scan0_data
    config_data += mem1_data
    config_data += scan1_data
    config_data += isect_data
    config_data += memd0_data
    config_data += memd1_data
    skip_addr = interconnect.get_skip_addr()
    config_data = compress_config_data(config_data, skip_compression=skip_addr)

    print("BITSTREAM START")
    for addr, config in config_data:
        print("{0:08X} {1:08X}".format(addr, config))
    print("BITSTREAM END")

    # Create tester and perform init routine...
    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    tester.zero_inputs()

    # Stall during config
    tester.poke(circuit.interface["stall"], 1)

    for addr, index in config_data:
        tester.configure(addr, index)
        #  tester.config_read(addr)
        tester.eval()

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    # Get flush handle and apply flush to start off app
    flush_x, flush_y = placement["i11"]
    flush = f"glb2io_1_X{flush_x:02X}_Y{flush_y:02X}"
    tester.poke(circuit.interface[flush], 1)
    tester.eval()
    tester.step(2)
    tester.poke(circuit.interface[flush], 0)
    tester.eval()

    # Just set final ready to always 1 for simplicity...
    readyin_x, readyin_y = placement["i12"]
    readyin = f"glb2io_1_X{readyin_x:02X}_Y{readyin_y:02X}"

    for i in range(50):
        tester.poke(circuit.interface[readyin], 1)
        tester.eval()
        # tester.expect(circuit.interface[data_out], out_data[0][i])
        # toggle the clock
        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)


def align_data(data, alignment):
    to_add = alignment - (len(data) - (len(data) // alignment) * alignment)
    if to_add == alignment:
        return data
    data += [0] * to_add
    return data


def random_data(length):
    retlist = []
    for i in range(length):
        # Don't include 0
        retlist.append(rand.randint(1, 2 ** 6 - 1))
    return retlist


def get_sparse_sequences(len1, len2, num_match, value_limit):
    '''
        Returns seqA, seqB: sparse sequences of len1 and len2, respectively, num_match
    '''
    if num_match > len1 or num_match > len2:
        num_match = len1
        if len1 > len2:
            num_match = len2
        print(f"Requested num match too high - setting it to smallest length: {num_match}")
    matching_numbers = []
    while len(matching_numbers) < num_match:
        new_rand = rand.randint(0, value_limit)
        if new_rand not in matching_numbers:
            matching_numbers.append(new_rand)
    seqA = []
    seqB = []
    seqA += matching_numbers
    seqB += matching_numbers

    while len(seqA) < len1:
        new_rand = rand.randint(0, value_limit)
        if new_rand not in seqA:
            seqA.append(new_rand)
    while len(seqB) < len2:
        new_rand = rand.randint(0, value_limit)
        if new_rand not in seqB and new_rand not in seqA:
            seqB.append(new_rand)

    seqA.sort()
    seqB.sort()
    print(f"SEQA: {seqA}\nSEQB: {seqB}")
    return seqA, seqB


def spVspV_test(trace, run_tb, cwd, data0=[1, 2, 6, 10], data1=[3, 6, 8]):
    # Streams and code to create them and align them
    # Fill data with random, align to 4
    datad0 = random_data(len(data0))
    data0_len = len(data0)
    datad1 = random_data(len(data1))
    data1_len = len(data1)

    out_data = []
    out_coord = []

    both = set(data0).intersection(data1)
    both = list(both)
    both.sort()
    ind0 = [data0.index(x) for x in both]
    ind1 = [data1.index(x) for x in both]

    out_coord = both
    for i in range(len(ind0)):
        out_data.append(datad0[ind0[i]] * datad1[ind1[i]])

    num_cycles = data0_len + data1_len + 200

    print(f"DATA0: {data0}")
    print(f"DATAD0: {datad0}")
    print(f"DATA1: {data1}")
    print(f"DATAD1: {datad1}")
    print(f"common coords: {both}")
    print(f"result data: {out_data}")

    # Align these guys after the fact...
    data0 = align_data(data0, 4)
    datad0 = align_data(datad0, 4)
    data1 = align_data(data1, 4)
    datad1 = align_data(datad1, 4)

    print(f"ALIGNED LENGTH 0: {len(data0)}")
    print(f"ALIGNED LENGTH 1: {len(data1)}")
    print(f"ADATA0: {data0}")
    print(f"ADATAD0: {datad0}")
    print(f"ADATA1: {data1}")
    print(f"ADATAD1: {datad1}")
    chip_size = 6
    num_tracks = 5

    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=num_tracks,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=[ScannerCore, IntersectCore, PeakCore])

    # Created CGRA with all cores!

    netlist = {
        # Intersect to DATA MEM
        "e0": [("j0", "coord_out"), ("r15", "reg")],
        "e1": [("r15", "reg"), ("m32", "data_in_0")],
        "e2": [("j0", "pos_out_0"), ("m13", "addr_in_0")],
        "e3": [("j0", "pos_out_1"), ("m14", "addr_in_0")],
        "e4": [("j0", "valid_out"), ("m13", "ren_in_0"), ("m14", "ren_in_0")],
        "e5": [("j0", "eos_out"), ("r16", "reg")],
        "e6": [("r16", "reg"), ("i10", "f2io_1")],
        # Intersect to SCAN
        "e7": [("j0", "ready_out_0"), ("s1", "ready_in")],
        "e8": [("j0", "ready_out_1"), ("s2", "ready_in")],
        # Flush
        "e9": [("i11", "io2f_1"),
               ("j0", "flush"),
               ("s1", "flush"),
               ("s2", "flush"),
               ("m3", "flush"),
               ("m4", "flush"),
               ("m13", "flush"),
               ("m14", "flush"),
               ("m31", "flush"),
               ("m32", "flush")],
        # I/O to Intersect
        "e10": [("s1", "data_out"), ("j0", "coord_in_0")],
        "e11": [("s2", "data_out"), ("j0", "coord_in_1")],
        "e12": [("s1", "valid_out"), ("j0", "valid_in_0")],
        "e13": [("s2", "valid_out"), ("j0", "valid_in_1")],
        "e14": [("s1", "eos_out"), ("j0", "eos_in_0")],
        "e15": [("s2", "eos_out"), ("j0", "eos_in_1")],
        # This should technically be the only input I/O
        "e16": [("i12", "io2f_1"), ("j0", "ready_in")],
        # Mem to Scanner
        "e17": [("m3", "data_out_0"), ("s1", "data_in")],
        "e18": [("m4", "data_out_0"), ("s2", "data_in")],
        "e19": [("m3", "valid_out_0"), ("s1", "valid_in")],
        "e20": [("m4", "valid_out_0"), ("s2", "valid_in")],
        # Scanner to Mem
        "e21": [("s1", "addr_out"), ("m3", "addr_in_0")],
        "e22": [("s2", "addr_out"), ("m4", "addr_in_0")],
        "e23": [("s1", "ready_out"), ("m3", "ren_in_0")],
        "e24": [("s2", "ready_out"), ("m4", "ren_in_0")],
        # Data mem to PE
        "e25": [("m13", "data_out_0"), ("p20", "data0")],
        "e26": [("m14", "data_out_0"), ("p20", "data1")],
        # MEM Fifo result...
        "e27": [("p20", "alu_res"), ("m31", "data_in_0")],
        "e28": [("m14", "valid_out_0"), ("m31", "wen_in_0")],
        "e29": [("m14", "valid_out_0"), ("m32", "wen_in_0")],
        "e30": [("i35", "io2f_1"), ("m31", "ren_in_0"), ("m32", "ren_in_0")],
        # Get mem outputs
        "e31": [("m31", "valid_out_0"), ("i50", "f2io_1")],
        "e32": [("m32", "valid_out_0"), ("i51", "f2io_1")],
        "e33": [("m31", "data_out_0"), ("I52", "f2io_16")],
        "e34": [("m32", "data_out_0"), ("I53", "f2io_16")]
    }

    bus = {
        "e0": 16,
        "e1": 16,
        "e2": 16,
        "e3": 16,
        "e4": 1,
        "e5": 1,
        "e6": 1,
        "e7": 1,
        "e8": 1,
        "e9": 1,
        "e10": 16,
        "e11": 16,
        "e12": 1,
        "e13": 1,
        "e14": 1,
        "e15": 1,
        "e16": 1,
        "e17": 16,
        "e18": 16,
        "e19": 1,
        "e20": 1,
        "e21": 16,
        "e22": 16,
        "e23": 1,
        "e24": 1,
        "e25": 16,
        "e26": 16,
        "e27": 16,
        "e28": 1,
        "e29": 1,
        "e30": 1,
        "e31": 1,
        "e32": 1,
        "e33": 16,
        "e34": 16
    }

    placement, routing = pnr(interconnect, (netlist, bus), cwd=cwd)
    config_data = interconnect.get_route_bitstream(routing)

    # Get configuration
    mem0_x, mem0_y = placement["m3"]
    mem0_data = interconnect.configure_placement(mem0_x, mem0_y, {"config": ["mek", {"init": data0}]})
    scan0_x, scan0_y = placement["s1"]
    scan0_data = interconnect.configure_placement(scan0_x, scan0_y, data0_len)
    mem1_x, mem1_y = placement["m4"]
    mem1_data = interconnect.configure_placement(mem1_x, mem1_y, {"config": ["mek", {"init": data1}]})
    scan0_x, scan0_y = placement["s2"]
    scan1_data = interconnect.configure_placement(scan0_x, scan0_y, data1_len)
    isect_x, isect_y = placement["j0"]
    isect_data = interconnect.configure_placement(isect_x, isect_y, 5)

    memd0_x, memd0_y = placement["m13"]
    memd0_data = interconnect.configure_placement(memd0_x, memd0_y, {"config": ["mek", {"init": datad0}]})
    memd1_x, memd1_y = placement["m14"]
    memd1_data = interconnect.configure_placement(memd1_x, memd1_y, {"config": ["mek", {"init": datad1}]})

    # Configure these guys as fifos...
    memcf_x, memcf_y = placement["m32"]
    memcf_data = interconnect.configure_placement(memcf_x, memcf_y, "fifo")
    memdf_x, memdf_y = placement["m31"]
    memdf_data = interconnect.configure_placement(memdf_x, memdf_y, "fifo")

    # PE as mul
    pemul_x, pemul_y = placement["p20"]
    pemul_data = interconnect.configure_placement(pemul_x, pemul_y, asm.umult0())

    config_data += mem0_data
    config_data += scan0_data
    config_data += mem1_data
    config_data += scan1_data
    config_data += isect_data
    config_data += memd0_data
    config_data += memd1_data

    config_data += memcf_data
    config_data += memdf_data
    config_data += pemul_data

    skip_addr = interconnect.get_skip_addr()
    config_data = compress_config_data(config_data, skip_compression=skip_addr)

    # Create tester and perform init routine...
    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    tester.zero_inputs()

    # Stall during config
    tester.poke(circuit.interface["stall"], 1)

    for addr, index in config_data:
        tester.configure(addr, index)
        #  tester.config_read(addr)
        tester.eval()

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    # Get flush handle and apply flush to start off app
    flush_x, flush_y = placement["i11"]
    flush = f"glb2io_1_X{flush_x:02X}_Y{flush_y:02X}"
    tester.poke(circuit.interface[flush], 1)
    tester.eval()
    tester.step(2)
    tester.poke(circuit.interface[flush], 0)
    tester.eval()

    # Just set final ready to always 1 for simplicity...
    readyin_x, readyin_y = placement["i12"]
    readyin = f"glb2io_1_X{readyin_x:02X}_Y{readyin_y:02X}"

    pop_x, pop_y = placement["i35"]
    pop = f"glb2io_1_X{pop_x:02X}_Y{pop_y:02X}"

    cvalid_x, cvalid_y = placement["i51"]
    cvalid = f"io2glb_1_X{cvalid_x:02X}_Y{cvalid_y:02X}"
    cdata_x, cdata_y = placement["I53"]
    cdata = f"io2glb_16_X{cdata_x:02X}_Y{cdata_y:02X}"

    dvalid_x, dvalid_y = placement["i50"]
    dvalid = f"io2glb_1_X{dvalid_x:02X}_Y{dvalid_y:02X}"
    ddata_x, ddata_y = placement["I52"]
    ddata = f"io2glb_16_X{ddata_x:02X}_Y{ddata_y:02X}"

    eos_out_x, eos_out_y = placement["i10"]
    eos_out = f"io2glb_1_X{eos_out_x:02X}_Y{eos_out_y:02X}"

    for i in range(num_cycles):
        tester.poke(circuit.interface[readyin], 1)
        tester.poke(circuit.interface[pop], 1)
        tester.eval()

        # If we have valid, print the two datas
        tester_if = tester._if(circuit.interface[cvalid])
        tester_if.print("COORD: %d, VAL: %d\n", circuit.interface[cdata], circuit.interface[ddata])
        if_eos_finish = tester._if(circuit.interface[eos_out])
        if_eos_finish.print("EOS IS HIGH\n")

        # tester_if._else().print("")
        # tester.expect(circuit.interface[data_out], out_data[0][i])
        # toggle the clock
        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)

    return out_coord, out_data


def check_results(res1, res2):
    for key, value in res1.items():
        print(f"RES1\n{key}:\t{value}")
    for key, value in res2.items():
        print(f"RES2\n{key}:\t{value}")
    common_keys = set(res1.keys()).intersection(res2.keys())
    no_mismatch = True
    # Go through each signal
    for key in common_keys:
        # Check if same length
        if len(res1[key]) != len(res2[key]):
            no_mismatch = False
            print(f"Length mismatch on {key}. {len(res1[key])} != {len(res2[key])}")
            print("Going to next list")
        else:
            for i in range(len(res1[key])):
                if res1[key][i] != res2[key][i]:
                    no_mismatch = False
                    print(f"Value mismatch on {key}. {res1[key][i]} != {res2[key][i]}")
                    break
    return no_mismatch


def run_test(len1, len2, num_match, value_limit=100, dump_dir="mek_dump", log_name="xrun.log", trace=False):
    rand.seed(0)
    seqA, seqB = get_sparse_sequences(len1, len2, num_match, value_limit)
    out_coord, out_data = spVspV_test(trace=trace,
                                      run_tb=run_tb_fn,
                                      cwd=dump_dir,
                                      data0=seqA,
                                      data1=seqB)

    out_coord = list(out_coord)
    for i in range(len(out_coord)):
        print(f"EXP_COORD: {out_coord[i]}, EXP_DATA {out_data[i]}")

    results_file = dump_dir + "/" + log_name
    # Values should be in dump_dir/xrun.log
    loglines = None
    with open(results_file, 'r') as rf:
        loglines = rf.readlines()

    assert loglines is not None, "Error extracting simulation log..."
    check_lines = [x for x in loglines if "COORD" in x]
    # split_lines = [re.split('[,\s\t]+', x.strip()) for x in check_lines]
    split_lines = [re.split('[, \t]+', x.strip()) for x in check_lines]
    coord_sim = [int(x[1]) for x in split_lines]
    data_sim = [int(x[3]) for x in split_lines]

    expected_results = {
        "coord": out_coord,
        "data": out_data
    }
    sim_results = {
        "coord": coord_sim,
        "data": data_sim
    }

    match = check_results(expected_results, sim_results)

    if match:
        print("SUCCESS: SIM MATCHES!")
    else:
        print("ERROR: MISMATCH BETWEEN SIM AND EXPECTED!")


def spVspV_regress(dump_dir="muk_dump", log_name="xrun.log", trace=False):

    out_file = open("test_results.txt", "w+")
    value_limit = 4096
    num_mismatch = 0

    # Create sequence class length generators
    classA = SparseSequenceGenerator()
    classB = SparseSequenceGenerator()

    num_per_class = 5
    rand.seed(0)

    # Iterate through the different combinations of class constraints
    for classA_const in range(len(SparseSequenceConstraints)):
        classA.set_constraint_class(SparseSequenceConstraints(classA_const + 1))
        for classB_const in range(len(SparseSequenceConstraints)):
            classB.set_constraint_class(SparseSequenceConstraints(classB_const + 1))
            for test in range(num_per_class):
                len1 = classA.get_length()
                len2 = classB.get_length()
                smaller_len = len1
                if len2 < len1:
                    smaller_len = len2
                num_match = rand.randint(0, smaller_len)
                print(f"\n\n\n\n\n\nNEW TEST\nlen1={len1}\nlen2={len2}\nnum_match={num_match}")
                success = run_test(len1, len2, num_match, value_limit,
                                   dump_dir=dump_dir, log_name=log_name, trace=trace)
                report_msg = ""
                if success is False:
                    report_msg = f"REPORT: FAILURE: len1={len1}, len2={len2}, num_match={num_match}"
                    num_mismatch += 1
                else:
                    report_msg = f"REPORT: SUCCESS: len1={len1}, len2={len2}, num_match={num_match}"

                print(report_msg)
                out_file.write(report_msg + "\n")

    print(f"\n\n\nNum Mismatches: {num_mismatch}\n\n\n")


def scanner_test_new(trace, run_tb, cwd):

    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=[ScannerCore])

    netlist = {
        # Scanner to I/O
        "e0": [("s4", "data_out"), ("I0", "f2io_16")],
        "e1": [("s4", "valid_out"), ("i1", "f2io_1")],
        "e2": [("s4", "eos_out"), ("i2", "f2io_1")],
        "e3": [("i3", "io2f_1"), ("s4", "ready_in")],
        # Scanner to Mem
        "e4": [("m5", "data_out_0"), ("s4", "data_in")],
        "e5": [("m5", "valid_out_0"), ("s4", "valid_in")],
        "e6": [("s4", "addr_out"), ("m5", "addr_in_0")],
        "e7": [("s4", "ready_out"), ("m5", "ren_in_0")],
        "e8": [("i6", "io2f_1"), ("s4", "flush")],
        "e9": [("i6", "io2f_1"), ("m5", "flush")]
    }

    bus = {"e0": 16,
           "e1": 1,
           "e2": 1,
           "e3": 1,
           "e4": 16,
           "e5": 1,
           "e6": 16,
           "e7": 1,
           "e8": 1,
           "e9": 1
           }

    placement, routing = pnr(interconnect, (netlist, bus), cwd=cwd)
    config_data = interconnect.get_route_bitstream(routing)

    ptr_0 = 0
    val_0 = 0

    ptr_eos = 12
    val_eos = 0

    data_0 = (ptr_0 << 8) | val_0
    data_1 = (ptr_eos << 8) | val_eos

    data = [data_0, data_1, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    # data_len = len(data)
    inner_dim_offset = 4
    max_outer_dim = 1

    # Get configuration
    mem_x, mem_y = placement["m5"]
    mem_data = interconnect.configure_placement(mem_x, mem_y, {"config": ["mek", {"init": data}]})
    scan_x, scan_y = placement["s4"]
    scan_data = interconnect.configure_placement(scan_x, scan_y, (inner_dim_offset, max_outer_dim, 1, 1))
    config_data += scan_data
    config_data += mem_data
    skip_addr = interconnect.get_skip_addr()
    config_data = compress_config_data(config_data, skip_compression=skip_addr)

    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    tester.zero_inputs()

    tester.poke(circuit.interface["stall"], 1)

    flush_x, flush_y = placement["i6"]
    flush = f"glb2io_1_X{flush_x:02X}_Y{flush_y:02X}"

    for addr, index in config_data:
        tester.configure(addr, index)
        #  tester.config_read(addr)
        tester.eval()

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    # Now flush to synchronize everybody
    tester.poke(circuit.interface[flush], 1)
    tester.eval()
    tester.step(2)
    tester.poke(circuit.interface[flush], 0)
    tester.eval()

    data_out_x, data_out_y = placement["I0"]
    data_out = f"io2glb_16_X{data_out_x:02X}_Y{data_out_y:02X}"

    valid_x, valid_y = placement["i1"]
    valid = f"io2glb_1_X{valid_x:02X}_Y{valid_y:02X}"
    eos_x, eos_y = placement["i2"]
    eos = f"io2glb_1_X{eos_x:02X}_Y{eos_y:02X}"
    readyin_x, readyin_y = placement["i3"]
    readyin = f"glb2io_1_X{readyin_x:02X}_Y{readyin_y:02X}"

    val = 1
    for i in range(50):
        tester.poke(circuit.interface[readyin], (i > 25))
        tester.eval()
        # tester.expect(circuit.interface[data_out], out_data[0][i])
        # toggle the clock
        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)


def compress_matrix(matrix, row=True):
    size = len(matrix)
    compressed_rows = []
    compressed_indices = []

    addr = 0
    outer = []
    ptr = []
    inner = []
    data = []

    for i in range(size):
        compressed_indices.append([x for x, y in enumerate(matrix[i]) if y > 0])
        compressed_rows.append([x for x in matrix[i] if x > 0])
        if len(compressed_rows[i]) != 0:
            outer.append(i)
            ptr.append(addr)
            for j in range(len(compressed_rows[i])):
                data.append(compressed_rows[i][j])
                inner.append(compressed_indices[i][j])
            addr += len(compressed_rows[i])
            # inner.append(i)

    # Append end of stream
    outer.append(0)
    ptr.append(addr)
    print(f"{outer}, {ptr}, {inner}, {data}")

    return (outer, ptr, inner, data)


def prep_matrix_2_sram(outer, ptr, inner, compressed=True):

    assert compressed is True, "Only compressed, compressed format supported"
    stream = []
    # Assemble the control words as (ptr,outer) in memory
    for i in range(len(outer)):
        stream.append((outer[i] | (ptr[i] << 8)))
    # Align after the control words to get inner_offset
    stream_aligned = align_data(stream, 4)
    inner_offset = len(stream_aligned)
    stream_aligned += inner
    # Align once more so it goes to sram
    stream_aligned = align_data(stream_aligned, 4)
    return (inner_offset, stream_aligned)


def scanner_test_new_matrix(trace, run_tb, cwd):

    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=[ScannerCore])

    netlist = {
        # Scanner to I/O
        "e0": [("s4", "data_out"), ("I0", "f2io_16")],
        "e1": [("s4", "valid_out"), ("i1", "f2io_1")],
        "e2": [("s4", "eos_out"), ("i2", "f2io_1")],
        "e3": [("i3", "io2f_1"), ("s4", "ready_in")],
        # Scanner to Mem
        "e4": [("m5", "data_out_0"), ("s4", "data_in")],
        "e5": [("m5", "valid_out_0"), ("s4", "valid_in")],
        "e6": [("s4", "addr_out"), ("m5", "addr_in_0")],
        "e7": [("s4", "ready_out"), ("m5", "ren_in_0")],
        "e8": [("i6", "io2f_1"), ("s4", "flush")],
        "e9": [("i6", "io2f_1"), ("m5", "flush")]
    }

    bus = {"e0": 16,
           "e1": 1,
           "e2": 1,
           "e3": 1,
           "e4": 16,
           "e5": 1,
           "e6": 16,
           "e7": 1,
           "e8": 1,
           "e9": 1
           }

    placement, routing = pnr(interconnect, (netlist, bus), cwd=cwd)
    config_data = interconnect.get_route_bitstream(routing)

    ptr_0 = 0
    val_0 = 0

    ptr_eos = 12
    val_eos = 0

    # data_0 = (ptr_0 << 8) | val_0
    # data_1 = (ptr_eos << 8) | val_eos

    matrix_size = 4
    matrix = [[1, 2, 0, 0], [3, 0, 0, 4], [0, 0, 0, 0], [0, 1, 0, 2]]
    (outer, ptr, inner, matrix_vals) = compress_matrix(matrix, row=True)
    (inner_offset, data) = prep_matrix_2_sram(outer, ptr, inner)
    # data_len = len(data)
    inner_dim_offset = inner_offset
    max_outer_dim = matrix_size

    # Get configuration
    mem_x, mem_y = placement["m5"]
    mem_data = interconnect.configure_placement(mem_x, mem_y, {"config": ["mek", {"init": data}]})
    scan_x, scan_y = placement["s4"]
    scan_data = interconnect.configure_placement(scan_x, scan_y, (inner_dim_offset, max_outer_dim, 1, 4))
    config_data += scan_data
    config_data += mem_data
    skip_addr = interconnect.get_skip_addr()
    config_data = compress_config_data(config_data, skip_compression=skip_addr)

    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    tester.zero_inputs()

    tester.poke(circuit.interface["stall"], 1)

    flush_x, flush_y = placement["i6"]
    flush = f"glb2io_1_X{flush_x:02X}_Y{flush_y:02X}"

    for addr, index in config_data:
        tester.configure(addr, index)
        #  tester.config_read(addr)
        tester.eval()

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    # Now flush to synchronize everybody
    tester.poke(circuit.interface[flush], 1)
    tester.eval()
    tester.step(2)
    tester.poke(circuit.interface[flush], 0)
    tester.eval()

    data_out_x, data_out_y = placement["I0"]
    data_out = f"io2glb_16_X{data_out_x:02X}_Y{data_out_y:02X}"

    valid_x, valid_y = placement["i1"]
    valid = f"io2glb_1_X{valid_x:02X}_Y{valid_y:02X}"
    eos_x, eos_y = placement["i2"]
    eos = f"io2glb_1_X{eos_x:02X}_Y{eos_y:02X}"
    readyin_x, readyin_y = placement["i3"]
    readyin = f"glb2io_1_X{readyin_x:02X}_Y{readyin_y:02X}"

    val = 1
    for i in range(50):
        tester.poke(circuit.interface[readyin], (i > 25))
        tester.eval()
        # tester.expect(circuit.interface[data_out], out_data[0][i])
        # toggle the clock
        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)


def mem_scanner_intersect_test_new_matrix(trace, run_tb, cwd):

    chip_size = 4
    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=[ScannerCore, IntersectCore])

    netlist = {
        # Intersect to DATA MEM
        "e0": [("j0", "coord_out"), ("r15", "reg")],
        "e1": [("r15", "reg"), ("I6", "f2io_16")],
        "e2": [("j0", "pos_out_0"), ("m13", "addr_in_0")],
        "e3": [("j0", "pos_out_1"), ("m14", "addr_in_0")],
        "e4": [("j0", "valid_out"), ("m13", "ren_in_0"), ("m14", "ren_in_0")],
        "e5": [("j0", "eos_out"), ("r16", "reg")],
        "e6": [("r16", "reg"), ("i10", "f2io_1")],
        # Intersect to SCAN
        "e7": [("j0", "ready_out_0"), ("s1", "ready_in")],
        "e8": [("j0", "ready_out_1"), ("s2", "ready_in")],
        # Flush
        "e9": [("i11", "io2f_1"),
               ("j0", "flush"),
               ("s1", "flush"),
               ("s2", "flush"),
               ("m3", "flush"),
               ("m4", "flush"),
               ("m13", "flush"),
               ("m14", "flush")],
        # I/O to Intersect
        "e10": [("s1", "data_out"), ("j0", "coord_in_0")],
        "e11": [("s2", "data_out"), ("j0", "coord_in_1")],
        "e12": [("s1", "valid_out"), ("j0", "valid_in_0")],
        "e13": [("s2", "valid_out"), ("j0", "valid_in_1")],
        "e14": [("s1", "eos_out"), ("j0", "eos_in_0")],
        "e15": [("s2", "eos_out"), ("j0", "eos_in_1")],
        # This should technically be the only input I/O
        "e16": [("i12", "io2f_1"), ("j0", "ready_in")],
        # Mem to Scanner
        "e17": [("m3", "data_out_0"), ("s1", "data_in")],
        "e18": [("m4", "data_out_0"), ("s2", "data_in")],
        "e19": [("m3", "valid_out_0"), ("s1", "valid_in")],
        "e20": [("m4", "valid_out_0"), ("s2", "valid_in")],
        # Scanner to Mem
        "e21": [("s1", "addr_out"), ("m3", "addr_in_0")],
        "e22": [("s2", "addr_out"), ("m4", "addr_in_0")],
        "e23": [("s1", "ready_out"), ("m3", "ren_in_0")],
        "e24": [("s2", "ready_out"), ("m4", "ren_in_0")],
        # Data mem to IO (data, valid)
        "e25": [("m13", "data_out_0"), ("I17", "f2io_16")],
        "e26": [("m14", "data_out_0"), ("I18", "f2io_16")],
        "e27": [("m13", "valid_out_0"), ("i19", "f2io_1")],
        "e28": [("m14", "valid_out_0"), ("i20", "f2io_1")],
        "e29": [("s1", "payload_ptr"), ("j0", "payload_ptr_0")],
        "e30": [("s2", "payload_ptr"), ("j0", "payload_ptr_1")],

    }

    bus = {
        "e0": 16,
        "e1": 16,
        "e2": 16,
        "e3": 16,
        "e4": 1,
        "e5": 1,
        "e6": 1,
        "e7": 1,
        "e8": 1,
        "e9": 1,
        "e10": 16,
        "e11": 16,
        "e12": 1,
        "e13": 1,
        "e14": 1,
        "e15": 1,
        "e16": 1,
        "e17": 16,
        "e18": 16,
        "e19": 1,
        "e20": 1,
        "e21": 16,
        "e22": 16,
        "e23": 1,
        "e24": 1,
        "e25": 16,
        "e26": 16,
        "e27": 1,
        "e28": 1,
        "e29": 16,
        "e30": 16,
    }

    placement, routing = pnr(interconnect, (netlist, bus), cwd=cwd)
    config_data = interconnect.get_route_bitstream(routing)

    # data0 = [1, 2, 6, 10]
    # data0_len = len(data0)
    # data1 = [3, 6, 8, 0]
    # # Need to provide 4 or else the machine doesn't work, so subtracting 1 here...
    # data1_len = len(data1) - 1

    # datad0 = [11, 12, 13, 14]
    # datad1 = [15, 16, 17, 18]

    matrix_size = 4
    matrix = [[1, 2, 0, 0], [3, 0, 0, 4], [0, 0, 0, 0], [0, 5, 0, 6]]
    (outer_r, ptr_r, inner_r, matrix_vals_r) = compress_matrix(matrix, row=True)
    (inner_offset_r, data_r) = prep_matrix_2_sram(outer_r, ptr_r, inner_r)
    (outer_c, ptr_c, inner_c, matrix_vals_c) = compress_matrix(matrix, row=False)
    (inner_offset_c, data_c) = prep_matrix_2_sram(outer_c, ptr_c, inner_c)
    # data_len = len(data)
    max_outer_dim = matrix_size

    # Get configuration
    mem0_x, mem0_y = placement["m3"]
    mem0_data = interconnect.configure_placement(mem0_x, mem0_y, {"config": ["mek", {"init": data_r}]})
    scan0_x, scan0_y = placement["s1"]
    scan0_data = interconnect.configure_placement(scan0_x, scan0_y, (inner_offset_r, max_outer_dim, 1, 4))
    mem1_x, mem1_y = placement["m4"]
    mem1_data = interconnect.configure_placement(mem1_x, mem1_y, {"config": ["mek", {"init": data_c}]})
    scan1_x, scan1_y = placement["s2"]
    # Now scan just the first row as a pretend column...
    scan1_data = interconnect.configure_placement(scan1_x, scan1_y, (inner_offset_c, max_outer_dim, 0, 4))
    isect_x, isect_y = placement["j0"]
    isect_data = interconnect.configure_placement(isect_x, isect_y, 5)

    memd0_x, memd0_y = placement["m13"]
    memd0_data = interconnect.configure_placement(memd0_x,
                                                  memd0_y,
                                                  {"config": ["mek", {"init": align_data(matrix_vals_r, 4)}]})
    memd1_x, memd1_y = placement["m14"]
    memd1_data = interconnect.configure_placement(memd1_x,
                                                  memd1_y,
                                                  {"config": ["mek", {"init": align_data(matrix_vals_c, 4)}]})

    config_data += mem0_data
    config_data += scan0_data
    config_data += mem1_data
    config_data += scan1_data
    config_data += isect_data
    config_data += memd0_data
    config_data += memd1_data
    skip_addr = interconnect.get_skip_addr()
    config_data = compress_config_data(config_data, skip_compression=skip_addr)

    print("BITSTREAM START")
    for addr, config in config_data:
        print("{0:08X} {1:08X}".format(addr, config))
    print("BITSTREAM END")

    # Create tester and perform init routine...
    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    tester.zero_inputs()

    # Stall during config
    tester.poke(circuit.interface["stall"], 1)

    for addr, index in config_data:
        tester.configure(addr, index)
        #  tester.config_read(addr)
        tester.eval()

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    # Get flush handle and apply flush to start off app
    flush_x, flush_y = placement["i11"]
    flush = f"glb2io_1_X{flush_x:02X}_Y{flush_y:02X}"
    tester.poke(circuit.interface[flush], 1)
    tester.eval()
    tester.step(2)
    tester.poke(circuit.interface[flush], 0)
    tester.eval()

    # Just set final ready to always 1 for simplicity...
    readyin_x, readyin_y = placement["i12"]
    readyin = f"glb2io_1_X{readyin_x:02X}_Y{readyin_y:02X}"

    for i in range(50):
        tester.poke(circuit.interface[readyin], 1)
        tester.eval()
        # tester.expect(circuit.interface[data_out], out_data[0][i])
        # toggle the clock
        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)


def spMspV_test(trace, run_tb, cwd):
    # Streams and code to create them and align them
    num_cycles = 50
    chip_size = 8
    num_tracks = 5

    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=num_tracks,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=[ScannerCore, IntersectCore, PeakCore, RegCore])

    # Created CGRA with all cores!

    netlist = {
        # Intersect to DATA MEM
        "e0": [("j0", "coord_out"), ("r15", "reg")],
        "e1": [("r15", "reg"), ("m32", "data_in_0")],
        "e2": [("j0", "pos_out_0"), ("m13", "addr_in_0")],
        "e3": [("j0", "pos_out_1"), ("m14", "addr_in_0")],
        "e4": [("j0", "valid_out"), ("m13", "ren_in_0"), ("m14", "ren_in_0")],
        "e5": [("j0", "eos_out"), ("r16", "reg")],
        "e6": [("r16", "reg"), ("i10", "f2io_1"), ("R99", "flush"), ("p101", "bit2")],
        # Intersect to SCAN
        "e7": [("j0", "ready_out_0"), ("s1", "ready_in")],
        "e8": [("j0", "ready_out_1"), ("s2", "ready_in")],
        # Flush
        "e9": [("i11", "io2f_1"),
               ("j0", "flush"),
               ("s1", "flush"),
               ("s2", "flush"),
               ("m3", "flush"),
               ("m4", "flush"),
               ("m13", "flush"),
               ("m14", "flush"),
               ("m31", "flush"),
               ("m32", "flush")],
        # I/O to Intersect
        "e10": [("s1", "data_out"), ("j0", "coord_in_0")],
        "e11": [("s2", "data_out"), ("j0", "coord_in_1")],
        "e12": [("s1", "valid_out"), ("j0", "valid_in_0")],
        "e13": [("s2", "valid_out"), ("j0", "valid_in_1")],
        "e14": [("s1", "eos_out"), ("j0", "eos_in_0")],
        "e15": [("s2", "eos_out"), ("j0", "eos_in_1")],
        # This should technically be the only input I/O
        "e16": [("i12", "io2f_1"), ("j0", "ready_in")],
        # Mem to Scanner
        "e17": [("m3", "data_out_0"), ("s1", "data_in")],
        "e18": [("m4", "data_out_0"), ("s2", "data_in")],
        "e19": [("m3", "valid_out_0"), ("s1", "valid_in")],
        "e20": [("m4", "valid_out_0"), ("s2", "valid_in")],
        # Scanner to Mem
        "e21": [("s1", "addr_out"), ("m3", "addr_in_0")],
        "e22": [("s2", "addr_out"), ("m4", "addr_in_0")],
        "e23": [("s1", "ready_out"), ("m3", "ren_in_0")],
        "e24": [("s2", "ready_out"), ("m4", "ren_in_0")],
        # Data mem to PE
        "e25": [("m13", "data_out_0"), ("p20", "data0")],
        "e26": [("m14", "data_out_0"), ("p20", "data1")],
        # MEM Fifo result...
        "e27": [("p100", "alu_res"), ("m31", "data_in_0")],
        "e29": [("R99", "valid_out"), ("p101", "bit1")],
        "e30": [("i35", "io2f_1"), ("m31", "ren_in_0"), ("m32", "ren_in_0")],
        # Get mem outputs
        "e31": [("m31", "valid_out_0"), ("i50", "f2io_1")],
        "e32": [("m32", "valid_out_0"), ("i51", "f2io_1")],
        "e33": [("m31", "data_out_0"), ("I52", "f2io_16")],
        "e34": [("m32", "data_out_0"), ("I53", "f2io_16")],
        "e35": [("s1", "payload_ptr"), ("j0", "payload_ptr_0")],
        "e36": [("s2", "payload_ptr"), ("j0", "payload_ptr_1")],
        "e37": [("p100", "alu_res"), ("R99", "data_in")],
        "e38": [("R99", "data_out"), ("p100", "data0")],
        "e39": [("p20", "alu_res"), ("p100", "data1")],
        "e40": [("m14", "valid_out_0"), ("R99", "write_en")],
        "e41": [("p101", "res_p"), ("m31", "wen_in_0")],
        "e42": [("p101", "res_p"), ("m32", "wen_in_0")],
    }

    bus = {
        "e0": 16,
        "e1": 16,
        "e2": 16,
        "e3": 16,
        "e4": 1,
        "e5": 1,
        "e6": 1,
        "e7": 1,
        "e8": 1,
        "e9": 1,
        "e10": 16,
        "e11": 16,
        "e12": 1,
        "e13": 1,
        "e14": 1,
        "e15": 1,
        "e16": 1,
        "e17": 16,
        "e18": 16,
        "e19": 1,
        "e20": 1,
        "e21": 16,
        "e22": 16,
        "e23": 1,
        "e24": 1,
        "e25": 16,
        "e26": 16,
        "e27": 16,
        # "e28": 1,
        "e29": 1,
        "e30": 1,
        "e31": 1,
        "e32": 1,
        "e33": 16,
        "e34": 16,
        "e35": 16,
        "e36": 16,
        "e37": 16,
        "e38": 16,
        "e39": 16,
        "e40": 1,
        "e41": 1,
        "e42": 1,
    }

    placement, routing = pnr(interconnect, (netlist, bus), cwd=cwd)
    config_data = interconnect.get_route_bitstream(routing)

    matrix_size = 4
    matrix = [[1, 2, 0, 0], [3, 0, 0, 4], [0, 0, 0, 0], [0, 5, 0, 6]]
    (outer_r, ptr_r, inner_r, matrix_vals_r) = compress_matrix(matrix, row=True)
    (inner_offset_r, data_r) = prep_matrix_2_sram(outer_r, ptr_r, inner_r)
    (outer_c, ptr_c, inner_c, matrix_vals_c) = compress_matrix(matrix, row=False)
    (inner_offset_c, data_c) = prep_matrix_2_sram(outer_c, ptr_c, inner_c)
    # data_len = len(data)
    max_outer_dim = matrix_size

    # Get configuration
    mem0_x, mem0_y = placement["m3"]
    mem0_data = interconnect.configure_placement(mem0_x, mem0_y, {"config": ["mek", {"init": data_r}]})
    scan0_x, scan0_y = placement["s1"]
    scan0_data = interconnect.configure_placement(scan0_x, scan0_y, (inner_offset_r, max_outer_dim, 1, 4))
    mem1_x, mem1_y = placement["m4"]
    mem1_data = interconnect.configure_placement(mem1_x, mem1_y, {"config": ["mek", {"init": data_c}]})
    scan1_x, scan1_y = placement["s2"]
    # Now scan just the first row as a pretend column...
    scan1_data = interconnect.configure_placement(scan1_x, scan1_y, (inner_offset_c, max_outer_dim, 0, 4))
    isect_x, isect_y = placement["j0"]
    isect_data = interconnect.configure_placement(isect_x, isect_y, 5)

    memd0_x, memd0_y = placement["m13"]
    memd0_data = interconnect.configure_placement(memd0_x,
                                                  memd0_y,
                                                  {"config": ["mek", {"init": align_data(matrix_vals_r, 4)}]})
    memd1_x, memd1_y = placement["m14"]
    memd1_data = interconnect.configure_placement(memd1_x,
                                                  memd1_y,
                                                  {"config": ["mek", {"init": align_data(matrix_vals_c, 4)}]})

    # This app should basically emit all the rows * + eos, then we can make accum in network

    # Configure these guys as fifos...
    memcf_x, memcf_y = placement["m32"]
    memcf_data = interconnect.configure_placement(memcf_x, memcf_y, "fifo")
    memdf_x, memdf_y = placement["m31"]
    memdf_data = interconnect.configure_placement(memdf_x, memdf_y, "fifo")

    # PE as mul
    pemul_x, pemul_y = placement["p20"]
    pemul_data = interconnect.configure_placement(pemul_x, pemul_y, asm.umult0())

    # PE as add
    peadd_x, peadd_y = placement["p100"]
    peadd_data = interconnect.configure_placement(peadd_x, peadd_y, asm.add())

    # PE as AND
    peand_x, peand_y = placement["p101"]
    peand_data = interconnect.configure_placement(peand_x, peand_y, asm.lut_and())

    # REG
    reg_x, reg_y = placement["R99"]
    reg_data = interconnect.configure_placement(reg_x, reg_y, (0, 0, 0, 0), pnr_tag="R")

    config_data += mem0_data
    config_data += scan0_data
    config_data += mem1_data
    config_data += scan1_data
    config_data += isect_data
    config_data += memd0_data
    config_data += memd1_data
    config_data += memcf_data
    config_data += memdf_data
    config_data += pemul_data
    config_data += peadd_data
    config_data += peand_data
    config_data += reg_data

    skip_addr = interconnect.get_skip_addr()
    config_data = compress_config_data(config_data, skip_compression=skip_addr)

    # Create tester and perform init routine...
    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    tester.zero_inputs()

    # Stall during config
    tester.poke(circuit.interface["stall"], 1)

    for addr, index in config_data:
        tester.configure(addr, index)
        #  tester.config_read(addr)
        tester.eval()

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    # Get flush handle and apply flush to start off app
    flush_x, flush_y = placement["i11"]
    flush = f"glb2io_1_X{flush_x:02X}_Y{flush_y:02X}"
    tester.poke(circuit.interface[flush], 1)
    tester.eval()
    tester.step(2)
    tester.poke(circuit.interface[flush], 0)
    tester.eval()

    # Just set final ready to always 1 for simplicity...
    readyin_x, readyin_y = placement["i12"]
    readyin = f"glb2io_1_X{readyin_x:02X}_Y{readyin_y:02X}"

    pop_x, pop_y = placement["i35"]
    pop = f"glb2io_1_X{pop_x:02X}_Y{pop_y:02X}"

    cvalid_x, cvalid_y = placement["i51"]
    cvalid = f"io2glb_1_X{cvalid_x:02X}_Y{cvalid_y:02X}"
    cdata_x, cdata_y = placement["I53"]
    cdata = f"io2glb_16_X{cdata_x:02X}_Y{cdata_y:02X}"

    dvalid_x, dvalid_y = placement["i50"]
    dvalid = f"io2glb_1_X{dvalid_x:02X}_Y{dvalid_y:02X}"
    ddata_x, ddata_y = placement["I52"]
    ddata = f"io2glb_16_X{ddata_x:02X}_Y{ddata_y:02X}"

    eos_out_x, eos_out_y = placement["i10"]
    eos_out = f"io2glb_1_X{eos_out_x:02X}_Y{eos_out_y:02X}"

    for i in range(num_cycles):
        tester.poke(circuit.interface[readyin], 1)
        tester.poke(circuit.interface[pop], 1)
        tester.eval()

        # If we have valid, print the two datas
        tester_if = tester._if(circuit.interface[cvalid])
        tester_if.print("COORD: %d, VAL: %d\n", circuit.interface[cdata], circuit.interface[ddata])
        if_eos_finish = tester._if(circuit.interface[eos_out])
        if_eos_finish.print("EOS IS HIGH\n")

        # tester_if._else().print("")
        # tester.expect(circuit.interface[data_out], out_data[0][i])
        # toggle the clock

        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)

    # return out_coord, out_data


def scan_matrix_hierarchical(trace, run_tb, cwd):
    # Streams and code to create them and align them
    num_cycles = 50
    chip_size = 6
    num_tracks = 5

    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=num_tracks,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=[ScannerCore, IntersectCore])

    # Create netlist builder and register the needed cores...
    nlb = NetlistBuilder(interconnect=interconnect, cwd=cwd)
    scanner_root = nlb.register_core("scanner")
    scanner_rows = nlb.register_core("scanner")
    mem_root = nlb.register_core("memtile")
    mem_rows = nlb.register_core("memtile")
    mem_vals = nlb.register_core("memtile")
    reg_inner_coord = nlb.register_core("register")
    reg_eos_out = nlb.register_core("register")
    ready_in = nlb.register_core("io_1")
    valid_out = nlb.register_core("io_1")
    eos_out = nlb.register_core("io_1")
    flush_in = nlb.register_core("io_1")
    coord_out = nlb.register_core("io_16")
    val_out = nlb.register_core("io_16")

    flushable = [scanner_root, scanner_rows, mem_root, mem_rows, mem_vals]

    connections = []
    scan_root_to_mem_root = [
        ([(scanner_root, "addr_out"), (mem_root, "addr_in_0")], 16),
        ([(scanner_root, "ready_out"), (mem_root, "ren_in_0")], 1),
        ([(mem_root, "data_out_0"), (scanner_root, "data_in")], 16),
        ([(mem_root, "valid_out_0"), (scanner_root, "valid_in")], 1)
    ]

    scan_root_to_scan_rows = [
        ([(scanner_root, "pos_out"), (scanner_rows, "us_pos_in")], 16),
        ([(scanner_root, "valid_out"), (scanner_rows, "us_valid_in")], 1),
        ([(scanner_root, "eos_out"), (scanner_rows, "us_eos_in")], 1),
        ([(scanner_rows, "us_ready_out"), (scanner_root, "ready_in")], 1)
    ]

    scan_rows_to_mem_rows = [
        ([(scanner_rows, "addr_out"), (mem_rows, "addr_in_0")], 16),
        ([(scanner_rows, "ready_out"), (mem_rows, "ren_in_0")], 1),
        ([(mem_rows, "data_out_0"), (scanner_rows, "data_in")], 16),
        ([(mem_rows, "valid_out_0"), (scanner_rows, "valid_in")], 1)
    ]

    scan_rows_to_mem_vals = [
        ([(scanner_rows, "pos_out"), (mem_vals, "addr_in_0")], 16),
        ([(scanner_rows, "valid_out"), (mem_vals, "ren_in_0")], 1)
    ]

    # Outputs delayed EOS, inner coord, takes in a ready from the IO
    scan_rows_to_io = [
        ([(scanner_rows, "eos_out"), (reg_eos_out, "reg")], 1),
        ([(reg_eos_out, "reg"), (eos_out, "f2io_1")], 1),
        # Register the coord out to pass to out
        ([(scanner_rows, "coord_out"), (reg_inner_coord, "reg")], 16),
        ([(reg_inner_coord, "reg"), (coord_out, "f2io_16")], 16),
        ([(ready_in, "io2f_1"), (scanner_rows, "ready_in")], 1)
    ]

    mem_to_out = [
        ([(mem_vals, "data_out_0"), (val_out, "f2io_16")], 16),
        ([(mem_vals, "valid_out_0"), (valid_out, "f2io_1")], 1)
    ]

    # Add all flushes...
    flush_connection = [([(flush_in, "io2f_1"), *[(x, "flush") for x in flushable]], 1)]

    connections += scan_root_to_mem_root
    connections += scan_root_to_scan_rows
    connections += scan_rows_to_mem_rows
    connections += scan_rows_to_mem_vals
    connections += scan_rows_to_io
    connections += mem_to_out
    connections += flush_connection

    nlb.add_connections(connections=connections)
    # (netlist, bus) = nlb.get_full_info()
    nlb.get_route_config()

    # placement, routing = pnr(interconnect, (netlist, bus), cwd=cwd)
    # config_data = interconnect.get_route_bitstream(routing)

    matrix_size = 4
    matrix = [[1, 2, 0, 0], [3, 0, 0, 4], [0, 0, 0, 0], [0, 5, 0, 6]]
    (outer, ptr, inner, matrix_vals) = compress_matrix(matrix, row=True)
    root = [0, 3]
    root = align_data(root, 4)
    outer = align_data(outer, 4)
    ptr = align_data(ptr, 4)
    inner = align_data(inner, 4)
    inner_offset_root = len(root)
    matrix_vals = align_data(matrix_vals, 4)

    root_data = root + outer
    inner_offset_row = len(ptr)
    row_data = ptr + inner

    # data_len = len(data)
    max_outer_dim = matrix_size

    nlb.configure_tile(scanner_root, (inner_offset_root, max_outer_dim, 0, 1, 1))
    nlb.configure_tile(scanner_rows, (inner_offset_row, max_outer_dim, 0, 4, 0))
    nlb.configure_tile(mem_root, {"config": ["mek", {"init": root_data}]})
    nlb.configure_tile(mem_rows, {"config": ["mek", {"init": row_data}]})
    nlb.configure_tile(mem_vals, {"config": ["mek", {"init": matrix_vals}]})
    # This does some cleanup like partitioning into compressed/uncompressed space
    nlb.finalize_config()

    config_data = nlb.get_config_data()

    # Create tester and perform init routine...
    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    tester.zero_inputs()

    # Stall during config
    tester.poke(circuit.interface["stall"], 1)

    for addr, index in config_data:
        tester.configure(addr, index)
        #  tester.config_read(addr)
        tester.eval()

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    # Get flush handle and apply flush to start off app
    h_flush_in = nlb.get_handle(flush_in, prefix="glb2io_1_")
    tester.poke(circuit.interface[h_flush_in], 1)
    tester.eval()
    tester.step(2)
    tester.poke(circuit.interface[h_flush_in], 0)
    tester.eval()

    h_ready_in = nlb.get_handle(ready_in, prefix="glb2io_1_")
    h_valid_out = nlb.get_handle(valid_out, prefix="io2glb_1_")
    h_eos_out = nlb.get_handle(eos_out, prefix="io2glb_1_")
    h_flush_in = nlb.get_handle(flush_in, prefix="glb2io_1_")
    h_coord_out = nlb.get_handle(coord_out, prefix="io2glb_16_")
    h_val_out = nlb.get_handle(val_out, prefix="io2glb_16_")

    for i in range(num_cycles):
        tester.poke(circuit.interface[h_ready_in], 1)
        # tester.poke(circuit.interface[pop], 1)
        tester.eval()

        # If we have valid, print the two datas
        tester_if = tester._if(circuit.interface[h_valid_out])
        tester_if.print("COORD: %d, VAL: %d\n", circuit.interface[h_coord_out], circuit.interface[h_val_out])
        if_eos_finish = tester._if(circuit.interface[h_eos_out])
        if_eos_finish.print("EOS IS HIGH\n")

        # tester_if._else().print("")
        # tester.expect(circuit.interface[data_out], out_data[0][i])
        # toggle the clock

        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)

    # return out_coord, out_data


def scan_vector_hierarchical(trace, run_tb, cwd):
    # Streams and code to create them and align them
    num_cycles = 50
    chip_size = 6
    num_tracks = 5

    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=num_tracks,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=[ScannerCore, IntersectCore])

    # Create netlist builder and register the needed cores...
    nlb = NetlistBuilder(interconnect=interconnect, cwd=cwd)
    scanner_root = nlb.register_core("scanner")
    mem_root = nlb.register_core("memtile")
    mem_vals = nlb.register_core("memtile")
    reg_inner_coord = nlb.register_core("register")
    reg_eos_out = nlb.register_core("register")
    ready_in = nlb.register_core("io_1")
    valid_out = nlb.register_core("io_1")
    eos_out = nlb.register_core("io_1")
    flush_in = nlb.register_core("io_1")
    coord_out = nlb.register_core("io_16")
    val_out = nlb.register_core("io_16")

    flushable = [scanner_root, mem_root, mem_vals]

    connections = []
    scan_root_to_mem_root = [
        ([(scanner_root, "addr_out"), (mem_root, "addr_in_0")], 16),
        ([(scanner_root, "ready_out"), (mem_root, "ren_in_0")], 1),
        ([(mem_root, "data_out_0"), (scanner_root, "data_in")], 16),
        ([(mem_root, "valid_out_0"), (scanner_root, "valid_in")], 1)
    ]

    scan_root_to_mem_vals = [
        ([(scanner_root, "pos_out"), (mem_vals, "addr_in_0")], 16),
        ([(scanner_root, "valid_out"), (mem_vals, "ren_in_0")], 1)
    ]

    # Outputs delayed EOS, inner coord, takes in a ready from the IO
    scan_root_to_io = [
        ([(scanner_root, "eos_out"), (reg_eos_out, "reg")], 1),
        ([(reg_eos_out, "reg"), (eos_out, "f2io_1")], 1),
        # Register the coord out to pass to out
        ([(scanner_root, "coord_out"), (reg_inner_coord, "reg")], 16),
        ([(reg_inner_coord, "reg"), (coord_out, "f2io_16")], 16),
        ([(ready_in, "io2f_1"), (scanner_root, "ready_in")], 1)
    ]

    mem_to_out = [
        ([(mem_vals, "data_out_0"), (val_out, "f2io_16")], 16),
        ([(mem_vals, "valid_out_0"), (valid_out, "f2io_1")], 1)
    ]

    # Add all flushes...
    flush_connection = [([(flush_in, "io2f_1"), *[(x, "flush") for x in flushable]], 1)]

    connections += scan_root_to_mem_root
    connections += scan_root_to_mem_vals
    connections += scan_root_to_io
    connections += mem_to_out
    connections += flush_connection

    nlb.add_connections(connections=connections)
    # (netlist, bus) = nlb.get_full_info()
    nlb.get_route_config()

    # placement, routing = pnr(interconnect, (netlist, bus), cwd=cwd)
    # config_data = interconnect.get_route_bitstream(routing)

    # vector_len = 14
    # num_nonzero = rand.randint(0, vector_len)
    # vector = [0] * vector_len
    # for i in range(num_nonzero):
    #     vector[i] = rand.randint(0, 25)
    # print(f"vector: {vector}")
    vector = [1, 2, 3, 0, 4, 5, 0, 6, 0]

    outer = []
    matrix_vals = []
    for i in range(len(vector)):
        if vector[i] != 0:
            outer.append(i)
            matrix_vals.append(vector[i])

    # outer = [0, 1, 2, 4, 5, 7]
    # matrix_vals = [1, 2, 3, 4, 5, 6]
    root = [0, len(outer)]

    # matrix = [[1, 2, 0, 0], [3, 0, 0, 4], [0, 0, 0, 0], [0, 5, 0, 6]]
    # (outer, ptr, inner, matrix_vals) = compress_matrix(matrix, row=True)
    root = align_data(root, 4)
    outer = align_data(outer, 4)
    matrix_vals = align_data(matrix_vals, 4)

    print(f"root: {root}\nouter: {outer}\nvalues: {matrix_vals}")
    inner_offset_root = len(root)
    root_data = root + outer

    # data_len = len(data)
    max_outer_dim = 4

    nlb.configure_tile(scanner_root, (inner_offset_root, max_outer_dim, 0, 1, 1))
    nlb.configure_tile(mem_root, {"config": ["mek", {"init": root_data}]})
    nlb.configure_tile(mem_vals, {"config": ["mek", {"init": matrix_vals}]})
    # This does some cleanup like partitioning into compressed/uncompressed space
    nlb.finalize_config()

    config_data = nlb.get_config_data()

    # Create tester and perform init routine...
    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    tester.zero_inputs()

    # Stall during config
    tester.poke(circuit.interface["stall"], 1)

    for addr, index in config_data:
        tester.configure(addr, index)
        #  tester.config_read(addr)
        tester.eval()

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    # Get flush handle and apply flush to start off app
    h_flush_in = nlb.get_handle(flush_in, prefix="glb2io_1_")
    tester.poke(circuit.interface[h_flush_in], 1)
    tester.eval()
    tester.step(2)
    tester.poke(circuit.interface[h_flush_in], 0)
    tester.eval()

    h_ready_in = nlb.get_handle(ready_in, prefix="glb2io_1_")
    h_valid_out = nlb.get_handle(valid_out, prefix="io2glb_1_")
    h_eos_out = nlb.get_handle(eos_out, prefix="io2glb_1_")
    h_flush_in = nlb.get_handle(flush_in, prefix="glb2io_1_")
    h_coord_out = nlb.get_handle(coord_out, prefix="io2glb_16_")
    h_val_out = nlb.get_handle(val_out, prefix="io2glb_16_")

    for i in range(num_cycles):
        tester.poke(circuit.interface[h_ready_in], 1)
        # tester.poke(circuit.interface[pop], 1)
        tester.eval()

        # If we have valid, print the two datas
        tester_if = tester._if(circuit.interface[h_valid_out])
        tester_if.print("COORD: %d, VAL: %d\n", circuit.interface[h_coord_out], circuit.interface[h_val_out])
        if_eos_finish = tester._if(circuit.interface[h_eos_out])
        if_eos_finish.print("EOS IS HIGH\n")

        # tester_if._else().print("")
        # tester.expect(circuit.interface[data_out], out_data[0][i])
        # toggle the clock

        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)


def spM_spV_hierarchical(trace, run_tb, cwd):
    # Streams and code to create them and align them
    num_cycles = 50
    chip_size = 6
    num_tracks = 5

    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=num_tracks,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=[ScannerCore, IntersectCore])

    # Create netlist builder and register the needed cores...
    nlb = NetlistBuilder(interconnect=interconnect, cwd=cwd)

    # Matrix A
    scan_mroot = nlb.register_core("scanner", flushable=True)
    scan_mrows = nlb.register_core("scanner", flushable=True)
    mem_mroot = nlb.register_core("memtile", flushable=True)
    mem_mrows = nlb.register_core("memtile", flushable=True)
    mem_mvals = nlb.register_core("memtile", flushable=True)

    # Vector B
    scan_vroot = nlb.register_core("scanner", flushable=True)
    mem_vroot = nlb.register_core("memtile", flushable=True)
    mem_vvals = nlb.register_core("memtile", flushable=True)

    # Intersect the two...
    isect = nlb.register_core("intersect", flushable=True)

    reg_coord = nlb.register_core("register")
    reg_eos_out = nlb.register_core("register")
    reg_valid_out = nlb.register_core("register")

    valid_out = nlb.register_core("io_1")
    eos_out = nlb.register_core("io_1")
    coord_out = nlb.register_core("io_16")
    val_out_0 = nlb.register_core("io_16")
    val_out_1 = nlb.register_core("io_16")

    ready_in = nlb.register_core("io_1")
    flush_in = nlb.register_core("io_1")

    connections = []
    # Set up streaming out matrix from scan_mrows
    scan_mroot_to_mem_mroot = [
        ([(scan_mroot, "addr_out"), (mem_mroot, "addr_in_0")], 16),
        ([(scan_mroot, "ready_out"), (mem_mroot, "ren_in_0")], 1),
        ([(mem_mroot, "data_out_0"), (scan_mroot, "data_in")], 16),
        ([(mem_mroot, "valid_out_0"), (scan_mroot, "valid_in")], 1)
    ]

    scan_mroot_to_scan_mrows = [
        ([(scan_mroot, "pos_out"), (scan_mrows, "us_pos_in")], 16),
        ([(scan_mroot, "valid_out"), (scan_mrows, "us_valid_in")], 1),
        ([(scan_mroot, "eos_out"), (scan_mrows, "us_eos_in")], 1),
        ([(scan_mrows, "us_ready_out"), (scan_mroot, "ready_in")], 1)
    ]

    scan_mrows_to_mem_mrows = [
        ([(scan_mrows, "addr_out"), (mem_mrows, "addr_in_0")], 16),
        ([(scan_mrows, "ready_out"), (mem_mrows, "ren_in_0")], 1),
        ([(mem_mrows, "data_out_0"), (scan_mrows, "data_in")], 16),
        ([(mem_mrows, "valid_out_0"), (scan_mrows, "valid_in")], 1)
    ]

    # Set up streaming out vector
    scan_vroot_to_mem_vroot = [
        ([(scan_vroot, "addr_out"), (mem_vroot, "addr_in_0")], 16),
        ([(scan_vroot, "ready_out"), (mem_vroot, "ren_in_0")], 1),
        ([(mem_vroot, "data_out_0"), (scan_vroot, "data_in")], 16),
        ([(mem_vroot, "valid_out_0"), (scan_vroot, "valid_in")], 1)
    ]

    # Scan to intersect...
    scans_to_intersect = [
        ([(scan_mrows, "coord_out"), (isect, "coord_in_0")], 16),
        ([(scan_vroot, "coord_out"), (isect, "coord_in_1")], 16),
        ([(scan_mrows, "payload_ptr"), (isect, "payload_ptr_0")], 16),
        ([(scan_vroot, "payload_ptr"), (isect, "payload_ptr_1")], 16),
        ([(scan_mrows, "valid_out"), (isect, "valid_in_0")], 1),
        ([(scan_vroot, "valid_out"), (isect, "valid_in_1")], 1),
        ([(scan_mrows, "eos_out"), (isect, "eos_in_0")], 1),
        ([(scan_vroot, "eos_out"), (isect, "eos_in_1")], 1),
        ([(isect, "ready_out_0"), (scan_mrows, "ready_in")], 1),
        ([(isect, "ready_out_1"), (scan_vroot, "ready_in")], 1)
    ]

    # Basically apply ready_in to the isect
    isect_to_io = [
        ([(ready_in, "io2f_1"), (isect, "ready_in")], 1),
        # Register coord_out
        ([(isect, "coord_out"), (reg_coord, "reg")], 16),
        ([(reg_coord, "reg"), (coord_out, "f2io_16")], 16),
        # Register valid_out
        # ([(isect, "valid_out"), (reg_valid_out, "reg")], 1),
        ([(reg_valid_out, "reg"), (valid_out, "f2io_1")], 1),
        # Register eos_out
        ([(isect, "eos_out"), (reg_eos_out, "reg")], 1),
        ([(reg_eos_out, "reg"), (eos_out, "f2io_1")], 1),
    ]

    # Read from the corresponding memories to get actual values
    isect_to_value_mems = [
        ([(isect, "pos_out_0"), (mem_mvals, "addr_in_0")], 16),
        ([(isect, "pos_out_1"), (mem_vvals, "addr_in_0")], 16),
        ([(isect, "valid_out"), (mem_mvals, "ren_in_0"), (mem_vvals, "ren_in_0"), (reg_valid_out, "reg")], 1),
    ]

    #
    value_mems_to_io = [
        ([(mem_mvals, "data_out_0"), (val_out_0, "f2io_16")], 16),
        ([(mem_vvals, "data_out_0"), (val_out_1, "f2io_16")], 16),
    ]

    # Add all flushes...
    flush_connection = nlb.emit_flush_connection(flush_in)
    print(f"flush_connection: {flush_connection}")

    connections += scan_mroot_to_mem_mroot
    connections += scan_mroot_to_scan_mrows
    connections += scan_mrows_to_mem_mrows
    connections += scan_vroot_to_mem_vroot
    connections += scans_to_intersect
    connections += isect_to_io
    connections += isect_to_value_mems
    connections += value_mems_to_io
    connections += flush_connection

    nlb.add_connections(connections=connections)
    nlb.get_route_config()

    matrix_size = 4
    matrix = [[1, 2, 0, 0], [3, 0, 0, 4], [0, 0, 0, 0], [0, 5, 0, 6]]
    (mouter, mptr, minner, mmatrix_vals) = compress_matrix(matrix, row=True)
    mroot = [0, 3]
    mroot = align_data(mroot, 4)
    mouter = align_data(mouter, 4)
    mptr = align_data(mptr, 4)
    minner = align_data(minner, 4)
    minner_offset_root = len(mroot)
    mmatrix_vals = align_data(mmatrix_vals, 4)

    mroot_data = mroot + mouter
    minner_offset_row = len(mptr)
    mrow_data = mptr + minner

    # data_len = len(data)
    max_outer_dim = matrix_size

    vector = [7, 0, 8, 9]
    vouter = []
    vmatrix_vals = []
    for i in range(len(vector)):
        if vector[i] != 0:
            vouter.append(i)
            vmatrix_vals.append(vector[i])
    vroot = [0, len(vouter)]

    vouter = align_data(vouter, 4)
    vroot = align_data(vroot, 4)
    vmatrix_vals = align_data(vmatrix_vals, 4)

    vinner_offset_root = len(vroot)
    vroot_data = vroot + vouter

    nlb.configure_tile(scan_mroot, (minner_offset_root, max_outer_dim, 0, 1, 1))
    nlb.configure_tile(scan_mrows, (minner_offset_row, max_outer_dim, 0, 4, 0))
    nlb.configure_tile(scan_vroot, (vinner_offset_root, max_outer_dim, 0, 4, 1))
    nlb.configure_tile(mem_mroot, {"config": ["mek", {"init": mroot_data}]})
    nlb.configure_tile(mem_mrows, {"config": ["mek", {"init": mrow_data}]})
    nlb.configure_tile(mem_mvals, {"config": ["mek", {"init": mmatrix_vals}]})
    nlb.configure_tile(mem_vroot, {"config": ["mek", {"init": vroot_data}]})
    nlb.configure_tile(mem_vvals, {"config": ["mek", {"init": vmatrix_vals}]})
    nlb.configure_tile(isect, 5)
    # This does some cleanup like partitioning into compressed/uncompressed space
    nlb.finalize_config()

    config_data = nlb.get_config_data()

    # Create tester and perform init routine...
    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    tester.zero_inputs()

    # Stall during config
    tester.poke(circuit.interface["stall"], 1)

    for addr, index in config_data:
        tester.configure(addr, index)
        #  tester.config_read(addr)
        tester.eval()

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    # Get flush handle and apply flush to start off app
    h_flush_in = nlb.get_handle(flush_in, prefix="glb2io_1_")
    tester.poke(circuit.interface[h_flush_in], 1)
    tester.eval()
    tester.step(2)
    tester.poke(circuit.interface[h_flush_in], 0)
    tester.eval()

    h_ready_in = nlb.get_handle(ready_in, prefix="glb2io_1_")
    h_valid_out = nlb.get_handle(valid_out, prefix="io2glb_1_")
    h_eos_out = nlb.get_handle(eos_out, prefix="io2glb_1_")
    h_flush_in = nlb.get_handle(flush_in, prefix="glb2io_1_")
    h_coord_out = nlb.get_handle(coord_out, prefix="io2glb_16_")
    h_val_out_0 = nlb.get_handle(val_out_0, prefix="io2glb_16_")
    h_val_out_1 = nlb.get_handle(val_out_1, prefix="io2glb_16_")

    for i in range(num_cycles):
        tester.poke(circuit.interface[h_ready_in], 1)
        # tester.poke(circuit.interface[pop], 1)
        tester.eval()

        # If we have valid, print the two datas
        tester_if = tester._if(circuit.interface[h_valid_out])
        tester_if.print("COORD: %d, VAL0: %d, VAL1: %d\n",
                        circuit.interface[h_coord_out],
                        circuit.interface[h_val_out_0],
                        circuit.interface[h_val_out_1])
        if_eos_finish = tester._if(circuit.interface[h_eos_out])
        if_eos_finish.print("EOS IS HIGH\n")

        # tester_if._else().print("")
        # tester.expect(circuit.interface[data_out], out_data[0][i])
        # toggle the clock

        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)


def spM_spM_intersect_hierarchical(trace, run_tb, cwd):
    # Streams and code to create them and align them
    num_cycles = 50
    chip_size = 6
    num_tracks = 5

    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=num_tracks,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=[ScannerCore, IntersectCore])

    # Create netlist builder and register the needed cores...
    nlb = NetlistBuilder(interconnect=interconnect, cwd=cwd)

    # Matrix A
    scan_aroot = nlb.register_core("scanner", flushable=True)
    scan_arows = nlb.register_core("scanner", flushable=True)
    mem_aroot = nlb.register_core("memtile", flushable=True)
    mem_arows = nlb.register_core("memtile", flushable=True)
    mem_avals = nlb.register_core("memtile", flushable=True)

    # Matrix B
    scan_broot = nlb.register_core("scanner", flushable=True)
    scan_brows = nlb.register_core("scanner", flushable=True)
    mem_broot = nlb.register_core("memtile", flushable=True)
    mem_brows = nlb.register_core("memtile", flushable=True)
    mem_bvals = nlb.register_core("memtile", flushable=True)

    # Intersect the two...
    isect_row = nlb.register_core("intersect", flushable=True)
    isect_col = nlb.register_core("intersect", flushable=True)

    reg_coord = nlb.register_core("register")
    reg_eos_out = nlb.register_core("register")
    reg_valid_out = nlb.register_core("register")

    valid_out = nlb.register_core("io_1")
    eos_out = nlb.register_core("io_1")
    coord_out = nlb.register_core("io_16")
    val_out_0 = nlb.register_core("io_16")
    val_out_1 = nlb.register_core("io_16")

    ready_in = nlb.register_core("io_1")
    flush_in = nlb.register_core("io_1")

    connections = []
    # Set up streaming out matrix from scan_mrows
    scan_aroot_to_mem_aroot = [
        ([(scan_aroot, "addr_out"), (mem_aroot, "addr_in_0")], 16),
        ([(scan_aroot, "ready_out"), (mem_aroot, "ren_in_0")], 1),
        ([(mem_aroot, "data_out_0"), (scan_aroot, "data_in")], 16),
        ([(mem_aroot, "valid_out_0"), (scan_aroot, "valid_in")], 1)
    ]

    scan_broot_to_mem_broot = [
        ([(scan_broot, "addr_out"), (mem_broot, "addr_in_0")], 16),
        ([(scan_broot, "ready_out"), (mem_broot, "ren_in_0")], 1),
        ([(mem_broot, "data_out_0"), (scan_broot, "data_in")], 16),
        ([(mem_broot, "valid_out_0"), (scan_broot, "valid_in")], 1)
    ]

    # top level intersection
    root_scans_to_intersect = [
        ([(scan_aroot, "coord_out"), (isect_row, "coord_in_0")], 16),
        ([(scan_broot, "coord_out"), (isect_row, "coord_in_1")], 16),
        ([(scan_aroot, "payload_ptr"), (isect_row, "payload_ptr_0")], 16),
        ([(scan_broot, "payload_ptr"), (isect_row, "payload_ptr_1")], 16),
        ([(scan_aroot, "valid_out"), (isect_row, "valid_in_0")], 1),
        ([(scan_broot, "valid_out"), (isect_row, "valid_in_1")], 1),
        ([(scan_aroot, "eos_out"), (isect_row, "eos_in_0")], 1),
        ([(scan_broot, "eos_out"), (isect_row, "eos_in_1")], 1),
        ([(isect_row, "ready_out_0"), (scan_aroot, "ready_in")], 1),
        ([(isect_row, "ready_out_1"), (scan_broot, "ready_in")], 1)
    ]

    # top intersect to the next level of scanners
    intersect_to_scan_rows = [
        ([(isect_row, "pos_out_0"), (scan_arows, "us_pos_in")], 16),
        ([(isect_row, "pos_out_1"), (scan_brows, "us_pos_in")], 16),
        ([(isect_row, "valid_out"), (scan_arows, "us_valid_in"), (scan_brows, "us_valid_in")], 1),
        ([(isect_row, "eos_out"), (scan_arows, "us_eos_in"), (scan_brows, "us_eos_in")], 1),
        ([(scan_arows, "us_ready_out"), (isect_row, "ready_in")], 1)
    ]

    scan_arows_to_mem_arows = [
        ([(scan_arows, "addr_out"), (mem_arows, "addr_in_0")], 16),
        ([(scan_arows, "ready_out"), (mem_arows, "ren_in_0")], 1),
        ([(mem_arows, "data_out_0"), (scan_arows, "data_in")], 16),
        ([(mem_arows, "valid_out_0"), (scan_arows, "valid_in")], 1)
    ]

    scan_brows_to_mem_brows = [
        ([(scan_brows, "addr_out"), (mem_brows, "addr_in_0")], 16),
        ([(scan_brows, "ready_out"), (mem_brows, "ren_in_0")], 1),
        ([(mem_brows, "data_out_0"), (scan_brows, "data_in")], 16),
        ([(mem_brows, "valid_out_0"), (scan_brows, "valid_in")], 1)
    ]

    # row scanners to intersect
    row_scans_to_intersect = [
        ([(scan_arows, "coord_out"), (isect_col, "coord_in_0")], 16),
        ([(scan_brows, "coord_out"), (isect_col, "coord_in_1")], 16),
        ([(scan_arows, "payload_ptr"), (isect_col, "payload_ptr_0")], 16),
        ([(scan_brows, "payload_ptr"), (isect_col, "payload_ptr_1")], 16),
        ([(scan_arows, "valid_out"), (isect_col, "valid_in_0")], 1),
        ([(scan_brows, "valid_out"), (isect_col, "valid_in_1")], 1),
        ([(scan_arows, "eos_out"), (isect_col, "eos_in_0")], 1),
        ([(scan_brows, "eos_out"), (isect_col, "eos_in_1")], 1),
        ([(isect_col, "ready_out_0"), (scan_arows, "ready_in")], 1),
        ([(isect_col, "ready_out_1"), (scan_brows, "ready_in")], 1)
    ]

    # Basically apply ready_in to the isect
    isect_to_io = [
        ([(ready_in, "io2f_1"), (isect_col, "ready_in")], 1),
        # Register coord_out
        ([(isect_col, "coord_out"), (reg_coord, "reg")], 16),
        ([(reg_coord, "reg"), (coord_out, "f2io_16")], 16),
        # Register valid_out
        # ([(isect, "valid_out"), (reg_valid_out, "reg")], 1),
        ([(reg_valid_out, "reg"), (valid_out, "f2io_1")], 1),
        # Register eos_out
        ([(isect_col, "eos_out"), (reg_eos_out, "reg")], 1),
        ([(reg_eos_out, "reg"), (eos_out, "f2io_1")], 1),
    ]

    # Read from the corresponding memories to get actual values
    isect_to_value_mems = [
        ([(isect_col, "pos_out_0"), (mem_avals, "addr_in_0")], 16),
        ([(isect_col, "pos_out_1"), (mem_bvals, "addr_in_0")], 16),
        ([(isect_col, "valid_out"), (mem_avals, "ren_in_0"), (mem_bvals, "ren_in_0"), (reg_valid_out, "reg")], 1),
    ]

    #
    value_mems_to_io = [
        ([(mem_avals, "data_out_0"), (val_out_0, "f2io_16")], 16),
        ([(mem_bvals, "data_out_0"), (val_out_1, "f2io_16")], 16),
    ]

    flush_connection = nlb.emit_flush_connection(flush_in)

    connections += scan_aroot_to_mem_aroot
    connections += scan_broot_to_mem_broot
    connections += root_scans_to_intersect
    connections += intersect_to_scan_rows
    connections += scan_arows_to_mem_arows
    connections += scan_brows_to_mem_brows
    connections += row_scans_to_intersect
    connections += isect_to_io
    connections += isect_to_value_mems
    connections += value_mems_to_io
    connections += flush_connection

    # Add all flushes...
    nlb.add_connections(connections=connections)
    nlb.get_route_config()

    matrix_size = 4
    matrix = [[1, 2, 0, 0], [3, 0, 0, 4], [0, 0, 0, 0], [0, 5, 0, 6]]
    (mouter, mptr, minner, mmatrix_vals) = compress_matrix(matrix, row=True)
    mroot = [0, 3]
    mroot = align_data(mroot, 4)
    mouter = align_data(mouter, 4)
    mptr = align_data(mptr, 4)
    minner = align_data(minner, 4)
    minner_offset_root = len(mroot)
    mmatrix_vals = align_data(mmatrix_vals, 4)

    mroot_data = mroot + mouter
    minner_offset_row = len(mptr)
    mrow_data = mptr + minner

    # data_len = len(data)
    max_outer_dim = matrix_size

    mmatrix_vals_alt = [x + 5 for x in mmatrix_vals]

    nlb.configure_tile(scan_aroot, (minner_offset_root, max_outer_dim, 0, 1, 1))
    nlb.configure_tile(scan_arows, (minner_offset_row, max_outer_dim, 0, 4, 0))
    nlb.configure_tile(scan_broot, (minner_offset_root, max_outer_dim, 0, 1, 1))
    nlb.configure_tile(scan_brows, (minner_offset_row, max_outer_dim, 0, 4, 0))
    nlb.configure_tile(mem_aroot, {"config": ["mek", {"init": mroot_data}]})
    nlb.configure_tile(mem_arows, {"config": ["mek", {"init": mrow_data}]})
    nlb.configure_tile(mem_avals, {"config": ["mek", {"init": mmatrix_vals}]})
    nlb.configure_tile(mem_broot, {"config": ["mek", {"init": mroot_data}]})
    nlb.configure_tile(mem_brows, {"config": ["mek", {"init": mrow_data}]})
    nlb.configure_tile(mem_bvals, {"config": ["mek", {"init": mmatrix_vals_alt}]})
    nlb.configure_tile(isect_row, 5)
    nlb.configure_tile(isect_col, 5)
    # This does some cleanup like partitioning into compressed/uncompressed space
    nlb.finalize_config()

    config_data = nlb.get_config_data()

    # Create tester and perform init routine...
    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    tester.zero_inputs()

    # Stall during config
    tester.poke(circuit.interface["stall"], 1)

    for addr, index in config_data:
        tester.configure(addr, index)
        #  tester.config_read(addr)
        tester.eval()

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    # Get flush handle and apply flush to start off app
    h_flush_in = nlb.get_handle(flush_in, prefix="glb2io_1_")
    tester.poke(circuit.interface[h_flush_in], 1)
    tester.eval()
    tester.step(2)
    tester.poke(circuit.interface[h_flush_in], 0)
    tester.eval()

    h_ready_in = nlb.get_handle(ready_in, prefix="glb2io_1_")
    h_valid_out = nlb.get_handle(valid_out, prefix="io2glb_1_")
    h_eos_out = nlb.get_handle(eos_out, prefix="io2glb_1_")
    h_flush_in = nlb.get_handle(flush_in, prefix="glb2io_1_")
    h_coord_out = nlb.get_handle(coord_out, prefix="io2glb_16_")
    h_val_out_0 = nlb.get_handle(val_out_0, prefix="io2glb_16_")
    h_val_out_1 = nlb.get_handle(val_out_1, prefix="io2glb_16_")

    for i in range(num_cycles):
        tester.poke(circuit.interface[h_ready_in], 1)
        # tester.poke(circuit.interface[pop], 1)
        tester.eval()

        # If we have valid, print the two datas
        tester_if = tester._if(circuit.interface[h_valid_out])
        tester_if.print("COORD: %d, VAL0: %d, VAL1: %d\n", circuit.interface[h_coord_out],
                        circuit.interface[h_val_out_0],
                        circuit.interface[h_val_out_1])
        if_eos_finish = tester._if(circuit.interface[h_eos_out])
        if_eos_finish.print("EOS IS HIGH\n")

        # tester_if._else().print("")
        # tester.expect(circuit.interface[data_out], out_data[0][i])
        # toggle the clock

        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)


def spM_spM_elementwise_hierarchical(trace, run_tb, cwd):
    # Streams and code to create them and align them
    num_cycles = 50
    chip_size = 6
    num_tracks = 5

    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=num_tracks,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=[ScannerCore, IntersectCore])

    # Create netlist builder and register the needed cores...
    nlb = NetlistBuilder(interconnect=interconnect, cwd=cwd)

    # Matrix A
    scan_aroot = nlb.register_core("scanner", flushable=True)
    scan_arows = nlb.register_core("scanner", flushable=True)
    mem_aroot = nlb.register_core("memtile", flushable=True)
    mem_arows = nlb.register_core("memtile", flushable=True)
    mem_avals = nlb.register_core("memtile", flushable=True)

    # Matrix B
    scan_broot = nlb.register_core("scanner", flushable=True)
    scan_brows = nlb.register_core("scanner", flushable=True)
    mem_broot = nlb.register_core("memtile", flushable=True)
    mem_brows = nlb.register_core("memtile", flushable=True)
    mem_bvals = nlb.register_core("memtile", flushable=True)

    # Intersect the two...
    isect_row = nlb.register_core("intersect", flushable=True)
    isect_col = nlb.register_core("intersect", flushable=True)

    reg_coord = nlb.register_core("register")
    reg_eos_out = nlb.register_core("register")
    reg_valid_out = nlb.register_core("register")

    valid_out = nlb.register_core("io_1")
    eos_out = nlb.register_core("io_1")
    coord_out = nlb.register_core("io_16")
    val_out_0 = nlb.register_core("io_16")
    val_out_1 = nlb.register_core("io_16")

    ready_in = nlb.register_core("io_1")
    flush_in = nlb.register_core("io_1")

    connections = []
    # Set up streaming out matrix from scan_mrows
    scan_aroot_to_mem_aroot = [
        ([(scan_aroot, "addr_out"), (mem_aroot, "addr_in_0")], 16),
        ([(scan_aroot, "ready_out"), (mem_aroot, "ren_in_0")], 1),
        ([(mem_aroot, "data_out_0"), (scan_aroot, "data_in")], 16),
        ([(mem_aroot, "valid_out_0"), (scan_aroot, "valid_in")], 1)
    ]

    scan_broot_to_mem_broot = [
        ([(scan_broot, "addr_out"), (mem_broot, "addr_in_0")], 16),
        ([(scan_broot, "ready_out"), (mem_broot, "ren_in_0")], 1),
        ([(mem_broot, "data_out_0"), (scan_broot, "data_in")], 16),
        ([(mem_broot, "valid_out_0"), (scan_broot, "valid_in")], 1)
    ]

    # top level intersection
    root_scans_to_intersect = [
        ([(scan_aroot, "coord_out"), (isect_row, "coord_in_0")], 16),
        ([(scan_broot, "coord_out"), (isect_row, "coord_in_1")], 16),
        ([(scan_aroot, "payload_ptr"), (isect_row, "payload_ptr_0")], 16),
        ([(scan_broot, "payload_ptr"), (isect_row, "payload_ptr_1")], 16),
        ([(scan_aroot, "valid_out"), (isect_row, "valid_in_0")], 1),
        ([(scan_broot, "valid_out"), (isect_row, "valid_in_1")], 1),
        ([(scan_aroot, "eos_out"), (isect_row, "eos_in_0")], 1),
        ([(scan_broot, "eos_out"), (isect_row, "eos_in_1")], 1),
        ([(isect_row, "ready_out_0"), (scan_aroot, "ready_in")], 1),
        ([(isect_row, "ready_out_1"), (scan_broot, "ready_in")], 1)
    ]

    # top intersect to the next level of scanners
    intersect_to_scan_rows = [
        ([(isect_row, "pos_out_0"), (scan_arows, "us_pos_in")], 16),
        ([(isect_row, "pos_out_1"), (scan_brows, "us_pos_in")], 16),
        ([(isect_row, "valid_out"), (scan_arows, "us_valid_in"), (scan_brows, "us_valid_in")], 1),
        ([(isect_row, "eos_out"), (scan_arows, "us_eos_in"), (scan_brows, "us_eos_in")], 1),
        ([(scan_arows, "us_ready_out"), (isect_row, "ready_in")], 1)
    ]

    scan_arows_to_mem_arows = [
        ([(scan_arows, "addr_out"), (mem_arows, "addr_in_0")], 16),
        ([(scan_arows, "ready_out"), (mem_arows, "ren_in_0")], 1),
        ([(mem_arows, "data_out_0"), (scan_arows, "data_in")], 16),
        ([(mem_arows, "valid_out_0"), (scan_arows, "valid_in")], 1)
    ]

    scan_brows_to_mem_brows = [
        ([(scan_brows, "addr_out"), (mem_brows, "addr_in_0")], 16),
        ([(scan_brows, "ready_out"), (mem_brows, "ren_in_0")], 1),
        ([(mem_brows, "data_out_0"), (scan_brows, "data_in")], 16),
        ([(mem_brows, "valid_out_0"), (scan_brows, "valid_in")], 1)
    ]

    # row scanners to intersect
    row_scans_to_intersect = [
        ([(scan_arows, "coord_out"), (isect_col, "coord_in_0")], 16),
        ([(scan_brows, "coord_out"), (isect_col, "coord_in_1")], 16),
        ([(scan_arows, "payload_ptr"), (isect_col, "payload_ptr_0")], 16),
        ([(scan_brows, "payload_ptr"), (isect_col, "payload_ptr_1")], 16),
        ([(scan_arows, "valid_out"), (isect_col, "valid_in_0")], 1),
        ([(scan_brows, "valid_out"), (isect_col, "valid_in_1")], 1),
        ([(scan_arows, "eos_out"), (isect_col, "eos_in_0")], 1),
        ([(scan_brows, "eos_out"), (isect_col, "eos_in_1")], 1),
        ([(isect_col, "ready_out_0"), (scan_arows, "ready_in")], 1),
        ([(isect_col, "ready_out_1"), (scan_brows, "ready_in")], 1)
    ]

    # Basically apply ready_in to the isect
    isect_to_io = [
        ([(ready_in, "io2f_1"), (isect_col, "ready_in")], 1),
        # Register coord_out
        ([(isect_col, "coord_out"), (reg_coord, "reg")], 16),
        ([(reg_coord, "reg"), (coord_out, "f2io_16")], 16),
        # Register valid_out
        # ([(isect, "valid_out"), (reg_valid_out, "reg")], 1),
        ([(reg_valid_out, "reg"), (valid_out, "f2io_1")], 1),
        # Register eos_out
        ([(isect_col, "eos_out"), (reg_eos_out, "reg")], 1),
        ([(reg_eos_out, "reg"), (eos_out, "f2io_1")], 1),
    ]

    # Read from the corresponding memories to get actual values
    isect_to_value_mems = [
        ([(isect_col, "pos_out_0"), (mem_avals, "addr_in_0")], 16),
        ([(isect_col, "pos_out_1"), (mem_bvals, "addr_in_0")], 16),
        ([(isect_col, "valid_out"), (mem_avals, "ren_in_0"), (mem_bvals, "ren_in_0"), (reg_valid_out, "reg")], 1),
    ]

    #
    value_mems_to_io = [
        ([(mem_avals, "data_out_0"), (val_out_0, "f2io_16")], 16),
        ([(mem_bvals, "data_out_0"), (val_out_1, "f2io_16")], 16),
    ]
    # }
    flush_connection = nlb.emit_flush_connection(flush_in)

    connections += scan_aroot_to_mem_aroot
    connections += scan_broot_to_mem_broot
    connections += root_scans_to_intersect
    connections += intersect_to_scan_rows
    connections += scan_arows_to_mem_arows
    connections += scan_brows_to_mem_brows
    connections += row_scans_to_intersect
    connections += isect_to_io
    connections += isect_to_value_mems
    connections += value_mems_to_io
    connections += flush_connection

    # Add all flushes...
    nlb.add_connections(connections=connections)
    nlb.get_route_config()

    matrix_size = 4
    matrix = [[1, 2, 0, 0], [3, 0, 0, 4], [0, 0, 0, 0], [0, 5, 0, 6]]
    (mouter, mptr, minner, mmatrix_vals) = compress_matrix(matrix, row=True)
    mroot = [0, 3]
    mroot = align_data(mroot, 4)
    mouter = align_data(mouter, 4)
    mptr = align_data(mptr, 4)
    minner = align_data(minner, 4)
    minner_offset_root = len(mroot)
    mmatrix_vals = align_data(mmatrix_vals, 4)

    mroot_data = mroot + mouter
    minner_offset_row = len(mptr)
    mrow_data = mptr + minner

    # data_len = len(data)
    max_outer_dim = matrix_size

    mmatrix_vals_alt = [x + 5 for x in mmatrix_vals]

    nlb.configure_tile(scan_aroot, (minner_offset_root, max_outer_dim, 0, 1, 1))
    nlb.configure_tile(scan_arows, (minner_offset_row, max_outer_dim, 0, 4, 0))
    nlb.configure_tile(scan_broot, (minner_offset_root, max_outer_dim, 0, 1, 1))
    nlb.configure_tile(scan_brows, (minner_offset_row, max_outer_dim, 0, 4, 0))
    nlb.configure_tile(mem_aroot, {"config": ["mek", {"init": mroot_data}]})
    nlb.configure_tile(mem_arows, {"config": ["mek", {"init": mrow_data}]})
    nlb.configure_tile(mem_avals, {"config": ["mek", {"init": mmatrix_vals}]})
    nlb.configure_tile(mem_broot, {"config": ["mek", {"init": mroot_data}]})
    nlb.configure_tile(mem_brows, {"config": ["mek", {"init": mrow_data}]})
    nlb.configure_tile(mem_bvals, {"config": ["mek", {"init": mmatrix_vals_alt}]})
    nlb.configure_tile(isect_row, 5)
    nlb.configure_tile(isect_col, 5)
    # This does some cleanup like partitioning into compressed/uncompressed space
    nlb.finalize_config()

    config_data = nlb.get_config_data()

    # Create tester and perform init routine...
    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    tester.zero_inputs()

    # Stall during config
    tester.poke(circuit.interface["stall"], 1)

    for addr, index in config_data:
        tester.configure(addr, index)
        #  tester.config_read(addr)
        tester.eval()

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    # Get flush handle and apply flush to start off app
    h_flush_in = nlb.get_handle(flush_in, prefix="glb2io_1_")
    tester.poke(circuit.interface[h_flush_in], 1)
    tester.eval()
    tester.step(2)
    tester.poke(circuit.interface[h_flush_in], 0)
    tester.eval()

    h_ready_in = nlb.get_handle(ready_in, prefix="glb2io_1_")
    h_valid_out = nlb.get_handle(valid_out, prefix="io2glb_1_")
    h_eos_out = nlb.get_handle(eos_out, prefix="io2glb_1_")
    h_flush_in = nlb.get_handle(flush_in, prefix="glb2io_1_")
    h_coord_out = nlb.get_handle(coord_out, prefix="io2glb_16_")
    h_val_out_0 = nlb.get_handle(val_out_0, prefix="io2glb_16_")
    h_val_out_1 = nlb.get_handle(val_out_1, prefix="io2glb_16_")

    for i in range(num_cycles):
        tester.poke(circuit.interface[h_ready_in], 1)
        # tester.poke(circuit.interface[pop], 1)
        tester.eval()

        # If we have valid, print the two datas
        tester_if = tester._if(circuit.interface[h_valid_out])
        tester_if.print("COORD: %d, VAL0: %d, VAL1: %d\n",
                        circuit.interface[h_coord_out],
                        circuit.interface[h_val_out_0],
                        circuit.interface[h_val_out_1])
        if_eos_finish = tester._if(circuit.interface[h_eos_out])
        if_eos_finish.print("EOS IS HIGH\n")

        # tester_if._else().print("")
        # tester.expect(circuit.interface[data_out], out_data[0][i])
        # toggle the clock

        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)


def spM_spM_elementwise_hierarchical_json(trace, run_tb, cwd):
    # Streams and code to create them and align them
    num_cycles = 50
    chip_size = 6
    num_tracks = 5
    altcore = [ScannerCore, IntersectCore]

    interconnect = create_cgra(width=chip_size, height=chip_size,
                               io_sides=NetlistBuilder.io_sides(),
                               num_tracks=num_tracks,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=altcore)

    nlb = NetlistBuilder(interconnect=interconnect, cwd=cwd)
    # Create netlist builder and register the needed cores...

    # Matrix A
    scan_aroot = nlb.register_core("scanner", flushable=True)
    scan_arows = nlb.register_core("scanner", flushable=True)
    mem_aroot = nlb.register_core("memtile", flushable=True)
    mem_arows = nlb.register_core("memtile", flushable=True)
    mem_avals = nlb.register_core("memtile", flushable=True)

    # Matrix B
    scan_broot = nlb.register_core("scanner", flushable=True)
    scan_brows = nlb.register_core("scanner", flushable=True)
    mem_broot = nlb.register_core("memtile", flushable=True)
    mem_brows = nlb.register_core("memtile", flushable=True)
    mem_bvals = nlb.register_core("memtile", flushable=True)

    # Intersect the two...
    isect_row = nlb.register_core("intersect", flushable=True)
    isect_col = nlb.register_core("intersect", flushable=True)

    reg_coord = nlb.register_core("register")
    reg_eos_out = nlb.register_core("register")
    reg_valid_out = nlb.register_core("register")

    valid_out = nlb.register_core("io_1")
    eos_out = nlb.register_core("io_1")
    coord_out = nlb.register_core("io_16")
    val_out_0 = nlb.register_core("io_16")
    val_out_1 = nlb.register_core("io_16")

    ready_in = nlb.register_core("io_1")
    flush_in = nlb.register_core("io_1")

    conn_dict = {
        # Set up streaming out matrix from scan_mrows
        'scan_aroot_to_mem_aroot': [
            ([(scan_aroot, "addr_out"), (mem_aroot, "addr_in_0")], 16),
            ([(scan_aroot, "ready_out"), (mem_aroot, "ren_in_0")], 1),
            ([(mem_aroot, "data_out_0"), (scan_aroot, "data_in")], 16),
            ([(mem_aroot, "valid_out_0"), (scan_aroot, "valid_in")], 1)
        ],

        'scan_broot_to_mem_broot': [
            ([(scan_broot, "addr_out"), (mem_broot, "addr_in_0")], 16),
            ([(scan_broot, "ready_out"), (mem_broot, "ren_in_0")], 1),
            ([(mem_broot, "data_out_0"), (scan_broot, "data_in")], 16),
            ([(mem_broot, "valid_out_0"), (scan_broot, "valid_in")], 1)
        ],

        # top level intersection
        'root_scans_to_intersect': [
            ([(scan_aroot, "coord_out"), (isect_row, "coord_in_0")], 16),
            ([(scan_broot, "coord_out"), (isect_row, "coord_in_1")], 16),
            ([(scan_aroot, "payload_ptr"), (isect_row, "payload_ptr_0")], 16),
            ([(scan_broot, "payload_ptr"), (isect_row, "payload_ptr_1")], 16),
            ([(scan_aroot, "valid_out"), (isect_row, "valid_in_0")], 1),
            ([(scan_broot, "valid_out"), (isect_row, "valid_in_1")], 1),
            ([(scan_aroot, "eos_out"), (isect_row, "eos_in_0")], 1),
            ([(scan_broot, "eos_out"), (isect_row, "eos_in_1")], 1),
            ([(isect_row, "ready_out_0"), (scan_aroot, "ready_in")], 1),
            ([(isect_row, "ready_out_1"), (scan_broot, "ready_in")], 1)
        ],

        # top intersect to the next level of scanners
        'intersect_to_scan_rows': [
            ([(isect_row, "pos_out_0"), (scan_arows, "us_pos_in")], 16),
            ([(isect_row, "pos_out_1"), (scan_brows, "us_pos_in")], 16),
            ([(isect_row, "valid_out"), (scan_arows, "us_valid_in"), (scan_brows, "us_valid_in")], 1),
            ([(isect_row, "eos_out"), (scan_arows, "us_eos_in"), (scan_brows, "us_eos_in")], 1),
            ([(scan_arows, "us_ready_out"), (isect_row, "ready_in")], 1)
        ],

        'scan_arows_to_mem_arows': [
            ([(scan_arows, "addr_out"), (mem_arows, "addr_in_0")], 16),
            ([(scan_arows, "ready_out"), (mem_arows, "ren_in_0")], 1),
            ([(mem_arows, "data_out_0"), (scan_arows, "data_in")], 16),
            ([(mem_arows, "valid_out_0"), (scan_arows, "valid_in")], 1)
        ],

        'scan_brows_to_mem_brows': [
            ([(scan_brows, "addr_out"), (mem_brows, "addr_in_0")], 16),
            ([(scan_brows, "ready_out"), (mem_brows, "ren_in_0")], 1),
            ([(mem_brows, "data_out_0"), (scan_brows, "data_in")], 16),
            ([(mem_brows, "valid_out_0"), (scan_brows, "valid_in")], 1)
        ],

        # row scanners to intersect
        'row_scans_to_intersect': [
            ([(scan_arows, "coord_out"), (isect_col, "coord_in_0")], 16),
            ([(scan_brows, "coord_out"), (isect_col, "coord_in_1")], 16),
            ([(scan_arows, "payload_ptr"), (isect_col, "payload_ptr_0")], 16),
            ([(scan_brows, "payload_ptr"), (isect_col, "payload_ptr_1")], 16),
            ([(scan_arows, "valid_out"), (isect_col, "valid_in_0")], 1),
            ([(scan_brows, "valid_out"), (isect_col, "valid_in_1")], 1),
            ([(scan_arows, "eos_out"), (isect_col, "eos_in_0")], 1),
            ([(scan_brows, "eos_out"), (isect_col, "eos_in_1")], 1),
            ([(isect_col, "ready_out_0"), (scan_arows, "ready_in")], 1),
            ([(isect_col, "ready_out_1"), (scan_brows, "ready_in")], 1)
        ],

        # Basically apply ready_in to the isect
        'isect_to_io': [
            ([(ready_in, "io2f_1"), (isect_col, "ready_in")], 1),
            # Register coord_out
            ([(isect_col, "coord_out"), (reg_coord, "reg")], 16),
            ([(reg_coord, "reg"), (coord_out, "f2io_16")], 16),
            # Register valid_out
            # ([(isect, "valid_out"), (reg_valid_out, "reg")], 1),
            ([(reg_valid_out, "reg"), (valid_out, "f2io_1")], 1),
            # Register eos_out
            ([(isect_col, "eos_out"), (reg_eos_out, "reg")], 1),
            ([(reg_eos_out, "reg"), (eos_out, "f2io_1")], 1),
        ],

        # Read from the corresponding memories to get actual values
        'isect_to_value_mems': [
            ([(isect_col, "pos_out_0"), (mem_avals, "addr_in_0")], 16),
            ([(isect_col, "pos_out_1"), (mem_bvals, "addr_in_0")], 16),
            ([(isect_col, "valid_out"), (mem_avals, "ren_in_0"), (mem_bvals, "ren_in_0"), (reg_valid_out, "reg")], 1),
        ],

        'value_mems_to_io': [
            ([(mem_avals, "data_out_0"), (val_out_0, "f2io_16")], 16),
            ([(mem_bvals, "data_out_0"), (val_out_1, "f2io_16")], 16),
        ]
    }

    connections = nlb.connections_from_json(conn_dict)
    connections += nlb.emit_flush_connection(flush_in)
    # Add all flushes...
    nlb.add_connections(connections=connections)
    nlb.get_route_config()

    # App data
    matrix_size = 4
    matrix = [[1, 2, 0, 0], [3, 0, 0, 4], [0, 0, 0, 0], [0, 5, 0, 6]]
    (mouter, mptr, minner, mmatrix_vals) = compress_matrix(matrix, row=True)
    mroot = [0, 3]
    mroot = align_data(mroot, 4)
    mouter = align_data(mouter, 4)
    mptr = align_data(mptr, 4)
    minner = align_data(minner, 4)
    minner_offset_root = len(mroot)
    mmatrix_vals = align_data(mmatrix_vals, 4)
    mroot_data = mroot + mouter
    minner_offset_row = len(mptr)
    mrow_data = mptr + minner
    max_outer_dim = matrix_size
    mmatrix_vals_alt = [x + 5 for x in mmatrix_vals]

    nlb.configure_tile(scan_aroot, (minner_offset_root, max_outer_dim, 0, 1, 1))
    nlb.configure_tile(scan_arows, (minner_offset_row, max_outer_dim, 0, 4, 0))
    nlb.configure_tile(scan_broot, (minner_offset_root, max_outer_dim, 0, 1, 1))
    nlb.configure_tile(scan_brows, (minner_offset_row, max_outer_dim, 0, 4, 0))
    nlb.configure_tile(mem_aroot, {"config": ["mek", {"init": mroot_data}]})
    nlb.configure_tile(mem_arows, {"config": ["mek", {"init": mrow_data}]})
    nlb.configure_tile(mem_avals, {"config": ["mek", {"init": mmatrix_vals}]})
    nlb.configure_tile(mem_broot, {"config": ["mek", {"init": mroot_data}]})
    nlb.configure_tile(mem_brows, {"config": ["mek", {"init": mrow_data}]})
    nlb.configure_tile(mem_bvals, {"config": ["mek", {"init": mmatrix_vals_alt}]})
    nlb.configure_tile(isect_row, 5)
    nlb.configure_tile(isect_col, 5)

    # This does some cleanup like partitioning into compressed/uncompressed space
    nlb.finalize_config()

    # Create tester and perform init routine...
    tester = nlb.get_tester()

    h_flush_in = nlb.get_handle(flush_in, prefix="glb2io_1_")
    h_ready_in = nlb.get_handle(ready_in, prefix="glb2io_1_")
    h_valid_out = nlb.get_handle(valid_out, prefix="io2glb_1_")
    h_eos_out = nlb.get_handle(eos_out, prefix="io2glb_1_")
    h_flush_in = nlb.get_handle(flush_in, prefix="glb2io_1_")
    h_coord_out = nlb.get_handle(coord_out, prefix="io2glb_16_")
    h_val_out_0 = nlb.get_handle(val_out_0, prefix="io2glb_16_")
    h_val_out_1 = nlb.get_handle(val_out_1, prefix="io2glb_16_")
    stall_in = nlb.get_handle_str("stall")

    tester.reset()
    tester.zero_inputs()
    # Stall during config
    tester.poke(stall_in, 1)

    # After stalling, we can configure the circuit
    # with its configuration bitstream
    nlb.configure_circuit()

    tester.done_config()
    tester.poke(stall_in, 0)
    tester.eval()

    # Get flush handle and apply flush to start off app
    tester.poke(h_flush_in, 1)
    tester.eval()
    tester.step(2)
    tester.poke(h_flush_in, 0)
    tester.eval()

    for i in range(num_cycles):
        tester.poke(h_ready_in, 1)
        # tester.poke(circuit.interface[pop], 1)
        tester.eval()

        # If we have valid, print the two datas
        tester_if = tester._if(h_valid_out)
        tester_if.print("COORD: %d, VAL0: %d, VAL1: %d\n",
                        h_coord_out,
                        h_val_out_0,
                        h_val_out_1)
        if_eos_finish = tester._if(h_eos_out)
        if_eos_finish.print("EOS IS HIGH\n")

        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)


def spM_spM_elementwise_hierarchical_json_coords(trace, run_tb, cwd):
    """This performs elementwise multiply of two sparse matrices but includes all coords

    Args:
        trace (bool): [description]
        run_tb (function): [description]
        cwd (str): [description]
    """
    num_cycles = 250
    chip_size = 12
    num_tracks = 10
    altcore = [ScannerCore, IntersectCore, FakePECore, LookupCore, WriteScannerCore]

    interconnect = create_cgra(width=chip_size, height=chip_size,
                               io_sides=NetlistBuilder.io_sides(),
                               num_tracks=num_tracks,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=altcore)

    nlb = NetlistBuilder(interconnect=interconnect, cwd=cwd)
    # Create netlist builder and register the needed cores...

    # Matrix A
    scan_aroot = nlb.register_core("scanner", flushable=True, name="scan_aroot")
    scan_arows = nlb.register_core("scanner", flushable=True, name="scan_arows")
    mem_aroot = nlb.register_core("memtile", flushable=True, name="mem_aroot")
    mem_arows = nlb.register_core("memtile", flushable=True, name="mem_arows")
    mem_avals = nlb.register_core("memtile", flushable=True, name="mem_avals")
    mem_avals_lu = nlb.register_core("lookup", flushable=True, name="mem_avals_lu")

    # Matrix B
    scan_broot = nlb.register_core("scanner", flushable=True, name="scan_broot")
    scan_brows = nlb.register_core("scanner", flushable=True, name="scan_brows")
    mem_broot = nlb.register_core("memtile", flushable=True, name="mem_broot")
    mem_brows = nlb.register_core("memtile", flushable=True, name="mem_brows")
    mem_bvals = nlb.register_core("memtile", flushable=True, name="mem_bvals")
    mem_bvals_lu = nlb.register_core("lookup", flushable=True, name="mem_bvals_lu")

    wscan_root = nlb.register_core("write_scanner", flushable=True, name="wscan_root")
    wscan_rows = nlb.register_core("write_scanner", flushable=True, name="wscan_rows")
    wscan_vals = nlb.register_core("write_scanner", flushable=True, name="wscan_vals")
    mem_xroot = nlb.register_core("memtile", flushable=True, name="mem_xroot")
    mem_xrows = nlb.register_core("memtile", flushable=True, name="mem_xrows")
    mem_xvals = nlb.register_core("memtile", flushable=True, name="mem_xvals")

    pe_mul = nlb.register_core("fake_pe", name="pe_mul")

    # Intersect the two...
    isect_row = nlb.register_core("intersect", flushable=True, name="isect_row")
    isect_col = nlb.register_core("intersect", flushable=True, name="isect_col")

    # valid_out = nlb.register_core("io_1")
    # eos_out = nlb.register_core("io_1")
    # coord_out = nlb.register_core("io_16")
    val_out_0 = nlb.register_core("io_16", name="val_out_0")
    val_out_1 = nlb.register_core("io_16", name="val_out_1")

    # ready_in = nlb.register_core("io_1")
    flush_in = nlb.register_core("io_1", name="flush_in")

    conn_dict = {
        # Set up streaming out matrix from scan_mrows
        'scan_aroot_to_mem_aroot': [
            ([(scan_aroot, "addr_out"), (mem_aroot, "addr_in_0")], 16),
            ([(scan_aroot, "ready_out"), (mem_aroot, "ren_in_0")], 1),
            ([(mem_aroot, "data_out_0"), (scan_aroot, "data_in")], 16),
            ([(mem_aroot, "valid_out_0"), (scan_aroot, "valid_in")], 1),
        ],

        'scan_broot_to_mem_broot': [
            ([(scan_broot, "addr_out"), (mem_broot, "addr_in_0")], 16),
            ([(scan_broot, "ready_out"), (mem_broot, "ren_in_0")], 1),
            ([(mem_broot, "data_out_0"), (scan_broot, "data_in")], 16),
            ([(mem_broot, "valid_out_0"), (scan_broot, "valid_in")], 1),
        ],

        # top level intersection
        'root_scans_to_intersect': [
            ([(scan_aroot, "coord_out"), (isect_row, "coord_in_0")], 16),
            ([(scan_broot, "coord_out"), (isect_row, "coord_in_1")], 16),
            ([(scan_aroot, "pos_out"), (isect_row, "pos_in_0")], 16),
            ([(scan_broot, "pos_out"), (isect_row, "pos_in_1")], 16),
            ([(scan_aroot, "valid_out_0"), (isect_row, "valid_in_0")], 1),
            ([(scan_broot, "valid_out_0"), (isect_row, "valid_in_1")], 1),
            ([(scan_aroot, "valid_out_1"), (isect_row, "valid_in_2")], 1),
            ([(scan_broot, "valid_out_1"), (isect_row, "valid_in_3")], 1),
            ([(scan_aroot, "eos_out_0"), (isect_row, "eos_in_0")], 1),
            ([(scan_broot, "eos_out_0"), (isect_row, "eos_in_1")], 1),
            ([(scan_aroot, "eos_out_1"), (isect_row, "eos_in_2")], 1),
            ([(scan_broot, "eos_out_1"), (isect_row, "eos_in_3")], 1),
            ([(isect_row, "ready_out_0"), (scan_aroot, "ready_in_0")], 1),
            ([(isect_row, "ready_out_1"), (scan_broot, "ready_in_0")], 1),
            ([(isect_row, "ready_out_2"), (scan_aroot, "ready_in_1")], 1),
            ([(isect_row, "ready_out_3"), (scan_broot, "ready_in_1")], 1),
        ],

        # top intersect to the next level of scanners
        'intersect_to_scan_rows': [
            ([(isect_row, "pos_out_0"), (scan_arows, "us_pos_in")], 16),
            ([(isect_row, "pos_out_1"), (scan_brows, "us_pos_in")], 16),
            # Bring intersect coord to the scanner to emit final coords
            # ([(isect_row, "coord_out"), (scan_arows, "us_coord_in"), (scan_brows, "us_coord_in")], 16),
            # ([(isect_row, "coord_out"), (scan_arows, "us_coord_in"), (scan_brows, "us_coord_in")], 16),
            ([(isect_row, "valid_out_1"), (scan_arows, "us_valid_in")], 1),
            ([(isect_row, "valid_out_2"), (scan_brows, "us_valid_in")], 1),
            # ([(isect_row, "valid_out"), (scan_arows, "us_valid_in"), (scan_brows, "us_valid_in")], 1),
            ([(isect_row, "eos_out_1"), (scan_arows, "us_eos_in")], 1),
            ([(isect_row, "eos_out_2"), (scan_brows, "us_eos_in")], 1),
            ([(scan_arows, "us_ready_out"), (isect_row, "ready_in_1")], 1),
            ([(scan_brows, "us_ready_out"), (isect_row, "ready_in_2")], 1),
        ],

        'scan_arows_to_mem_arows': [
            ([(scan_arows, "addr_out"), (mem_arows, "addr_in_0")], 16),
            ([(scan_arows, "ready_out"), (mem_arows, "ren_in_0")], 1),
            ([(mem_arows, "data_out_0"), (scan_arows, "data_in")], 16),
            ([(mem_arows, "valid_out_0"), (scan_arows, "valid_in")], 1),
        ],

        'scan_brows_to_mem_brows': [
            ([(scan_brows, "addr_out"), (mem_brows, "addr_in_0")], 16),
            ([(scan_brows, "ready_out"), (mem_brows, "ren_in_0")], 1),
            ([(mem_brows, "data_out_0"), (scan_brows, "data_in")], 16),
            ([(mem_brows, "valid_out_0"), (scan_brows, "valid_in")], 1),
        ],

        # row scanners to intersect
        'row_scans_to_intersect': [
            ([(scan_arows, "coord_out"), (isect_col, "coord_in_0")], 16),
            ([(scan_brows, "coord_out"), (isect_col, "coord_in_1")], 16),
            ([(scan_arows, "pos_out"), (isect_col, "pos_in_0")], 16),
            ([(scan_brows, "pos_out"), (isect_col, "pos_in_1")], 16),
            ([(scan_arows, "valid_out_0"), (isect_col, "valid_in_0")], 1),
            ([(scan_brows, "valid_out_0"), (isect_col, "valid_in_1")], 1),
            ([(scan_arows, "valid_out_1"), (isect_col, "valid_in_2")], 1),
            ([(scan_brows, "valid_out_1"), (isect_col, "valid_in_3")], 1),
            ([(scan_arows, "eos_out_0"), (isect_col, "eos_in_0")], 1),
            ([(scan_brows, "eos_out_0"), (isect_col, "eos_in_1")], 1),
            ([(scan_arows, "eos_out_1"), (isect_col, "eos_in_2")], 1),
            ([(scan_brows, "eos_out_1"), (isect_col, "eos_in_3")], 1),
            ([(isect_col, "ready_out_0"), (scan_arows, "ready_in_0")], 1),
            ([(isect_col, "ready_out_1"), (scan_brows, "ready_in_0")], 1),
            ([(isect_col, "ready_out_2"), (scan_arows, "ready_in_1")], 1),
            ([(isect_col, "ready_out_3"), (scan_brows, "ready_in_1")], 1),
        ],

        # Basically apply ready_in to the isect
        'isects_to_merger': [
            # Send isect row and isect col to merger inside isect_col
            ([(isect_col, "coord_out"), (isect_col, "cmrg_coord_in_0")], 16),
            ([(isect_row, "coord_out"), (isect_col, "cmrg_coord_in_1")], 16),
            ([(isect_col, "valid_out_0"), (isect_col, "cmrg_valid_in_0")], 1),
            ([(isect_row, "valid_out_0"), (isect_col, "cmrg_valid_in_1")], 1),
            ([(isect_col, "eos_out_0"), (isect_col, "cmrg_eos_in_0")], 1),
            ([(isect_row, "eos_out_0"), (isect_col, "cmrg_eos_in_1")], 1),
            ([(isect_col, "cmrg_ready_out_0"), (isect_col, "ready_in_0")], 1),
            ([(isect_col, "cmrg_ready_out_1"), (isect_row, "ready_in_0")], 1),
        ],

        # Read from the corresponding memories to get actual values
        'isect_to_value_mems': [
            ([(isect_col, "pos_out_0"), (mem_avals_lu, "pos_in")], 16),
            ([(isect_col, "pos_out_1"), (mem_bvals_lu, "pos_in")], 16),
            ([(isect_col, "valid_out_1"), (mem_avals_lu, "valid_in")], 1),
            ([(isect_col, "valid_out_2"), (mem_bvals_lu, "valid_in")], 1),
            ([(isect_col, "eos_out_1"), (mem_avals_lu, "eos_in")], 1),
            ([(isect_col, "eos_out_2"), (mem_bvals_lu, "eos_in")], 1),
            ([(mem_avals_lu, "ready_out"), (isect_col, "ready_in_1")], 1),
            ([(mem_bvals_lu, "ready_out"), (isect_col, "ready_in_2")], 1),
            # Actual memory lookup
            ([(mem_avals_lu, "addr_out"), (mem_avals, "addr_in_0")], 16),
            ([(mem_bvals_lu, "addr_out"), (mem_bvals, "addr_in_0")], 16),
            ([(mem_avals_lu, "ren"), (mem_avals, "ren_in_0")], 1),
            ([(mem_bvals_lu, "ren"), (mem_bvals, "ren_in_0")], 1),
            ([(mem_avals, "data_out_0"), (mem_avals_lu, "data_in")], 16),
            ([(mem_bvals, "data_out_0"), (mem_bvals_lu, "data_in")], 16),

            # ([(isect_col, "pos_out_0"), (mem_avals, "addr_in_0")], 16),
            # ([(isect_col, "pos_out_1"), (mem_bvals, "addr_in_0")], 16),
            # ([(isect_col, "valid_out"), (mem_avals, "ren_in_0"), (mem_bvals, "ren_in_0"), (reg_valid_out, "reg")], 1),
        ],

        'value_mems_to_pe_and_io': [
            ([(mem_avals, "data_out_0"), (val_out_0, "f2io_16")], 16),
            ([(mem_bvals, "data_out_0"), (val_out_1, "f2io_16")], 16),
            ([(mem_avals_lu, "data_out"), (pe_mul, "data_in_0")], 16),
            ([(mem_avals_lu, "valid_out"), (pe_mul, "valid_in_0")], 1),
            ([(mem_avals_lu, "eos_out"), (pe_mul, "eos_in_0")], 1),
            ([(pe_mul, "ready_out_0"), (mem_avals_lu, "ready_in")], 1),
            ([(mem_bvals_lu, "data_out"), (pe_mul, "data_in_1")], 16),
            ([(mem_bvals_lu, "valid_out"), (pe_mul, "valid_in_1")], 1),
            ([(mem_bvals_lu, "eos_out"), (pe_mul, "eos_in_1")], 1),
            ([(pe_mul, "ready_out_1"), (mem_bvals_lu, "ready_in")], 1),
        ],

        'to_wscan': [
            ([(wscan_root, "ready_out_0"), (isect_col, "cmrg_ready_in_1")], 1),
            ([(isect_col, "cmrg_valid_out_1"), (wscan_root, "valid_in_0")], 1),
            ([(isect_col, "cmrg_eos_out_1"), (wscan_root, "eos_in_0")], 1),
            ([(isect_col, "cmrg_coord_out_1"), (wscan_root, "data_in_0")], 16),
            # Col coord
            ([(wscan_rows, "ready_out_0"), (isect_col, "cmrg_ready_in_0")], 1),
            ([(isect_col, "cmrg_valid_out_0"), (wscan_rows, "valid_in_0")], 1),
            ([(isect_col, "cmrg_eos_out_0"), (wscan_rows, "eos_in_0")], 1),
            ([(isect_col, "cmrg_coord_out_0"), (wscan_rows, "data_in_0")], 16),

            ([(pe_mul, "data_out"), (wscan_vals, "data_in_0")], 16),
            ([(pe_mul, "valid_out"), (wscan_vals, "valid_in_0")], 1),
            ([(pe_mul, "eos_out"), (wscan_vals, "eos_in_0")], 1),
            ([(wscan_vals, "ready_out_0"), (pe_mul, "ready_in")], 1),
        ],

        'wscan_to_mems': [
            ([(wscan_root, "data_out"), (mem_xroot, "data_in_0")], 16),
            ([(wscan_root, "addr_out"), (mem_xroot, "addr_in_0")], 16),
            ([(wscan_root, "wen"), (mem_xroot, "wen_in_0")], 1),
            ([(mem_xroot, "sram_ready_out"), (wscan_root, "ready_in")], 1),

            ([(wscan_rows, "data_out"), (mem_xrows, "data_in_0")], 16),
            ([(wscan_rows, "addr_out"), (mem_xrows, "addr_in_0")], 16),
            ([(wscan_rows, "wen"), (mem_xrows, "wen_in_0")], 1),
            ([(mem_xrows, "sram_ready_out"), (wscan_rows, "ready_in")], 1),

            ([(wscan_vals, "data_out"), (mem_xvals, "data_in_0")], 16),
            ([(wscan_vals, "addr_out"), (mem_xvals, "addr_in_0")], 16),
            ([(wscan_vals, "wen"), (mem_xvals, "wen_in_0")], 1),
            ([(mem_xvals, "sram_ready_out"), (wscan_vals, "ready_in")], 1),
        ]

    }

    connections = nlb.connections_from_json(conn_dict)
    connections += nlb.emit_flush_connection(flush_in)
    # Add all flushes...
    nlb.add_connections(connections=connections)
    nlb.get_route_config()

    # App data
    matrix_size = 4
    matrixA = [[1, 2, 0, 0], [3, 0, 0, 4], [0, 0, 0, 0], [0, 5, 0, 6]]
    matrixB = [[1, 2, 0, 0], [0, 3, 4, 0], [0, 0, 0, 0], [0, 5, 0, 6]]
    (mouterA, mptrA, minnerA, mmatrix_valsA) = compress_matrix(matrixA, row=True)
    (mouterB, mptrB, minnerB, mmatrix_valsB) = compress_matrix(matrixB, row=True)
    mrootA = [0, 3]
    mrootB = [0, 3]
    mrootA = align_data(mrootA, 4)
    mrootB = align_data(mrootB, 4)
    mouterA = align_data(mouterA, 4)
    mouterB = align_data(mouterB, 4)
    mptrA = align_data(mptrA, 4)
    mptrB = align_data(mptrB, 4)
    minnerA = align_data(minnerA, 4)
    minnerB = align_data(minnerB, 4)
    minner_offset_rootA = len(mrootA)
    minner_offset_rootB = len(mrootB)
    mmatrix_valsA = align_data(mmatrix_valsA, 4)
    mmatrix_valsB = align_data(mmatrix_valsB, 4)
    mroot_dataA = mrootA + mouterA
    mroot_dataB = mrootB + mouterB
    minner_offset_rowA = len(mptrA)
    minner_offset_rowB = len(mptrB)
    mrow_dataA = mptrA + minnerA
    mrow_dataB = mptrB + minnerB
    max_outer_dim = matrix_size
    # mmatrix_vals_alt = [x + 5 for x in mmatrix_vals]

    nlb.configure_tile(scan_aroot, (minner_offset_rootA, max_outer_dim, [0], [1], 1, 0, 0, 0, 0))
    nlb.configure_tile(scan_broot, (minner_offset_rootB, max_outer_dim, [0], [1], 1, 0, 0, 0, 0))
    nlb.configure_tile(scan_arows, (minner_offset_rowA, max_outer_dim, [0], [4], 0, 0, 0, 0, 1))
    nlb.configure_tile(scan_brows, (minner_offset_rowB, max_outer_dim, [0], [4], 0, 0, 0, 0, 1))
    nlb.configure_tile(mem_aroot, {"config": ["mek", {"init": mroot_dataA}], "mode": 2})
    nlb.configure_tile(mem_arows, {"config": ["mek", {"init": mrow_dataA}], "mode": 2})
    nlb.configure_tile(mem_avals, {"config": ["mek", {"init": mmatrix_valsA}], "mode": 2})
    nlb.configure_tile(mem_broot, {"config": ["mek", {"init": mroot_dataB}], "mode": 2})
    nlb.configure_tile(mem_brows, {"config": ["mek", {"init": mrow_dataB}], "mode": 2})
    nlb.configure_tile(mem_bvals, {"config": ["mek", {"init": mmatrix_valsB}], "mode": 2})
    nlb.configure_tile(isect_row, (0, 0))
    # Configure to do merging
    nlb.configure_tile(isect_col, (1, 1))

    nlb.configure_tile(mem_xroot, {"config": ["mek", {}], "mode": 4})
    nlb.configure_tile(mem_xrows, {"config": ["mek", {}], "mode": 4})
    nlb.configure_tile(mem_xvals, {"config": ["mek", {}], "mode": 4})

    nlb.configure_tile(wscan_root, (16, 0, 0, 0))
    nlb.configure_tile(wscan_rows, (16, 0, 0, 1))
    nlb.configure_tile(wscan_vals, (0, 1, 1, 0))

    nlb.configure_tile(pe_mul, 1)
    nlb.configure_tile(mem_avals_lu, (0))
    nlb.configure_tile(mem_bvals_lu, (0))

    # This does some cleanup like partitioning into compressed/uncompressed space
    nlb.finalize_config()

    # Create tester and perform init routine...
    tester = nlb.get_tester()

    h_flush_in = nlb.get_handle(flush_in, prefix="glb2io_1_")
    # h_ready_in = nlb.get_handle(ready_in, prefix="glb2io_1_")
    # h_valid_out = nlb.get_handle(valid_out, prefix="io2glb_1_")
    # h_eos_out = nlb.get_handle(eos_out, prefix="io2glb_1_")
    h_flush_in = nlb.get_handle(flush_in, prefix="glb2io_1_")
    # h_coord_out = nlb.get_handle(coord_out, prefix="io2glb_16_")
    h_val_out_0 = nlb.get_handle(val_out_0, prefix="io2glb_16_")
    h_val_out_1 = nlb.get_handle(val_out_1, prefix="io2glb_16_")
    stall_in = nlb.get_handle_str("stall")

    tester.reset()
    tester.zero_inputs()
    # Stall during config
    tester.poke(stall_in, 1)

    # After stalling, we can configure the circuit
    # with its configuration bitstream
    nlb.configure_circuit()

    tester.done_config()
    tester.poke(stall_in, 0)
    tester.eval()

    # Get flush handle and apply flush to start off app
    tester.poke(h_flush_in, 1)
    tester.eval()
    tester.step(2)
    tester.poke(h_flush_in, 0)
    tester.eval()

    for i in range(num_cycles):
        # tester.poke(h_ready_in, 1)
        # tester.poke(circuit.interface[pop], 1)
        tester.eval()

        # If we have valid, print the two datas
        # tester_if = tester._if(h_valid_out)
        # tester_if.print("COORD: %d, VAL0: %d, VAL1: %d\n",
        tester.print("VAL0: %d, VAL1: %d\n",
                     h_val_out_0,
                     h_val_out_1)
        # if_eos_finish = tester._if(h_eos_out)
        # if_eos_finish.print("EOS IS HIGH\n")

        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)
    nlb.display_names()


def spM_spM_multiplication_hierarchical_json(trace, run_tb, cwd):
    # Streams and code to create them and align them
    num_cycles = 250
    chip_size = 12
    num_tracks = 5
    altcore = [ScannerCore, IntersectCore, FakePECore, RegCore, LookupCore, WriteScannerCore]

    interconnect = create_cgra(width=chip_size, height=chip_size,
                               io_sides=NetlistBuilder.io_sides(),
                               num_tracks=num_tracks,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=altcore)

    nlb = NetlistBuilder(interconnect=interconnect, cwd=cwd)
    # Create netlist builder and register the needed cores...

    # Matrix A
    scan_aroot = nlb.register_core("scanner", flushable=True, name="scan_aroot")
    scan_arows = nlb.register_core("scanner", flushable=True, name="scan_arows")
    mem_aroot = nlb.register_core("memtile", flushable=True, name="mem_aroot")
    mem_arows = nlb.register_core("memtile", flushable=True, name="mem_arows")
    mem_avals = nlb.register_core("memtile", flushable=True, name="mem_avals")
    mem_avals_lu = nlb.register_core("lookup", flushable=True, name="mem_avals_lu")

    # Matrix B
    scan_broot = nlb.register_core("scanner", flushable=True, name="scan_broot")
    scan_brows = nlb.register_core("scanner", flushable=True, name="scan_brows")
    mem_broot = nlb.register_core("memtile", flushable=True, name="mem_broot")
    mem_brows = nlb.register_core("memtile", flushable=True, name="mem_brows")
    mem_bvals = nlb.register_core("memtile", flushable=True, name="mem_bvals")
    mem_bvals_lu = nlb.register_core("lookup", flushable=True, name="mem_bvals_lu")

    wscan_root = nlb.register_core("write_scanner", flushable=True, name="wscan_root")
    wscan_rows = nlb.register_core("write_scanner", flushable=True, name="wscan_rows")
    wscan_vals = nlb.register_core("write_scanner", flushable=True, name="wscan_vals")
    mem_xroot = nlb.register_core("memtile", flushable=True, name="mem_xroot")
    mem_xrows = nlb.register_core("memtile", flushable=True, name="mem_xrows")
    mem_xvals = nlb.register_core("memtile", flushable=True, name="mem_xvals")

    # Intersect the two...
    # isect_row = nlb.register_core("intersect", flushable=True, name="isect_row")
    isect_col = nlb.register_core("intersect", flushable=True, name="isect_col")

    # reg_coord = nlb.register_core("register", name="reg_coord")
    # reg_eos_out = nlb.register_core("register", name="reg_eos_out")
    # reg_valid_out = nlb.register_core("register", name="reg_valid_out")

    # valid_out = nlb.register_core("io_1", name="valid_out")
    # eos_out = nlb.register_core("io_1", name="eos_out")
    # coord_out = nlb.register_core("io_16", name="coord_out")
    val_out_0 = nlb.register_core("io_16", name="val_out_0")
    val_out_1 = nlb.register_core("io_16", name="val_out_1")
    accum_data_out = nlb.register_core("io_16", name="accum_data_out")
    accum_valid_out = nlb.register_core("io_1", name="accum_valid_out")
    accum_eos_out = nlb.register_core("io_1", name="accum_eos_out")

    ready_in = nlb.register_core("io_1", name="ready_in")
    ready_in_bulk = nlb.register_core("io_1", name="ready_in_bulk")
    flush_in = nlb.register_core("io_1", name="flush_in")

    accum_reg = nlb.register_core("regcore", flushable=True, name="accum_reg")
    # pe_mul = nlb.register_core("pe", name="pe_mul")
    pe_mul = nlb.register_core("fake_pe", name="pe_mul")

    conn_dict = {
        # Set up streaming out matrix from scan_mrows

        'upper_coords_to_wscan': [
            # Row Coord
            ([(wscan_root, "ready_out_0"), (scan_aroot, "ready_in_0")], 1),
            ([(scan_aroot, "valid_out_0"), (wscan_root, "valid_in_0")], 1),
            ([(scan_aroot, "eos_out_0"), (wscan_root, "eos_in_0")], 1),
            ([(scan_aroot, "coord_out"), (wscan_root, "data_in_0")], 16),
            # Col coord
            ([(wscan_rows, "ready_out_0"), (scan_broot, "ready_in_0")], 1),
            ([(scan_broot, "valid_out_0"), (wscan_rows, "valid_in_0")], 1),
            ([(scan_broot, "eos_out_0"), (wscan_rows, "eos_in_0")], 1),
            ([(scan_broot, "coord_out"), (wscan_rows, "data_in_0")], 16),
            # Values
            # ([(wscan_vals, "ready_out_0"), (scan_aroot, "ready_in_0")], 1),

        ],

        'bulk_ready_1_unused': [
            ([(ready_in_bulk, "io2f_1"), (isect_col, "ready_in_0")], 1)
            # ([(ready_in_bulk, "io2f_1"), (scan_arows, "ready_in_1"),
            #   (scan_brows, "ready_in_1"), (isect_col, "ready_in_0")], 1)
        ],

        'scan_aroot_to_mem_aroot': [
            ([(scan_aroot, "addr_out"), (mem_aroot, "addr_in_0")], 16),
            ([(scan_aroot, "ready_out"), (mem_aroot, "ren_in_0")], 1),
            ([(mem_aroot, "data_out_0"), (scan_aroot, "data_in")], 16),
            ([(mem_aroot, "valid_out_0"), (scan_aroot, "valid_in")], 1)
        ],

        'scan_broot_to_mem_broot': [
            ([(scan_broot, "addr_out"), (mem_broot, "addr_in_0")], 16),
            ([(scan_broot, "ready_out"), (mem_broot, "ren_in_0")], 1),
            ([(mem_broot, "data_out_0"), (scan_broot, "data_in")], 16),
            ([(mem_broot, "valid_out_0"), (scan_broot, "valid_in")], 1)
        ],

        # top level intersection
        'root_scans_to_row_scans': [
            # ([(scan_aroot, "coord_out"), (isect_row, "coord_in_0")], 16),
            # ([(scan_broot, "coord_out"), (isect_row, "coord_in_1")], 16),
            ([(scan_aroot, "pos_out"), (scan_arows, "us_pos_in")], 16),
            ([(scan_broot, "pos_out"), (scan_brows, "us_pos_in")], 16),
            ([(scan_aroot, "valid_out_1"), (scan_arows, "us_valid_in")], 1),
            ([(scan_broot, "valid_out_1"), (scan_brows, "us_valid_in")], 1),
            ([(scan_aroot, "eos_out_1"), (scan_arows, "us_eos_in")], 1),
            ([(scan_broot, "eos_out_1"), (scan_brows, "us_eos_in")], 1),
            ([(scan_arows, "us_ready_out"), (scan_aroot, "ready_in_1")], 1),
            ([(scan_brows, "us_ready_out"), (scan_broot, "ready_in_1")], 1)
        ],

        'scan_arows_to_mem_arows': [
            ([(scan_arows, "addr_out"), (mem_arows, "addr_in_0")], 16),
            ([(scan_arows, "ready_out"), (mem_arows, "ren_in_0")], 1),
            ([(mem_arows, "data_out_0"), (scan_arows, "data_in")], 16),
            ([(mem_arows, "valid_out_0"), (scan_arows, "valid_in")], 1)
        ],

        'scan_brows_to_mem_brows': [
            ([(scan_brows, "addr_out"), (mem_brows, "addr_in_0")], 16),
            ([(scan_brows, "ready_out"), (mem_brows, "ren_in_0")], 1),
            ([(mem_brows, "data_out_0"), (scan_brows, "data_in")], 16),
            ([(mem_brows, "valid_out_0"), (scan_brows, "valid_in")], 1)
        ],

        # row scanners to intersect
        'row_scans_to_intersect': [
            ([(scan_arows, "coord_out"), (isect_col, "coord_in_0")], 16),
            ([(scan_brows, "coord_out"), (isect_col, "coord_in_1")], 16),
            # ([(scan_arows, "payload_ptr"), (isect_col, "payload_ptr_0")], 16),
            ([(scan_arows, "pos_out"), (isect_col, "pos_in_0")], 16),
            # ([(scan_brows, "payload_ptr"), (isect_col, "payload_ptr_1")], 16),
            ([(scan_brows, "pos_out"), (isect_col, "pos_in_1")], 16),
            ([(scan_arows, "valid_out_0"), (isect_col, "valid_in_0")], 1),
            ([(scan_brows, "valid_out_0"), (isect_col, "valid_in_1")], 1),
            ([(scan_arows, "valid_out_1"), (isect_col, "valid_in_2")], 1),
            ([(scan_brows, "valid_out_1"), (isect_col, "valid_in_3")], 1),
            ([(scan_arows, "eos_out_0"), (isect_col, "eos_in_0")], 1),
            ([(scan_brows, "eos_out_0"), (isect_col, "eos_in_1")], 1),
            ([(scan_arows, "eos_out_1"), (isect_col, "eos_in_2")], 1),
            ([(scan_brows, "eos_out_1"), (isect_col, "eos_in_3")], 1),
            # coord, pos will naturally be aligned by the structure of the streams
            ([(isect_col, "ready_out_0"), (scan_arows, "ready_in_0")], 1),
            ([(isect_col, "ready_out_2"), (scan_arows, "ready_in_1")], 1),
            ([(isect_col, "ready_out_1"), (scan_brows, "ready_in_0")], 1),
            ([(isect_col, "ready_out_3"), (scan_brows, "ready_in_1")], 1)
        ],

        # Read from the corresponding memories to get actual values
        'isect_to_value_mems': [
            # Links betweens isect and lookup blocks
            ([(isect_col, "pos_out_0"), (mem_avals_lu, "pos_in")], 16),
            ([(isect_col, "pos_out_1"), (mem_bvals_lu, "pos_in")], 16),
            # TODO: Decouple fifos...
            ([(mem_avals_lu, "ready_out"), (isect_col, "ready_in_1")], 1),
            ([(mem_bvals_lu, "ready_out"), (isect_col, "ready_in_2")], 1),
            ([(isect_col, "valid_out_1"), (mem_avals_lu, "valid_in")], 1),
            ([(isect_col, "valid_out_2"), (mem_bvals_lu, "valid_in")], 1),
            ([(isect_col, "eos_out_1"), (mem_avals_lu, "eos_in")], 1),
            ([(isect_col, "eos_out_2"), (mem_bvals_lu, "eos_in")], 1),
            # Links between lookup and memories...
            ([(mem_avals_lu, "addr_out"), (mem_avals, "addr_in_0")], 16),
            ([(mem_bvals_lu, "addr_out"), (mem_bvals, "addr_in_0")], 16),
            ([(mem_avals_lu, "ren"), (mem_avals, "ren_in_0")], 1),
            ([(mem_bvals_lu, "ren"), (mem_bvals, "ren_in_0")], 1),
            ([(mem_avals, "data_out_0"), (mem_avals_lu, "data_in")], 16),
            ([(mem_bvals, "data_out_0"), (mem_bvals_lu, "data_in")], 16),
            # ([(isect_col, "valid_out"), (mem_avals, "ren_in_0"), (mem_bvals, "ren_in_0"), (reg_valid_out, "reg")], 1),
        ],

        # Pass values to multiplier and accum reg...

        'lookup_to_PE': [
            # ([(mem_avals, "data_out_0"), (val_out_0, "f2io_16"), (pe_mul, "data_in_0")], 16),
            ([(mem_avals, "data_out_0"), (val_out_0, "f2io_16")], 16),
            # ([(mem_bvals, "data_out_0"), (val_out_1, "f2io_16"), (pe_mul, "data_in_1")], 16),
            ([(mem_bvals, "data_out_0"), (val_out_1, "f2io_16")], 16),
            # Link between lookup blocks and pe
            ([(mem_avals_lu, "data_out"), (pe_mul, "data_in_0")], 16),
            ([(mem_avals_lu, "valid_out"), (pe_mul, "valid_in_0")], 1),
            ([(mem_avals_lu, "eos_out"), (pe_mul, "eos_in_0")], 1),
            ([(pe_mul, "ready_out_0"), (mem_avals_lu, "ready_in")], 1),
            ([(mem_bvals_lu, "data_out"), (pe_mul, "data_in_1")], 16),
            ([(mem_bvals_lu, "valid_out"), (pe_mul, "valid_in_1")], 1),
            ([(mem_bvals_lu, "eos_out"), (pe_mul, "eos_in_1")], 1),
            ([(pe_mul, "ready_out_1"), (mem_bvals_lu, "ready_in")], 1),
        ],

        'pe_mul_to_accum_reg': [
            ([(pe_mul, "data_out"), (accum_reg, "data_in")], 16),
            ([(pe_mul, "valid_out"), (accum_reg, "valid_in")], 1),
            ([(pe_mul, "eos_out"), (accum_reg, "eos_in")], 1),
            ([(accum_reg, "ready_out"), (pe_mul, "ready_in")], 1),
        ],

        'accum_reg_to_io': [
            ([(accum_reg, "data_out"), (accum_data_out, "f2io_16"), (wscan_vals, "data_in_0")], 16),
            ([(accum_reg, "valid_out"), (accum_valid_out, "f2io_1"), (wscan_vals, "valid_in_0")], 1),
            ([(accum_reg, "eos_out"), (accum_eos_out, "f2io_1"), (wscan_vals, "eos_in_0")], 1),
            # ([(ready_in, "io2f_1"), (accum_reg, "ready_in")], 1),
            ([(wscan_vals, "ready_out_0"), (accum_reg, "ready_in")], 1),
        ],

        'wscan_to_mems': [
            ([(wscan_root, "data_out"), (mem_xroot, "data_in_0")], 16),
            ([(wscan_root, "addr_out"), (mem_xroot, "addr_in_0")], 16),
            ([(wscan_root, "wen"), (mem_xroot, "wen_in_0")], 1),
            ([(mem_xroot, "sram_ready_out"), (wscan_root, "ready_in")], 1),

            ([(wscan_rows, "data_out"), (mem_xrows, "data_in_0")], 16),
            ([(wscan_rows, "addr_out"), (mem_xrows, "addr_in_0")], 16),
            ([(wscan_rows, "wen"), (mem_xrows, "wen_in_0")], 1),
            ([(mem_xrows, "sram_ready_out"), (wscan_rows, "ready_in")], 1),

            ([(wscan_vals, "data_out"), (mem_xvals, "data_in_0")], 16),
            ([(wscan_vals, "addr_out"), (mem_xvals, "addr_in_0")], 16),
            ([(wscan_vals, "wen"), (mem_xvals, "wen_in_0")], 1),
            ([(mem_xvals, "sram_ready_out"), (wscan_vals, "ready_in")], 1),
        ]
    }

    connections = nlb.connections_from_json(conn_dict)
    connections += nlb.emit_flush_connection(flush_in)
    # Add all flushes...
    nlb.add_connections(connections=connections)
    nlb.get_route_config()

    # App data
    matrix_size = 4
    matrix = [[1, 2, 0, 0], [3, 0, 0, 4], [0, 0, 0, 0], [0, 5, 6, 0]]
    # matrix_a = [[1, 2, 0, 0], [3, 0, 0, 4], [0, 0, 0, 0], [0, 5, 0, 6]]
    # matrix = [[1, 2, 0, 0], [3, 0, 0, 4], [0, 0, 0, 0], [0, 5, 0, 6]]
    (mouter, mptr, minner, mmatrix_vals) = compress_matrix(matrix, row=True)
    mroot = [0, 3]
    mroot = align_data(mroot, 4)
    mouter = align_data(mouter, 4)
    mptr = align_data(mptr, 4)
    minner = align_data(minner, 4)
    minner_offset_root = len(mroot)
    mmatrix_vals = align_data(mmatrix_vals, 4)
    mroot_data = mroot + mouter
    minner_offset_row = len(mptr)
    mrow_data = mptr + minner
    max_outer_dim = matrix_size
    mmatrix_vals_alt = [x + 5 for x in mmatrix_vals]

    matA_strides = [0]
    matA_ranges = [1]

    matB_strides = [0]
    matB_ranges = [1]

    nlb.configure_tile(scan_aroot, (minner_offset_root, max_outer_dim, matA_strides, matA_ranges, 1, 1, 0, 3, 0))
    # nlb.configure_tile(scan_aroot, (minner_offset_root, max_outer_dim, 0, 1, 1))
    nlb.configure_tile(scan_arows, (minner_offset_row, max_outer_dim, [0], [4], 0, 0, 0, 0, 2))
    nlb.configure_tile(scan_broot, (minner_offset_root, max_outer_dim, matB_strides, matB_ranges, 1, 1, 1, 3, 0))
    # nlb.configure_tile(scan_broot, (minner_offset_root, max_outer_dim, 0, 1, 1))
    nlb.configure_tile(scan_brows, (minner_offset_row, max_outer_dim, [0], [4], 0, 0, 0, 0, 2))
    nlb.configure_tile(mem_aroot, {"config": ["mek", {"init": mroot_data}], "mode": 2})
    nlb.configure_tile(mem_arows, {"config": ["mek", {"init": mrow_data}], "mode": 2})
    nlb.configure_tile(mem_avals, {"config": ["mek", {"init": mmatrix_vals}], "mode": 2})
    nlb.configure_tile(mem_broot, {"config": ["mek", {"init": mroot_data}], "mode": 2})
    nlb.configure_tile(mem_brows, {"config": ["mek", {"init": mrow_data}], "mode": 2})
    nlb.configure_tile(mem_bvals, {"config": ["mek", {"init": mmatrix_vals_alt}], "mode": 2})
    # Configure in WOM
    nlb.configure_tile(mem_xroot, {"config": ["mek", {}], "mode": 4})
    nlb.configure_tile(mem_xrows, {"config": ["mek", {}], "mode": 4})
    nlb.configure_tile(mem_xvals, {"config": ["mek", {}], "mode": 4})
    # nlb.configure_tile(isect_row, 5)
    # nlb.configure_tile(scan_aroot, (minner_offset_root, max_outer_dim, 0, 1, 1))
    nlb.configure_tile(wscan_root, (16, 0, 0, 0))
    nlb.configure_tile(wscan_rows, (16, 0, 0, 1))
    nlb.configure_tile(wscan_vals, (0, 1, 1, 0))
    nlb.configure_tile(isect_col, 5)
    # Configure the stop level
    nlb.configure_tile(accum_reg, (2))
    # nlb.configure_tile(pe_mul, asm.umult0())
    nlb.configure_tile(pe_mul, 1)
    nlb.configure_tile(mem_avals_lu, (0))
    nlb.configure_tile(mem_bvals_lu, (0))

    # This does some cleanup like partitioning into compressed/uncompressed space
    nlb.finalize_config()

    # Create tester and perform init routine...
    tester = nlb.get_tester()

    h_flush_in = nlb.get_handle(flush_in, prefix="glb2io_1_")
    # h_ready_in = nlb.get_handle(ready_in, prefix="glb2io_1_")
    h_ready_in_bulk = nlb.get_handle(ready_in_bulk, prefix="glb2io_1_")
    # h_valid_out = nlb.get_handle(valid_out, prefix="io2glb_1_")
    h_valid_out = nlb.get_handle(accum_valid_out, prefix="io2glb_1_")
    # h_eos_out = nlb.get_handle(eos_out, prefix="io2glb_1_")
    h_eos_out = nlb.get_handle(accum_eos_out, prefix="io2glb_1_")
    h_flush_in = nlb.get_handle(flush_in, prefix="glb2io_1_")
    # h_coord_out = nlb.get_handle(coord_out, prefix="io2glb_16_")
    # h_val_out_0 = nlb.get_handle(val_out_0, prefix="io2glb_16_")
    h_val_out_0 = nlb.get_handle(accum_data_out, prefix="io2glb_16_")
    # h_val_out_1 = nlb.get_handle(val_out_1, prefix="io2glb_16_")
    stall_in = nlb.get_handle_str("stall")

    tester.reset()
    tester.zero_inputs()
    # Stall during config
    tester.poke(stall_in, 1)

    # After stalling, we can configure the circuit
    # with its configuration bitstream
    nlb.configure_circuit()

    tester.done_config()
    tester.poke(stall_in, 0)
    tester.eval()

    # Get flush handle and apply flush to start off app
    tester.poke(h_flush_in, 1)
    tester.eval()
    tester.step(2)
    tester.poke(h_flush_in, 0)
    tester.eval()

    for i in range(num_cycles):
        # tester.poke(h_ready_in, 1)
        tester.poke(h_ready_in_bulk, 1)
        # tester.poke(circuit.interface[pop], 1)
        tester.eval()

        # If we have valid, print the two datas
        # tester_if = tester._if(tester.peek(h_valid_out))
        # tester_if.print("COORD: %d, VAL0: %d, VAL1: %d, EOS: %d\n",
        #                 h_coord_out,
        #                 h_val_out_0,
        #                 h_val_out_1,
        #                 h_eos_out)

        tester_if = tester._if(tester.peek(h_valid_out))
        tester_if.print("DATA: %d, EOS: %d\n",
                        h_val_out_0,
                        h_eos_out)
        tester_finish = tester._if(tester.peek(h_valid_out) and tester.peek(h_eos_out) & (tester.peek(h_val_out_0) == 0))
        tester_finish.print("Observed end of application...early finish...")
        # tester_finish.finish()

        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)

    # Get the primitive mapping so it's easy to read the design.place
    nlb.display_names()


def test_GLB_to_WS(trace, run_tb, cwd):
    # Streams and code to create them and align them
    num_cycles = 250
    chip_size = 8
    num_tracks = 5
    altcore = [ScannerCore, WriteScannerCore]

    interconnect = create_cgra(width=chip_size, height=chip_size,
                               io_sides=NetlistBuilder.io_sides(),
                               num_tracks=num_tracks,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=altcore)

    nlb = NetlistBuilder(interconnect=interconnect, cwd=cwd)
    # Create netlist builder and register the needed cores...

    wscan_root = nlb.register_core("write_scanner", flushable=True, name="wscan_root")
    wscan_rows = nlb.register_core("write_scanner", flushable=True, name="wscan_rows")
    wscan_vals = nlb.register_core("write_scanner", flushable=True, name="wscan_vals")
    mem_xroot = nlb.register_core("memtile", flushable=True, name="mem_xroot")
    mem_xrows = nlb.register_core("memtile", flushable=True, name="mem_xrows")
    mem_xvals = nlb.register_core("memtile", flushable=True, name="mem_xvals")

    root_valid_in = nlb.register_core("io_1", name="root_valid_in")
    root_eos_in = nlb.register_core("io_1", name="root_eos_in")
    root_ready_out = nlb.register_core("io_1", name="root_ready_out")
    root_data_in = nlb.register_core("io_16", name="root_data_in")

    rows_valid_in = nlb.register_core("io_1", name="rows_valid_in")
    rows_eos_in = nlb.register_core("io_1", name="rows_eos_in")
    rows_ready_out = nlb.register_core("io_1", name="rows_ready_out")
    rows_data_in = nlb.register_core("io_16", name="rows_data_in")

    vals_valid_in = nlb.register_core("io_1", name="vals_valid_in")
    vals_eos_in = nlb.register_core("io_1", name="vals_eos_in")
    vals_ready_out = nlb.register_core("io_1", name="vals_ready_out")
    vals_data_in = nlb.register_core("io_16", name="vals_data_in")

    flush_in = nlb.register_core("io_1", name="flush_in")

    # f2io_16
    conn_dict = {
        # Set up streaming out matrix from scan_mrows

        'upper_coords_to_wscan': [
            # Row Coord
            ([(wscan_root, "ready_out_0"), (root_ready_out, "f2io_1")], 1),
            ([(root_valid_in, "io2f_1 "), (wscan_root, "valid_in_0")], 1),
            ([(root_eos_in, "io2f_1"), (wscan_root, "eos_in_0")], 1),
            ([(root_data_in, "io2f_16"), (wscan_root, "data_in_0")], 16),
            # Col coord
            ([(wscan_rows, "ready_out_0"), (rows_ready_out, "f2io_1")], 1),
            ([(rows_valid_in, "io2f_1"), (wscan_rows, "valid_in_0")], 1),
            ([(rows_eos_in, "io2f_1"), (wscan_rows, "eos_in_0")], 1),
            ([(rows_data_in, "io2f_16"), (wscan_rows, "data_in_0")], 16),
            # Values
            # ([(wscan_vals, "ready_out_0"), (scan_aroot, "ready_in_0")], 1),
            ([(wscan_vals, "ready_out_0"), (vals_ready_out, "f2io_1")], 1),
            ([(vals_valid_in, "io2f_1"), (wscan_vals, "valid_in_0")], 1),
            ([(vals_eos_in, "io2f_1"), (wscan_vals, "eos_in_0")], 1),
            ([(vals_data_in, "io2f_16"), (wscan_vals, "data_in_0")], 16),

        ],

        'wscan_to_mems': [
            ([(wscan_root, "data_out"), (mem_xroot, "data_in_0")], 16),
            ([(wscan_root, "addr_out"), (mem_xroot, "addr_in_0")], 16),
            ([(wscan_root, "wen"), (mem_xroot, "wen_in_0")], 1),
            ([(mem_xroot, "sram_ready_out"), (wscan_root, "ready_in")], 1),

            ([(wscan_rows, "data_out"), (mem_xrows, "data_in_0")], 16),
            ([(wscan_rows, "addr_out"), (mem_xrows, "addr_in_0")], 16),
            ([(wscan_rows, "wen"), (mem_xrows, "wen_in_0")], 1),
            ([(mem_xrows, "sram_ready_out"), (wscan_rows, "ready_in")], 1),

            ([(wscan_vals, "data_out"), (mem_xvals, "data_in_0")], 16),
            ([(wscan_vals, "addr_out"), (mem_xvals, "addr_in_0")], 16),
            ([(wscan_vals, "wen"), (mem_xvals, "wen_in_0")], 1),
            ([(mem_xvals, "sram_ready_out"), (wscan_vals, "ready_in")], 1),
        ]
    }

    connections = nlb.connections_from_json(conn_dict)
    connections += nlb.emit_flush_connection(flush_in)
    # Add all flushes...
    nlb.add_connections(connections=connections)
    nlb.get_route_config()

    # App data
    matrix_size = 4
    matrix = [[1, 2, 0, 0], [3, 0, 0, 4], [0, 0, 0, 0], [0, 5, 6, 0]]
    # matrix_a = [[1, 2, 0, 0], [3, 0, 0, 4], [0, 0, 0, 0], [0, 5, 0, 6]]
    # matrix = [[1, 2, 0, 0], [3, 0, 0, 4], [0, 0, 0, 0], [0, 5, 0, 6]]
    (mouter, mptr, minner, mmatrix_vals) = compress_matrix(matrix, row=True)
    mroot = [0, 3]
    mroot = align_data(mroot, 4)
    mouter = align_data(mouter, 4)
    mptr = align_data(mptr, 4)
    minner = align_data(minner, 4)
    minner_offset_root = len(mroot)
    mmatrix_vals = align_data(mmatrix_vals, 4)
    mroot_data = mroot + mouter
    minner_offset_row = len(mptr)
    mrow_data = mptr + minner
    max_outer_dim = matrix_size
    mmatrix_vals_alt = [x + 5 for x in mmatrix_vals]

    matA_strides = [0]
    matA_ranges = [1]

    matB_strides = [0]
    matB_ranges = [1]

    # nlb.configure_tile(scan_aroot, (minner_offset_root, max_outer_dim, matA_strides, matA_ranges, 1, 1, 0, 3, 0))
    # # nlb.configure_tile(scan_aroot, (minner_offset_root, max_outer_dim, 0, 1, 1))
    # nlb.configure_tile(scan_arows, (minner_offset_row, max_outer_dim, [0], [4], 0, 0, 0, 0, 2))
    # nlb.configure_tile(scan_broot, (minner_offset_root, max_outer_dim, matB_strides, matB_ranges, 1, 1, 1, 3, 0))
    # # nlb.configure_tile(scan_broot, (minner_offset_root, max_outer_dim, 0, 1, 1))
    # nlb.configure_tile(scan_brows, (minner_offset_row, max_outer_dim, [0], [4], 0, 0, 0, 0, 2))
    # nlb.configure_tile(mem_aroot, {"config": ["mek", {"init": mroot_data}], "mode": 2})
    # nlb.configure_tile(mem_arows, {"config": ["mek", {"init": mrow_data}], "mode": 2})
    # nlb.configure_tile(mem_avals, {"config": ["mek", {"init": mmatrix_vals}], "mode": 2})
    # nlb.configure_tile(mem_broot, {"config": ["mek", {"init": mroot_data}], "mode": 2})
    # nlb.configure_tile(mem_brows, {"config": ["mek", {"init": mrow_data}], "mode": 2})
    # nlb.configure_tile(mem_bvals, {"config": ["mek", {"init": mmatrix_vals_alt}], "mode": 2})
    # Configure in WOM
    nlb.configure_tile(mem_xroot, {"config": ["mek", {}], "mode": 4})
    nlb.configure_tile(mem_xrows, {"config": ["mek", {}], "mode": 4})
    nlb.configure_tile(mem_xvals, {"config": ["mek", {}], "mode": 4})
    # nlb.configure_tile(isect_row, 5)
    # nlb.configure_tile(scan_aroot, (minner_offset_root, max_outer_dim, 0, 1, 1))
    nlb.configure_tile(wscan_root, (16, 0, 0, 0, 1))
    nlb.configure_tile(wscan_rows, (16, 0, 0, 1, 1))
    nlb.configure_tile(wscan_vals, (0, 1, 1, 0, 1))
    # nlb.configure_tile(isect_col, 5)
    # # Configure the stop level
    # nlb.configure_tile(accum_reg, (2))
    # # nlb.configure_tile(pe_mul, asm.umult0())
    # nlb.configure_tile(pe_mul, 1)
    # nlb.configure_tile(mem_avals_lu, (0))
    # nlb.configure_tile(mem_bvals_lu, (0))

    # This does some cleanup like partitioning into compressed/uncompressed space
    nlb.finalize_config()

    # Create tester and perform init routine...
    tester = nlb.get_tester()

    h_flush_in = nlb.get_handle(flush_in, prefix="glb2io_1_")
    stall_in = nlb.get_handle_str("stall")
    # h_ready_in = nlb.get_handle(ready_in, prefix="glb2io_1_")
    # h_valid_out = nlb.get_handle(valid_out, prefix="io2glb_1_")
    h_root_ready_out = nlb.get_handle(root_ready_out, prefix="io2glb_1_")
    h_root_valid_in = nlb.get_handle(root_valid_in, prefix="glb2io_1_")
    h_root_eos_in = nlb.get_handle(root_eos_in, prefix="glb2io_1_")
    h_root_data_in = nlb.get_handle(root_data_in, prefix="glb2io_1_")
    # h_eos_out = nlb.get_handle(eos_out, prefix="io2glb_1_")
    h_rows_ready_out = nlb.get_handle(rows_ready_out, prefix="io2glb_1_")
    h_rows_valid_in = nlb.get_handle(rows_valid_in, prefix="glb2io_1_")
    h_rows_eos_in = nlb.get_handle(rows_eos_in, prefix="glb2io_1_")
    h_rows_data_in = nlb.get_handle(rows_data_in, prefix="glb2io_1_")

    h_vals_ready_out = nlb.get_handle(vals_ready_out, prefix="io2glb_1_")
    h_vals_valid_in = nlb.get_handle(vals_valid_in, prefix="glb2io_1_")
    h_vals_eos_in = nlb.get_handle(vals_eos_in, prefix="glb2io_1_")
    h_vals_data_in = nlb.get_handle(vals_data_in, prefix="glb2io_1_")

    tester.reset()
    tester.zero_inputs()
    # Stall during config
    tester.poke(stall_in, 1)

    # After stalling, we can configure the circuit
    # with its configuration bitstream
    nlb.configure_circuit()

    tester.done_config()
    tester.poke(stall_in, 0)
    tester.eval()

    # Get flush handle and apply flush to start off app
    tester.poke(h_flush_in, 1)
    tester.eval()
    tester.step(2)
    tester.poke(h_flush_in, 0)
    tester.eval()

    # 0 out the eos-s
    tester.poke(h_root_eos_in, 0)
    tester.poke(h_rows_eos_in, 0)
    tester.poke(h_vals_eos_in, 0)

    for i in range(num_cycles):
        # tester.poke(h_ready_in, 1)
        # tester.poke(circuit.interface[pop], 1)
        tester.eval()

        # If we have valid, print the two datas
        # tester_if = tester._if(tester.peek(h_valid_out))
        # tester_if.print("COORD: %d, VAL0: %d, VAL1: %d, EOS: %d\n",
        #                 h_coord_out,
        #                 h_val_out_0,
        #                 h_val_out_1,
        #                 h_eos_out)

        tester_if = tester._if(tester.peek(h_valid_out))
        tester_if.print("DATA: %d, EOS: %d\n",
                        h_val_out_0,
                        h_eos_out)
        tester_finish = tester._if(tester.peek(h_valid_out) and tester.peek(h_eos_out) & (tester.peek(h_val_out_0) == 0))
        tester_finish.print("Observed end of application...early finish...")
        # tester_finish.finish()

        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)

    # Get the primitive mapping so it's easy to read the design.place
    nlb.display_names()


if __name__ == "__main__":
    # conv_3_3 - default tb - use command line to override
    from conftest import run_tb_fn
    parser = argparse.ArgumentParser(description='Tile_MemCore TB Generator')
    parser.add_argument('--config_path',
                        type=str,
                        default="conv_3_3_recipe/buf_inst_input_10_to_buf_inst_output_3_ubuf")
    parser.add_argument('--stream_path',
                        type=str,
                        default="conv_3_3_recipe/buf_inst_input_10_to_buf_inst_output_3_ubuf_0_top_SMT.csv")
    parser.add_argument('--in_file_name', type=str, default="input")
    parser.add_argument('--out_file_name', type=str, default="output")
    parser.add_argument('--tempdir_override', action="store_true")
    parser.add_argument('--trace', action="store_true")
    args = parser.parse_args()

    # Make sure DISABLE_GP=1
    os.environ['DISABLE_GP'] = "1"

    spM_spM_elementwise_hierarchical_json_coords(trace=args.trace, run_tb=run_tb_fn, cwd="mek_dump")
    # spM_spM_multiplication_hierarchical_json(trace=args.trace, run_tb=run_tb_fn, cwd="mek_dump")
    exit()

    spVspV_regress(dump_dir="mek_dump",
                   log_name="xrun.log",
                   trace=args.trace)
    # basic_tb(config_path=args.config_path,
    #          stream_path=args.stream_path,
    #          in_file_name=args.in_file_name,
    #          out_file_name=args.out_file_name,
    #          cwd=args.tempdir_override,
    #          trace=args.trace,
    #          run_tb=run_tb_fn)
