import math
from bit_vector import BitVector
from common.configurable_model import ConfigurableModel


def gen_simple_cb(width: int,
                  num_tracks: int):
    CONFIG_ADDR_WIDTH = 32
    CONFIG_DATA_WIDTH = 32

    sel_bits = math.ceil(math.log(num_tracks, 2))

    # TODO(rsetaluri): This assert is hacky! Instead we should make the config
    # general for any number of tracks. Furthermore, we should abstract out the
    # config into a separate module.
    assert sel_bits <= CONFIG_DATA_WIDTH

    ParentCls = ConfigurableModel(CONFIG_DATA_WIDTH, CONFIG_ADDR_WIDTH)

    class _SimpleCB(ParentCls):
        def __init__(self):
            super().__init__()

        def __call__(self, *args):
            assert len(args) == num_tracks
            select = self.config[BitVector(0, CONFIG_ADDR_WIDTH)]
            select_as_int = select.unsigned_value
            if select_as_int in range(num_tracks):
                return args[select_as_int]
            return BitVector(0, width)

    return _SimpleCB
