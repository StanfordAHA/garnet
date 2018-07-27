import random
from bit_vector import BitVector
from simple_cb.simple_cb import gen_simple_cb


def test_cb_functional_model():
    """
    Small test to show the usage of the simple cb functional model.
    """
    WIDTH = 16
    NUM_TRACKS = 10
    SELECT_INDEX = 2
    simple_cb = gen_simple_cb(WIDTH, NUM_TRACKS)
    simple_cb_inst = simple_cb()

    config_addr = BitVector(0, 32)
    config_data = BitVector(SELECT_INDEX, 32)
    simple_cb_inst.config[config_addr] = config_data
    assert simple_cb_inst.config[config_addr] == config_data
    data = [random.randint(0, 2 ** WIDTH - 1) for _ in range(NUM_TRACKS)]
    res = simple_cb_inst(*data)
    assert res == data[SELECT_INDEX]
