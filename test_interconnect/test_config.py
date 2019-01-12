"""Test the configuration for configuration registers
The majority of code was written for simple_cb and simple_sb
"""

import pytest
import tempfile
import magma
from bit_vector import BitVector
from common.core import Core
from interconnect.tile_circuit import TileCircuit, SBConnectionType
from interconnect.sb import DisjointSB, SwitchBoxSide, SwitchBoxIO
from common.testers import BasicTester


@pytest.mark.parametrize('num_tracks', [2])
@pytest.mark.parametrize('bit_width', [1, 16])
def test_sb(num_tracks, bit_width):
    addr_width = 8
    addr_data = 32
    tile = TileCircuit.create(DisjointSB(0, 0, bit_width, num_tracks))

    class DummyCore(Core):
        def __init__(self):
            super().__init__()

            # PEP 8 rename
            t_data = magma.Bits(bit_width)

            self.add_ports(
                data_out=magma.Out(t_data),
                data_in=magma.In(t_data)
            )
            self.wire(self.ports.data_out, self.ports.data_in)

        def inputs(self):
            return []

        def outputs(self):
            return [self.ports.data_out]

        def name(self):
            return "DummyCore"

    core = DummyCore()
    tile.set_core(core)
    # set core connections. we connect it to every sb
    conns = []
    for side in SwitchBoxSide:
        for io in SwitchBoxIO:
            for track in range(num_tracks):
                conns.append(SBConnectionType(side, track, io))
    tile.set_core_connection("data_out", conns)

    # small hacks here to get the generator working properly
    tile.wires += core.wires

    tile.realize()
    tile.add_config_reg(addr_width, addr_data)
    circuit = tile.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)

    for config_data in [BitVector(x, 32) for x in range(num_tracks)]:
        tester.reset()
        tester.configure(BitVector(0, 8), config_data)
        tester.configure(BitVector(0, 8), config_data + 1, False)
        tester.config_read(BitVector(0, 8))
        tester.eval()
        tester.expect(circuit.read_config_data, config_data)
        # inputs = [fault.random.random_bv(16) for _ in range(num_tracks)]
        # for i, input_ in enumerate(inputs):
        #    tester.poke(circuit.I[i], input_)
        # tester.eval()
        # tester.expect(circuit.O, inputs[config_data.as_uint()])

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])
