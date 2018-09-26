from common.dummy_core_magma import DummyCore
import magma
from bit_vector import BitVector
from tile.tile_magma import Tile
from common.testers import BasicTester
import tempfile
from fault.random import random_bv


def test_tile():
    core = DummyCore()
    tile = Tile(core)
    tile_circ = tile.circuit()
    # No functional model for tile yet, so we have to use the
    # standard fault tester for now
    tester = BasicTester(tile_circ, tile_circ.clk, tile_circ.reset)
    # assign the tile a random ID for configuration
    tile_id = random_bv(16)
    tester.poke(tile_circ.tile_id, tile_id)
    tester.reset()

    # First, write to all configuration registers in the tile
    # This test should be applicapable to any tile, regardless
    # of the core it's using
    data_written = {}
    for i, feat in enumerate(tile.features()):
        feat_addr = BitVector(i, 8)
        for reg in feat.registers.values():
            reg_addr = BitVector(reg.addr, 8)
            upper_config_addr = BitVector.concat(reg_addr, feat_addr)
            config_addr = BitVector.concat(upper_config_addr, tile_id)
            # Ensure the register is wide enough to contain the random value
            rand_data = random_bv(reg.width)
            # Make sure we pass 32 bits of config data to configure
            config_data = BitVector(rand_data, 32)
            tester.configure(config_addr, config_data)
            # Keep track of data written so we know what to expect to read back
            data_written[config_addr] = config_data

    # Now, read back all the configuration we just wrote
    for addr in data_written:
        tester.config_read(addr)
        expected_data = data_written[addr]
        tester.expect(tile_circ.read_config_data, expected_data)

    # Connect all tile inputs
    for side_in in (tile_circ.north.I, tile_circ.south.I,
                    tile_circ.east.I, tile_circ.west.I):
        for i in range(len(side_in.layer1)):
            tester.poke(side_in.layer1[i], BitVector(1, 1))
        for j in range(len(side_in.layer16)):
            tester.poke(side_in.layer16[i], BitVector(1, 16))

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])
