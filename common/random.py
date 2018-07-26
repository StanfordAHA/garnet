import random
from bit_vector import BitVector


def random_bv(width):
    return BitVector(random.randint(0, (1 << width) - 1), width)


def random_bit():
    return random.randint(0, 1)
