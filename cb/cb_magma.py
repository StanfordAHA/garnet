import os
import math

import magma as m
import mantle as mantle

from common.configurable_circuit import ConfigInterface


def make_name(width, num_tracks, has_constant, default_value,
              feedthrough_outputs):
    return (f"connect_box_width_width_{width}"
            f"_num_tracks_{num_tracks}"
            f"_has_constant{has_constant}"
            f"_default_value{default_value}"
            f"_feedthrough_outputs_{feedthrough_outputs}")


def generate_inputs(num_tracks, feedthrough_outputs, width):
    """
    Example feedthrough_outputs parameter:
        "feedthrough_outputs": "1111101111",
    """
    IO = []
    for i in range(0, num_tracks):
        if (feedthrough_outputs[i] == '1'):
            IO.append(f"in_{i}")
            IO.append(m.In(m.Bits(width)))
    return IO


def generate_reset_value(constant_bit_count, default_value, reset_val,
                         mux_sel_bit_count):
    config_reg_reset_bit_vector = []

    if (constant_bit_count > 0):
        print('constant_bit_count =', constant_bit_count)

        reset_bits = m.bitutils.int2seq(default_value,
                                        constant_bit_count)
        default_bits = m.bitutils.int2seq(reset_val, mux_sel_bit_count)

        print('default val bits =', reset_bits)
        print('reset val bits   =', default_bits)

        # concat before assert
        config_reg_reset_bit_vector += default_bits
        config_reg_reset_bit_vector += reset_bits

        config_reg_reset_bit_vector = \
            m.bitutils.seq2int(config_reg_reset_bit_vector)
        print('reset bit vec as int =', config_reg_reset_bit_vector)

    else:
        config_reg_reset_bit_vector = reset_val

    return config_reg_reset_bit_vector


def generate_output_mux(num_tracks, feedthrough_outputs, has_constant, width,
                        mux_sel_bit_count, constant_bit_count, io,
                        config_register):
    pow_2_tracks = 2**m.bitutils.clog2(num_tracks)
    print('# of tracks =', pow_2_tracks)
    output_mux = mantle.Mux(height=pow_2_tracks, width=width)
    m.wire(output_mux.S, config_register.O[:m.bitutils.clog2(pow_2_tracks)])

    # This is only here because this is the way the switch box numbers
    # things.
    # We really should get rid of this feedthrough parameter
    sel_out = 0
    for i in range(0, pow_2_tracks):
        # in_track = 'I' + str(i)
        if (i < num_tracks):
            if (feedthrough_outputs[i] == '1'):
                m.wire(getattr(output_mux, 'I' + str(sel_out)),
                       getattr(io, 'in_' + str(i)))
                sel_out += 1

    if (has_constant == 0):
        while (sel_out < pow_2_tracks):
            m.wire(getattr(output_mux, 'I' + str(sel_out)), m.uint(0, width))
            sel_out += 1
    else:
        const_val = config_register.O[
            mux_sel_bit_count:
            mux_sel_bit_count + constant_bit_count
        ]
        while (sel_out < pow_2_tracks):
            m.wire(getattr(output_mux, 'I' + str(sel_out)), const_val)
            sel_out += 1
    return output_mux


@m.cache_definition
def define_cb(width, num_tracks, has_constant, default_value,
              feedthrough_outputs):
    CONFIG_DATA_WIDTH = 32
    CONFIG_ADDR_WIDTH = 32

    constant_bit_count = has_constant * width
    feedthrough_count = num_tracks
    for i in range(0, len(feedthrough_outputs)):
        feedthrough_count -= feedthrough_outputs[i] == '1'

    reset_val = num_tracks - feedthrough_count + has_constant - 1

    mux_sel_bit_count = m.bitutils.clog2(
        num_tracks - feedthrough_count + has_constant)

    config_bit_count = mux_sel_bit_count + constant_bit_count

    config_reg_width = int(math.ceil(config_bit_count / 32.0)*32)

    class _CB(m.Circuit):
        name = make_name(width, num_tracks, has_constant, default_value,
                         feedthrough_outputs)

        # TODO: We chose to use explicit clock interface here so the names
        # match the genesis verilog for regression testing, this should really
        # use m.ClockInterface
        IO = ["clk", m.In(m.Clock),
              "reset", m.In(m.AsyncReset)]

        IO += generate_inputs(num_tracks, feedthrough_outputs, width)

        IO += [
            "out", m.Out(m.Bits(width)),
        ]
        IO += ConfigInterface(CONFIG_ADDR_WIDTH, CONFIG_DATA_WIDTH)

        @classmethod
        def definition(io):

            config_reg_reset_bit_vector = \
                generate_reset_value(constant_bit_count, default_value,
                                     reset_val, mux_sel_bit_count)

            config_cb = mantle.Register(config_reg_width,
                                        init=config_reg_reset_bit_vector,
                                        has_ce=True,
                                        has_async_reset=True)

            config_addr_zero = m.bits(0, 8) == io.config_addr[24:32]

            config_cb(io.config_data, CE=m.bit(io.config_en) & config_addr_zero)

            # if the top 8 bits of config_addr are 0, then read_data is equal
            # to the value of the config register, otherwise it is 0
            m.wire(io.read_data,
                   mantle.mux([m.uint(0, 32), config_cb.O],
                              config_addr_zero))

            output_mux = generate_output_mux(num_tracks, feedthrough_outputs,
                                             has_constant, width,
                                             mux_sel_bit_count,
                                             constant_bit_count, io, config_cb)

            # NOTE: This is a dummy! fix it later!
            m.wire(output_mux.O, io.out)
            return

    return _CB
