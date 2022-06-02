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
from lake.modules.io_core import *

import kratos as kts

if __name__ == "__main__":
    from memtile_util import LakeCoreBase
else:
    from .memtile_util import LakeCoreBase


class IOCoreReadyValid(LakeCoreBase):

    def __init__(self,
                 data_width=16,  # CGRA Params
                 config_data_width=32,
                 config_addr_width=8,
                 tracks_supported=[1, 16, 17]):

        buffet_name = "IOCoreReadyValid"
        super().__init__(config_data_width=config_data_width,
                         config_addr_width=config_addr_width,
                         data_width=data_width,
                         name="IOCoreReadyValid")

        # Capture everything to the tile object
        self.data_width = data_width
        self.config_data_width = config_data_width
        self.config_addr_width = config_addr_width
        self.tracks_supported = tracks_supported

        cache_key = (self.data_width,
                     self.config_data_width,
                     self.config_addr_width,
                     "IOCoreReadyValid")

        # Check for circuit caching
        if cache_key not in LakeCoreBase._circuit_cache:
            # Instantiate core object here - will only use the object representation to
            # query for information. The circuit representation will be cached and retrieved
            # in the following steps.
            self.dut = IOCore(data_width=data_width,
                              tracks_supported=self.tracks_supported)

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
        with open("iocorerv_cfg.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"(\"{reg}\", 0),  # {self.registers[reg].width}\n"
                cfg_dump.write(write_line)
        with open("iocorerv_synth.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"{reg}\n"
                cfg_dump.write(write_line)

    def get_config_bitstream(self, config_tuple):
        configs = []
        return []
        print("Configuring io core...")
        config_lower = [("tile_en", 1)]
        config_lower += self.dut.get_bitstream()
        for name, v in config_lower:
            configs = [self.get_config_data(name, v)] + configs
        # return configs

    def pnr_info(self):
        return [PnRTag("I", 2, self.DEFAULT_PRIORITY),
                PnRTag("i", 1, self.DEFAULT_PRIORITY),
                ]

    # def inputs(self):
    #     raw_inputs = super(IOCoreReadyValid, self).inputs()
    #     ins = [p for p in raw_inputs if "glb2io" not in p.qualified_name()]
    #     return ins

    # def outputs(self):
    #     raw_outputs = super(IOCoreReadyValid, self).outputs()
    #     outs = [p for p in raw_outputs if "io2glb" not in p.qualified_name()]
    #     return outs


if __name__ == "__main__":
    rviocore = IOCoreReadyValid()
