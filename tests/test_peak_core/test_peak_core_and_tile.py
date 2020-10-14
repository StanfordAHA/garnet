import glob
import os
import random
import shutil
import tempfile

import pytest

from hwtypes import BitVector

from fault.tester.sequence_tester import SequenceTester, Driver, Monitor

from lassen.sim import PE_fc
from lassen.asm import add, sub, Mode_t

from gemstone.common.testers import BasicTester

from canal.util import IOSide
from archipelago import pnr

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
def sequence():
    """
    a 4-tuple (config_data, a, b, output)

    * config_data - bitstream for configuring the core to perform a random
                    instruction
    * a, b - random input values for data0, data
    * output - expected outputs given a, b
    """
    core = PeakCore(PE_fc)
    sequence = []
    for _ in range(5):
        # Choose a random operation from lassen.asm
        op = random.choice([add, sub])
        # Get encoded instruction (using bypass registers for now)
        instruction = op(ra_mode=Mode_t.BYPASS, rb_mode=Mode_t.BYPASS)
        # Convert to bitstream format
        config_data = core.get_config_bitstream(instruction)
        # Generate random inputs
        a, b = (BitVector.random(16) for _ in range(2))
        # Get expected output
        output = core.wrapper.model(instruction, a, b)[0]
        sequence.append((config_data, a, b, output))
    return sequence


class BasicSequenceTester(SequenceTester, BasicTester):
    """
    Extend SequenceTester with BasicTester methods (e.g. reset, configure)
    """

    def __init__(self, circuit, driver, monitor, sequence, clock, reset):
        super().__init__(circuit, driver, monitor, sequence, clock)
        self.reset_port = reset


class CoreDriver(Driver):
    def consume(self, config_data, a, b, output):
        for addr, data in config_data:
            self.tester.configure(addr, data)
        self.tester.circuit.data0 = a
        self.tester.circuit.data1 = b


class CoreMonitor(Monitor):
    def observe(self, config_data, a, b, output):
        self.tester.circuit.alu_res.expect(output)


def test_peak_core_sequence(sequence, cw_files):
    """
    Core level test
    * configures core using instruction bitstream
    * drives input values onto data0 and data1 ports
    * checks alu_res output
    """

    def core_output_monitor(tester, config_data, a, b, output):
        tester.expect(tester._circuit.alu_res, output)

    core = PeakCore(PE_fc)
    core.name = lambda: "PECore"
    circuit = core.circuit()

    tester = BasicSequenceTester(circuit, CoreDriver(), CoreMonitor(),
                                 sequence, circuit.clk, circuit.reset)
    tester.reset()

    with tempfile.TemporaryDirectory() as tempdir:
        for filename in cw_files:
            shutil.copy(filename, tempdir)

        tester.compile_and_run("verilator",
                               directory=tempdir,
                               magma_opts={"coreir_libs": {"float_CW"}},
                               flags=["-Wno-fatal"])


def test_peak_tile_sequence(sequence, cw_files):
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
    x, y = placement["p0"]
    # print(placement)
    # {'I0': (1, 0), 'I1': (2, 0), 'I2': (0, 1), 'p0': (1, 1)}

    # print(routing)
    # {'e0': [[CB_io2f_16, SB_T0_NORTH_SB_IN_B16, CB_data0]],
    #  'e1': [[CB_io2f_16, SB_T1_NORTH_SB_IN_B16, SB_T2_WEST_SB_OUT_B16,
    #          RMUX_T2_WEST_B16, SB_T2_EAST_SB_IN_B16, CB_data1]],
    #  'e3': [[CB_alu_res, SB_T0_WEST_SB_OUT_B16, RMUX_T0_WEST_B16, CB_f2io_16]]}

    assert route_config == [(262401, 0), (17236481, 0), (459265, 0),
                            (327937, 10), (459009, 786432), (459009, 0)]

    route_config = compress_config_data(route_config)

    tile_id = x << 8 | y
    tile = interconnect.tile_circuits[x, y]
    circuit = tile.circuit()

    class TileDriver(Driver):
        def consume(self, config_data, a, b, output):
            for addr, data in config_data:
                addr = interconnect.get_config_addr(addr, 0, x, y)
                self.tester.configure(addr, data)
            # TODO: We assume these inputs from the test routing app,
            # this should be done based on the configuration (so we can test
            # multiple)
            self.tester.circuit.SB_T0_NORTH_SB_IN_B16 = a
            self.tester.circuit.SB_T2_EAST_SB_IN_B16 = b

    class TileMonitor(Monitor):
        def observe(self, config_data, a, b, output):
            # TODO: We assume this output from the test routing app,
            # should be based on cofig
            self.tester.circuit.SB_T0_WEST_SB_OUT_B16.expect(output)

    tester = BasicSequenceTester(circuit, TileDriver(), TileMonitor(),
                                 sequence, circuit.clk, circuit.reset)
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
