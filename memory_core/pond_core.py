import magma
from gemstone.generator.from_magma import FromMagma
from typing import List
from lake.top.pond import Pond
from lake.top.extract_tile_info import *
import kratos as kts
from gemstone.generator.from_magma import FromMagma
from typing import List
from lake.top.pond import Pond
from lake.top.extract_tile_info import *
from gemstone.common.core import PnRTag


import kratos as kts

if __name__ == "__main__":
    from memtile_util import LakeCoreBase
else:
    from .memtile_util import LakeCoreBase


class PondCore(LakeCoreBase):

    def __init__(self,
                 data_width=16,  # CGRA Params
                 mem_depth=32,
                 default_iterator_support=3,
                 interconnect_input_ports=2,  # Connection to int
                 interconnect_output_ports=2,
                 mem_input_ports=1,
                 mem_output_ports=1,
                 config_data_width=32,
                 config_addr_width=8,
                 cycle_count_width=16,
                 add_clk_enable=True,
                 add_flush=True):

        lake_name = "Pond_pond"

        super().__init__(config_data_width=config_data_width,
                         config_addr_width=config_addr_width,
                         data_width=data_width,
                         name="PondCore")

        # Capture everything to the tile object
        self.interconnect_input_ports = interconnect_input_ports
        self.interconnect_output_ports = interconnect_output_ports
        self.mem_input_ports = mem_input_ports
        self.mem_output_ports = mem_output_ports
        self.mem_depth = mem_depth
        self.data_width = data_width
        self.config_data_width = config_data_width
        self.config_addr_width = config_addr_width
        self.add_clk_enable = add_clk_enable
        self.add_flush = add_flush
        self.cycle_count_width = cycle_count_width
        self.default_iterator_support = default_iterator_support
        self.default_config_width = kts.clog2(self.mem_depth)

        cache_key = (self.data_width, self.mem_depth,
                     self.interconnect_input_ports, self.interconnect_output_ports,
                     self.mem_input_ports, self.mem_output_ports,
                     self.config_data_width, self.config_addr_width,
                     self.add_clk_enable, self.add_flush,
                     self.cycle_count_width, self.default_iterator_support)

        # Check for circuit caching
        if cache_key not in LakeCoreBase._circuit_cache:
            # Instantiate core object here - will only use the object representation to
            # query for information. The circuit representation will be cached and retrieved
            # in the following steps.
            self.dut = Pond(data_width=data_width,  # CGRA Params
                            mem_depth=mem_depth,
                            default_iterator_support=default_iterator_support,
                            interconnect_input_ports=interconnect_input_ports,  # Connection to int
                            interconnect_output_ports=interconnect_output_ports,
                            mem_input_ports=mem_input_ports,
                            mem_output_ports=mem_output_ports,
                            config_data_width=config_data_width,
                            config_addr_width=config_addr_width,
                            cycle_count_width=cycle_count_width,
                            add_clk_enable=add_clk_enable,
                            add_flush=add_flush)

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
        with open("pond_cfg.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"(\"{reg}\", 0),  # {self.registers[reg].width}\n"
                cfg_dump.write(write_line)
        with open("pond_synth.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"{reg}\n"
                cfg_dump.write(write_line)

    def get_config_bitstream(self, instr):
        configs = []
        # need to download the csv and get configuration files
        app_name = instr["app_name"]
        # hardcode the config bitstream depends on the apps
        config_mem = []
        print("app is", app_name)
        use_json = True
        if use_json:
            top_controller_node = instr['config'][1]
            config_mem = self.dut.get_static_bitstream_json(top_controller_node)
        for name, v in config_mem:
            configs += [self.get_config_data(name, v)]
        # gate config signals
        conf_names = []
        for conf_name in conf_names:
            configs += [self.get_config_data(conf_name, 1)]
        print(configs)
        return configs

    def pnr_info(self):
        return PnRTag("M", self.DEFAULT_PRIORITY, 1)


if __name__ == "__main__":
    pc = PondCore()
