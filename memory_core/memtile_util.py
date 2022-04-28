import magma
import tempfile
import mantle
import urllib.request
import collections
from canal.interconnect import Interconnect
from gemstone.common.configurable import ConfigurationType, \
    ConfigRegister, _generate_config_register
from gemstone.common.core import ConfigurableCore, CoreFeature, PnRTag
from gemstone.common.mux_wrapper import MuxWrapper
from gemstone.generator.const import Const
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.from_verilog import FromVerilog
from typing import List
from lake.top.lake_top import LakeTop
from lake.top.pond import Pond
from lake.passes.passes import change_sram_port_names
from lake.passes.passes import lift_config_reg
from lake.utils.sram_macro import SRAMMacroInfo
from lake.top.extract_tile_info import *
from lake.utils.parse_clkwork_csv import generate_data_lists
import lake.utils.parse_clkwork_config as lake_parse_conf
from lake.utils.util import get_configs_dict, set_configs_sv, extract_formal_annotation
import math
import kratos as kts

ONYX_PORT_REMAP = {
    'FIFO': {
        'data_in_0': 'input_width_16_num_0',
        'ren_in_0': 'input_width_1_num_0',
        'wen_in_0': 'input_width_1_num_1',
        'data_out_0': 'output_width_16_num_0',
        'valid_out_0': 'output_width_1_num_2',
        'empty': 'output_width_1_num_0',
        'full': 'output_width_1_num_1',
    },
    'UB': {
        'chain_data_in_0': 'input_width_16_num_0',
        'chain_data_in_1': 'input_width_16_num_1',
        'data_in_0': 'input_width_16_num_2',
        'data_in_1': 'input_width_16_num_3',
        'valid_out_0': 'output_width_1_num_0',
        'valid_out_1': 'output_width_1_num_1',
        'data_out_0': 'output_width_16_num_0',
        'data_out_1': 'output_width_16_num_1',
    },
    'RAM': {
        'rd_addr_in_0': 'input_width_16_num_1',
        'wr_addr_in_0': 'input_width_16_num_2',
        'data_in_0': 'input_width_16_num_0',
        'data_out_0': 'output_width_16_num_0',
        'ren_in_0': 'input_width_1_num_0',
        'wen_in_0': 'input_width_1_num_1',
    },
    'ROM': {
        'rd_addr_in_0': 'input_width_16_num_2',
        'data_out_0': 'output_width_16_num_0',
        'ren_in_0': 'input_width_1_num_0',
    },
    'STENCIL_VALID': {
        'stencil_valid': 'output_width_1_num_3'
    }
}


class LakeCoreBase(ConfigurableCore):

    _circuit_cache = {}

    def __init__(self,
                 config_data_width=32,
                 config_addr_width=8,
                 data_width=16,
                 gate_flush=True,
                 name="LakeBase_inst"):

        self.__name = name
        self.__inputs = []
        self.__outputs = []
        self.__features = []
        self.data_width = data_width
        self.__gate_flush = gate_flush

        super().__init__(config_addr_width=config_addr_width,
                         config_data_width=config_data_width)

    def wrap_lake_core(self):
        # Typedefs for ease
        if self.data_width:
            TData = magma.Bits[self.data_width]
        else:
            TData = magma.Bits[16]  # This shouldn't be used if the data_width was None
        TBit = magma.Bits[1]
        # Enumerate input and output ports
        # (clk and reset are assumed)
        core_interface = get_interface(self.dut)
        cfgs = extract_top_config(self.dut)
        assert len(cfgs) > 0, "No configs?"

        # We basically add in the configuration bus differently
        # than the other ports...
        skip_names = ["config_data_in",
                      "config_write",
                      "config_addr_in",
                      "config_data_out",
                      "config_read",
                      "config_en",
                      "clk_en"]

        # Create a list of signals that will be able to be
        # hardwired to a constant at runtime...
        control_signals = []
        # The rest of the signals to wire to the underlying representation...
        other_signals = []

        # for port_name, port_size, port_width, is_ctrl, port_dir, explicit_array in core_interface:
        for io_info in core_interface:
            if io_info.port_name in skip_names:
                continue
            ind_ports = io_info.port_width
            intf_type = TBit
            # For our purposes, an explicit array means the inner data HAS to be 16 bits
            if io_info.expl_arr:
                ind_ports = io_info.port_size[0]
                intf_type = TData
            dir_type = magma.In
            app_list = self.__inputs
            if io_info.port_dir == "PortDirection.Out":
                dir_type = magma.Out
                app_list = self.__outputs
            if ind_ports > 1:
                for i in range(ind_ports):
                    self.add_port(f"{io_info.port_name}_{i}", dir_type(intf_type))
                    app_list.append(self.ports[f"{io_info.port_name}_{i}"])
            else:
                self.add_port(io_info.port_name, dir_type(intf_type))
                app_list.append(self.ports[io_info.port_name])

            # classify each signal for wiring to underlying representation...
            if io_info.is_ctrl:
                control_signals.append((io_info.port_name, io_info.port_width))
            else:
                if ind_ports > 1:
                    for i in range(ind_ports):
                        other_signals.append((f"{io_info.port_name}_{i}",
                                              io_info.port_dir,
                                              io_info.expl_arr,
                                              i,
                                              io_info.port_name))
                else:
                    other_signals.append((io_info.port_name,
                                          io_info.port_dir,
                                          io_info.expl_arr,
                                          0,
                                          io_info.port_name))

        assert(len(self.__outputs) > 0)

        # We call clk_en stall at this level for legacy reasons????
        self.add_ports(
            stall=magma.In(TBit),
        )

        # put a 1-bit register and a mux to select the control signals
        for control_signal, width in control_signals:
            if control_signal == "flush" and not self.__gate_flush:
                continue
            if width == 1:
                mux = MuxWrapper(2, 1, name=f"{control_signal}_sel")
                reg_value_name = f"{control_signal}_reg_value"
                reg_sel_name = f"{control_signal}_reg_sel"
                self.add_config(reg_value_name, 1)
                self.add_config(reg_sel_name, 1)
                self.wire(mux.ports.I[0], self.ports[control_signal])
                self.wire(mux.ports.I[1], self.registers[reg_value_name].ports.O)
                self.wire(mux.ports.S, self.registers[reg_sel_name].ports.O)
                # 0 is the default wire, which takes from the routing network
                self.wire(mux.ports.O[0], self.underlying.ports[control_signal][0])
            else:
                for i in range(width):
                    mux = MuxWrapper(2, 1, name=f"{control_signal}_{i}_sel")
                    reg_value_name = f"{control_signal}_{i}_reg_value"
                    reg_sel_name = f"{control_signal}_{i}_reg_sel"
                    self.add_config(reg_value_name, 1)
                    self.add_config(reg_sel_name, 1)
                    self.wire(mux.ports.I[0], self.ports[f"{control_signal}_{i}"])
                    self.wire(mux.ports.I[1], self.registers[reg_value_name].ports.O)
                    self.wire(mux.ports.S, self.registers[reg_sel_name].ports.O)
                    # 0 is the default wire, which takes from the routing network
                    self.wire(mux.ports.O[0], self.underlying.ports[control_signal][i])

        # Wire the other signals up...
        for pname, pdir, expl_arr, ind, uname in other_signals:
            # If we are in an explicit array moment, use the given wire name...
            if expl_arr is False:
                # And if not, use the index
                self.wire(self.ports[pname][0], self.underlying.ports[uname][ind])
            else:
                self.wire(self.ports[pname], self.underlying.ports[pname])

        # CLK, RESET, and STALL PER STANDARD PROCEDURE

        # Need to invert this
        self.resetInverter = FromMagma(mantle.DefineInvert(1))
        self.wire(self.resetInverter.ports.I[0],
                  self.convert(self.ports.reset, magma.bit))
        self.wire(self.convert(self.resetInverter.ports.O[0],
                               magma.asyncreset),
                  self.underlying.ports.rst_n)
        self.wire(self.ports.clk, self.underlying.ports.clk)

        # Mem core uses clk_en (essentially active low stall)
        self.stallInverter = FromMagma(mantle.DefineInvert(1))
        self.wire(self.stallInverter.ports.I, self.ports.stall)
        self.wire(self.stallInverter.ports.O[0], self.underlying.ports.clk_en[0])

        # we have six? features in total
        # 0:    TILE
        # 1:    TILE
        # 1-4:  SMEM
        # Feature 0: Tile
        self.__features: List[CoreFeature] = [self]
        # Features 1-4: SRAM
        self.num_sram_features = self.dut.total_sets
        for sram_index in range(self.num_sram_features):
            core_feature = CoreFeature(self, sram_index + 1)
            core_feature.skip_compression = True
            self.__features.append(core_feature)

        # Wire the config
        for idx, core_feature in enumerate(self.__features):
            if(idx > 0):
                self.add_port(f"config_{idx}",
                              magma.In(ConfigurationType(self.config_addr_width, self.config_data_width)))
                # port aliasing
                core_feature.ports["config"] = self.ports[f"config_{idx}"]
        self.add_port("config", magma.In(ConfigurationType(self.config_addr_width, self.config_data_width)))

        if self.num_sram_features > 0:
            # or the signal up
            t = ConfigurationType(self.config_addr_width, self.config_data_width)
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
                      self.underlying.ports.config_addr_in[0:self.config_addr_width])
            self.wire(or_gates["config_data"].ports.O,
                      self.underlying.ports.config_data_in)

        # read data out
        for idx, core_feature in enumerate(self.__features):
            if(idx > 0):
                # self.add_port(f"read_config_data_{idx}",
                self.add_port(f"read_config_data_{idx}",
                              magma.Out(magma.Bits[self.config_data_width]))
                # port aliasing
                core_feature.ports["read_config_data"] = \
                    self.ports[f"read_config_data_{idx}"]

        # MEM Config
        configurations = []
        # merged_configs = []
        skip_cfgs = []

        for cfg_info in cfgs:
            if cfg_info.port_name in skip_cfgs:
                continue
            if cfg_info.expl_arr:
                if cfg_info.port_size[0] > 1:
                    for i in range(cfg_info.port_size[0]):
                        configurations.append((f"{cfg_info.port_name}_{i}", cfg_info.port_width))
                else:
                    configurations.append((cfg_info.port_name, cfg_info.port_width))
            else:
                configurations.append((cfg_info.port_name, cfg_info.port_width))

        # Do all the stuff for the main config
        main_feature = self.__features[0]
        for config_reg_name, width in configurations:
            main_feature.add_config(config_reg_name, width)
            if(width == 1):
                self.wire(main_feature.registers[config_reg_name].ports.O[0],
                          self.underlying.ports[config_reg_name][0])
            else:
                self.wire(main_feature.registers[config_reg_name].ports.O,
                          self.underlying.ports[config_reg_name])

        # SRAM
        # These should also account for num features
        # or_all_cfg_rd = FromMagma(mantle.DefineOr(4, 1))
        if self.num_sram_features > 0:
            or_all_cfg_rd = FromMagma(mantle.DefineOr(self.num_sram_features, 1))
            or_all_cfg_rd.instance_name = f"OR_CONFIG_WR_SRAM"
            or_all_cfg_wr = FromMagma(mantle.DefineOr(self.num_sram_features, 1))
            or_all_cfg_wr.instance_name = f"OR_CONFIG_RD_SRAM"

            for sram_index in range(self.num_sram_features):
                core_feature = self.__features[sram_index + 1]
                self.add_port(f"config_en_{sram_index}", magma.In(magma.Bit))
                # port aliasing
                core_feature.ports["config_en"] = \
                    self.ports[f"config_en_{sram_index}"]
                # Sort of a temp hack - the name is just config_data_out
                if self.num_sram_features == 1:
                    self.wire(core_feature.ports.read_config_data,
                              self.underlying.ports["config_data_out"])
                else:
                    self.wire(core_feature.ports.read_config_data,
                              self.underlying.ports[f"config_data_out_{sram_index}"])
                and_gate_en = FromMagma(mantle.DefineAnd(2, 1))
                and_gate_en.instance_name = f"AND_CONFIG_EN_SRAM_{sram_index}"
                # also need to wire the sram signal
                # the config enable is the OR of the rd+wr
                or_gate_en = FromMagma(mantle.DefineOr(2, 1))
                or_gate_en.instance_name = f"OR_CONFIG_EN_SRAM_{sram_index}"

                self.wire(or_gate_en.ports.I0, core_feature.ports.config.write)
                self.wire(or_gate_en.ports.I1, core_feature.ports.config.read)
                self.wire(and_gate_en.ports.I0, or_gate_en.ports.O)
                self.wire(and_gate_en.ports.I1[0], core_feature.ports.config_en)
                self.wire(and_gate_en.ports.O[0],
                          self.underlying.ports["config_en"][sram_index])
                # Still connect to the OR of all the config rd/wr
                self.wire(core_feature.ports.config.write,
                          or_all_cfg_wr.ports[f"I{sram_index}"])
                self.wire(core_feature.ports.config.read,
                          or_all_cfg_rd.ports[f"I{sram_index}"])

            self.wire(or_all_cfg_rd.ports.O[0], self.underlying.ports.config_read[0])
            self.wire(or_all_cfg_wr.ports.O[0], self.underlying.ports.config_write[0])

    def get_config_bitstream(self, instr):
        return

    def get_static_bitstream(self):
        return

    def instruction_type(self):
        raise NotImplementedError()  # pragma: nocover

    def inputs(self):
        return self.__inputs

    def outputs(self):
        return self.__outputs

    def features(self):
        return self.__features

    def name(self):
        return self.__name

    def pnr_info(self):
        return PnRTag("blank", self.DEFAULT_PRIORITY - 1, self.DEFAULT_PRIORITY)

    def num_data_inputs(self):
        return self.interconnect_input_ports

    def num_data_outputs(self):
        return self.interconnect_output_ports
