from fault.tester import Tester
from interconnect.cyclone import *
from interconnect.circuit import *
from io_core.io1bit_magma import *
from io_core.io16bit_magma import *
import tempfile
import fault
import fault.random
import pytest


@pytest.mark.parametrize("bit_width", [1, 16])
def test_io_tile(bit_width: int):
    addr_width = 8
    data_width = 32

    tile_id_width = 16
    x = 0
    y = 0
    num_tests = 100

    if bit_width == 1:
        io_core = IO1bit()
    else:
        assert bit_width == 16
        io_core = IO16bit()
    core = CoreInterface(io_core)

    tiles: Dict[int, Tile] = {}

    switchbox = SwitchBox(x, y, 0, bit_width, [])
    tile = Tile(x, y, bit_width, switchbox)
    tile.set_core(core)
    tiles[bit_width] = tile

    # fake the connections from other tiles's switchbox
    sb_node_out = SwitchBoxNode(0, 1, 0, bit_width, SwitchBoxSide.NORTH,
                                SwitchBoxIO.SB_OUT)
    sb_node_in = SwitchBoxNode(0, 1, 0, bit_width, SwitchBoxSide.NORTH,
                               SwitchBoxIO.SB_IN)
    input_port_f = tile.ports[f"f2io_{bit_width}"]
    output_port_f = tile.ports[f"io2f_{bit_width}"]
    # add the connection
    sb_node_out.add_edge(input_port_f)
    output_port_f.add_edge(sb_node_in)

    tile_circuit = TileCircuit(tiles, addr_width, data_width,
                               tile_id_width=tile_id_width)

    circuit = tile_circuit.circuit()
    tile_id = fault.random.random_bv(tile_id_width)

    # actual tests
    tester = Tester(circuit)
    tester.poke(circuit.tile_id, tile_id)
    input_ports = [circuit.glb2io, circuit.interface[f"f2io_{bit_width}"]]
    output_ports = [circuit.interface[f"io2f_{bit_width}"], circuit.io2glb]

    for i in range(num_tests):
        for idx in range(2):
            input_port = input_ports[idx]
            output_port = output_ports[idx]
            value = fault.random.random_bv(bit_width)
            tester.poke(input_port, value)
            tester.eval()
            tester.expect(output_port, value)

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])
