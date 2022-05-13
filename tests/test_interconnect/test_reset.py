import tempfile
import glob
import shutil
import os
from gemstone.common.testers import BasicTester
from canal.util import IOSide
import lassen.asm as asm
from archipelago import pnr
import pytest
from cgra import create_cgra, compress_config_data


@pytest.fixture()
def io_sides():
    return IOSide.North | IOSide.East | IOSide.South | IOSide.West


@pytest.mark.parametrize("batch_size", [100])
def test_interconnect_reset(batch_size: int, run_tb, io_sides):
    # we test a simple point-wise multiplier function
    # to account for different CGRA size, we feed in data to the very top-left
    # SB and route through horizontally to reach very top-right SB
    # we configure the top-left PE as multiplier
    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides,
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2))

    netlist = {
        "e0": [("I0", "io2f_16"), ("p0", "data0")],
        "e1": [("I1", "io2f_16"), ("p0", "data1")],
        "e3": [("p0", "res"), ("I2", "f2io_16")],
    }
    bus = {"e0": 16, "e1": 16, "e3": 16}

    placement, routing, _ = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    x, y = placement["p0"]

    tile_id = x << 8 | y
    tile = interconnect.tile_circuits[(x, y)]
    add_bs = tile.core.get_config_bitstream(asm.umult0())
    for addr, data in add_bs:
        config_data.append(((addr << 24) | tile_id, data))
    config_data = compress_config_data(config_data)

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()

    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    # reset them
    tester.reset()
    for addr, index in config_data:
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, 0)

    # configure new one
    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    run_tb(tester)
