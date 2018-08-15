from bit_vector import BitVector
from global_controller.global_controller import gen_global_controller
import fault
import random


def test_global_controller_functional_model():
    """
    Small test to show the usage of the GC functional model.
    """
    CONFIG_DATA_WIDTH = 32
    CONFIG_ADDR_WIDTH = 32
    CONFIG_OP_WIDTH = 5
    gc = gen_global_controller(CONFIG_DATA_WIDTH,
                               CONFIG_ADDR_WIDTH,
                               CONFIG_OP_WIDTH)
    gc_inst = gc()
    max_config_data = (2**CONFIG_DATA_WIDTH) - 1
    max_config_addr = (2**CONFIG_ADDR_WIDTH) - 1
    # Set some data to read later
    random_input = random.randint(1, max_config_data)
    gc_inst.set_config_data_in(random_input)

    random_addr = random.randint(1, max_config_addr)
    # read the random input data
    gc_inst.config_read(random_addr)
    res = gc_inst()
    # assert read immediately
    assert res.read[0] == 1
    # Read must be deasserted by the end of the top
    assert res.read[-1] == 0
    assert res.config_addr_out[0] == random_addr
    assert res.config_data_to_jtag[-1] == random_input
