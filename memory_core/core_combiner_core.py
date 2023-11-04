from gemstone.generator.from_magma import FromMagma
from typing import List
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
import os

if __name__ == "__main__":
    from memtile_util import LakeCoreBase
else:
    from .memtile_util import LakeCoreBase


class CoreCombinerCore(LakeCoreBase):

    if os.getenv('WHICH_SOC') == "amber":
        mem_width_default=16
    else:
        mem_width_default=64

    def __init__(self,
                 data_width=16,  # CGRA Params
                 config_data_width=32,
                 config_addr_width=8,
                 fifo_depth=2,
                 controllers_list=None,
                 use_sim_sram=True,
                 tech_map_name='Intel',
                 pnr_tag="C",
                 name=None,
                 input_prefix="",
                 dual_port=False,
                 rf=False,
                 mem_width=mem_width_default,
                 mem_depth=512):

        self.pnr_tag = pnr_tag
        self.input_prefix = input_prefix

        self.dual_port = dual_port
        self.rf = rf
        self.mem_width = mem_width
        self.mem_depth = mem_depth

        self.fw = mem_width // data_width

        self.read_delay = 1
        if self.rf:
            self.read_delay = 0

        cc_core_name = "CoreCombiner"

        assert controllers_list is not None and len(controllers_list) > 0
        for controller in controllers_list:
            cc_core_name += f"_{str(controller)}"

        if name is not None:
            cc_core_name = name

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
        self.tech_map_name = tech_map_name
        self.fifo_depth = fifo_depth

        self.runtime_mode = None

        cache_key = (self.data_width,
                     self.config_data_width,
                     self.config_addr_width,
                     cc_core_name,
                     dual_port,
                     rf)

        # Check for circuit caching
        if cache_key not in LakeCoreBase._circuit_cache:
            # Instantiate core object here - will only use the object representation to
            # query for information. The circuit representation will be cached and retrieved
            # in the following steps.
            self.CC = CoreCombiner(data_width=data_width,
                                   mem_width=self.mem_width,
                                   mem_depth=self.mem_depth,
                                   banks=1,
                                   config_width=16,
                                   config_addr_width=8,
                                   config_data_width=32,
                                   name=f"{cc_core_name}_inner",
                                   controllers=controllers_list,
                                   use_sim_sram=self.use_sim_sram,
                                   do_config_lift=False,
                                   io_prefix=self.input_prefix,
                                   rw_same_cycle=self.dual_port,
                                   read_delay=self.read_delay,
                                   fifo_depth=self.fifo_depth,
                                   tech_map_name=tech_map_name)

            self.dut = self.CC.dut

            print(self.dut)

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
        configs = []

        # Basically this means we are doing a dense app
        if isinstance(config_tuple, dict):
            instr = config_tuple
            # Check if mem or PE
            if self.pnr_tag == 'm':
                if 'config' in instr:
                    instr_new = instr['config']
                    for k, v in instr.items():
                        if k != "config":
                            instr_new[k] = v
                    instr = instr_new

                if 'mode' in instr and instr['mode'] == 'lake':
                    instr['mode'] = 'UB'
                    if 'stencil_valid' in instr:
                        instr['mode'] = 'stencil_valid'
                elif 'mode' in instr and instr['mode'] == 'sram':
                    instr['mode'] = 'ROM'
                    config_extra_rom = [(f"{self.get_port_remap()['ROM']['wen']}_reg_sel", 1)]
                    for name, v in config_extra_rom:
                        configs = [self.get_config_data(name, v)] + configs
                elif 'mode' not in instr and 'stencil_valid' in instr:
                    instr['mode'] = 'stencil_valid'
                else:
                    # Default to UB mode since we get varying consistency in controller indication
                    instr['mode'] = 'UB'

                print("BEFORE")
                config_pre = self.dut.get_bitstream(instr)
                print("AFTER")

                # Add the runtime configuration to the final config
                for name, v in config_pre:
                    configs = [self.get_config_data(name, v)] + configs

                print("MEK2")
                print(configs)
                # Add in preloaded memory
                if "init" in instr and instr['init'] is not None:
                    # this is SRAM content
                    content = instr['init']
                    for addr, data in enumerate(content):
                        if (not isinstance(data, int)) and len(data) == 2:
                            addr, data = data
                            
                        if os.getenv('WHICH_SOC') == "amber":
                            addr = addr >> 2
                        else:
                            addr_shift = 0
                            if self.fw > 1:
                                addr_shift = kts.clog2(self.fw)
                            addr = addr >> addr_shift

                        feat_addr = addr // 256 + 1
                        # And also transform this based on memory depth
                        addr = (addr % 256)
                        configs.append((addr, feat_addr, data))
                print(configs)
                return configs
            elif self.pnr_tag == 'p':
                instr['mode'] = 'alu'
                config_pre = self.dut.get_bitstream(instr)
                for name, v in config_pre:
                    configs = [self.get_config_data(name, v)] + configs
                print(configs)
                return configs
        elif not isinstance(config_tuple, tuple):
            # It's a PE then...
            config_kwargs = {
                'mode': 'alu',
                'use_dense': True,
                'op': int(config_tuple)
            }
            instr = config_kwargs
            config_pre = self.dut.get_bitstream(instr)
            for name, v in config_pre:
                configs = [self.get_config_data(name, v)] + configs
            config_dense_bypass = [(f"{self.get_port_remap()['alu']['data0']}_dense", 1),
                                   (f"{self.get_port_remap()['alu']['data1']}_dense", 1),
                                   (f"{self.get_port_remap()['alu']['data2']}_dense", 1),
                                   (f"{self.get_port_remap()['alu']['res']}_dense", 1)]
            for name, v in config_dense_bypass:
                configs = [self.get_config_data(name, v)] + configs
            print(configs)
            return configs
        else:
            _, config_kwargs = config_tuple
        assert 'mode' in config_kwargs

        print(config_kwargs)

        # config_dict = {}
        # config_dict[self.runtime_mode] = config_kwargs

        # op = config_tuple
        # config_pe = [("tile_en", 1)]
        configs_cc = []
        configs_cc += self.dut.get_bitstream(config_kwargs)

        for name, v in configs_cc:
            configs = [self.get_config_data(name, v)] + configs
        return configs

    def pnr_info(self):
        # return PnRTag("C", self.DEFAULT_PRIORITY, 1)
        return PnRTag(self.pnr_tag, self.DEFAULT_PRIORITY, 1)

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
