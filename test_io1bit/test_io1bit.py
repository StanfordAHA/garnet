import random
from bit_vector import BitVector
from io1bit.io1bit import gen_io1bit


def test_io1bit_functional_model():
    """
    Small test to show the usage of the io1bit functional model.
    """

    # Three modes in IO
    IN_MODE = random.choice([0, 2])
    OUT_16_MODE = 1
    OUT_1_MODE = 3

    # First, test IO input mode
    io1bit = gen_io1bit()
    io1bit_inst = io1bit()
    config_addr = BitVector(0, 32)
    config_data = BitVector(IN_MODE, 32)
    io1bit_inst.config[config_addr] = config_data
    assert io1bit_inst.config[config_addr] == config_data
    io1bit_inst.config_read(config_addr)
    assert io1bit_inst.read_data == config_data
    pad = random.randint(0, 1)
    f2p_1 = random.randint(0, 1)
    f2p_16 = random.randint(0, 1)
    res = io1bit_inst(pad, f2p_16, f2p_1)
    assert res == pad

    # Second, test IO output 16bit mode
    io1bit = gen_io1bit()
    io1bit_inst = io1bit()
    config_addr = BitVector(0, 32)
    config_data = BitVector(OUT_16_MODE, 32)
    io1bit_inst.config[config_addr] = config_data
    assert io1bit_inst.config[config_addr] == config_data
    io1bit_inst.config_read(config_addr)
    assert io1bit_inst.read_data == config_data
    pad = random.randint(0, 1)
    f2p_1 = random.randint(0, 1)
    f2p_16 = random.randint(0, 1)
    res = io1bit_inst(pad, f2p_16, f2p_1)
    assert res == f2p_16

    # Third, test IO output 1bit mode
    io1bit = gen_io1bit()
    io1bit_inst = io1bit()
    config_addr = BitVector(0, 32)
    config_data = BitVector(OUT_1_MODE, 32)
    io1bit_inst.config[config_addr] = config_data
    assert io1bit_inst.config[config_addr] == config_data
    io1bit_inst.config_read(config_addr)
    assert io1bit_inst.read_data == config_data
    pad = random.randint(0, 1)
    f2p_1 = random.randint(0, 1)
    f2p_16 = random.randint(0, 1)
    res = io1bit_inst(pad, f2p_16, f2p_1)
    assert res == f2p_1
