import os
import math

import magma as m
import mantle as mantle


def run_cmd(cmd):
        res = os.system(cmd)
        assert(res == 0)


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


def generate_output_mux(num_tracks, feedthrough_outputs, has_constant, width,
                        mux_sel_bit_count, constant_bit_count, io,
                        config_register):
    pow_2_tracks = 2**m.bitutils.clog2(num_tracks)
    print('# of tracks =', pow_2_tracks)
    output_mux = mantle.Mux(height=pow_2_tracks, width=width)
    m.wire(output_mux.S, config_register.O[:m.bitutils.clog2(width)])

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

    class ConnectBox(m.Circuit):
        name = make_name(width, num_tracks, has_constant, default_value,
                         feedthrough_outputs)

        # TODO: We chose to use explicit clock interface here so the names
        # match the genesis verilog for regression testing, this should really
        # use m.ClockInterface
        IO = ["clk", m.In(m.Clock),
              "reset", m.In(m.Reset)]

        IO += generate_inputs(num_tracks, feedthrough_outputs, width)

        IO += [
            "out", m.Out(m.Bits(width)),
            "config_addr", m.In(m.Bits(CONFIG_ADDR_WIDTH)),
            "config_data", m.In(m.Bits(CONFIG_DATA_WIDTH)),
            "config_en", m.In(m.Bit),
            "read_data", m.Out(m.Bits(CONFIG_DATA_WIDTH))
        ]

        @classmethod
        def definition(io):
            feedthrough_count = num_tracks
            for i in range(0, len(feedthrough_outputs)):
                feedthrough_count -= feedthrough_outputs[i] == '1'

            mux_sel_bit_count = m.bitutils.clog2(
                num_tracks - feedthrough_count + has_constant)

            constant_bit_count = has_constant * width

            config_bit_count = mux_sel_bit_count + constant_bit_count

            config_reg_width = int(math.ceil(config_bit_count / 32.0)*32)

            reset_val = num_tracks - feedthrough_count + has_constant - 1
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

            config_cb = mantle.Register(config_reg_width,
                                        init=config_reg_reset_bit_vector,
                                        has_ce=True,
                                        has_reset=True)

            config_addr_zero = mantle.eq(m.uint(0, 8), io.config_addr[24:32])

            m.wire(io.config_en & config_addr_zero, config_cb.CE)

            m.wire(config_cb.RESET, io.reset)
            m.wire(config_cb.I, io.config_data)

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

    return ConnectBox


def generate_genesis_cb(p_width,
                        num_tracks,
                        feedthrough_outputs,
                        has_constant,
                        default_value):
        run_cmd('Genesis2.pl -parse -generate ' +
                '-top cb -input ./tests/cb.vp ' +
                '-parameter cb.width=' +
                str(p_width) +
                ' -parameter cb.num_tracks=' +
                str(num_tracks) +
                ' -parameter cb.has_constant=' +
                str(has_constant) +
                ' -parameter cb.default_value=' +
                str(default_value) +
                ' -parameter cb.feedthrough_outputs=' +
                feedthrough_outputs)
