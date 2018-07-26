import math
from bit_vector import BitVector
from common.configurable_model import ConfigurableModel


def gen_simple_cb(width: int,
                  num_tracks: int):
    CONFIG_ADDR_WIDTH = 32
    CONFIG_DATA_WIDTH = 32
    CONFIG_ADDR = BitVector(0, CONFIG_ADDR_WIDTH)

    sel_bits = math.ceil(math.log(num_tracks, 2))

    # TODO(rsetaluri): This assert is hacky! Instead we should make the config
    # general for any number of tracks. Furthermore, we should abstract out the
    # config into a separate module.
    assert sel_bits <= CONFIG_DATA_WIDTH

    ParentCls = ConfigurableModel(CONFIG_DATA_WIDTH, CONFIG_ADDR_WIDTH)

    class _SimpleCB(ParentCls):
        def __init__(self):
            super().__init__()
            self.__reset()

        def __reset(self):
            self.last_clock = None
            self.out = None
            self.read_data = None
            self.config[CONFIG_ADDR] = BitVector(0, 32)

        def __call__(self, clk, reset, *args):
            config_addr, config_data, config_en = args[-3:]
            inputs = args[:-3]
            assert len(inputs) == num_tracks, f"{len(inputs)} != {num_tracks}"
            if reset:
                self.__reset()
            else:
                if config_en and clk and not self.last_clock:
                    self.config[CONFIG_ADDR] = config_data
                self.last_clock = clk
                select = self.config[CONFIG_ADDR]
                select_as_int = select.unsigned_value
                if select_as_int in range(num_tracks):
                    self.out = inputs[select_as_int]
                else:
                    self.out = BitVector(0, width)
            # TODO: set self.read_data
            return self.out, self.read_data

    return _SimpleCB
