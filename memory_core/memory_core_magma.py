import magma
import mantle
from gemstone.common.configurable import ConfigurationType, \
    ConfigRegister, _generate_config_register
from gemstone.common.core import ConfigurableCore, CoreFeature, PnRTag
from gemstone.common.mux_wrapper import MuxWrapper
from gemstone.generator.const import Const
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.from_verilog import FromVerilog
from memory_core import memory_core_genesis2
from typing import List


class MemCore(ConfigurableCore):
    __circuit_cache = {}

    def __init__(self, data_width, word_width, data_depth,
                 num_banks, use_sram_stub):

        super().__init__(8, 32)

        self.data_width = data_width
        self.data_depth = data_depth
        self.num_banks = num_banks
        self.word_width = word_width
        if use_sram_stub:
            self.use_sram_stub = 1
        else:
            self.use_sram_stub = 0

        TData = magma.Bits[self.word_width]
        TBit = magma.Bits[1]

        self.add_ports(
            data_in=magma.In(TData),
            addr_in=magma.In(TData),
            data_out=magma.Out(TData),
            flush=magma.In(TBit),
            wen_in=magma.In(TBit),
            ren_in=magma.In(TBit),

            stall=magma.In(magma.Bits[4]),

            valid_out=magma.Out(TBit),

            switch_db=magma.In(TBit)
        )
        # Instead of a single read_config_data, we have multiple for each
        # "sub"-feature of this core.
        # self.ports.pop("read_config_data")

        if (data_width, word_width, data_depth,
            num_banks, use_sram_stub) not in \
           MemCore.__circuit_cache:

            wrapper = memory_core_genesis2.memory_core_wrapper
            param_mapping = memory_core_genesis2.param_mapping
            generator = wrapper.generator(param_mapping, mode="declare")
            circ = generator(data_width=self.data_width,
                             data_depth=self.data_depth,
                             word_width=self.word_width,
                             num_banks=self.num_banks,
                             use_sram_stub=self.use_sram_stub)
            MemCore.__circuit_cache[(data_width, word_width,
                                     data_depth, num_banks,
                                     use_sram_stub)] = circ
        else:
            circ = MemCore.__circuit_cache[(data_width, word_width,
                                            data_depth, num_banks,
                                            use_sram_stub)]

        self.underlying = FromMagma(circ)

        # put a 1-bit register and a mux to select the control signals
        control_signals = ["wen_in", "ren_in", "flush", "switch_db"]
        for control_signal in control_signals:
            # TODO: consult with Ankita to see if we can use the normal
            # mux here
            mux = MuxWrapper(2, 1, name=f"{control_signal}_sel")
            reg_value_name = f"{control_signal}_reg_value"
            reg_sel_name = f"{control_signal}_reg_sel"
            self.add_config(reg_value_name, 1)
            self.add_config(reg_sel_name, 1)
            self.wire(mux.ports.I[0], self.ports[control_signal])
            self.wire(mux.ports.I[1], self.registers[reg_value_name].ports.O)
            self.wire(mux.ports.S, self.registers[reg_sel_name].ports.O)
            # 0 is the default wire, which takes from the routing network
            self.wire(mux.ports.O[0], self.underlying.ports[control_signal])

        self.wire(self.ports.data_in, self.underlying.ports.data_in)
        self.wire(self.ports.addr_in, self.underlying.ports.addr_in)
        self.wire(self.ports.data_out, self.underlying.ports.data_out)
        self.wire(self.ports.reset, self.underlying.ports.reset)
        self.wire(self.ports.clk, self.underlying.ports.clk)
        self.wire(self.ports.valid_out[0], self.underlying.ports.valid_out)

        # PE core uses clk_en (essentially active low stall)
        self.stallInverter = FromMagma(mantle.DefineInvert(1))
        self.wire(self.stallInverter.ports.I, self.ports.stall[0:1])
        self.wire(self.stallInverter.ports.O[0], self.underlying.ports.clk_en)

        zero_signals = (
            ("chain_wen_in", 1),
            ("chain_in", self.word_width),
        )
        one_signals = (
            ("config_read", 1),
            ("config_write", 1)
        )
        # enable read and write by default
        for name, width in zero_signals:
            val = magma.bits(0, width) if width > 1 else magma.bit(0)
            self.wire(Const(val), self.underlying.ports[name])
        for name, width in one_signals:
            val = magma.bits(1, width) if width > 1 else magma.bit(1)
            self.wire(Const(val), self.underlying.ports[name])
        self.wire(Const(magma.bits(0, 24)),
                  self.underlying.ports.config_addr[0:24])

        # we have five features in total
        # 0:    TILE
        # 1-4:  SMEM
        # Feature 0: Tile
        self.__features: List[CoreFeature] = [self]
        # Features 1-4: SRAM
        for sram_index in range(4):
            core_feature = CoreFeature(self, sram_index + 1)
            self.__features.append(core_feature)

        # Wire the config
        for idx, core_feature in enumerate(self.__features):
            if(idx > 0):
                self.add_port(f"config_{idx}",
                              magma.In(ConfigurationType(8, 32)))
                # port aliasing
                core_feature.ports["config"] = self.ports[f"config_{idx}"]
        self.add_port("config", magma.In(ConfigurationType(8, 32)))

        # or the signal up
        t = ConfigurationType(8, 32)
        t_names = ["config_addr", "config_data"]
        or_gates = {}
        for t_name in t_names:
            port_type = t[t_name]
            or_gate = FromMagma(mantle.DefineOr(len(self.__features),
                                                len(port_type)))
            or_gate.instance_name = f"OR_{t_name}_FEATURE"
            for idx, core_feature in enumerate(self.__features):
                self.wire(or_gate.ports[f"I{idx}"],
                          core_feature.ports.config[t_name])
            or_gates[t_name] = or_gate

        self.wire(or_gates["config_addr"].ports.O,
                  self.underlying.ports.config_addr[24:32])
        self.wire(or_gates["config_data"].ports.O,
                  self.underlying.ports.config_data)

        # only the first one has config_en
#        self.wire(self.__features[0].ports.config.write[0],
#                  self.underlying.ports.config_en)

        # read data out
        for idx, core_feature in enumerate(self.__features):
            if(idx > 0):
                self.add_port(f"read_config_data_{idx}",
                              magma.Out(magma.Bits[32]))
                # port aliasing
                core_feature.ports["read_config_data"] = \
                    self.ports[f"read_config_data_{idx}"]

        # MEM config
        # self.wire(self.ports.read_config_data,
        #          self.underlying.ports.read_config_data)

        configurations = [
            ("stencil_width", 32),
            ("read_mode", 1),
            ("arbitrary_addr", 1),
            ("starting_addr", 32),
            ("iter_cnt", 32),
            ("dimensionality", 32),
            ("circular_en", 1),
            ("almost_count", 4),
            ("enable_chain", 1),
            ("mode", 2),
            ("tile_en", 1),
            ("chain_idx", 4),
            ("depth", 13)
        ]
        # Do all the stuff for the main config
        main_feature = self.__features[0]
        for config_reg_name, width in configurations:
            main_feature.add_config(config_reg_name, width)
            if(width == 1):
                self.wire(main_feature.registers[config_reg_name].ports.O[0],
                          self.underlying.ports[config_reg_name])
            else:
                self.wire(main_feature.registers[config_reg_name].ports.O,
                          self.underlying.ports[config_reg_name])

        for idx in range(8):
            main_feature.add_config(f"stride_{idx}", 32)
            main_feature.add_config(f"range_{idx}", 32)
            self.wire(main_feature.registers[f"stride_{idx}"].ports.O,
                      self.underlying.ports[f"stride_{idx}"])
            self.wire(main_feature.registers[f"range_{idx}"].ports.O,
                      self.underlying.ports[f"range_{idx}"])

        # SRAM
        for sram_index in range(4):
            core_feature = self.__features[sram_index + 1]
            self.wire(core_feature.ports.read_config_data,
                      self.underlying.ports[f"read_data_sram_{sram_index}"])
            # also need to wire the sram signal
            self.wire(core_feature.ports.config.write[0],
                      self.underlying.ports["config_en_sram"][sram_index])

        self._setup_config()

        conf_names = list(self.registers.keys())
        conf_names.sort()
        with open("mem_cfg.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"|{reg}|{idx}|{self.registers[reg].width}||\n"
                cfg_dump.write(write_line)

    def get_reg_index(self, register_name):
        conf_names = list(self.registers.keys())
        conf_names.sort()
        idx = conf_names.index(register_name)
        return idx

    def get_config_bitstream(self, instr):
        raise NotImplementedError()

    def instruction_type(self):
        raise NotImplementedError()

    def inputs(self):
        return [self.ports.data_in, self.ports.addr_in, self.ports.flush,
                self.ports.ren_in, self.ports.wen_in, self.ports.switch_db]

    def outputs(self):
        return [self.ports.data_out, self.ports.valid_out]

    def features(self):
        return self.__features

    def name(self):
        return "MemCore"

    def pnr_info(self):
        return PnRTag("m", self.DEFAULT_PRIORITY, self.DEFAULT_PRIORITY - 1)
