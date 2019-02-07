import random
from io_core.io1bit import gen_io1bit


def test_io1bit_functional_model():
    """
    io1bit is does nothing but connection from input to output.
    """

    io1bit=gen_io1bit()
    io1bit_inst=io1bit()

    glb2io = random.randint(0, 1)
    f2io = random.randint(0, 1)
    io2glb, io2f = io1bit_inst(glb2io, f2io)

    assert io2glb == f2io
    assert io2f == glb2io
