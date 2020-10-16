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
    def lower(self, config_data, a, b, output):
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
    * Generates 1x1 CGRA
    * configures PE_tile using test application
    * similar input driver and output monitor behavior to core test except:
      * inputs are driven onto the appropriate tile ports based on the
        generated route for the application
      * output is similarly monitored based on the generate route
    """
    # Use 1x1 CGRA to test PE TILE
    # TODO: Do we need to test without interconnect (i.e. just tile)
    io_sides = IOSide.North | IOSide.East | IOSide.South | IOSide.West
    interconnect = create_cgra(1, 1, io_sides, num_tracks=3)

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

    route_config = compress_config_data(route_config)

    circuit = interconnect.circuit()
    input_a = interconnect.get_top_input_port_by_coord(placement["I0"], 16)
    input_b = interconnect.get_top_input_port_by_coord(placement["I1"], 16)
    output_port = interconnect.get_top_output_port_by_coord(placement["I2"],
                                                            16)

    class TileDriver(Driver):
        def lower(self, config_data, a, b, output):
            for addr, data in config_data:
                addr = interconnect.get_config_addr(addr, 0, x, y)
                self.tester.configure(addr, data)
            setattr(self.tester.circuit, input_a, a)
            setattr(self.tester.circuit, input_b, b)

    class TileMonitor(Monitor):
        def observe(self, config_data, a, b, output):
            getattr(self.tester.circuit, output_port).expect(output)

    tester = BasicSequenceTester(circuit, TileDriver(), TileMonitor(),
                                 sequence, circuit.clk, circuit.reset)
    tester.reset()
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
