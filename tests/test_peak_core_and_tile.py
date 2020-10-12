import glob
import os
import random
import shutil

import pytest

from hwtypes import BitVector

from fault.tester.sequence_tester import (SequenceTester, InputSequence,
                                          OutputSequence)

from lassen.sim import PE_fc
from lassen.asm import add, sub, Mode_t

from gemstone.common.testers import BasicTester

from canal.util import IOSide

from peak_core.peak_core import PeakCore

from cgra import create_cgra, compress_config_data


class BasicSequenceTester(SequenceTester, BasicTester):
    def __init__(self, circuit, sequences, clock, reset):
        super().__init__(circuit, sequences, clock)
        self.reset_port = reset


def core_input_driver(tester, value):
    config_data, a, b, = value
    for addr, data in config_data:
        tester.configure(addr, data)
    tester.poke(tester._circuit.data0, a)
    tester.poke(tester._circuit.data1, b)


def core_output_monitor(tester, value):
    tester.expect(tester._circuit.alu_res, value)


@pytest.fixture()
def sequences():
    core = PeakCore(PE_fc)
    inputs = []
    outputs = []
    for _ in range(5):
        op = random.choice([add, sub])
        instruction = op(ra_mode=Mode_t.BYPASS, rb_mode=Mode_t.BYPASS)
        config_data = core.get_config_bitstream(instruction)
        a, b = (BitVector.random(16) for _ in range(2))
        inputs.append((config_data, a, b))
        outputs.append(core.wrapper.model(instruction, a, b)[0])
    return inputs, outputs


def test_peak_core_sequence(sequences):
    inputs, outputs = sequences
    core = PeakCore(PE_fc)
    core.name = lambda: "PECore"
    circuit = core.circuit()

    tester = BasicSequenceTester(circuit, [
        (core_input_driver, InputSequence(inputs)),
        (core_output_monitor, OutputSequence(outputs))
    ], circuit.clk, circuit.reset)
    tester.reset()

    tester.compile_and_run("verilator",
                           magma_opts={"coreir_libs": {"float_DW"}},
                           flags=["-Wno-fatal"])


def make_tile_input_driver(interconnect, x, y):
    def tile_input_driver(tester, value):
        config_data, a, b, = value
        for addr, data in config_data:
            # Convert to tile level address space
            addr = interconnect.get_config_addr(addr, 0, x, y)
            tester.configure(addr, data)

        # TODO: We assume these inputs from the test routing app,
        # this should be done based on the configuration (so we can test
        # multiple)
        tester.poke(tester._circuit.SB_T0_NORTH_SB_IN_B16, a)
        tester.poke(tester._circuit.SB_T0_EAST_SB_IN_B16, b)
    return tile_input_driver


def tile_output_monitor(tester, value):
    # TODO: We assume this output from the test routing app,
    # should be based on cofig
    tester.expect(tester._circuit.SB_T0_WEST_SB_OUT_B16, value)


def test_peak_tile_sequence(sequences):
    inputs, outputs = sequences
    # Use stub CGRA to get PE_tile
    # TODO: Is there an API to just get a PE_tile?
    io_sides = IOSide.North | IOSide.East | IOSide.South | IOSide.West
    interconnect = create_cgra(2, 2, io_sides, num_tracks=3)

    # Use test application to get a configuration
    # TODO: We should randomize or cover all possible configurations of the
    # CB/SBs
    # placement, routing generated from:
    # netlist = {
    #     "e0": [("I0", "io2f_16"), ("p0", "data0")],
    #     "e1": [("I1", "io2f_16"), ("p0", "data1")],
    #     "e3": [("p0", "alu_res"), ("I2", "f2io_16")],
    # }
    # bus = {"e0": 16, "e1": 16, "e3": 16}

    # from archipelago import pnr
    # placement, routing = pnr(interconnect, (netlist, bus))
    # route_config = interconnect.get_route_bitstream(routing)
    # x, y = placement["p0"]

    # placement = {'I0': (1, 0), 'I1': (2, 0), 'I2': (0, 1), 'p0': (1, 1)}
    # routing = {'e0': [[CB_io2f_16, SB_T0_NORTH_SB_IN_B16, CB_data0]],
    #            'e1': [[CB_io2f_16, SB_T0_NORTH_SB_IN_B16,
    #                    SB_T0_WEST_SB_OUT_B16, RMUX_T0_WEST_B16,
    #                    SB_T0_EAST_SB_IN_B16, CB_data1]],
    #            'e3': [[CB_alu_res, SB_T0_WEST_SB_OUT_B16, RMUX_T0_WEST_B16, CB_f2io_16]]}

    route_config = [(262401, 0), (459265, 0), (459265, 0), (327937, 2),
                    (459009, 786432), (459009, 0)]
    route_config = compress_config_data(route_config)
    x, y = (1, 1)

    tile_id = x << 8 | y
    tile = interconnect.tile_circuits[x, y]
    circuit = tile.circuit()

    input_driver = make_tile_input_driver(interconnect, x, y)
    output_monitor = tile_output_monitor

    tester = BasicSequenceTester(circuit, [
        (input_driver, InputSequence(inputs)),
        (output_monitor, OutputSequence(outputs))
    ], circuit.clk, circuit.reset)
    tester.reset()
    tester.poke(circuit.tile_id, tile_id)
    for addr, data in route_config:
        tester.configure(addr, data)

    for filename in ["DW_fp_add.v", "DW_fp_mult.v"]:
        shutil.copy(os.path.join("peak_core", filename), "build")

    for aoi_mux in glob.glob("tests/*.sv"):
        shutil.copy(aoi_mux, "build")

    tester.compile_and_run("verilator",
                           magma_opts={"coreir_libs": {"float_DW"}},
                           flags=["-Wno-fatal"])
