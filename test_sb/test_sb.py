from bit_vector import BitVector
from sb.sb import gen_sb
from random import randint


def test_sb_functional_model():
    """
    Small tests to show the usage of the sb functional model.
    """
    sb = gen_sb(16, 2, 4, "00", "11", 1, 0, 101010)

    # TEST #1
    # First digit of each element in the array is #side
    # second digit is #track
    # This particular pattern is used to debug output incase of wrong result
    # Last element is random PE output
    data = [11, 12, 21, 22, 31, 32, 41, 42, 46]

    # This configuration enables the SB to output the PE output value
    sb_inst = sb()
    sb_inst.reset()
    sb_inst.configure(BitVector(0, 32), BitVector(65535, 32))
    res = sb_inst(*data)
    assert res == [[data[8], data[8]], [data[8], data[8]], [data[8], data[8]], [data[8], data[8]]]    # nopep8

    # TEST #2
    # Random integer inputs to the SB
    data2 = [randint(0, 10000) for j in range(9)]

    # This configuration enables the SB to output the 2nd input to the muxes
    sb_inst2 = sb()
    sb_inst2.reset()
    sb_inst2.configure(BitVector(0, 32), BitVector(43690, 32))
    res2 = sb_inst2(*data2)
    assert res2 == [[data2[6], data2[7]], [data2[6], data2[7]], [data2[6], data2[7]], [data2[4], data2[5]]]  # nopep8
