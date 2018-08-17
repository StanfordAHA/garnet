import math
from bit_vector import BitVector


def gen_sb(width: int,
           num_tracks: int,
           sides: int,
           feedthrough_outputs: str,
           registered_outputs: str,
           pe_output_count: int,
           is_bidi: int,
           sb_fs: str):
    CONFIG_DATA_WIDTH = 32
    CONFIG_ADDR_WIDTH = 32

    feedthrough_count = feedthrough_outputs.count("1")
    registered_count = registered_outputs.count("1")
    outputs_driven_per_side = num_tracks - feedthrough_count
    mux_height = (sides - 1) + pe_output_count
    config_bit_count_per_output = math.ceil(math.log(mux_height, 2))
    config_bit_count_per_side = config_bit_count_per_output * \
        outputs_driven_per_side
    config_bit_count_total = config_bit_count_per_side * sides

    if registered_count > 0:
        config_bit_count_total += registered_count * sides
    num_config_regs = math.ceil(config_bit_count_total / CONFIG_DATA_WIDTH)
    reset_val = BitVector(0, CONFIG_DATA_WIDTH)

    class SB:
        def __init__(self):
            self.config = [BitVector(0, CONFIG_DATA_WIDTH)
                           for _ in range(num_config_regs)]
            self.reset()

        def reset(self):
            self.configure(BitVector(0, CONFIG_ADDR_WIDTH), reset_val)
            self.read_data = None
            self.out = [[None for j in range(num_tracks)] for i in range(sides)]

        def configure(self, addr: BitVector, data: BitVector):
            addr_high_bits = addr[24:32]
            config_reg_select = addr_high_bits.as_uint()
            if config_reg_select in range(num_config_regs):
                self.config[config_reg_select] = data

        def __call__(self, *args):
            assert len(args) == (sides * num_tracks+1)
            length = sides * num_tracks+1
            for i in range(0, sides):
                for j in range(0, num_tracks):

                    config_bit_l = (config_bit_count_per_side * i) + \
                        config_bit_count_per_output * j
                    config_bit_h = config_bit_l + \
                        config_bit_count_per_output - 1

                    start = math.floor(config_bit_l / CONFIG_DATA_WIDTH)
                    end = math.floor((config_bit_h - 1) / CONFIG_DATA_WIDTH)
                    lo_int = config_bit_l % CONFIG_DATA_WIDTH
                    hi_int = config_bit_h % CONFIG_DATA_WIDTH

                    if start == end:
                        config_bit_select = self.config[start][lo_int:hi_int+1]
                    config_bit_select_as_int = config_bit_select.as_uint()

                    if (i > config_bit_select_as_int):
                        out_select = config_bit_select_as_int * num_tracks + j
                    else:
                        out_select = (config_bit_select_as_int+1) * \
                            num_tracks + j

                    if (config_bit_select_as_int == mux_height-1):
                        self.out[i][j] = args[sides * num_tracks]
                    else:
                        self.out[i][j] = args[out_select]
            return self.out
    return SB
