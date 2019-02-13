import random
from io_core.io16bit import gen_io16bit


def test_io16bit_functional_model():
    """
    io1bit is does nothing but connection from input to output.
    """

    io16bit = gen_io16bit()
    io16bit_inst = io16bit()

    glb2io = random.randint(0, 1)
    f2io = random.randint(0, 1)
    io2glb, io2f = io16bit_inst(glb2io, f2io)

    assert io2glb == f2io
    assert io2f == glb2io
