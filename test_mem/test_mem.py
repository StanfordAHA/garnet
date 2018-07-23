import random
from bit_vector import BitVector
from mem.mem import gen_mem


def test_cb_functional_model():
    """
    Small test to show the usage of the memory functional model
    """
    DATA_WIDTH = 4
    DATA_DEPTH = 4
    mem = gen_mem(DATA_DEPTH, DATA_WIDTH)
    mem_inst = mem()

    config_addr = BitVector(0, 32)
    config_data = BitVector(0, 32)
    mem_inst.config[config_addr] = config_data
    assert mem_inst.config[config_addr] == config_data
    num_tests = 4
    data = [random.randint(0, 2 ** DATA_WIDTH - 1) for _ in range(num_tests)]
    addr = [random.randint(0, DATA_DEPTH - 1) for _ in range(num_tests)]
    for data, addr in zip(data, addr):
        mem_inst.write(addr, data)
        assert mem_inst.read(addr) == data
