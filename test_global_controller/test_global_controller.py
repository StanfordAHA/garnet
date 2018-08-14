from bit_vector import BitVector
from global_controller.global_controller import gen_global_controller


def test_global_controller_functional_model():
    """
    Small test to show the usage of the GC functional model.
    """
    gc = gen_global_controller(32, 32, 5)
    gc_inst = gc()
    gc_inst.set_config_data_in(24)
    gc_inst.config_read(99)
    res = gc_inst()
    assert res.read[0] == 1
    assert res.config_addr_out[0] == 99
    assert res.config_data_to_jtag[1] == 24
