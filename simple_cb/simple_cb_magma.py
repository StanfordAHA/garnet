import os
import math

import magma as m
import mantle as mantle


def make_name(width, num_tracks):
    return (f"simple_cb_width_{width}"
            f"_num_tracks_{num_tracks}")


def generate_mux(inputs, sel, default=None):
    if default is None:
        height = len(inputs)
        mux_inputs = [i for i in inputs]
    else:
        height = 2 ** m.bitutils.clog2(len(inputs))
        mux_inputs = [i for i in inputs]
        mux_inputs += [default for _ in range(height - len(inputs))]
    return mantle.mux(mux_inputs, sel)


@m.cache_definition
def define_simple_cb(width, num_tracks):
    CONFIG_DATA_WIDTH = 32
    CONFIG_ADDR_WIDTH = 32

    assert num_tracks > 0
    sel_bits = m.bitutils.clog2(num_tracks)
    # TODO(rsetaluri): This assert is hacky! Instead we should make the config
    # general for any number of tracks. Furthermore, we should abstract out the
    # config into a separate module.
    assert sel_bits <= CONFIG_DATA_WIDTH
    config_reset = num_tracks - 1

    T = m.Bits(width)

    class _SimpleCB(m.Circuit):
        name = make_name(width, num_tracks)

        IO = [
            "I", m.In(m.Array(num_tracks, T)),
            "O", m.Out(T),
            "config_addr", m.In(m.Bits(CONFIG_ADDR_WIDTH)),
            "config_data", m.In(m.Bits(CONFIG_DATA_WIDTH)),
            "config_en", m.In(m.Bit),
            "read_data", m.Out(m.Bits(CONFIG_DATA_WIDTH))
        ]
        IO += m.ClockInterface(has_async_reset=True)

        @classmethod
        def definition(io):
            config = mantle.Register(CONFIG_DATA_WIDTH,
                                     init=config_reset,
                                     has_ce=True,
                                     has_async_reset=True)

            config_addr_zero = mantle.eq(m.uint(0, 8), io.config_addr[24:32])
            config(io.config_data, CE=(io.config_en & config_addr_zero))

            # If the top 8 bits of config_addr are 0, then read_data is equal
            # to the value of the config register, otherwise it is 0.
            m.wire(io.read_data,
                   mantle.mux([m.uint(0, CONFIG_DATA_WIDTH), config.O],
                              config_addr_zero))

            # NOTE: This is not robust in the case that the mux which needs more
            # than 32 select bits (i.e. >= 2^32 inputs). This is unlikely to
            # happen, but this code is not general.
            out = generate_mux(io.I, config.O[:sel_bits], m.uint(0, width))
            m.wire(out, io.O)

    return _SimpleCB
