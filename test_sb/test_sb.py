from bit_vector import BitVector
from sb.sb import gen_sb


def test_sb_functional_model():
    """
    Small tests to show the usage of the sb functional model.
    """
    sb = gen_sb(16, 2, 4, "00", "11", 1, 0, 101010)
    sb_inst = sb()
    sb_inst.reset()
    sb_inst.configure(BitVector(0, 32), BitVector(65535, 32))
    data = [11, 12, 21, 22, 31, 32, 41, 42, 46]
    res = sb_inst(*data)
    assert res == [[data[8], data[8]], [data[8], data[8]], [data[8], data[8]], [data[8], data[8]]]    # nopep8

    sb_inst2 = sb()
    sb_inst2.reset()
    sb_inst2.configure(BitVector(0, 32), BitVector(43690, 32))
    res2 = sb_inst2(*data)
    assert res2 == [[data[6], data[7]], [data[6], data[7]], [data[6], data[7]], [data[4], data[5]]]  # nopep8
