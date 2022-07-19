from gemstone.common.testers import BasicTester
from canal.util import IOSide
import magma
import mantle
from canal.interconnect import Interconnect
from gemstone.common.configurable import ConfigurationType
from gemstone.common.core import ConfigurableCore, CoreFeature, PnRTag
from gemstone.common.mux_wrapper import MuxWrapper
from gemstone.generator.from_magma import FromMagma
from typing import List
# from memory_core.intersect_core import IntersectCore
from gemstone.common.util import compress_config_data
# from memory_core.scanner_core import ScannerCore
from lake.top.extract_tile_info import *
from archipelago import pnr
# from cgra.util import create_cgra

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
                 ready_valid=False,
                 name="LakeBase_inst"):

        self.__name = name
        self.__inputs = []
        self.__outputs = []
        self.__blacklist = []
        self.__features = []
        self.data_width = data_width
        self.__gate_flush = gate_flush
        self.__ready_valid = ready_valid
        self.__combinational_ports = set()

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
                intf_type = magma.Bits[io_info.port_width]
            # Due to some tooling weirdness, I've also included a way to explicitly mark
            # a wire as a "full" (16b) bus...
            elif io_info.full_bus:
                ind_ports = 1
                intf_type = magma.Bits[io_info.port_width]
            dir_type = magma.In
            app_list = self.__inputs
            if io_info.port_dir == "PortDirection.Out":
                dir_type = magma.Out
                app_list = self.__outputs
            if ind_ports > 1:
                for i in range(ind_ports):
                    self.add_port(f"{io_info.port_name}_{i}", dir_type(intf_type))
                    if '_ready' in io_info.port_name or '_valid' in io_info.port_name:
                        pass
                    else:
                        app_list.append(self.ports[f"{io_info.port_name}_{i}"])
            else:
                self.add_port(io_info.port_name, dir_type(intf_type))
                if '_ready' in io_info.port_name or '_valid' in io_info.port_name:
                    pass
                else:
                    app_list.append(self.ports[io_info.port_name])

            # Blacklist flush from ready/validness...
            if io_info.port_name == 'flush':
                self.__blacklist.append(self.ports[io_info.port_name])

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

        # ready valid interface
        if self.__ready_valid:
            port_names = self.ports.keys()
            self.__combinational_ports.add("flush")
            for p in self.__inputs:
                name = p.qualified_name()
                if name in self.__combinational_ports:
                    continue
                ready_name = name + "_ready"
                valid_name = name + "_valid"
                # Only add dummy if they don't already exist
                if valid_name in port_names and ready_name in port_names:
                    continue
                p = self.add_port(ready_name, magma.BitOut)
                self.add_port(valid_name, magma.BitIn)
                # valid is floating
                self.wire(p, magma.Const(1))
            for p in self.__outputs:
                name = p.qualified_name()
                if name in self.__combinational_ports:
                    continue
                ready_name = name + "_ready"
                valid_name = name + "_valid"
                if valid_name in port_names and ready_name in port_names:
                    continue
                self.add_port(ready_name, magma.BitIn)
                p = self.add_port(valid_name, magma.BitOut)
                # ready is floating
                self.wire(p, magma.Const(1))

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

    def combinational_ports(self):
        return self.__combinational_ports

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


class CoreMappingUndefinedException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


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
        self._config_finalized = False
        self._circuit = None
        self._core_names = {}
        self._core_used = {}
        self._dest_counts = {}
        self._core_remappings = {}
        self._core_runtime_mode = {}
        self._core_map = {}

    def register_core(self, core, flushable=False, config=None, name=""):
        ''' Register the core/primitive with the
            data structure and return unique ID
        '''
        # self.core_map = {
        #         "register": "r",
        #         "io_16": "I",
        #         "io_1": "i",
        #         "pe": "p",
        #         "fake_pe": "f",
        #         "scanner": "s",
        #         "intersect": "j",
        #         "memtile": "m",
        #         "regcore": "R",
        #         "lookup": "L"
        #     }

        # if core not in self.core_map:
        #     tag = core.pnr_info().tag_name
        #     # raise CoreMappingUndefinedException
        # else:
        #     tag = self.core_map[core]

        cc_core_supported = None

        if core == "scanner":
            core = "read_scanner"

        for core_key, core_value in self._interconnect.tile_circuits.items():
            # print(f"{core_key}, {core_value.name()}")
            if "CoreCombiner" in core_value.name():
                # print("Found core combiner...")
                # Get supported components
                cc_core = core_value.core
                cc_core_supported = cc_core.get_modes_supported()
                # print(f"Modes: {cc_core_supported}")

        prioritize_combiner = True

        core_remapping = None

        print_diag = False

        # Choose the core combiner if the resource is in there...
        if cc_core_supported is not None and core in cc_core_supported and prioritize_combiner:
            tag = "C"
            # tag = cc_core.pnr_info().get_tag_name()
            core_remapping = cc_core.get_port_remap()[core]
            print_diag = True
            cc_core.set_runtime_mode(core)
        elif core == "register":
            tag = "r"
        elif core == "io_16":
            tag = "I"
        elif core == "io_1":
            tag = "i"
        elif core == "pe":
            tag = "p"
        elif core == "fake_pe":
            tag = "f"
        elif core == "scanner":
            tag = "s"
        elif core == "intersect":
            tag = "j"
        elif core == "memtile":
            tag = "m"
        elif core == "regcore":
            tag = "R"
        elif core == "lookup":
            tag = "L"
        elif core == "write_scanner":
            tag = "w"
        elif core == "buffet":
            tag = "B"
        elif core == "glb":
            tag = "G"
        elif core == "repeat":
            tag = "Q"
        elif core == "repeat_signal_generator":
            tag = "q"
        else:
            tag = core.pnr_info().tag_name

        ret_str = f"{tag}{self._core_num}"
        if print_diag:
            print(f"Did this on: {ret_str}")
        if flushable:
            self._flushable.append(ret_str)
        self._cores.append(ret_str)
        self._core_num += 1
        self._core_names[ret_str] = name
        self._core_used[ret_str] = 0
        if core_remapping is not None:
            self._core_remappings[ret_str] = core_remapping
            self._core_runtime_mode[ret_str] = core
        if config is not None:
            self._core_config[ret_str] = (config, 0)
        return ret_str

    def add_connections_dict(self, connection_dict, defer_placement=False):
        for conn_block_name, connections_list in connection_dict.items():
            print(f"Adding connection block: {conn_block_name}")
            assert isinstance(connections_list, list), f"Expecting list of connections at: {conn_block_name}"
            self.add_connections(connections_list, defer_placement=defer_placement)

    def add_connections(self, connections, defer_placement=False, verbose=False):
        if isinstance(connections, dict):
            self.add_connections_dict(connections, defer_placement=defer_placement)
        else:
            for connection, width in connections:
                self.add_connection(connection, width)
        self._placement_up_to_date = False
        if defer_placement:
            if verbose:
                print("Deferring new placement...")
        else:
            if verbose:
                print("Used add connections...automatically updating placement + routing")
            self.generate_placement()

    def add_connection(self, connection, width):
        # print(connection)
        conn_name = f"e{self._connection_num}"
        self._connection_num += 1
        # Dissect the connection to check if a core is used
        for (core, io_name) in connection:
            self._core_used[core] = 1
        # Add sink counts to prevent multiple drivers
        skip_source = True
        for (core, io_name) in connection:
            if skip_source is False:
                if (core, io_name) not in self._dest_counts:
                    self._dest_counts[(core, io_name)] = 1
                else:
                    self._dest_counts[(core, io_name)] += 1
            skip_source = False
        self._netlist[conn_name] = connection
        self._bus[conn_name] = width
        self._placement_up_to_date = False

    def get_name(self, prim_name):
        assert prim_name in self._core_names.keys(), f"{prim_name} not a valid primitive in this netlist"
        return self._core_names[prim_name]

    def display_names(self):
        for key, val in self._core_names.items():
            print(f"{key}\t===>\t{val}")

    def get_netlist(self):
        return self._netlist

    def get_bus(self):
        return self._bus

    def get_full_info(self):
        return (self.get_netlist(), self.get_bus())

    def generate_placement(self):
        # Check for multiple drivers...
        for (core, io_name), num_drivers in self._dest_counts.items():
            # print(f"Core: {core}/{self._core_names[core]}: Pin: {io_name}, Num_Drivers: {num_drivers}")
            if num_drivers > 1:
                print("MORE THAN 1 DRIVER!!!!")
                print(f"Core: {core}/{self._core_names[core]}: Pin: {io_name}, Num_Drivers: {num_drivers}")
                raise RuntimeError
        if self._placement_up_to_date:
            return

        # Do remapping here...
        for conn_name, connection_list in self._netlist.items():
            for i, connection_tuple in enumerate(connection_list):
                mapped_core, signal_name = connection_tuple
                if mapped_core in self._core_remappings:
                    # print(f"Signal {signal_name} being remapped according to {self._core_remappings[mapped_core]}")
                    if signal_name == "flush":
                        continue
                    assert signal_name in self._core_remappings[mapped_core]
                    remapped_sig = self._core_remappings[mapped_core][signal_name]
                    self._netlist[conn_name][i] = (mapped_core, remapped_sig)

        print("Done remapping...")

        self._placement, self._routing, _ = pnr(self._interconnect, (self._netlist, self._bus), cwd=self._cwd, harden_flush=False)
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
        """Returns the final configuration stream for programming the app

        Returns:
            list: final bitstream to plug into the chip
        """
        if self._config_finalized:
            return self._config_data
        else:
            print("Config not finalized...finalizing")
            self.finalize_config()
            return self._config_data

    def get_placement(self):
        if self._placement_up_to_date is False:
            self.generate_placement()
        return self._placement

    def get_handle(self, core, prefix="glb2io_1_X"):
        self.get_placement()
        if core in self._placement:
            core_x, core_y = self._placement[core]
        else:
            print(f"Core {core}/{self._core_names[core]} not in placement...can't get handle...")
            raise RuntimeError
        return self._circuit.interface[f"{prefix}X{core_x:02X}_Y{core_y:02X}"]

    def get_handle_str(self, base_sig):
        return self._circuit.interface[base_sig]

    def get_core_runtimes(self):
        return self._core_runtime_mode

    def get_core_object(self, mapped_name):
        return self._core_names

    def add_config(self, new_config):
        self._config_data += new_config

    def get_flushable(self):
        return self._flushable

    def connections_from_json(self, conn_json):
        """Returns high-level connections for building netlist from json

        Args:
            conn_json (list): List of connections to use

        Returns:
            list: concatenated list from json
        """
        ret_conns = []
        for conn_block_name, connections_list in conn_json.items():
            print(f"Adding connection block: {conn_block_name}")
            assert isinstance(connections_list, list), f"Expecting list of connections at: {conn_block_name}"
            ret_conns += connections_list
        return ret_conns

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
        # Also generate placement..
        self.generate_placement()
        skip_addr = self._interconnect.get_skip_addr()
        self._config_data = compress_config_data(self._config_data, skip_compression=skip_addr)
        # Check for unused potential handles...
        for core, used in self._core_used.items():
            if used == 0:
                print(f"Core {core} is not being used...any accesses to its handle will cause a crash...")
        self._config_finalized = True
        self._circuit = self._interconnect.circuit()

    def get_tester(self):
        assert self._interconnect is not None, "Need to define the interconnect first..."
        # self._circuit = self._interconnect.circuit()
        self._tester = BasicTester(self._circuit, self._circuit.clk, self._circuit.reset)
        return self._tester

    def get_circuit(self):
        # self._circuit = self._interconnect.circuit()
        return self._circuit

    def get_config_data(self):
        return self._config_data

    def configure_circuit(self, readback=False):
        cfgdat = self._config_data
        for addr, index in cfgdat:
            self._tester.configure(addr, index)
            if readback is True:
                self._tester.config_read(addr)
            self._tester.eval()

    @staticmethod
    def io_sides():
        return IOSide.North | IOSide.East | IOSide.South | IOSide.West
