import magma
import tempfile
import urllib.request
from canal.interconnect import Interconnect
from gemstone.generator.const import Const
from gemstone.generator.from_magma import FromMagma
from gemstone.common.core import PnRTag
from typing import List
from lake.top.lake_top import LakeTop
from lake.passes.passes import change_sram_port_names
from lake.utils.sram_macro import SRAMMacroInfo
from lake.top.extract_tile_info import *
import kratos as kts
from lake.top.tech_maps import *

if __name__ == "__main__":
    from memtile_util import LakeCoreBase
    from memory_mode import MemoryMode
else:
    from .memtile_util import LakeCoreBase
    from .memory_mode import MemoryMode


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


def lift_mem_ports(tile, tile_core):  # pragma: nocover
    ports = ["chain_wen_in", "chain_valid_out", "chain_in", "chain_out"]
    for port in ports:
        lift_mem_core_ports(port, tile, tile_core)


def lift_mem_core_ports(port, tile, tile_core):  # pragma: nocover
    tile.add_port(port, tile_core.ports[port].base_type())
    tile.wire(tile.ports[port], tile_core.ports[port])


class MemCore(LakeCoreBase):

    def __init__(self,
                 data_width=16,  # CGRA Params
                 mem_width=64,
                 mem_depth=512,
                 banks=1,
                 input_iterator_support=6,  # Addr Controllers
                 output_iterator_support=6,
                 config_width=16,
                 interconnect_input_ports=2,  # Connection to int
                 interconnect_output_ports=2,
                 mem_input_ports=1,
                 mem_output_ports=1,
                 use_sim_sram=True,
                 read_delay=1,  # Cycle delay in read (SRAM vs Register File)
                 rw_same_cycle=False,  # Does the memory allow r+w in same cycle?
                 agg_height=4,
                 config_data_width=32,
                 config_addr_width=8,
                 num_tiles=1,
                 fifo_mode=True,
                 add_clk_enable=True,
                 add_flush=True,
                 gate_flush=True,
                 override_name=None,
                 gen_addr=True,
                 tech_map=TSMC_Tech_Map(depth=512, width=32)):

        lake_name = "LakeTop"

        super().__init__(config_data_width=config_data_width,
                         config_addr_width=config_addr_width,
                         data_width=data_width,
                         gate_flush=gate_flush,
                         name="MemCore")

        # Capture everything to the tile object
        # self.data_width = data_width
        self.mem_width = mem_width
        self.mem_depth = mem_depth
        self.banks = banks
        self.fw_int = int(self.mem_width / self.data_width)
        self.input_iterator_support = input_iterator_support
        self.output_iterator_support = output_iterator_support
        self.config_width = config_width
        self.interconnect_input_ports = interconnect_input_ports
        self.interconnect_output_ports = interconnect_output_ports
        self.mem_input_ports = mem_input_ports
        self.mem_output_ports = mem_output_ports
        self.use_sim_sram = use_sim_sram
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
        self.tech_map = tech_map
        # self.app_ctrl_depth_width = app_ctrl_depth_width
        # self.stcl_valid_iter = stcl_valid_iter
        # Typedefs for ease
        TData = magma.Bits[self.data_width]
        TBit = magma.Bits[1]

        cache_key = (self.data_width, self.mem_width, self.mem_depth, self.banks,
                     self.input_iterator_support, self.output_iterator_support,
                     self.interconnect_input_ports, self.interconnect_output_ports,
                     self.use_sim_sram, self.read_delay,
                     self.rw_same_cycle, self.agg_height, self.config_data_width, self.config_addr_width,
                     self.num_tiles, self.fifo_mode,
                     self.add_clk_enable, self.add_flush, self.gen_addr, str(self.tech_map))

        # Check for circuit caching
        if cache_key not in LakeCoreBase._circuit_cache:

            # Instantiate core object here - will only use the object representation to
            # query for information. The circuit representation will be cached and retrieved
            # in the following steps.
            self.LT = LakeTop(data_width=self.data_width,
                              mem_width=self.mem_width,
                              mem_depth=self.mem_depth,
                              banks=self.banks,
                              input_iterator_support=self.input_iterator_support,
                              output_iterator_support=self.output_iterator_support,
                              config_width=self.config_width,
                              interconnect_input_ports=self.interconnect_input_ports,
                              interconnect_output_ports=self.interconnect_output_ports,
                              use_sim_sram=self.use_sim_sram,
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
                              gen_addr=self.gen_addr,
                              tech_map=self.tech_map)

            print(self.LT.dut)
            print(self.LT.dut.get_mode_map())

            # Nonsensical but LakeTop now has its ow n internal dut
            self.dut = self.LT.dut

            circ = kts.util.to_magma(self.dut,
                                     flatten_array=True,
                                     check_multiple_driver=False,
                                     optimize_if=False,
                                     check_flip_flop_always_ff=False)
            LakeCoreBase._circuit_cache[cache_key] = (circ, self.dut)
        else:
            circ, self.dut = LakeCoreBase._circuit_cache[cache_key]

        # Save as underlying circuit object
        self.underlying = FromMagma(circ)

        self.wrap_lake_core()

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
        config_runtime = []

        modes = {
            'UB': 0,
            'FIFO': 1,
            'ROM': 2
        }

        mode_map = {
            "lake": MemoryMode.UNIFIED_BUFFER,
            "rom": MemoryMode.ROM,
            "sram": MemoryMode.SRAM,
            "fifo": MemoryMode.FIFO,
        }

        if 'mode' in instr and instr['mode'] == 'lake':
            instr['mode'] = 'UB'
            if 'stencil_valid' in instr['config']:
                instr['mode'] = 'stencil_valid'
        if 'mode' in instr and instr['mode'] == 'sram':
            instr['mode'] = 'ROM'
        config_pre = self.dut.get_bitstream(instr)
        # Add the runtime configuration to the final config
        for name, v in config_pre:
            configs = [self.get_config_data(name, v)] + configs
        # Add in preloaded memory
        if "init" in instr:
            # this is SRAM content
            content = instr['init']
            for addr, data in enumerate(content):
                if (not isinstance(data, int)) and len(data) == 2:
                    addr, data = data
                addr = addr >> 2
                feat_addr = addr // 256 + 1
                addr = (addr % 256)
                configs.append((addr, feat_addr, data))
        print(configs)
        return configs

        # Extract the runtime + preload config
        if "config" in instr:
            top_config = instr['config']
            if "init" in top_config:
                instr["init"] = top_config["init"]

        # Add in preloaded memory
        if "init" in instr:
            # this is SRAM content
            content = instr['init']
            for addr, data in enumerate(content):
                if (not isinstance(data, int)) and len(data) == 2:
                    addr, data = data
                addr = addr >> 2
                feat_addr = addr // 256 + 1
                addr = (addr % 256)
                configs.append((addr, feat_addr, data))

        # Extract mode to the enum
        if "is_rom" in instr and instr["is_rom"]:
            mode = mode_map["rom"]
        else:
            mode = mode_map[instr['mode']]

        if mode == MemoryMode.UNIFIED_BUFFER:
            config_runtime = self.dut.get_static_bitstream_json(top_config)
        elif mode == MemoryMode.ROM:
            # Rom mode is simply SRAM mode with the writes disabled
            config_runtime = [("tile_en", 1),
                              ("mode", 2),
                              ("wen_in_0_reg_sel", 1),
                              ("wen_in_1_reg_sel", 1)]
        elif mode == MemoryMode.SRAM:
            # SRAM mode gives 1 write port, 1 read port currently
            config_runtime = [("tile_en", 1),
                              ("mode", 2),
                              ("wen_in_1_reg_sel", 1)]
        elif mode == MemoryMode.FIFO:
            # FIFO mode gives 1 write port, 1 read port currently
            assert 'depth' in top_config, "FIFO configuration needs a 'depth' - please include one in the config"
            fifo_depth = int(top_config['depth'])

            config_runtime = [("tile_en", 1),
                              ("mode", 1),
                              ("wen_in_1_reg_sel", 1),
                              ("strg_fifo_fifo_depth", fifo_depth)]

        # Add the runtime configuration to the final config
        for name, v in config_runtime:
            if name == "flush_reg_sel" or name == "flush_reg_value":
                continue
            configs = [self.get_config_data(name, v)] + configs

        print(configs)
        return configs

    def get_static_bitstream(self, config_path, in_file_name, out_file_name):

        # Don't do the rest anymore...
        return self.dut.get_static_bitstream(config_path=config_path,
                                             in_file_name=in_file_name,
                                             out_file_name=out_file_name)

    def pnr_info(self):
        return PnRTag("m", self.DEFAULT_PRIORITY - 1, self.DEFAULT_PRIORITY)


if __name__ == "__main__":
    mc = MemCore()
