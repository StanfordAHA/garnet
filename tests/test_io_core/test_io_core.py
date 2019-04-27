import random
from io_core.io_core import gen_io_core


def test_io_core_functional_model():

    io_core = gen_io_core()
    io_core_inst = io_core()

    glb2io_16bit = random.randint(0, 2**16 - 1)
    glb2io_1bit = random.randint(0, 1)
    f2io_16bit = random.randint(0, 2**16 - 1)
    f2io_1bit = random.randint(0, 1)
    io2f_16bit, io2f_1bit, io2glb_16bit, io2glb_1bit = \
        io_core_inst(glb2io_16bit, glb2io_1bit, f2io_16bit, f2io_1bit)

    assert io2glb_16bit == f2io_16bit
    assert io2glb_1bit == f2io_1bit
    assert io2f_16bit == glb2io_16bit
    assert io2f_1bit == glb2io_1bit
