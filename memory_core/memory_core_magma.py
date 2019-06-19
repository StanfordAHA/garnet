import magma
import mantle
from canal.interconnect import Interconnect
from gemstone.common.configurable import ConfigurationType, \
    ConfigRegister, _generate_config_register
from gemstone.common.core import ConfigurableCore, CoreFeature, PnRTag
from gemstone.common.mux_wrapper import MuxWrapper
from gemstone.generator.const import Const
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.from_verilog import FromVerilog
from memory_core import memory_core_genesis2
from typing import List


def config_mem_tile(interconnect: Interconnect, full_cfg, new_config_data, x_place, y_place, mcore_cfg):
    for config_reg, val, feat in new_config_data:
        full_cfg.append((interconnect.get_config_addr(
                         mcore_cfg.get_reg_index(config_reg),
                         feat, x_place, y_place), val))


def chain_pass(interconnect: Interconnect):  # pragma: nocover
    for (x, y) in interconnect.tile_circuits:
        tile = interconnect.tile_circuits[(x, y)]
        tile_core = tile.core
        if isinstance(tile_core, MemCore):
            # lift ports up
            lift_mem_ports(tile, tile_core)

            previous_tile = interconnect.tile_circuits[(x, y - 1)]
            if not isinstance(previous_tile.core, MemCore):
                interconnect.wire(Const(0), tile.ports.chain_wen_in)
                interconnect.wire(Const(0), tile.ports.chain_in)
            else:
                interconnect.wire(previous_tile.ports.chain_valid_out,
                                  tile.ports.chain_wen_in)
                interconnect.wire(previous_tile.ports.chain_out,
                                  tile.ports.chain_in)


def lift_mem_ports(tile, tile_core):  # pragma: nocover
    ports = ["chain_wen_in", "chain_valid_out", "chain_in", "chain_out"]
    for port in ports:
        lift_mem_core_ports(port, tile, tile_core)


def lift_mem_core_ports(port, tile, tile_core):  # pragma: nocover
    tile.add_port(port, tile_core.ports[port].base_type())
    tile.wire(tile.ports[port], tile_core.ports[port])


class MemCore(ConfigurableCore):
    __circuit_cache = {}

    def __init__(self, data_width, word_width, data_depth,
                 num_banks, use_sram_stub, iterator_support=6):

        super().__init__(8, 32)
        self.iterator_support = iterator_support
        self.data_width = data_width
        self.data_depth = data_depth
        self.num_banks = num_banks
        self.word_width = word_width
        if use_sram_stub:
            self.use_sram_stub = 1
        else:
            self.use_sram_stub = 0  # pragma: nocover

        TData = magma.Bits[self.word_width]
        TBit = magma.Bits[1]

        self.add_ports(
            data_in=magma.In(TData),
            addr_in=magma.In(TData),
            data_out=magma.Out(TData),
            flush=magma.In(TBit),
            wen_in=magma.In(TBit),
            ren_in=magma.In(TBit),
            valid_out=magma.Out(TBit),
            switch_db=magma.In(TBit),
            almost_full=magma.Out(TBit),
            almost_empty=magma.Out(TBit),
            full=magma.Out(TBit),
            empty=magma.Out(TBit),
            stall=magma.In(magma.Bits[1]),
            chain_wen_in=magma.In(TBit),
            chain_valid_out=magma.Out(TBit),
            chain_in=magma.In(TData),
            chain_out=magma.Out(TData)
        )

        if (data_width, word_width, data_depth,
            num_banks, use_sram_stub, iterator_support) not in \
            MemCore.__circuit_cache:

            wrapper = memory_core_genesis2.memory_core_wrapper
            param_mapping = memory_core_genesis2.param_mapping
            generator = wrapper.generator(param_mapping, mode="declare")
            circ = generator(data_width=self.data_width,
                             data_depth=self.data_depth,
                             word_width=self.word_width,
                             num_banks=self.num_banks,
                             use_sram_stub=self.use_sram_stub,
                             iterator_support=self.iterator_support)
            MemCore.__circuit_cache[(data_width, word_width,
                                     data_depth, num_banks,
                                     use_sram_stub,
                                     iterator_support)] = circ
        else:
            circ = MemCore.__circuit_cache[(data_width, word_width,
                                            data_depth, num_banks,
                                            use_sram_stub,
                                            iterator_support)]

        self.underlying = FromMagma(circ)

        # put a 1-bit register and a mux to select the control signals
        control_signals = ["wen_in", "ren_in", "flush", "switch_db",
                           "chain_wen_in"]
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
        self.wire(self.ports.almost_empty[0],
                  self.underlying.ports.almost_empty)
        self.wire(self.ports.almost_full[0], self.underlying.ports.almost_full)
        self.wire(self.ports.empty[0], self.underlying.ports.empty)
        self.wire(self.ports.full[0], self.underlying.ports.full)

        self.wire(self.ports.chain_valid_out[0],
                  self.underlying.ports.chain_valid_out)
        self.wire(self.ports.chain_in, self.underlying.ports.chain_in)
        self.wire(self.ports.chain_out, self.underlying.ports.chain_out)

        # PE core uses clk_en (essentially active low stall)
        self.stallInverter = FromMagma(mantle.DefineInvert(1))
        self.wire(self.stallInverter.ports.I, self.ports.stall)
        self.wire(self.stallInverter.ports.O[0], self.underlying.ports.clk_en)

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

        # read data out
        for idx, core_feature in enumerate(self.__features):
            if(idx > 0):
                self.add_port(f"read_config_data_{idx}",
                              magma.Out(magma.Bits[32]))
                # port aliasing
                core_feature.ports["read_config_data"] = \
                    self.ports[f"read_config_data_{idx}"]

        # MEM Config
        configurations = [
            ("stencil_width", 16),
            ("arbitrary_addr", 1),
            ("starting_addr", 16),
            ("iter_cnt", 32),
            ("dimensionality", 4),
            ("circular_en", 1),
            ("almost_count", 4),
            ("enable_chain", 1),
            ("mode", 2),
            ("tile_en", 1),
            ("chain_idx", 4),
            ("depth", 16),
            ("rate_matched", 1)
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

        for idx in range(iterator_support):
            main_feature.add_config(f"stride_{idx}", 16)
            main_feature.add_config(f"range_{idx}", 32)
            self.wire(main_feature.registers[f"stride_{idx}"].ports.O,
                      self.underlying.ports[f"stride_{idx}"])
            self.wire(main_feature.registers[f"range_{idx}"].ports.O,
                      self.underlying.ports[f"range_{idx}"])

        # SRAM
        or_all_cfg_rd = FromMagma(mantle.DefineOr(4, 1))
        or_all_cfg_rd.instance_name = f"OR_CONFIG_WR_SRAM"
        or_all_cfg_wr = FromMagma(mantle.DefineOr(4, 1))
        or_all_cfg_wr.instance_name = f"OR_CONFIG_RD_SRAM"
        for sram_index in range(4):
            core_feature = self.__features[sram_index + 1]
            self.add_port(f"config_en_{sram_index}", magma.In(magma.Bit))
            # port aliasing
            core_feature.ports["config_en"] = \
                self.ports[f"config_en_{sram_index}"]
            self.wire(core_feature.ports.read_config_data,
                      self.underlying.ports[f"read_data_sram_{sram_index}"])
            # also need to wire the sram signal
            # the config enable is the OR of the rd+wr
            or_gate_en = FromMagma(mantle.DefineOr(2, 1))
            or_gate_en.instance_name = f"OR_CONFIG_EN_SRAM_{sram_index}"

            self.wire(or_gate_en.ports.I0, core_feature.ports.config.write)
            self.wire(or_gate_en.ports.I1, core_feature.ports.config.read)
            self.wire(core_feature.ports.config_en,
                      self.underlying.ports["config_en_sram"][sram_index])
            # Still connect to the OR of all the config rd/wr
            self.wire(core_feature.ports.config.write,
                      or_all_cfg_wr.ports[f"I{sram_index}"])
            self.wire(core_feature.ports.config.read,
                      or_all_cfg_rd.ports[f"I{sram_index}"])

        self.wire(or_all_cfg_rd.ports.O[0], self.underlying.ports.config_read)
        self.wire(or_all_cfg_wr.ports.O[0], self.underlying.ports.config_write)
        self._setup_config()

        conf_names = list(self.registers.keys())
        conf_names.sort()
        with open("mem_cfg.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"|{reg}|{idx}|{self.registers[reg].width}||\n"
                cfg_dump.write(write_line)
        with open("mem_synth.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"{reg}\n"
                cfg_dump.write(write_line)

    def get_reg_index(self, register_name):
        conf_names = list(self.registers.keys())
        conf_names.sort()
        idx = conf_names.index(register_name)
        return idx

    def get_config_bitstream(self, instr):
        configs = []
        mode_config = (self.get_reg_index("mode"), instr["mode"].value)
        if "depth" in instr and ("is_ub" not in instr or (not instr["is_ub"])):
            depth_config = (self.get_reg_index("depth"), instr["depth"])
            rate_matched = (self.get_reg_index("rate_matched"), 1)
            iter_cnt = (self.get_reg_index("iter_cnt"), instr["depth"])
            dimensionality = (self.get_reg_index("dimensionality"), 1)
            stride_0 = (self.get_reg_index("stride_0"), 1)
            range_0 = (self.get_reg_index("range_0"), instr["depth"])
            switch_db = (self.get_reg_index("switch_db_reg_sel"), 1)

            configs += [depth_config, rate_matched, iter_cnt, dimensionality,
                        stride_0, range_0, switch_db]
        if "content" in instr:
            # this is SRAM content
            content = instr["content"]
            for addr, data in enumerate(content):
                if (not isinstance(data, int)) and len(data) == 2:
                    addr, data = data
                feat_addr = addr // 256 + 1
                addr = addr % 256
                configs.append((addr, feat_addr, data))
        if "chain_en" in instr:
            configs += [(self.get_reg_index("enable_chain"), instr["chain_en"])]
            assert "chain_idx" in instr
            configs += [(self.get_reg_index("chain_idx"), instr["chain_idx"])]
        else:
            configs += [(self.get_reg_index("chain_wen_in_reg_sel"), 1)]
        if "chain_wen_in_sel" in instr:
            assert "chain_wen_in_reg" in instr
            configs += [(self.get_reg_index("chain_wen_in_reg_sel"),
                         instr["chain_wen_in_sel"]),
                        (self.get_reg_index("chain_wen_in_reg_value"),
                         instr["chain_wen_in_reg"])]
        # double buffer stuff
        if "is_ub" in instr and instr["is_ub"]:
            print("configuring unified buffer", instr)
            # unified buffer
            configs += [(self.get_reg_index("rate_matched"),
                         instr["rate_matched"]),
                        (self.get_reg_index("stencil_width"),
                         instr["stencil_width"]),
                        (self.get_reg_index("iter_cnt"),
                         instr["iter_cnt"]),
                        (self.get_reg_index("dimensionality"),
                         instr["dimensionality"]),
                        (self.get_reg_index("stride_0"),
                         instr["stride_0"]),
                        (self.get_reg_index("range_0"),
                         instr["range_0"]),
                        (self.get_reg_index("stride_1"),
                         instr["stride_1"]),
                        (self.get_reg_index("range_1"),
                         instr["range_1"]),
                        (self.get_reg_index("stride_2"),
                         instr["stride_2"]),
                        (self.get_reg_index("range_2"),
                         instr["range_2"]),
                        (self.get_reg_index("stride_3"),
                         instr["stride_3"]),
                        (self.get_reg_index("range_3"),
                         instr["range_3"]),
                        (self.get_reg_index("starting_addr"),
                         instr["starting_addr"]),
                        (self.get_reg_index("depth"),
                         instr["depth"])]
        tile_en = (self.get_reg_index("tile_en"), 1)
        # disable double buffer switch db for now
        switch_db_sel = (self.get_reg_index("switch_db_reg_sel"), 1)
        return [mode_config, tile_en, switch_db_sel] + configs

    def instruction_type(self):
        raise NotImplementedError()  # pragma: nocover

    def inputs(self):
        return [self.ports.data_in, self.ports.addr_in, self.ports.flush,
                self.ports.ren_in, self.ports.wen_in, self.ports.switch_db,
                self.ports.chain_wen_in, self.ports.chain_in]

    def outputs(self):
        return [self.ports.data_out, self.ports.valid_out,
                self.ports.almost_empty, self.ports.almost_full,
                self.ports.empty, self.ports.full, self.ports.chain_valid_out,
                self.ports.chain_out]

    def features(self):
        return self.__features

    def name(self):
        return "MemCore"

    def pnr_info(self):
        return PnRTag("m", self.DEFAULT_PRIORITY - 1, self.DEFAULT_PRIORITY)
