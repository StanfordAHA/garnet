from common.dummy_core_magma import DummyCore
import magma
from bit_vector import BitVector
from tile.tile_magma import Tile
from common.testers import BasicTester
import tempfile
from fault.random import random_bv


def check_SB_config_reg(tile_circ,
                        config_addr: BitVector,
                        data_written,
                        inputs_applied,
                        tester):
    sides = [tile_circ.north, tile_circ.west,
             tile_circ.south, tile_circ.east]
    config_data = data_written[config_addr]
    reg_addr = config_addr[24:32].as_uint()
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
        expected_input_port = input_layer[track]
    # This is for when we expected the SB output to be a core output
    else:
        # since we can't probe the tile's internal signals we have to rely on
        # the fact that the core just passes inputs through. To determine which
        # tile input to check, we have to examine the data in the CB's
        # config reg
        tile_id = config_addr[0:16]
        reg_addr = BitVector(0, 8)
        # 1 bit layer
        if(layer_idx == 0):
            feat_addr = BitVector(2, 8)
            side = tile_circ.north
        # 16 bit layer
        elif(layer_idx == 1):
            feat_addr = BitVector(3, 8)
            side = tile_circ.west
        # Assemble address for the appropriate CB config reg
        cb_addr_low = BitVector.concat(feat_addr, tile_id)
        cb_addr = BitVector.concat(reg_addr, cb_addr_low)
        cb_data = data_written[cb_addr]
        # Is the input to the core a tile input or an SB output (tile output)?
        if(cb_data < num_tracks):
            side = side.I
            track = (cb_data.as_uint()) % num_tracks
            if(layer_idx == 0):
                expected_input_port = side.layer1[track]
            elif(layer_idx == 1):
                expected_input_port = side.layer16[track]
        else:
            return
    expected_input = inputs_applied[expected_input_port]
    tester.expect(output, expected_input)


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
    features = tile.features()
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
                rand_data = rand_data % 4
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
        feature = features[feat_addr.as_uint()]
        # Ensure that writes to SB config registers made the proper changes
        # to tile output values
        if(feature == tile.sb):
            check_SB_config_reg(tile_circ,
                                addr,
                                data_written,
                                inputs_applied,
                                tester)

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])
