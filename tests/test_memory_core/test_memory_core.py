import argparse
from os import pathconf
import os
from archipelago.place import place
from fault.actions import Expect
from peak_core.peak_core import PeakCore
from memory_core.intersect_core import IntersectCore
from gemstone.common.util import compress_config_data
import pytest
from memory_core.memory_core_magma import MemCore
from memory_core.scanner_core import ScannerCore
from lake.utils.test_infra import lake_test_app_args
from lake.utils.parse_clkwork_csv import generate_data_lists
from gemstone.common.testers import ResetTester
from gemstone.common.testers import BasicTester
from cgra.util import create_cgra
from canal.util import IOSide
from memory_core.memory_core_magma import config_mem_tile
from archipelago import pnr
import lassen.asm as asm
import random as rand
import re
from memory_core.constraints import *

def io_sides():
    return IOSide.North | IOSide.East | IOSide.South | IOSide.West


def make_memory_core():
    mem_core = MemCore()
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

    #print("BITSTREAM START")
    #for addr, config in config_data:
    #    print("{0:08X} {1:08X}".format(addr, config))
    #print("BITSTREAM END")

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
        "e9": [("i11", "io2f_1"), ("j0", "flush"), ("s1", "flush"), ("s2", "flush"), ("m3", "flush"), ("m4", "flush"), ("m13", "flush"), ("m14", "flush")],
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
    


def spVspV_test(trace, run_tb, cwd, data0 = [1, 2, 6, 10], data1 = [3, 6, 8]):
    # Streams and code to create them and align them
    # Works
    #data0 = [1, 2, 6, 10]
    #data1 = [3, 6, 8]
    # Works
    #data0 = [1, 2, 6, 10]
    #data1 = [1, 3, 6, 8]
    # Works 
    #data0 = [1, 2, 6, 10, 12]
    #data1 = [1, 3, 6, 8]
    # 
#    data0 = [1, 2, 6, 10, 12, 17]
#    data1 = [1, 3, 6, 8, 16, 18]

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
    #out_coord = list(out_coord)
    #out_coord.sort()
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
        "e9": [("i11", "io2f_1"), ("j0", "flush"), ("s1", "flush"), ("s2", "flush"), ("m3", "flush"), ("m4", "flush"), ("m13", "flush"), ("m14", "flush"), ("m31", "flush"), ("m32", "flush")],
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

    #print("BITSTREAM START")
    #for addr, config in config_data:
    #    print("{0:08X} {1:08X}".format(addr, config))
    #print("BITSTREAM END")

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
        if_eos_finish.print("EOS IS HIGH\n");
        
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
    #intersect_test(trace=args.trace,
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
    split_lines = [re.split('[,\s\t]+', x.strip()) for x in check_lines]
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
                success = run_test(len1, len2, num_match, value_limit, dump_dir=dump_dir, log_name=log_name, trace=trace)
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

    #print("BITSTREAM START")
    #for addr, config in config_data:
    #    print("{0:08X} {1:08X}".format(addr, config))
    #print("BITSTREAM END")

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

    scanner_test_new(trace=True, run_tb=run_tb_fn, cwd="mek_dump")
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

