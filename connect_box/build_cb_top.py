import os
import math
import mantle as mantle

import magma as m

def power_log(x):
        return 2**(math.ceil(math.log(x, 2)))

def equals_cmp(a, b, width):
        eqC = mantle.EQ(width)
        m.wire(eqC.I0, a)
        m.wire(eqC.I1, b)

        return eqC

@m.cache_definition
def define_connect_box(width, num_tracks, has_constant, default_value, feedthrough_outputs):
    class ConnectBox(m.Circuit):
        name = f"connect_box_width_width_{str(width)}_num_tracks_{str(num_tracks)}_has_constant{str(has_constant)}_default_value{str(default_value)}_feedthrough_outputs_{feedthrough_outputs}"
        CONFIG_DATA_WIDTH = 32
        CONFIG_ADDR_WIDTH = 32

        IO = ["clk", m.In(m.Clock),
              "reset", m.In(m.Reset),
              "config_en", m.In(m.Bit),
              "config_data", m.In(m.Bits(CONFIG_DATA_WIDTH)),
              "config_addr", m.In(m.Bits(CONFIG_ADDR_WIDTH)),
              "read_data", m.Out(m.Bits(CONFIG_DATA_WIDTH)),
              "out", m.Out(m.Bits(width))]

        for i in range(0, num_tracks):
            if (feedthrough_outputs[i] == '1'):
                IO.append("in_" + str(i))
                IO.append(m.In(m.Bits(width)))
            
        @classmethod
        def definition(io):
            feedthrough_count = num_tracks
            for i in range(0, len(feedthrough_outputs)):
                feedthrough_count -= feedthrough_outputs[i] == '1'

            mux_sel_bit_count = int(math.ceil(math.log(num_tracks - feedthrough_count + has_constant, 2)))

            constant_bit_count = has_constant * width

            config_bit_count = mux_sel_bit_count + constant_bit_count

            config_reg_width = int(math.ceil(config_bit_count / 32.0)*32)

            config_addrs_needed = int(math.ceil(config_bit_count / 32.0))

            reset_val = num_tracks - feedthrough_count + has_constant - 1
            config_reg_reset_bit_vector = []

            CONFIG_DATA_WIDTH = 32
            CONFIG_ADDR_WIDTH = 32

            if (constant_bit_count > 0):
                print('constant_bit_count =', constant_bit_count)

                reset_bits = m.bitutils.int2seq(default_value, constant_bit_count)
                default_bits = m.bitutils.int2seq(reset_val, mux_sel_bit_count)

                print('default val bits =', reset_bits)
                print('reset val bits   =', default_bits)

                # concat before assert
                config_reg_reset_bit_vector += default_bits
                config_reg_reset_bit_vector += reset_bits

                config_reg_reset_bit_vector = m.bitutils.seq2int(config_reg_reset_bit_vector)
                print('reset bit vec as int =', config_reg_reset_bit_vector)
                
                #assert(len(config_reg_reset_bit_vector) == config_reg_width)

            else:
                config_reg_reset_bit_vector = reset_val

            config_cb = mantle.Register(config_reg_width,
                                        init=config_reg_reset_bit_vector,
                                        has_ce=True,
                                        has_reset=True)

            config_addr_zero = mantle.EQ(8)
            m.wire(m.uint(0, 8), config_addr_zero.I0)
            m.wire(config_addr_zero.I1, io.config_addr[24:32])

            config_en_set = mantle.And(2, 1)
            m.wire(config_en_set.I0, m.uint(1, 1))
            m.wire(config_en_set.I1[0], io.config_en)


            config_en_set_and_addr_zero = mantle.And(2, 1)
            m.wire(config_en_set_and_addr_zero.I0, config_en_set.O)
            m.wire(config_en_set_and_addr_zero.I1[0], config_addr_zero.O)

            m.wire(config_en_set_and_addr_zero.O[0], config_cb.CE)

            config_set_mux = mantle.Mux(height=2, width=CONFIG_DATA_WIDTH)
            m.wire(config_set_mux.I0, config_cb.O)
            m.wire(config_set_mux.I1, io.config_addr)
            m.wire(config_set_mux.S, config_en_set_and_addr_zero.O[0])

            m.wire(config_cb.RESET, io.reset)
            m.wire(config_cb.I, io.config_data)

            # Setting read data
            read_data_mux = mantle.Mux(height=2, width=CONFIG_DATA_WIDTH)
            m.wire(read_data_mux.S, equals_cmp(io.config_addr[24:32], m.uint(0, 8), 8).O)
            m.wire(read_data_mux.I1, config_cb.O)
            m.wire(read_data_mux.I0, m.uint(0, 32))

            m.wire(io.read_data, read_data_mux.O)

            pow_2_tracks = power_log(num_tracks)
            print('# of tracks =', pow_2_tracks)
            output_mux = mantle.Mux(height=pow_2_tracks, width=width)
            m.wire(output_mux.S, config_cb.O[0:math.ceil(math.log(width, 2))])

            # TODO: Get the cgrainfo.txt working

            # Note: Uncomment this line for select to make the unit test fail!
            #m.wire(output_mux.S, m.uint(0, math.ceil(math.log(width, 2))))

            # This is only here because this is the way the switch box numbers things.
            # We really should get rid of this feedthrough parameter
            sel_out = 0
            for i in range(0, pow_2_tracks):
                in_track = 'I' + str(i)
                if (i < num_tracks):
                        if (feedthrough_outputs[i] == '1'):
                                m.wire(getattr(output_mux, 'I' + str(sel_out)), getattr(io, 'in_' + str(i)))
                                sel_out += 1

            while (sel_out < pow_2_tracks):
                m.wire(getattr(output_mux, 'I' + str(sel_out)), m.uint(0, width))
                sel_out += 1
                
                
            # NOTE: This is a dummy! fix it later!
            m.wire(output_mux.O, io.out)
            return

    return ConnectBox


param_width = 16
param_num_tracks = 10
param_feedthrough_outputs = "1111101111"
param_has_constant = 1
param_default_value = 7

cb = define_connect_box(param_width, param_num_tracks, param_has_constant, param_default_value, param_feedthrough_outputs)
m.compile(cb.name, cb, output='coreir')
os.system('coreir -i ' + cb.name + '.json -o ' + cb.name + '.v')

os.system('Genesis2.pl -parse -generate -top cb -input cb.vp -parameter cb.width=' + str(param_width) + ' -parameter cb.num_tracks=' + str(param_num_tracks) + ' -parameter cb.has_constant=' + str(param_has_constant) + ' -parameter cb.default_value=' + str(param_default_value) + ' -parameter cb.feedthrough_outputs=' + param_feedthrough_outputs)

os.system('./run_sim.sh')

