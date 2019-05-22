import magma
import mantle
from gemstone.common.configurable import ConfigurationType, ConfigRegister,  _generate_config_register
from gemstone.common.core import ConfigurableCore, CoreFeature, PnRTag
from gemstone.common.coreir_wrap import CoreirWrap
from gemstone.generator.const import Const
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.from_verilog import FromVerilog
from memory_core import memory_core_genesis2
from typing import List
import coreir


class MemCore(ConfigurableCore):
    def __init__(self, data_width, word_width, data_depth,
                 num_banks, simple_config=0):
        super().__init__(8, 32)

        self.data_width = data_width
        self.data_depth = data_depth
        self.num_banks = num_banks
        self.word_width = word_width

        TData = magma.Bits[self.word_width]
        TBit = magma.Bits[1]

        self.add_ports(
            clk_in=magma.In(magma.Clock),
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
        self.ports.pop("read_config_data")

        wrapper = memory_core_genesis2.memory_core_wrapper
        param_mapping = memory_core_genesis2.param_mapping
        generator = wrapper.generator(param_mapping, mode="declare")
        circ = generator(data_width=self.data_width,
                         data_depth=self.data_depth,
                         word_width=self.word_width,
                         num_banks=self.num_banks)
        self.underlying = FromMagma(circ)

        self.wire(self.ports.data_in, self.underlying.ports.data_in)
        self.wire(self.ports.addr_in, self.underlying.ports.addr_in)
        self.wire(self.ports.data_out, self.underlying.ports.data_out)
        self.wire(self.ports.reset, self.underlying.ports.reset)
        self.wire(self.ports.clk_in, self.underlying.ports.clk_in)
        self.wire(self.ports.flush[0], self.underlying.ports.flush)
        self.wire(self.ports.wen_in[0], self.underlying.ports.wen_in)
        self.wire(self.ports.ren_in[0], self.underlying.ports.ren_in)
        self.wire(self.ports.switch_db[0], self.underlying.ports.switch_db)
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
        #self.__features: List[CoreFeature] = [CoreFeature(self, 0)]
        # Features 1-4: SRAM
        for sram_index in range(4):
            core_feature = CoreFeature(self, sram_index + 1)
            self.__features.append(core_feature)
        # Feature 5: LINEBUF
        # self.__features.append(CoreFeature(self, 5))
        # Feature 6:    FIFO
        # self.__features.append(CoreFeature(self, 6))
        # Feature 7:    DB
        # self.__features.append(CoreFeature(self, 7))

        # Wire the config
        for idx, core_feature in enumerate(self.__features):
            self.add_port(f"config_{idx}", magma.In(ConfigurationType(8, 32)))
            # port aliasing
            core_feature.ports["config"] = self.ports[f"config_{idx}"]
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
            self.add_port(f"read_config_data_{idx}",
                          magma.Out(magma.Bits[32]))
            # port aliasing
            core_feature.ports["read_config_data"] = \
                self.ports[f"read_config_data_{idx}"]

        # MEM config
  #      self.wire(self.ports.read_config_data_0,
  #                self.underlying.ports.read_data)


        # Do all the stuff for the main config
        main_feature = self.__features[0]
        main_feature.add_config("stencil_width", 32)
        #main_feature.registers["stencil_width"] = ConfigRegister(32, False, "stencil_width")
        self.wire(main_feature.registers["stencil_width"].ports.O,
                  self.underlying.ports["stencil_width"])

        main_feature.add_config("read_mode", 1)
        self.wire(main_feature.registers["read_mode"].ports.O,
                  self.underlying.ports["read_mode"])

        main_feature.add_config("arbitrary_addr", 2)
        self.wire(main_feature.registers["arbitrary_addr"].ports.O,
                  self.underlying.ports["arbitrary_addr"])

        main_feature.add_config("starting_addr", 32)
        self.wire(main_feature.registers["starting_addr"].ports.O,
                  self.underlying.ports["starting_addr"])

        main_feature.add_config("iter_cnt", 32)
        self.wire(main_feature.registers["iter_cnt"].ports.O,
                  self.underlying.ports["iter_cnt"])

        main_feature.add_config("dimensionality", 32)
        self.wire(main_feature.registers["dimensionality"].ports.O,
                  self.underlying.ports["dimensionality"])

        main_feature.add_config("circular_en", 1)
        self.wire(main_feature.registers["circular_en"].ports.O,
                  self.underlying.ports["circular_en"])

        main_feature.add_config("almost_count", 4)
        self.wire(main_feature.registers["almost_count"].ports.O,
                  self.underlying.ports["almost_count"])

        main_feature.add_config("enable_chain", 1)
        self.wire(main_feature.registers["enable_chain"].ports.O,
                  self.underlying.ports["enable_chain"])

        main_feature.add_config("mode", 2)
        self.wire(main_feature.registers["mode"].ports.O,
                  self.underlying.ports["mode"])

        main_feature.add_config("tile_en", 1)
        self.wire(main_feature.registers["tile_en"].ports.O,
                  self.underlying.ports["tile_en"])

        main_feature.add_config("chain_idx", 4)
        self.wire(main_feature.registers["chain_idx"].ports.O,
                  self.underlying.ports["chain_idx"])

        main_feature.add_config("depth", 13)
        self.wire(main_feature.registers["depth"].ports.O,
                  self.underlying.ports["depth"])

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
        # LINEBUF
#        core_feature = self.__features[5]
#        self.add_config("stencil_width", 32)
#        self.wire(self.registers["stencil_width"].ports.O,
#                  self.underlying.ports["stencil_width"])

#        self.wire(core_feature.ports.read_config_data,
#                  self.underlying.ports["read_data_linebuf"])
#        self.wire(core_feature.ports.config.write[0],
#                  self.underlying.ports["config_en_linebuf"])

        # FIFO
#        core_feature = self.__features[6]
#        self.wire(core_feature.ports.read_config_data,
#                  self.underlying.ports["read_data_fifo"])
#        self.wire(core_feature.ports.config.write[0],
#                  self.underlying.ports["config_en_fifo"])
        # DB
#        core_feature = self.__features[7]
#        self.wire(core_feature.ports.read_config_data,
#                  self.underlying.ports["read_data_db"])
#        self.wire(core_feature.ports.config.write[0],
#                  self.underlying.ports["config_en_db"])

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
