import tempfile
import glob
import shutil
import os
from gemstone.common.testers import BasicTester
from canal.util import IOSide
import lassen.asm as asm
from lassen.sim import PE_fc as lassen_fc
from peak.assembler import Assembler
from hwtypes.modifiers import strip_modifiers
from archipelago import pnr
import pytest
from cgra import create_cgra, compress_config_data


@pytest.fixture()
def io_sides():
    return IOSide.North | IOSide.East | IOSide.South | IOSide.West


@pytest.mark.skip(reason="04/2023 skip for clean master branch, see garnet issue 924")
@pytest.mark.parametrize("batch_size", [100])
def test_interconnect_reset(batch_size: int, run_tb, io_sides, get_mapping):
    # we test a simple point-wise multiplier function
    # to account for different CGRA size, we feed in data to the very top-left
    # SB and route through horizontally to reach very top-right SB
    # we configure the top-left PE as multiplier
    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides,
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2))

    pe_map, mem_map = get_mapping(interconnect)
    pe_map = pe_map["alu"]

    netlist = {
        "e0": [("I0", "io2f_17"), ("p0", pe_map["data0"])],
        "e1": [("I1", "io2f_17"), ("p0", pe_map["data1"])],
        "e3": [("p0", pe_map["res"]), ("I2", "f2io_17")],
    }
    bus = {"e0": 17, "e1": 17, "e3": 17}

    placement, routing, _ = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    x, y = placement["p0"]

    tile_id = x << 8 | y
    tile = interconnect.tile_circuits[(x, y)]
    instr_type = strip_modifiers(lassen_fc.Py.input_t.field_dict['inst'])
    asm_ = Assembler(instr_type)
    pe_bs = asm_.assemble(asm.umult0())
    add_bs = tile.core.get_config_bitstream(pe_bs)

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

    run_tb(tester, include_PE=True)
