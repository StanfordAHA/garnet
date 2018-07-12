from bit_vector import BitVector
from cb_functional_model import gen_cb

# Small test to show the usage of the cb functional model. For now we can leave
# @num_tracks and @default_value to None.
if __name__ == "__main__":
    cb = gen_cb(16, None, "1111", False, None)
    cb_inst = cb()
    cb_inst.configure(BitVector(0, 32), BitVector(2, 32))
    data = [8, 19, 2, 9]
    res = cb_inst(*data)
    assert res == data[2]
