from gemstone.generator.from_magma import FromMagma
from gemstone.common.core import PnRTag
from lake.modules.io_core import IOCore
from lake.modules.io_core_64 import IOCore_64
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
                 tracks_supported=[1, 17],
                 fifo_depth=2,
                 allow_bypass=False,
                 use_almost_full=False,
                 include_E64_HW=False):

        buffet_name = "IOCoreReadyValid"  # noqa "assigned but never used"
        super().__init__(config_data_width=config_data_width,
                         config_addr_width=config_addr_width,
                         data_width=data_width,
                         name="IOCoreReadyValid",
                         ready_valid=True)

        # Capture everything to the tile object
        self.data_width = data_width
        self.config_data_width = config_data_width
        self.config_addr_width = config_addr_width
        self.tracks_supported = tracks_supported
        self.allow_bypass = allow_bypass
        self.use_almost_full = use_almost_full
        self.include_E64_HW = include_E64_HW

        cache_key = (self.data_width,
                     self.config_data_width,
                     self.config_addr_width,
                     self.allow_bypass,
                     self.use_almost_full,
                     "IOCoreReadyValid")

        # Check for circuit caching
        if cache_key not in LakeCoreBase._circuit_cache:
            # Instantiate core object here - will only use the object representation to
            # query for information. The circuit representation will be cached and retrieved
            # in the following steps.

            if include_E64_HW:
                self.dut = IOCore_64(data_width=data_width,
                                     tracks_supported=self.tracks_supported,
                                     fifo_depth=fifo_depth,
                                     use_17_to_16_hack=False,
                                     allow_bypass=self.allow_bypass,
                                     use_almost_full=self.use_almost_full,
                                     add_flush=True)
            else:
                self.dut = IOCore(data_width=data_width,
                                  tracks_supported=self.tracks_supported,
                                  fifo_depth=fifo_depth,
                                  use_17_to_16_hack=False,
                                  allow_bypass=self.allow_bypass,
                                  use_almost_full=self.use_almost_full,
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
        with open("iocorerv_cfg.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"(\"{reg}\", 0),  # {self.registers[reg].width}\n"
                cfg_dump.write(write_line)
        with open("iocorerv_synth.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"{reg}\n"
                cfg_dump.write(write_line)

    def get_config_bitstream(self, config_tuple):
        # I believe there's always a delay of 2
        if isinstance(config_tuple, tuple):
            assert len(config_tuple) == 1 or len(config_tuple) == 2
            len_tuple = len(config_tuple)
            if len_tuple == 1:
                config_kwargs = config_tuple
            else:
                _, config_kwargs = config_tuple
        else:
            config_kwargs = config_tuple

        if 'ready_valid_mode' in config_kwargs:
            configs_pre = []

        elif self.include_E64_HW:
            configs_pre = [
                ('glb2io_17_0_valid_reg_sel', 1),
                ('glb2io_17_0_valid_reg_value', 1),

                ('glb2io_1_0_valid_reg_sel', 1),
                ('glb2io_1_0_valid_reg_value', 1),

                ('io2glb_17_0_ready_reg_sel', 1),
                ('io2glb_17_0_ready_reg_value', 1),

                ('io2glb_1_0_ready_reg_sel', 1),
                ('io2glb_1_0_ready_reg_value', 1),
            ]
            if 'exchange_64_mode' in config_kwargs and config_kwargs['exchange_64_mode'] == 1:
                configs_pre += [
                    ('glb2io_17_1_valid_reg_sel', 1),
                    ('glb2io_17_1_valid_reg_value', 1),

                    ('glb2io_17_2_valid_reg_sel', 1),
                    ('glb2io_17_2_valid_reg_value', 1),

                    ('glb2io_17_3_valid_reg_sel', 1),
                    ('glb2io_17_3_valid_reg_value', 1),

                    ('io2glb_17_1_ready_reg_sel', 1),
                    ('io2glb_17_1_ready_reg_value', 1),

                    ('io2glb_17_2_ready_reg_sel', 1),
                    ('io2glb_17_2_ready_reg_value', 1),

                    ('io2glb_17_3_ready_reg_sel', 1),
                    ('io2glb_17_3_ready_reg_value', 1),
                ]
        else:
            configs_pre = [
                ('glb2io_17_valid_reg_sel', 1),
                ('glb2io_17_valid_reg_value', 1),
                ('glb2io_1_valid_reg_sel', 1),
                ('glb2io_1_valid_reg_value', 1),
                ('io2glb_17_ready_reg_sel', 1),
                ('io2glb_17_ready_reg_value', 1),
                ('io2glb_1_ready_reg_sel', 1),
                ('io2glb_1_ready_reg_value', 1),
            ]
        dense_bypass = 0
        configs = []
        # add valid high reg sel

        exchange_64_mode = 0
        if 'exchange_64_mode' in config_kwargs:
            exchange_64_mode = config_kwargs['exchange_64_mode']

        sub_dict = {'dense_bypass': dense_bypass, 'exchange_64_mode': exchange_64_mode}
        tile_config = self.dut.get_bitstream(sub_dict)
        for name, v in configs_pre:
            configs = [self.get_config_data(name, v)] + configs
        for name, v in tile_config:
            configs = [self.get_config_data(name, v)] + configs
        return configs

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
