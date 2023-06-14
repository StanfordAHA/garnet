import pytest
import tempfile
from canal.util import IOSide
from gemstone.common.testers import BasicTester
import magma
from cgra import create_cgra
import common
from archipelago import pnr


dw_files = pytest.fixture(scope="module")(common.dw_files)


@pytest.mark.skip(reason="04/2023 skip for clean master branch, see garnet issue 924")
def test_basic(run_tb, get_mapping):
    """
    Configuration sequence test on 2x2 fabric + IO tiles.
    """
    # Create cgra generator object.
    chip_size = 2
    interconnect = create_cgra(width=chip_size, height=chip_size,
                               io_sides=IOSide.North, num_tracks=5, add_pd=True)
    # Poke the circuit with a reset sequence and short configuration sequence.
    sequence = common.basic_sequence(interconnect)
    sequence = sequence[:2]  # limit to 2 addr's
    circuit = interconnect.circuit()

    pe_map, mem_map = get_mapping(interconnect)
    pe_map = pe_map["alu"]

    netlist = {
        "e0": [("I0", "io2f_17"), ("p0", pe_map["data1"])],
    }
    bus = {"e0": 17}

    placement, routing, _ = pnr(interconnect, (netlist, bus))

    src0 = placement["I0"]

    # Configure IO tiles
    instr = {}
    for place in [src0]:
        iotile = interconnect.tile_circuits[place]
        value = iotile.core.get_config_bitstream(instr)
        for addr, data in value:
            sequence.append((interconnect.get_config_addr(addr, 0, place[0], place[1]), data))

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    common.configure(tester, sequence, check_read_data=True)

    # Compile and run the test using a verilator backend.
    run_tb(tester, include_PE=True)
