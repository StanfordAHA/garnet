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
from lake.modules.scanner import *

import kratos as kts

if __name__ == "__main__":
    from memtile_util import LakeCoreBase
else:
    from .memtile_util import LakeCoreBase


class ScannerCore(LakeCoreBase):

    def __init__(self,
                 data_width=16,  # CGRA Params
                 config_data_width=32,
                 config_addr_width=8):

        scan_name = "Scanner"
        super().__init__(config_data_width=config_data_width,
                         config_addr_width=config_addr_width,
                         data_width=data_width,
                         name="ScannerCore")

        # Capture everything to the tile object
        self.data_width = data_width
        self.config_data_width = config_data_width
        self.config_addr_width = config_addr_width

        cache_key = (self.data_width,
                     self.config_data_width,
                     self.config_addr_width,
                     "ScannerCore")

        # Check for circuit caching
        if cache_key not in LakeCoreBase._circuit_cache:
            # Instantiate core object here - will only use the object representation to
            # query for information. The circuit representation will be cached and retrieved
            # in the following steps.
            self.dut = Scanner(data_width=data_width)

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
        with open("scanner_cfg.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"(\"{reg}\", 0),  # {self.registers[reg].width}\n"
                cfg_dump.write(write_line)
        with open("scanner_synth.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"{reg}\n"
                cfg_dump.write(write_line)

    def get_config_bitstream(self, config_tuple):
        inner_offset, max_outer_dim, strides, ranges, is_root, \
            do_repeat, repeat_outer, repeat_factor, stop_lvl, \
            block_mode, lookup = config_tuple
        configs = []
        config_scanner = [("tile_en", 1)]
        config_scanner += self.dut.get_bitstream(inner_offset=inner_offset,
                                                 max_out=max_outer_dim,
                                                 ranges=ranges,
                                                 strides=strides,
                                                 root=is_root,
                                                 do_repeat=do_repeat,
                                                 repeat_outer=repeat_outer,
                                                 repeat_factor=repeat_factor,
                                                 stop_lvl=stop_lvl,
                                                 block_mode=block_mode,
                                                 lookup=lookup)
        for name, v in config_scanner:
            configs = [self.get_config_data(name, v)] + configs
        return configs

    def pnr_info(self):
        return PnRTag("s", self.DEFAULT_PRIORITY, 1)


if __name__ == "__main__":
    sc = ScannerCore()
