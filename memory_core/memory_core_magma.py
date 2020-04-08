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
from lake.top.lake_top import LakeTop
from lake.passes.passes import change_sram_port_names
from lake.passes.passes import lift_config_reg
from lake.utils.sram_macro import SRAMMacroInfo
import kratos as kts

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

    def __init__(self,
                 data_width=16,  # CGRA Params
                 mem_width=64,
                 mem_depth=512,
                 banks=1,
                 input_iterator_support=6,  # Addr Controllers
                 output_iterator_support=6,
                 interconnect_input_ports=2,  # Connection to int
                 interconnect_output_ports=2,
                 mem_input_ports=1,
                 mem_output_ports=1,
                 use_sram_stub=1,
                 sram_macro_info=SRAMMacroInfo(),
                 read_delay=1,  # Cycle delay in read (SRAM vs Register File)
                 rw_same_cycle=False,  # Does the memory allow r+w in same cycle?
                 agg_height=4,
                 max_agg_schedule=32,
                 input_max_port_sched=32,
                 output_max_port_sched=32,
                 align_input=1,
                 max_line_length=128,
                 max_tb_height=1,
                 tb_range_max=128,
                 tb_sched_max=64,
                 max_tb_stride=15,
                 num_tb=1,
                 tb_iterator_support=2,
                 multiwrite=1,
                 max_prefetch=64,
                 config_data_width=32,
                 config_addr_width=8,
                 remove_tb=False,
                 fifo_mode=True,
                 add_clk_enable=True,
                 add_flush=True,
                 core_reset_pos=False):

        super().__init__(config_addr_width, config_data_width)

        # Capture everything to the tile object
        self.data_width = data_width
        self.mem_width = mem_width
        self.mem_depth = mem_depth
        self.banks = banks
        self.fw_int = int(self.mem_width / self.data_width)
        self.input_iterator_support = input_iterator_support
        self.output_iterator_support = output_iterator_support
        self.interconnect_input_ports = interconnect_input_ports
        self.interconnect_output_ports = interconnect_output_ports
        self.mem_input_ports = mem_input_ports
        self.mem_output_ports = mem_output_ports
        self.use_sram_stub = use_sram_stub
        self.sram_macro_info = sram_macro_info
        self.read_delay = read_delay
        self.rw_same_cycle = rw_same_cycle
        self.agg_height = agg_height
        self.max_agg_schedule = max_agg_schedule
        self.input_max_port_sched = input_max_port_sched
        self.output_max_port_sched = output_max_port_sched
        self.align_input = align_input
        self.max_line_length = max_line_length
        self.max_tb_height = max_tb_height
        self.tb_range_max = tb_range_max
        self.tb_sched_max = tb_sched_max
        self.max_tb_stride = max_tb_stride
        self.num_tb = num_tb
        self.tb_iterator_support = tb_iterator_support
        self.multiwrite = multiwrite
        self.max_prefetch = max_prefetch
        self.config_data_width = config_data_width
        self.config_addr_width = config_addr_width
        self.remove_tb = remove_tb
        self.fifo_mode = fifo_mode
        self.add_clk_enable = add_clk_enable
        self.add_flush = add_flush
        self.core_reset_pos = core_reset_pos

        # Typedefs for ease
        TData = magma.Bits[self.data_width]
        TBit = magma.Bits[1]

        self.__inputs = []
        self.__outputs = []

        # Enumerate input and output ports
        # (clk and reset are assumed)
        if self.interconnect_input_ports > 1:
            for i in range(self.interconnect_input_ports):
                self.add_port(f"addr_in_{i}", magma.In(TData))
                self.__inputs.append(self.ports[f"addr_in_{i}"])
                self.add_port(f"data_in_{i}", magma.In(TData))
                self.__inputs.append(self.ports[f"data_in_{i}"])
                self.add_port(f"wen_in_{i}", magma.In(TBit))
                self.__inputs.append(self.ports[f"wen_in_{i}"])
        else:
            self.add_port("addr_in", magma.In(TData))
            self.__inputs.append(self.ports[f"addr_in"])
            self.add_port("data_in", magma.In(TData))
            self.__inputs.append(self.ports[f"data_in"])
            self.add_port("wen_in", magma.In(TBit))
            self.__inputs.append(self.ports.wen_in)

        if self.interconnect_output_ports > 1:
            for i in range(self.interconnect_output_ports):
                self.add_port(f"data_out_{i}", magma.Out(TData))
                self.__outputs.append(self.ports[f"data_out_{i}"])
                self.add_port(f"ren_in_{i}", magma.In(TBit))
                self.__inputs.append(self.ports[f"ren_in_{i}"])
                self.add_port(f"valid_out_{i}", magma.Out(TBit))
                self.__outputs.append(self.ports[f"valid_out_{i}"])
        else:
            self.add_port('data_out', magma.Out(TData))
            self.__outputs.append(self.ports[f"data_out"])
            self.add_port(f"ren_in", magma.In(TBit))
            self.__inputs.append(self.ports[f"ren_in"])
            self.add_port(f"valid_out", magma.Out(TBit))
            self.__outputs.append(self.ports[f"valid_out"])

        self.add_ports(
            flush=magma.In(TBit),
            full=magma.Out(TBit),
            empty=magma.Out(TBit),
            stall=magma.In(TBit),
            sram_ready_out=magma.Out(TBit)
          #  chain_wen_in=magma.In(TBit),
          #  chain_valid_out=magma.Out(TBit),
          #  chain_in=magma.In(TData),
          #  chain_out=magma.Out(TData)
        )

        self.__inputs.append(self.ports.flush)
        # self.__inputs.append(self.ports.stall)

        self.__outputs.append(self.ports.full)
        self.__outputs.append(self.ports.empty)
        self.__outputs.append(self.ports.sram_ready_out)

        # Instantiate core object here - will only use the object representation to
        # query for information. The circuit representation will be cached and retrieved
        # in the following steps.
        lt_dut = LakeTop(data_width=self.data_width,
                         mem_width=self.mem_width,
                         mem_depth=self.mem_depth,
                         banks=self.banks,
                         input_iterator_support=self.input_iterator_support,
                         output_iterator_support=self.output_iterator_support,
                         interconnect_input_ports=self.interconnect_input_ports,
                         interconnect_output_ports=self.interconnect_output_ports,
                         use_sram_stub=self.use_sram_stub,
                         sram_macro_info=self.sram_macro_info,
                         read_delay=self.read_delay,
                         rw_same_cycle=self.rw_same_cycle,
                         agg_height=self.agg_height,
                         max_agg_schedule=self.max_agg_schedule,
                         input_max_port_sched=self.input_max_port_sched,
                         output_max_port_sched=self.output_max_port_sched,
                         align_input=self.align_input,
                         max_line_length=self.max_line_length,
                         max_tb_height=self.max_tb_height,
                         tb_range_max=self.tb_range_max,
                         tb_sched_max=self.tb_sched_max,
                         max_tb_stride=self.max_tb_stride,
                         num_tb=self.num_tb,
                         tb_iterator_support=self.tb_iterator_support,
                         multiwrite=self.multiwrite,
                         max_prefetch=self.max_prefetch,
                         config_data_width=self.config_data_width,
                         config_addr_width=self.config_addr_width,
                         remove_tb=self.remove_tb,
                         fifo_mode=self.fifo_mode,
                         add_clk_enable=self.add_clk_enable,
                         add_flush=self.add_flush)

        # Check for circuit caching
        if (self.data_width, self.mem_width, self.mem_depth, self.banks,
            self.input_iterator_support, self.output_iterator_support,
            self.interconnect_input_ports, self.interconnect_output_ports,
            self.use_sram_stub, self.sram_macro_info, self.read_delay,
            self.rw_same_cycle, self.agg_height, self.max_agg_schedule,
            self.input_max_port_sched, self.output_max_port_sched,
            self.align_input, self.max_line_length, self.max_tb_height,
            self.tb_range_max, self.tb_sched_max, self.max_tb_stride,
            self.num_tb, self.tb_iterator_support, self.multiwrite,
            self.max_prefetch, self.config_data_width, self.config_addr_width,
            self.remove_tb, self.fifo_mode, self.add_clk_enable, self.add_flush) not in \
            MemCore.__circuit_cache or True:

            sram_macro_info = SRAMMacroInfo()

            change_sram_port_pass = change_sram_port_names(use_sram_stub, sram_macro_info)
            circ = kts.util.to_magma(lt_dut,
                                     flatten_array=True,
                                     check_multiple_driver=False,
                                     optimize_if=False,
                                     check_flip_flop_always_ff=False,
                                     additional_passes={"change_sram_port": change_sram_port_pass})
            MemCore.__circuit_cache[
                (self.data_width, self.mem_width, self.mem_depth, self.banks,
                self.input_iterator_support, self.output_iterator_support,
                self.interconnect_input_ports, self.interconnect_output_ports,
                self.use_sram_stub, self.sram_macro_info, self.read_delay,
                self.rw_same_cycle, self.agg_height, self.max_agg_schedule,
                self.input_max_port_sched, self.output_max_port_sched,
                self.align_input, self.max_line_length, self.max_tb_height,
                self.tb_range_max, self.tb_sched_max, self.max_tb_stride,
                self.num_tb, self.tb_iterator_support, self.multiwrite,
                self.max_prefetch, self.config_data_width, self.config_addr_width,
                self.remove_tb, self.fifo_mode, self.add_clk_enable, self.add_flush)] = circ
        else:
            circ = MemCore.__circuit_cache[(self.data_width, self.mem_width, self.mem_depth, self.banks,
                self.input_iterator_support, self.output_iterator_support,
                self.interconnect_input_ports, self.interconnect_output_ports,
                self.use_sram_stub, self.sram_macro_info, self.read_delay,
                self.rw_same_cycle, self.agg_height, self.max_agg_schedule,
                self.input_max_port_sched, self.output_max_port_sched,
                self.align_input, self.max_line_length, self.max_tb_height,
                self.tb_range_max, self.tb_sched_max, self.max_tb_stride,
                self.num_tb, self.tb_iterator_support, self.multiwrite,
                self.max_prefetch, self.config_data_width, self.config_addr_width,
                self.remove_tb, self.fifo_mode, self.add_clk_enable, self.add_flush)]

        # Save as underlying circuit object
        self.underlying = FromMagma(circ)

        # put a 1-bit register and a mux to select the control signals
        control_signals = [("wen_in", self.interconnect_input_ports),
                           ("ren_in", self.interconnect_output_ports),
                           ("flush", 1)] # ,
                           # "chain_wen_in"]
        for control_signal, width in control_signals:
            # TODO: consult with Ankita to see if we can use the normal
            # mux here
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

        if self.interconnect_input_ports > 1:
            for i in range(self.interconnect_input_ports):
                self.wire(self.ports[f"data_in_{i}"], self.underlying.ports[f"data_in_{i}"])
                self.wire(self.ports[f"addr_in_{i}"], self.underlying.ports[f"addr_in_{i}"])
        else:
            self.wire(self.ports.addr_in, self.underlying.ports.addr_in)
            self.wire(self.ports.data_in, self.underlying.ports.data_in)

        if self.interconnect_output_ports > 1:
            for i in range(self.interconnect_output_ports):
                self.wire(self.ports[f"data_out_{i}"], self.underlying.ports[f"data_out_{i}"])
        else:
            self.wire(self.ports.data_out, self.underlying.ports.data_out)

        # Need to invert this
#        self.wire(self.ports.reset, self.underlying.ports.reset)
        self.resetInverter = FromMagma(mantle.DefineInvert(1))
        self.wire(self.resetInverter.ports.I[0], self.ports.reset)
        self.wire(self.resetInverter.ports.O[0], self.underlying.ports.rst_n)
#        self.wire(self.ports.reset, self.underlying.ports.rst_n)
        self.wire(self.ports.clk, self.underlying.ports.clk)
        if self.interconnect_output_ports == 1:
            self.wire(self.ports.valid_out[0], self.underlying.ports.valid_out[0])
        else:
            for j in range(self.interconnect_output_ports):
                self.wire(self.ports[f"valid_out_{j}"][0], self.underlying.ports.valid_out[j])
#        self.wire(self.ports.almost_empty[0],
#                  self.underlying.ports.almost_empty)
#        self.wire(self.ports.almost_full[0], self.underlying.ports.almost_full)
        self.wire(self.ports.empty[0], self.underlying.ports.empty[0])
        self.wire(self.ports.full[0], self.underlying.ports.full[0])

#        self.wire(self.ports.chain_valid_out[0],
#                  self.underlying.ports.chain_valid_out)
#        self.wire(self.ports.chain_in, self.underlying.ports.chain_in)
#        self.wire(self.ports.chain_out, self.underlying.ports.chain_out)

        # PE core uses clk_en (essentially active low stall)
        self.stallInverter = FromMagma(mantle.DefineInvert(1))
        self.wire(self.stallInverter.ports.I, self.ports.stall)
        self.wire(self.stallInverter.ports.O[0], self.underlying.ports.clk_en[0])

        self.wire(self.ports.sram_ready_out[0], self.underlying.ports.sram_ready_out[0])
#        self.wire(Const(magma.bits(0, 24)),
#                  self.underlying.ports.config_addr_in[0:24])

        # we have five features in total
        # 0:    TILE
        # 1-4:  SMEM
        # Feature 0: Tile
        self.__features: List[CoreFeature] = [self]
        # Features 1-4: SRAM
        self.num_sram_features = lt_dut.total_sets
        print(f"{self.num_sram_features} total features")
        for sram_index in range(self.num_sram_features):
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
                  self.underlying.ports.config_addr_in[0:8])
        self.wire(or_gates["config_data"].ports.O,
                  self.underlying.ports.config_data_in)

        # read data out
        for idx, core_feature in enumerate(self.__features):
            if(idx > 0):
                # self.add_port(f"read_config_data_{idx}",
                self.add_port(f"read_config_data_{idx}",
                              magma.Out(magma.Bits[32]))
                # port aliasing
                core_feature.ports["read_config_data"] = \
                    self.ports[f"read_config_data_{idx}"]

        # MEM Config
        configurations = [
            ("tile_en", 1),
            ("fifo_ctrl_fifo_depth", 16),
            ("mode", 2)
        ]
#            ("stencil_width", 16), NOT YET
#            ("enable_chain", 1), NOT YET
#            ("chain_idx", 4), NOT YET

        # Add config registers to configurations
        # TODO: Have lake spit this information out automatically from the wrapper
        for i in range(self.interconnect_input_ports):
            configurations.append((f"strg_ub_agg_align_{i}_line_length", kts.clog2(self.max_line_length)))
            configurations.append((f"strg_ub_agg_in_{i}_in_period", kts.clog2(self.input_max_port_sched)))
            for j in range(self.input_max_port_sched):
                configurations.append((f"strg_ub_agg_in_{i}_in_sched_{j}", kts.clog2(self.agg_height)))
            configurations.append((f"strg_ub_agg_in_{i}_out_period", kts.clog2(self.input_max_port_sched)))
            for j in range(self.output_max_port_sched):
                configurations.append((f"strg_ub_agg_in_{i}_out_sched_{j}", kts.clog2(self.agg_height)))
            configurations.append((f"strg_ub_app_ctrl_write_depth_{i}", 32))

            configurations.append((f"strg_ub_input_addr_ctrl_address_gen_{i}_dimensionality", 4))
            configurations.append((f"strg_ub_input_addr_ctrl_address_gen_{i}_starting_addr", 32))
            for j in range(self.input_iterator_support):
                configurations.append((f"strg_ub_input_addr_ctrl_address_gen_{i}_ranges_{j}", 32))
                configurations.append((f"strg_ub_input_addr_ctrl_address_gen_{i}_strides_{j}", 32))

        for i in range(self.interconnect_output_ports):
            configurations.append((f"strg_ub_app_ctrl_input_port_{i}", kts.clog2(self.interconnect_input_ports)))
            configurations.append((f"strg_ub_app_ctrl_read_depth_{i}", 32))

            configurations.append((f"strg_ub_output_addr_ctrl_address_gen_{i}_dimensionality", 4))
            configurations.append((f"strg_ub_output_addr_ctrl_address_gen_{i}_starting_addr", 32))
            for j in range(self.output_iterator_support):
                configurations.append((f"strg_ub_output_addr_ctrl_address_gen_{i}_ranges_{j}", 32))
                configurations.append((f"strg_ub_output_addr_ctrl_address_gen_{i}_strides_{j}", 32))

            configurations.append((f"strg_ub_pre_fetch_{i}_input_latency", kts.clog2(self.max_prefetch)))
            configurations.append((f"strg_ub_sync_grp_sync_group_{i}", self.interconnect_output_ports))

            for j in range(self.num_tb):
                configurations.append((f"strg_ub_tba_{i}_tb_{j}_dimensionality", 2))
                for k in range(self.tb_range_max):
                    configurations.append((f"strg_ub_tba_{i}_tb_{j}_indices_{k}", kts.clog2(self.fw_int) + 1))
                configurations.append((f"strg_ub_tba_{i}_tb_{j}_range_inner", kts.clog2(self.tb_sched_max) + 1))
                configurations.append((f"strg_ub_tba_{i}_tb_{j}_range_outer", kts.clog2(self.tb_sched_max) + 1))
                configurations.append((f"strg_ub_tba_{i}_tb_{j}_stride", kts.clog2(self.max_tb_stride)))
                configurations.append((f"strg_ub_tba_{i}_tb_{j}_tb_height", max(1, kts.clog2(self.num_tb))))

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
            self.wire(core_feature.ports.read_config_data,
            #          self.underlying.ports[f"read_data_sram_{sram_index}"])
                      self.underlying.ports[f"config_data_out_{sram_index}"])
            # also need to wire the sram signal
            # the config enable is the OR of the rd+wr
            or_gate_en = FromMagma(mantle.DefineOr(2, 1))
            or_gate_en.instance_name = f"OR_CONFIG_EN_SRAM_{sram_index}"

            self.wire(or_gate_en.ports.I0, core_feature.ports.config.write)
            self.wire(or_gate_en.ports.I1, core_feature.ports.config.read)
            self.wire(core_feature.ports.config_en,
                      self.underlying.ports["config_en"][sram_index])
                      #self.underlying.ports["config_en_sram"][sram_index])
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
                        (self.get_reg_index("stride_4"),
                         instr["stride_4"]),
                        (self.get_reg_index("range_4"),
                         instr["range_4"]),
                        (self.get_reg_index("stride_5"),
                         instr["stride_5"]),
                        (self.get_reg_index("range_5"),
                         instr["range_5"]),
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
#        return [self.ports.data_in, self.ports.addr_in, self.ports.flush,
#                self.ports.ren_in, self.ports.wen_in, self.ports.switch_db,
#                self.ports.chain_wen_in, self.ports.chain_in]
        return self.__inputs
    def outputs(self):
#        return [self.ports.data_out, self.ports.valid_out,
#                self.ports.almost_empty, self.ports.almost_full,
#                self.ports.empty, self.ports.full, self.ports.chain_valid_out,
#                self.ports.chain_out]
        return self.__outputs
    def features(self):
        return self.__features

    def name(self):
        return "MemCore"

    def pnr_info(self):
        return PnRTag("m", self.DEFAULT_PRIORITY - 1, self.DEFAULT_PRIORITY)


if __name__ == "__main__":
    mc = MemCore()
