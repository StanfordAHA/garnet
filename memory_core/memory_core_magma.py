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
from memory_core import memory_core_genesis2
from typing import List
from lake.top.lake_top import LakeTop
from lake.passes.passes import change_sram_port_names
from lake.passes.passes import lift_config_reg
from lake.utils.sram_macro import SRAMMacroInfo
from lake.top.extract_tile_info import *
from lake.utils.parse_clkwork_csv import generate_data_lists
import lake.utils.parse_clkwork_config as lake_parse_conf
from lake.utils.util import get_configs_dict, set_configs_sv, extract_formal_annotation
import math
import kratos as kts

ControllerInfo = collections.namedtuple('ControllerInfo',
                                        'dim extent cyc_stride data_stride cyc_strt data_strt')


def config_mem_tile(interconnect: Interconnect, full_cfg, new_config_data, x_place, y_place, mcore_cfg):
    for config_reg, val, feat in new_config_data:
        idx, value = mcore_cfg.get_config_data(config_reg, val)
        full_cfg.append((interconnect.get_config_addr(
                         idx,
                         feat, x_place, y_place), value))


def chain_pass(interconnect: Interconnect):  # pragma: nocover
    for (x, y) in interconnect.tile_circuits:
        tile = interconnect.tile_circuits[(x, y)]
        tile_core = tile.core
        if isinstance(tile_core, MemCore):
            # lift ports up
            lift_mem_ports(tile, tile_core)

            previous_tile = interconnect.tile_circuits[(x, y - 1)]
            if not isinstance(previous_tile.core, MemCore):
                interconnect.wire(Const(0), tile.ports.chain_valid_in)
                interconnect.wire(Const(0), tile.ports.chain_data_in)
            else:
                interconnect.wire(previous_tile.ports.chain_valid_out,
                                  tile.ports.chain_valid_in)
                interconnect.wire(previous_tile.ports.chain_data_out,
                                  tile.ports.chain_data_in)


def transform_strides_and_ranges(ranges, strides, dimensionality):
    assert len(ranges) == len(strides), "Strides and ranges should be same length..."
    tform_ranges = [range_item - 2 for range_item in ranges[0:dimensionality]]
    range_sub_1 = [range_item - 1 for range_item in ranges]
    tform_strides = [strides[0]]
    offset = 0
    for i in range(dimensionality - 1):
        offset -= (range_sub_1[i] * strides[i])
        tform_strides.append(strides[i + 1] + offset)
    for j in range(len(ranges) - dimensionality):
        tform_strides.append(0)
        tform_ranges.append(0)
    return (tform_ranges, tform_strides)


def lift_mem_ports(tile, tile_core):  # pragma: nocover
    ports = ["chain_wen_in", "chain_valid_out", "chain_in", "chain_out"]
    for port in ports:
        lift_mem_core_ports(port, tile, tile_core)


def lift_mem_core_ports(port, tile, tile_core):  # pragma: nocover
    tile.add_port(port, tile_core.ports[port].base_type())
    tile.wire(tile.ports[port], tile_core.ports[port])


def get_pond(use_sram_stub=1):
    return MemCore(data_width=16,  # CGRA Params
                   mem_width=16,
                   mem_depth=32,
                   banks=1,
                   input_iterator_support=2,  # Addr Controllers
                   output_iterator_support=2,
                   input_config_width=16,
                   output_config_width=16,
                   interconnect_input_ports=1,  # Connection to int
                   interconnect_output_ports=1,
                   mem_input_ports=1,
                   mem_output_ports=1,
                   use_sram_stub=use_sram_stub,
                   read_delay=0,  # Cycle delay in read (SRAM vs Register File)
                   rw_same_cycle=True,  # Does the memory allow r+w in same cycle?
                   agg_height=0,
                   max_agg_schedule=16,
                   input_max_port_sched=16,
                   output_max_port_sched=16,
                   align_input=0,
                   max_line_length=128,
                   max_tb_height=1,
                   tb_range_max=1024,
                   tb_range_inner_max=16,
                   tb_sched_max=16,
                   max_tb_stride=15,
                   num_tb=0,
                   tb_iterator_support=2,
                   multiwrite=1,
                   max_prefetch=8,
                   config_data_width=32,
                   config_addr_width=8,
                   num_tiles=1,
                   app_ctrl_depth_width=16,
                   fifo_mode=False,
                   add_clk_enable=True,
                   add_flush=True,
                   core_reset_pos=False,
                   stcl_valid_iter=4,
                   override_name="Pond")


class MemCore(ConfigurableCore):
    __circuit_cache = {}

    def __init__(self,
                 data_width=16,  # CGRA Params
                 mem_width=64,
                 mem_depth=512,
                 banks=1,
                 input_iterator_support=6,  # Addr Controllers
                 output_iterator_support=6,
                 input_config_width=16,
                 output_config_width=16,
                 interconnect_input_ports=2,  # Connection to int
                 interconnect_output_ports=2,
                 mem_input_ports=1,
                 mem_output_ports=1,
                 use_sram_stub=True,
                 sram_macro_info=SRAMMacroInfo("TS1N16FFCLLSBLVTC512X32M4S",
                                               wtsel_value=0, rtsel_value=1),
                 read_delay=1,  # Cycle delay in read (SRAM vs Register File)
                 rw_same_cycle=False,  # Does the memory allow r+w in same cycle?
                 agg_height=4,
                 tb_sched_max=16,
                 config_data_width=32,
                 config_addr_width=8,
                 num_tiles=1,
                 fifo_mode=True,
                 add_clk_enable=True,
                 add_flush=True,
                 override_name=None,
                 gen_addr=True):

        # name
        if override_name:
            self.__name = override_name + "Core"
            lake_name = override_name
        else:
            self.__name = "MemCore"
            lake_name = "LakeTop"

        super().__init__(config_addr_width, config_data_width)

        # Capture everything to the tile object
        self.data_width = data_width
        self.mem_width = mem_width
        self.mem_depth = mem_depth
        self.banks = banks
        self.fw_int = int(self.mem_width / self.data_width)
        self.input_iterator_support = input_iterator_support
        self.output_iterator_support = output_iterator_support
        self.input_config_width = input_config_width
        self.output_config_width = output_config_width
        self.interconnect_input_ports = interconnect_input_ports
        self.interconnect_output_ports = interconnect_output_ports
        self.mem_input_ports = mem_input_ports
        self.mem_output_ports = mem_output_ports
        self.use_sram_stub = use_sram_stub
        self.sram_macro_info = sram_macro_info
        self.read_delay = read_delay
        self.rw_same_cycle = rw_same_cycle
        self.agg_height = agg_height
        self.config_data_width = config_data_width
        self.config_addr_width = config_addr_width
        self.num_tiles = num_tiles
        self.fifo_mode = fifo_mode
        self.add_clk_enable = add_clk_enable
        self.add_flush = add_flush
        self.gen_addr = gen_addr
        # self.app_ctrl_depth_width = app_ctrl_depth_width
        # self.stcl_valid_iter = stcl_valid_iter

        # Typedefs for ease
        TData = magma.Bits[self.data_width]
        TBit = magma.Bits[1]

        self.__inputs = []
        self.__outputs = []

        cache_key = (self.data_width, self.mem_width, self.mem_depth, self.banks,
                     self.input_iterator_support, self.output_iterator_support,
                     self.interconnect_input_ports, self.interconnect_output_ports,
                     self.use_sram_stub, self.sram_macro_info, self.read_delay,
                     self.rw_same_cycle, self.agg_height, self.config_data_width, self.config_addr_width,
                     self.num_tiles, self.fifo_mode,
                     self.add_clk_enable, self.add_flush, self.gen_addr)

        # Check for circuit caching
        if cache_key not in MemCore.__circuit_cache:

            # Instantiate core object here - will only use the object representation to
            # query for information. The circuit representation will be cached and retrieved
            # in the following steps.
            self.lt_dut = LakeTop(data_width=self.data_width,
                                  mem_width=self.mem_width,
                                  mem_depth=self.mem_depth,
                                  banks=self.banks,
                                  input_iterator_support=self.input_iterator_support,
                                  output_iterator_support=self.output_iterator_support,
                                  input_config_width=self.input_config_width,
                                  output_config_width=self.output_config_width,
                                  interconnect_input_ports=self.interconnect_input_ports,
                                  interconnect_output_ports=self.interconnect_output_ports,
                                  use_sram_stub=self.use_sram_stub,
                                  sram_macro_info=self.sram_macro_info,
                                  read_delay=self.read_delay,
                                  rw_same_cycle=self.rw_same_cycle,
                                  agg_height=self.agg_height,
                                  config_data_width=self.config_data_width,
                                  config_addr_width=self.config_addr_width,
                                  num_tiles=self.num_tiles,
                                  fifo_mode=self.fifo_mode,
                                  add_clk_enable=self.add_clk_enable,
                                  add_flush=self.add_flush,
                                  name=lake_name,
                                  gen_addr=self.gen_addr)

            change_sram_port_pass = change_sram_port_names(use_sram_stub, sram_macro_info)
            circ = kts.util.to_magma(self.lt_dut,
                                     flatten_array=True,
                                     check_multiple_driver=False,
                                     optimize_if=False,
                                     check_flip_flop_always_ff=False,
                                     additional_passes={"change_sram_port": change_sram_port_pass})
            MemCore.__circuit_cache[cache_key] = (circ, self.lt_dut)
        else:
            circ, self.lt_dut = MemCore.__circuit_cache[cache_key]

        # Save as underlying circuit object
        self.underlying = FromMagma(circ)

        # Enumerate input and output ports
        # (clk and reset are assumed)
        core_interface = get_interface(self.lt_dut)
        cfgs = extract_top_config(self.lt_dut)
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

        self.chain_idx_bits = max(1, kts.clog2(self.num_tiles))

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
        self.wire(self.resetInverter.ports.I[0], self.ports.reset)
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
        self.num_sram_features = self.lt_dut.total_sets
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

        conf_names = list(self.registers.keys())
        conf_names.sort()
        with open("mem_cfg.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"(\"{reg}\", 0),  # {self.registers[reg].width}\n"
                cfg_dump.write(write_line)
        with open("mem_synth.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"{reg}\n"
                cfg_dump.write(write_line)

    def get_config_bitstream(self, instr):
        configs = []
        if "init" in instr['config'][1]:
            config_mem = [("tile_en", 1),
                          ("mode", 2),
                          ("wen_in_0_reg_sel", 1),
                          ("wen_in_1_reg_sel", 1)]
            for name, v in config_mem:
                configs = [self.get_config_data(name, v)] + configs
            # this is SRAM content
            content = instr['config'][1]['init']
            for addr, data in enumerate(content):
                if (not isinstance(data, int)) and len(data) == 2:
                    addr, data = data
                feat_addr = addr // 256 + 1
                addr = (addr % 256) >> 2
                configs.append((addr, feat_addr, data))
            print(configs)
            return configs

        # unified buffer buffer stuff
        if "is_ub" in instr and instr["is_ub"]:
            depth = instr["range_0"]
            instr["depth"] = depth
            print("configure ub to have depth", depth)
        if "depth" in instr:
            # need to download the csv and get configuration files
            app_name = instr["app_name"]
            # hardcode the config bitstream depends on the apps
            config_mem = []
            print("app is", app_name)
            use_json = True
            if use_json:
                top_controller_node = instr['config'][1]
                config_mem = self.lt_dut.get_static_bitstream_json(top_controller_node)
            elif app_name == "conv_3_3":
                # Create a tempdir and download the files...
                with tempfile.TemporaryDirectory() as tempdir:
                    # Download files here and leverage lake bitstream code....
                    print(f'Downloading app files for {app_name}')
                    url_prefix = "https://raw.githubusercontent.com/dillonhuff/clockwork/" +\
                                 "fix_config/lake_controllers/conv_3_3_aha/buf_inst_input" +\
                                 "_10_to_buf_inst_output_3_ubuf/"
                    file_suffix = ["input_agg2sram.csv",
                                   "input_in2agg_0.csv",
                                   "output_2_sram2tb.csv",
                                   "output_2_tb2out_0.csv",
                                   "output_2_tb2out_1.csv",
                                   "stencil_valid.csv"]
                    for fs in file_suffix:
                        full_url = url_prefix + fs
                        print(f"Downloading from {full_url}")
                        urllib.request.urlretrieve(full_url, tempdir + "/" + fs)
                    config_path = tempdir
                    config_mem = self.get_static_bitstream(config_path=config_path,
                                                           in_file_name="input",
                                                           out_file_name="output")

            for name, v in config_mem:
                configs += [self.get_config_data(name, v)]
            # gate config signals
            conf_names = ["wen_in_1_reg_sel"]
            for conf_name in conf_names:
                configs += [self.get_config_data(conf_name, 1)]
        else:
            # for now config it as sram
            config_mem = [("tile_en", 1),
                          ("mode", 2),
                          ("wen_in_0_reg_sel", 1),
                          ("wen_in_1_reg_sel", 1)]
            for name, v in config_mem:
                configs = [self.get_config_data(name, v)] + configs
        print(configs)
        return configs

    def get_static_bitstream(self, config_path, in_file_name, out_file_name):

        # Don't do the rest anymore...
        return self.lt_dut.get_static_bitstream(config_path=config_path,
                                                in_file_name=in_file_name,
                                                out_file_name=out_file_name)

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
        return PnRTag("m", self.DEFAULT_PRIORITY - 1, self.DEFAULT_PRIORITY)

    def num_data_inputs(self):
        return self.interconnect_input_ports

    def num_data_outputs(self):
        return self.interconnect_output_ports


if __name__ == "__main__":
    mc = get_pond()