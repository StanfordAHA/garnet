from common.dummy_core_magma import DummyCore
from bit_vector import BitVector
from tile.tile_magma import Tile
from common.testers import BasicTester
import tempfile
from fault.random import random_bv


def check_all_config(tester,
                     tile_circ,
                     tile,
                     data_written,
                     inputs_applied):
    for addr in data_written:
        tester.config_read(addr)
        expected_data = data_written[addr]
        tester.expect(tile_circ.read_config_data, expected_data)


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

    # Connect random vals to all tile inputs
    inputs_applied = {}
    for side_in in (tile_circ.north.I, tile_circ.south.I,
                    tile_circ.east.I, tile_circ.west.I):
        for i in range(len(side_in.layer1)):
            port = side_in.layer1[i]
            rand_input = random_bv(1)
            inputs_applied[port] = rand_input
            tester.poke(port, rand_input)
        for j in range(len(side_in.layer16)):
            port = side_in.layer16[j]
            rand_input = random_bv(16)
            inputs_applied[port] = rand_input
            tester.poke(port, rand_input)

    # Write to all configuration registers in the tile
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
            # Further restrict random config data values based on feature
            # Only 0-3 valid for SB config_data
            if (feat == tile.sb):
                if((reg_addr % 2) == 0):
                    rand_data = rand_data % 4
                # Only 0-1 valid for SB regs
                else:
                    rand_data = rand_data % 2
            # Only 0-9 valid for CB config_data
            elif (feat in tile.cbs):
                rand_data = rand_data % 10
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
        feat_addr = addr[16:24]
        reg_addr = addr[24:32]

    check_all_config(tester,
                     tile_circ,
                     tile,
                     data_written,
                     inputs_applied)

    # Try writing to tile with wrong tile id
    for config_addr in data_written:
        new_tile_id = config_addr[0:16] + 1
        upper_config_addr = config_addr[16:32]
        new_config_addr = BitVector.concat(upper_config_addr, new_tile_id)
        random_data = random_bv(32)
        tester.configure(new_config_addr, random_data)

    # Read all the config back again to make sure nothing changed
    check_all_config(tester,
                     tile_circ,
                     tile,
                     data_written,
                     inputs_applied)

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])
