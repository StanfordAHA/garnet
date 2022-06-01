import magma
from gemstone.generator.from_magma import FromMagma
from typing import List
from canal.interconnect import Interconnect
from lake.top.extract_tile_info import *
import kratos as kts
from gemstone.generator.from_magma import FromMagma
from typing import List
from lake.top.pond import Pond
from lake.top.extract_tile_info import *
from gemstone.common.core import PnRTag
from lake.modules.write_scanner import *

import kratos as kts

if __name__ == "__main__":
    from memtile_util import LakeCoreBase
else:
    from .memtile_util import LakeCoreBase


class WriteScannerCore(LakeCoreBase):

    def __init__(self,
                 data_width=16,  # CGRA Params
                 config_data_width=32,
                 config_addr_width=8):

        scan_name = "WriteScanner"
        super().__init__(config_data_width=config_data_width,
                         config_addr_width=config_addr_width,
                         data_width=data_width,
                         name="WriteScannerCore")

        # Capture everything to the tile object
        self.data_width = data_width
        self.config_data_width = config_data_width
        self.config_addr_width = config_addr_width

        cache_key = (self.data_width,
                     self.config_data_width,
                     self.config_addr_width,
                     "WriteScannerCore")

        # Check for circuit caching
        if cache_key not in LakeCoreBase._circuit_cache:
            # Instantiate core object here - will only use the object representation to
            # query for information. The circuit representation will be cached and retrieved
            # in the following steps.
            self.dut = WriteScanner(data_width=data_width)

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
        with open("write_scanner_cfg.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"(\"{reg}\", 0),  # {self.registers[reg].width}\n"
                cfg_dump.write(write_line)
        with open("write_scanner_synth.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"{reg}\n"
                cfg_dump.write(write_line)

    def get_config_bitstream(self, config_tuple):
        inner_offset, compressed, lowest_level, stop_lvl, block_mode = config_tuple
        configs = []
        config_scanner = [("tile_en", 1),
                          ("addr_in_valid_reg_sel", 1 - lowest_level)]
        config_scanner += self.dut.get_bitstream(inner_offset=inner_offset,
                                                 compressed=compressed,
                                                 lowest_level=lowest_level,
                                                 stop_lvl=stop_lvl,
                                                 block_mode=block_mode)

        # Need to hardcode some wires to 0...
        # If we are not at the lowest level, then the write scanner only
        # uses a single input...
        # configs.append(("valid_in_1_reg_sel", 1))

        for name, v in config_scanner:
            configs = [self.get_config_data(name, v)] + configs
        return configs

    def pnr_info(self):
        return PnRTag("w", self.DEFAULT_PRIORITY, 1)


if __name__ == "__main__":
    sc = WriteScannerCore()
