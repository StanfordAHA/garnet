import glob
import os
import random
import shutil
import tempfile

import pytest

from hwtypes import BitVector

from fault.tester.sequence_tester import (SequenceTester, InputSequence,
                                          OutputSequence)

from lassen.sim import PE_fc
from lassen.asm import add, sub, Mode_t

from gemstone.common.testers import BasicTester

from archipelago import pnr

from canal.util import IOSide

from peak_core.peak_core import PeakCore

from cgra import create_cgra, compress_config_data


@pytest.fixture(scope="module")
def cw_files():
    filenames = ["CW_fp_add.v", "CW_fp_mult.v"]
    dirname = "peak_core"
    result_filenames = []
    for name in filenames:
        filename = os.path.join(dirname, name)
        assert os.path.isfile(filename)
        result_filenames.append(filename)
    return result_filenames


@pytest.fixture()
def sequences():
    """
    * inputs - a triple (config_data, a, and b)
      * config_data - bitstream for configuring the coreto perform a random instruction
      * a, b - random input values for data0, data
    * outputs - the expected output value given config_data, a, and b
    """
    core = PeakCore(PE_fc)
    inputs = []
    outputs = []
    for _ in range(5):
        # Choose a random operation from lassen.asm
        op = random.choice([add, sub])
        # Get encoded instruction (using bypass registers for now)
        instruction = op(ra_mode=Mode_t.BYPASS, rb_mode=Mode_t.BYPASS)
        # Convert to bitstream format
        config_data = core.get_config_bitstream(instruction)
        a, b = (BitVector.random(16) for _ in range(2))
        inputs.append((config_data, a, b))
        # generate expected output using model
        outputs.append(core.wrapper.model(instruction, a, b)[0])
    return inputs, outputs


class BasicSequenceTester(SequenceTester, BasicTester):
    """
    Extend SequenceTester with BasicTester methods (e.g. reset, configure)
    """

    def __init__(self, circuit, sequences, clock, reset):
        super().__init__(circuit, sequences, clock)
        self.reset_port = reset


def test_peak_core_sequence(sequences, cw_files):
    """
    Core level test
    * configures core using instruction bitstream
    * drives input values onto data0 and data1 ports
    * checks alu_res output
    """
    def core_input_driver(tester, value):
        config_data, a, b, = value
        for addr, data in config_data:
            tester.configure(addr, data)
        tester.poke(tester._circuit.data0, a)
        tester.poke(tester._circuit.data1, b)

    def core_output_monitor(tester, value):
        tester.expect(tester._circuit.alu_res, value)

    core = PeakCore(PE_fc)
    core.name = lambda: "PECore"
    circuit = core.circuit()

    inputs, outputs = sequences
    tester = BasicSequenceTester(circuit, [
        (core_input_driver, InputSequence(inputs)),
        (core_output_monitor, OutputSequence(outputs))
    ], circuit.clk, circuit.reset)
    tester.reset()

    with tempfile.TemporaryDirectory() as tempdir:
        for filename in cw_files:
            shutil.copy(filename, tempdir)

        tester.compile_and_run("verilator",
                               directory=tempdir,
                               magma_opts={"coreir_libs": {"float_CW"}},
                               flags=["-Wno-fatal"])


def test_peak_tile_sequence(sequences, cw_files):
    """
    Tile level test:
    * Generates CGRA to extract PE_tile
    * sets tile_id input based on test app
    * configures PE_tile based on fixed route (taken from a test app)
    * similar input driver and output monitor behavior to core test except:
      * inputs are driven onto the appropriate tile ports based on the fixed
        route configuration
      * output is similarly monitored based on the route config
    """
    # Use stub CGRA to get PE_tile
    # TODO: Is there an API to just get a PE_tile?
    io_sides = IOSide.North | IOSide.East | IOSide.South | IOSide.West
    interconnect = create_cgra(2, 2, io_sides, num_tracks=3)

    # Use test application to get a configuration
    # TODO: We should randomize or cover all possible configurations of the
    # CB/SBs
    netlist = {
        "e0": [("I0", "io2f_16"), ("p0", "data0")],
        "e1": [("I1", "io2f_16"), ("p0", "data1")],
        "e3": [("p0", "alu_res"), ("I2", "f2io_16")],
    }
    bus = {"e0": 16, "e1": 16, "e3": 16}

    placement, routing = pnr(interconnect, (netlist, bus))
    route_config = interconnect.get_route_bitstream(routing)
    assert route_config == ([(262401, 0), (459265, 0), (459265, 0),
                             (327937, 2), (459009, 786432), (459009, 0)])
    x, y = placement["p0"]

    route_config = compress_config_data(route_config)

    tile_id = x << 8 | y
    tile = interconnect.tile_circuits[x, y]
    circuit = tile.circuit()

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

    def tile_output_monitor(tester, value):
        # TODO: We assume this output from the test routing app,
        # should be based on cofig
        tester.expect(tester._circuit.SB_T0_WEST_SB_OUT_B16, value)

    inputs, outputs = sequences
    tester = BasicSequenceTester(circuit, [
        (tile_input_driver, InputSequence(inputs)),
        (tile_output_monitor, OutputSequence(outputs))
    ], circuit.clk, circuit.reset)
    tester.reset()
    tester.poke(circuit.tile_id, tile_id)
    for addr, data in route_config:
        tester.configure(addr, data)

    with tempfile.TemporaryDirectory() as tempdir:
        for filename in cw_files:
            shutil.copy(filename, tempdir)

        for aoi_mux in glob.glob("tests/*.sv"):
            shutil.copy(aoi_mux, tempdir)

        tester.compile_and_run("verilator",
                               directory=tempdir,
                               magma_opts={"coreir_libs": {"float_CW"}},
                               flags=["-Wno-fatal"])
