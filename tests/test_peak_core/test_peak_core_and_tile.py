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
from canal.pnr_io import route_one_tile
from archipelago import pnr

from peak_core.peak_core import PeakCore

from cgra import create_cgra, compress_config_data


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
    core.finalize()
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
        self.tester.circuit.res.expect(output)


def test_peak_core_sequence(sequence, run_tb):
    """
    Core level test
    * configures core using instruction bitstream
    * drives input values onto data0 and data1 ports
    * checks res output
    """

    def core_output_monitor(tester, config_data, a, b, output):
        tester.expect(tester._circuit.res, output)

    core = PeakCore(PE_fc)
    core.finalize()
    core.name = lambda: "PECore"
    circuit = core.circuit()

    tester = BasicSequenceTester(circuit, CoreDriver(), CoreMonitor(),
                                 sequence, circuit.clk, circuit.reset)
    tester.reset()

    run_tb(tester)


@pytest.mark.parametrize('seed', [0, 1])
def test_peak_tile_sequence(sequence, seed, run_tb):
    """
    Tile level test:
    * Generates 1x1 CGRA
    * configures PE_tile using test application
    * similar input driver and output monitor behavior to core test except:
      * inputs are driven onto the appropriate tile ports based on the
        generated route for the application
      * output is similarly monitored based on the generate route
    """
    interconnect = create_cgra(1, 1, IOSide.None_, num_tracks=3,
                               standalone=True)

    routing, port_mapping = route_one_tile(interconnect, 0, 0,
                                           ports=["data0", "data1", "res"],
                                           seed=seed)
    route_config = interconnect.get_route_bitstream(routing)
    route_config = compress_config_data(route_config)

    x, y = 0, 0
    circuit = interconnect.circuit()
    input_a = port_mapping["data0"]
    input_b = port_mapping["data1"]
    output_port = port_mapping["res"]

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

    run_tb(tester)
