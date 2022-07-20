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
from lake.modules.onyx_pe import OnyxPE

import kratos as kts

if __name__ == "__main__":
    from memtile_util import LakeCoreBase
else:
    from .memtile_util import LakeCoreBase


class OnyxPECore(LakeCoreBase):

    def __init__(self,
                 data_width=16,  # CGRA Params
                 config_data_width=32,
                 config_addr_width=8,
                 fifo_depth=8,
                 ext_pe_prefix="PG_"):

        pe_name = "onyxPEInst"
        super().__init__(config_data_width=config_data_width,
                         config_addr_width=config_addr_width,
                         data_width=data_width,
                         name="OnyxPECore",
                         ready_valid=True)

        # Capture everything to the tile object
        self.data_width = data_width
        self.config_data_width = config_data_width
        self.config_addr_width = config_addr_width

        cache_key = (self.data_width,
                     self.config_data_width,
                     self.config_addr_width,
                     "OnyxPECore",
                     ext_pe_prefix)

        # Check for circuit caching
        if cache_key not in LakeCoreBase._circuit_cache:
            # Instantiate core object here - will only use the object representation to
            # query for information. The circuit representation will be cached and retrieved
            # in the following steps.
            self.dut = OnyxPE(data_width=data_width,
                              fifo_depth=fifo_depth,
                              defer_fifos=False,
                              ext_pe_prefix=ext_pe_prefix)

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

        # self.wrapper = _PeakWrapper(peak_generator)

        # Generate core RTL (as magma).
        # self.peak_circuit = FromMagma(self.wrapper.rtl())

        conf_names = list(self.registers.keys())
        conf_names.sort()
        with open("onyx_pe_cfg.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"(\"{reg}\", 0),  # {self.registers[reg].width}\n"
                cfg_dump.write(write_line)
        with open("onyx_pe_synth.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"{reg}\n"
                cfg_dump.write(write_line)

    def get_config_bitstream(self, config_tuple):
        op = config_tuple
        configs = []
        config_pe = [("tile_en", 1)]
        config_pe += self.dut.get_bitstream(op=op)

        for name, v in config_pe:
            configs = [self.get_config_data(name, v)] + configs
        return configs

    def pnr_info(self):
        return PnRTag("f", self.DEFAULT_PRIORITY, 1)


if __name__ == "__main__":
    sc = OnyxPECore()
