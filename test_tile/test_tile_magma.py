from common.dummy_core_magma import DummyCore
import magma
from bit_vector import BitVector
from tile.tile_magma import Tile
from common.testers import BasicTester
import tempfile
from fault.random import random_bv


def check_SB_config_reg(tile_circ, reg_addr, config_data, tester):
    sides = [tile_circ.north, tile_circ.west,
             tile_circ.south, tile_circ.east]
    num_tracks = 5
    num_layers = 2
    # Decoding reg_addr to determine which mux
    # is controlled by this config reg
    regs_per_side = num_tracks * num_layers
    side_num = reg_addr // regs_per_side
    output_side = sides[side_num]
    output_layers = (output_side.O.layer1, output_side.O.layer16)
    addr_within_side = reg_addr % regs_per_side
    # Input and output will be from same track
    track = addr_within_side % num_tracks
    layer_idx = addr_within_side // num_tracks
    output_layer = output_layers[layer_idx]
    output = output_layer[track]
    # Now we are determining which input to expect
    # Input will not come from same side as output
    sides.remove(output_side)
    # 3 sides from which the SB can accept input
    if(config_data < 3):
        input_side = sides[config_data.as_uint()]
        input_layers = (input_side.I.layer1, input_side.I.layer16)
        input_layer = input_layers[layer_idx]
        expected_input = input_layer[track]
        tester.expect(expected_input, output)
    """
    This is for when we expected the SB output to be a core output
    else:
        if(layer_idx == 0):
            expected_input = tile_circ.core.data_out_1b
        elif(layer_idx == 1):
            expected_input = tile_circ.core.data_out_16b
    tester.expect(expected_input, output)
    """

# def check_CB_config_reg(tile, cb, reg_addr, config_data):


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
    for side_in in (tile_circ.north.I, tile_circ.south.I,
                    tile_circ.east.I, tile_circ.west.I):
        for i in range(len(side_in.layer1)):
            tester.poke(side_in.layer1[i], random_bv(1))
        for j in range(len(side_in.layer16)):
            tester.poke(side_in.layer16[i], random_bv(16))

    # Write to all configuration registers in the tile
    # This test should be applicapable to any tile, regardless
    # of the core it's using
    data_written = {}
    features = tile.features()
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
        feat_addr = addr[16:24]
        reg_addr = addr[24:32]
        feature = features[feat_addr.as_uint()]
        # Ensure that writes to SB config registers made the proper changes
        # to tile output values
        if(feature == tile.sb):
            check_SB_config_reg(tile_circ,
                                reg_addr.as_uint(),
                                config_data,
                                tester)
        # Ensure that writes to CB config registers made the proper changes
        # to core input values
        # elif(feature in tile.cbs):
            # check_CB_config_reg(tile, feature, reg_addr, config_data)

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])
