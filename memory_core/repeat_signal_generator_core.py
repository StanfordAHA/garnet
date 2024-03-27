from gemstone.generator.from_magma import FromMagma
from gemstone.common.core import PnRTag
from lake.modules.repeat_signal_generator import RepeatSignalGenerator
import kratos as kts

if __name__ == "__main__":
    from memtile_util import LakeCoreBase
else:
    from .memtile_util import LakeCoreBase


class RepeatSignalGeneratorCore(LakeCoreBase):

    def __init__(self,
                 data_width=16,  # CGRA Params
                 config_data_width=32,
                 config_addr_width=8,
                 passthru=True,
                 fifo_depth=8):

        lookup_name = "RepeatSignalGenerator"  # noqa "assigned but never used"
        super().__init__(config_data_width=config_data_width,
                         config_addr_width=config_addr_width,
                         data_width=data_width,
                         name="RepeatSignalGeneratorCore",
                         ready_valid=True)

        # Capture everything to the tile object
        self.data_width = data_width
        self.config_data_width = config_data_width
        self.config_addr_width = config_addr_width
        self.passthru = passthru

        cache_key = (self.data_width,
                     self.config_data_width,
                     self.config_addr_width,
                     self.passthru,
                     "RepeatSignalGeneratorCore")

        # Check for circuit caching
        if cache_key not in LakeCoreBase._circuit_cache:
            # Instantiate core object here - will only use the object representation to
            # query for information. The circuit representation will be cached and retrieved
            # in the following steps.
            self.dut = RepeatSignalGenerator(data_width=data_width,
                                             passthru=self.passthru,
                                             fifo_depth=fifo_depth,
                                             defer_fifos=False,
                                             add_flush=True)

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
        with open("repeat_signal_generator_cfg.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"(\"{reg}\", 0),  # {self.registers[reg].width}\n"
                cfg_dump.write(write_line)
        with open("repeat_signal_generator_synth.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"{reg}\n"
                cfg_dump.write(write_line)

    def get_config_bitstream(self, config_tuple):
        # stop_lvl = config_tuple
        _, config_kwargs = config_tuple
        configs = []
        config_lu = [("tile_en", 1)]
        # config_lu += self.dut.get_bitstream(stop_lvl=stop_lvl)
        config_lu += self.dut.get_bitstream(config_kwargs=config_kwargs)

        for name, v in config_lu:
            configs = [self.get_config_data(name, v)] + configs
        return configs

    def pnr_info(self):
        return PnRTag("q", self.DEFAULT_PRIORITY, 1)

    def get_modes_supported(self):
        return ['repeat_signal_generator']


if __name__ == "__main__":
    rsg_core = RepeatSignalGeneratorCore()
