from bit_vector import BitVector
from common.dummy_core_magma import DummyCore
from common.testers import BasicTester
from interconnect.cyclone import *
from interconnect.circuit import *
from interconnect.interconnect import *
import tempfile
import fault
import fault.random
import pytest
from interconnect.util import create_uniform_interconnect, SwitchBoxType


def test_interconnect():
    num_tracks = 2
    addr_width = 8
    data_width = 32
    bit_widths = [1, 16]

    tile_id_width = 16

    chip_size = 2
    track_length = 1

    # creates all the cores here
    # we don't want duplicated cores when snapping into different interconnect
    # graphs
    cores = {}
    for x in range(chip_size):
        for y in range(chip_size):
            cores[(x, y)] = DummyCore()

    def create_core(xx: int, yy: int):
        return cores[(xx, yy)]

    in_conn = []
    out_conn = []
    for side in SwitchBoxSide:
        in_conn.append((side, SwitchBoxIO.SB_IN))
        out_conn.append((side, SwitchBoxIO.SB_OUT))

    ics = {}
    for bit_width in bit_widths:
        ic = create_uniform_interconnect(chip_size, chip_size, bit_width,
                                         create_core,
                                         {f"data_in_{bit_width}b": in_conn,
                                          f"data_out_{bit_width}b": out_conn},
                                         {track_length: num_tracks},
                                         SwitchBoxType.Disjoint)
        ics[bit_width] = ic

    interconnect = Interconnect(ics, addr_width, data_width, tile_id_width,
                                lift_ports=True, fan_out_config=True)

    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    config_data = []
    test_data = []

    # we have a 2x2 (for instance) chip as follows
    # |-------|
    # | A | B |
    # |---|---|
    # | C | D |
    # ---------
    # we need to test all the line-tile routes. that is, per row and per column
    # A <-> B, A <-> C, B <-> D, C <-> D
    # and all-tile routes (which is snake-lie)
    # e.g. A -> C -> D -> B
    # TODO: add core input/output as well

    # vertical
    for bit_width in bit_widths:
        for track in range(num_tracks):
            for x in range(chip_size):
                src_node = None
                dst_node = None
                config_entry = []
                for y in range(chip_size):
                    tile_circuit = interconnect.tile_circuits[(x, y)]
                    tile = tile_circuit.tiles[bit_width]
                    pre_node = tile.get_sb(SwitchBoxSide.NORTH, track,
                                           SwitchBoxIO.SB_IN)
                    tile_circuit = interconnect.tile_circuits[(x, y)]
                    tile = tile_circuit.tiles[bit_width]
                    next_node = tile.get_sb(SwitchBoxSide.SOUTH, track,
                                            SwitchBoxIO.SB_OUT)
                    if y == 0:
                        src_node = pre_node
                    if y == chip_size - 1:
                        dst_node = next_node

                    entry = interconnect.get_route_bitstream_config(pre_node,
                                                                    next_node)

                    config_entry.append(entry)
                assert src_node is not None and dst_node is not None
                config_data.append(config_entry)
                value = fault.random.random_bv(bit_width)
                src_name = create_name(str(src_node))
                dst_name = create_name(str(dst_node))
                test_data.append((circuit.interface[src_name],
                                  circuit.interface[dst_name],
                                  value))

    # the actual test
    assert len(config_data) == len(test_data)
    # NOTE:
    # we don't test the configuration read here
    for i in range(len(config_data)):
        tester.reset()
        input_port, output_port, value = test_data[i]
        for addr, index in config_data[i]:
            tester.configure(BitVector(addr, data_width), index)
        tester.poke(input_port, value)
        tester.eval()
        tester.expect(output_port, value)

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])


test_interconnect()
