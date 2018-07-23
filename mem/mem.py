from common.configurable_model import ConfigurableModel
import functools
from bit_vector import BitVector


def check_addr(fn):
    @functools.wraps(fn)
    def wrapped(self, addr, *args):
        if not (0 <= addr < self.data_depth):
            raise ValueError(f"Invalid address ({addr}),"
                             f" must be within range(0, {self.data_depth})")
        return fn(self, addr, *args)
    return wrapped


def gen_mem(data_width: int,
            data_depth: int):
    class Mem(ConfigurableModel(32, 32)):
        def __init__(self):
            super().__init__()
            self.memory = {}
            self.data_depth = data_depth

        def __call__(self):
            # TODO: Should this define a __call__? What should the semantics
            # be?
            return

        @check_addr
        def read(self, addr):
            return self.memory[addr]

        @check_addr
        def write(self, addr, value):
            if isinstance(value, BitVector) and value.num_bits > data_width:
                raise ValueError(f"value.num_bits must be <= {data_width}")
            elif isinstance(value, int) and value.bit_length() > data_width:
                raise ValueError(f"value.bit_length() must be <= {data_width}")
            self.memory[addr] = value
    return Mem
