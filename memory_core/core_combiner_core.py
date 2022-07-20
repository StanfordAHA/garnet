from typing_extensions import runtime
import magma
from gemstone.generator.from_magma import FromMagma
from typing import List
from canal.interconnect import Interconnect
from lake.top.extract_tile_info import *
import kratos as kts
from gemstone.generator.from_magma import FromMagma
from typing import List
from lake.top.extract_tile_info import *
from gemstone.common.core import PnRTag
from lake.top.core_combiner import CoreCombiner
from lake.modules.intersect import Intersect
from lake.modules.scanner import Scanner
from lake.top.tech_maps import GF_Tech_Map
import kratos as kts

if __name__ == "__main__":
    from memtile_util import LakeCoreBase
else:
    from .memtile_util import LakeCoreBase


class CoreCombinerCore(LakeCoreBase):

    def __init__(self,
                 data_width=16,  # CGRA Params
                 config_data_width=32,
                 config_addr_width=8,
                 fifo_depth=8,
                 controllers_list=None,
                 use_sim_sram=True,
                 tech_map=GF_Tech_Map(depth=512, width=32)):

        cc_core_name = "CoreCombiner"

        assert controllers_list is not None and len(controllers_list) > 0
        for controller in controllers_list:
            cc_core_name += f"_{str(controller)}"

        super().__init__(config_data_width=config_data_width,
                         config_addr_width=config_addr_width,
                         data_width=data_width,
                         name=cc_core_name,
                         ready_valid=True)

        # Capture everything to the tile object
        self.data_width = data_width
        self.config_data_width = config_data_width
        self.config_addr_width = config_addr_width
        self.use_sim_sram = use_sim_sram
        self.tech_map = tech_map

        self.runtime_mode = None

        cache_key = (self.data_width,
                     self.config_data_width,
                     self.config_addr_width,
                     cc_core_name)

        # Check for circuit caching
        if cache_key not in LakeCoreBase._circuit_cache:
            # Instantiate core object here - will only use the object representation to
            # query for information. The circuit representation will be cached and retrieved
            # in the following steps.
            self.CC = CoreCombiner(data_width=data_width,
                                   mem_width=64,
                                   mem_depth=512,
                                   banks=1,
                                   config_width=16,
                                   config_addr_width=8,
                                   config_data_width=32,
                                   name=f"{cc_core_name}_inner",
                                   controllers=controllers_list,
                                   use_sim_sram=self.use_sim_sram,
                                   tech_map=self.tech_map,
                                   do_config_lift=False)

            self.dut = self.CC.dut

            print(self.dut)

            print("CALLING VERILOG ON CORE COMBINER")

            circ = kts.util.to_magma(self.dut,
                                     flatten_array=True,
                                     check_multiple_driver=False,
                                     optimize_if=False,
                                     check_flip_flop_always_ff=False)
            LakeCoreBase._circuit_cache[cache_key] = (circ, self.dut, self.CC)
        else:
            circ, self.dut, self.CC = LakeCoreBase._circuit_cache[cache_key]

        # Save as underlying circuit object
        self.underlying = FromMagma(circ)

        self.wrap_lake_core()

        conf_names = list(self.registers.keys())
        conf_names.sort()
        with open("cc_cfg.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"(\"{reg}\", 0),  # {self.registers[reg].width}\n"
                cfg_dump.write(write_line)
        with open("cc_synth.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"{reg}\n"
                cfg_dump.write(write_line)

    def set_runtime_mode(self, runtime_mode):
        print(f"SETTING RUNTIME MODE: {runtime_mode}")
        assert runtime_mode in self.get_modes_supported()
        self.runtime_mode = runtime_mode

    def get_config_bitstream(self, config_tuple):

        # print(self.runtime_mode)
        # assert self.runtime_mode is not None
        _, config_kwargs = config_tuple
        assert 'mode' in config_kwargs

        print(config_kwargs)

        # config_dict = {}
        # config_dict[self.runtime_mode] = config_kwargs

        # op = config_tuple
        configs = []
        # config_pe = [("tile_en", 1)]
        configs_cc = []
        configs_cc += self.dut.get_bitstream(config_kwargs)

        for name, v in configs_cc:
            configs = [self.get_config_data(name, v)] + configs
        return configs

    def pnr_info(self):
        return PnRTag("C", self.DEFAULT_PRIORITY, 1)

    def get_modes_supported(self):
        return self.CC.get_modes_supported()

    def get_port_remap(self):
        return self.CC.get_port_remap()

    def get_config_mapping(self):
        return self.CC.get_config_mapping()


if __name__ == "__main__":

    controllers = []

    scan = Scanner(data_width=16,
                   fifo_depth=8)

    isect = Intersect(data_width=16,
                      use_merger=True,
                      fifo_depth=8)

    controllers.append(scan)
    controllers.append(isect)

    cc = CoreCombinerCore(controllers_list=controllers)
