from gemstone.common.util import compress_config_data
import magma
import tempfile
from magma.logging import flush
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
from archipelago import pnr


class LakeCoreBase(ConfigurableCore):

    _circuit_cache = {}

    def __init__(self,
                 config_data_width=32,
                 config_addr_width=8,
                 data_width=16,
                 name="LakeBase_inst"):

        self.__name = name
        self.__inputs = []
        self.__outputs = []
        self.__features = []
        self.data_width = data_width

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

        # for port_name, port_size, port_width, is_ctrl, port_dir, explicit_array, full_bus in core_interface:
        for io_info in core_interface:
            if io_info.port_name in skip_names:
                continue
            ind_ports = io_info.port_width
            intf_type = TBit
            # For our purposes, an explicit array means the inner data HAS to be 16 bits
            if io_info.expl_arr:
                ind_ports = io_info.port_size[0]
                intf_type = TData
            # Due to some tooling weirdness, I've also included a way to explicitly mark
            # a wire as a "full" (16b) bus...
            elif io_info.full_bus:
                ind_ports = 1
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
                                              io_info.port_name,
                                              io_info.full_bus))
                else:
                    other_signals.append((io_info.port_name,
                                          io_info.port_dir,
                                          io_info.expl_arr,
                                          0,
                                          io_info.port_name,
                                          io_info.full_bus))

        assert(len(self.__outputs) > 0)

        # We call clk_en stall at this level for legacy reasons????
        self.add_ports(
            stall=magma.In(TBit),
        )

        # put a 1-bit register and a mux to select the control signals
        for control_signal, width in control_signals:
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
        for pname, pdir, expl_arr, ind, uname, full_bus in other_signals:
            # If we are in an explicit array moment, use the given wire name...
            if full_bus is True:
                self.wire(self.ports[pname], self.underlying.ports[pname])
            elif expl_arr is False:
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

        self._setup_config()

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


class NetlistBuilder():

    def __init__(self, interconnect: Interconnect = None, cwd=None) -> None:
        # self._registered_cores = {}
        self._netlist = {}
        self._bus = {}
        self._connection_num = 0
        self._core_num = 0
        assert interconnect is not None, "Can't build on blank interconnect"
        self._interconnect = interconnect
        self._placement = None
        self._routing = None
        self._placement_up_to_date = False
        self._config_data = None
        self._cwd = cwd
        self._config_data = []
        self._flushable = []
        self._cores = []
        self._core_config = {}

    def register_core(self, core, flushable=False, config=None):
        ''' Register the core/primitive with the
            data structure and return unique ID
        '''
        if core == "register":
            tag = "r"
        elif core == "io_16":
            tag = "I"
        elif core == "io_1":
            tag = "i"
        elif core == "pe":
            tag = "p"
        elif core == "scanner":
            tag = "s"
        elif core == "intersect":
            tag = "j"
        elif core == "memtile":
            tag = "m"
        elif core == "regcore":
            tag = "R"
        else:
            tag = core.pnr_info().tag_name

        ret_str = f"{tag}{self._core_num}"
        if flushable:
            self._flushable.append(ret_str)
        self._cores.append(ret_str)
        self._core_num += 1
        if config is not None:
            self._core_config[ret_str] = (config, 0)
        return ret_str

    def add_connections_dict(self, connection_dict):
        for conn_block_name, connections_list in connection_dict.items():
            print(f"Adding connection block: {conn_block_name}")
            assert isinstance(connections_list, list), f"Expecting list of connections at: {conn_block_name}"
            self.add_connections(connections_list)

    def add_connections(self, connections):
        if isinstance(connections, dict):
            self.add_connections_dict(connections)
        else:
            for connection, width in connections:
                self.add_connection(connection, width)
        self._placement_up_to_date = False
        print("Used add connections...automatically updating placement + routing")
        self.generate_placement()

    def add_connection(self, connection, width):
        conn_name = f"e{self._connection_num}"
        self._connection_num += 1
        self._netlist[conn_name] = connection
        self._bus[conn_name] = width
        self._placement_up_to_date = False

    def get_netlist(self):
        return self._netlist

    def get_bus(self):
        return self._bus

    def get_full_info(self):
        return (self.get_netlist(), self.get_bus())

    def generate_placement(self):
        if self._placement_up_to_date:
            return
        self._placement, self._routing = pnr(self._interconnect, (self._netlist, self._bus), cwd=self._cwd)
        self._placement_up_to_date = True

    def get_route_config(self):
        if self._placement_up_to_date is False:
            print("Routing/Placement out of date...updating")
            self.generate_placement()
        if len(self._config_data) > 0:
            print("Clearing config data - it was previously not empty")
            self._config_data = []
        self._config_data += self._interconnect.get_route_bitstream(self._routing)
        return self._config_data

    def get_config_data(self):
        return self._config_data

    def get_placement(self):
        if self._placement_up_to_date is False:
            self.generate_placement()
        return self._placement

    def get_handle(self, core, prefix="glb2io_1_X"):
        self.get_placement()
        core_x, core_y = self._placement[core]
        return f"{prefix}X{core_x:02X}_Y{core_y:02X}"

    def add_config(self, new_config):
        self._config_data += new_config

    def get_flushable(self):
        return self._flushable

    def emit_flush_connection(self, flush_handle):
        return [([(flush_handle, "io2f_1"), *[(x, "flush") for x in self._flushable]], 1)]

    def configure_tile(self, core, config, pnr_tag=None):
        # print(f"cores: {self._cores}")
        kwargs = {}
        if pnr_tag is not None:
            kwargs["pnr_tag"] = pnr_tag
        if self._placement_up_to_date is False:
            print("Routing/Placement out of date...updating")
            self.generate_placement()
            self.get_route_config()
        core_x, core_y = self._placement[core]
        core_config_data = self._interconnect.configure_placement(core_x, core_y, config, **kwargs)
        self._config_data += core_config_data

    def finalize_config(self):
        skip_addr = self._interconnect.get_skip_addr()
        self._config_data = compress_config_data(self._config_data, skip_compression=skip_addr)
