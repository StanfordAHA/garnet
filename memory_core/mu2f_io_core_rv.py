from gemstone.generator.from_magma import FromMagma
from gemstone.common.core import PnRTag
from lake.modules.mu2f_io_core import IOCore_mu2f
import kratos as kts

if __name__ == "__main__":
    from memtile_util import LakeCoreBase
else:
    from .memtile_util import LakeCoreBase


class MU2F_IOCoreReadyValid(LakeCoreBase):

    def __init__(self,
                 matrix_unit_data_width=16,  # CGRA Params
                 tile_array_data_width=17,
                 num_ios=2,
                 config_data_width=32,
                 config_addr_width=8,
                 fifo_depth=2,
                 allow_bypass=False,
                 use_almost_full=False):

        buffet_name = "MU2F_IOCoreReadyValid"  # noqa "assigned but never used"
        super().__init__(config_data_width=config_data_width,
                         config_addr_width=config_addr_width,
                         data_width=16,
                         name="MU2F_IOCoreReadyValid",
                         ready_valid=True, # setting ready_valid to false because custom ready_valid ports have already been created in the lake module
                         include_stall=True) # Temporary hack to remove the stall port, till stall port width is updated in generator 

        # Capture everything to the tile object
        self.matrix_unit_data_width = matrix_unit_data_width
        self.tile_array_data_width = tile_array_data_width
        self.num_ios = num_ios
        self.config_data_width = config_data_width
        self.config_addr_width = config_addr_width
        self.allow_bypass = allow_bypass
        self.use_almost_full = use_almost_full


        cache_key = ( self.matrix_unit_data_width,
                     self.tile_array_data_width,
                     self.num_ios,
                     self.config_data_width,
                     self.config_addr_width,
                     self.allow_bypass,
                     self.use_almost_full,
                     "MU2F_IOCoreReadyValid")

        # Check for circuit caching
        if cache_key not in LakeCoreBase._circuit_cache:
            # Instantiate core object here - will only use the object representation to
            # query for information. The circuit representation will be cached and retrieved
            # in the following steps.
            self.dut = IOCore_mu2f(matrix_unit_data_width=self.matrix_unit_data_width,
                              tile_array_data_width=self.tile_array_data_width,
                              fifo_depth=fifo_depth,
                              num_ios = self.num_ios,
                              allow_bypass=self.allow_bypass,
                              use_almost_full=self.use_almost_full,
                              add_flush=True,
                              add_clk_en=True)

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
        with open("mu2f_iocorerv_cfg.txt", "w+") as cfg_dump:
            for idx, reg in enumerate(conf_names):
                write_line = f"(\"{reg}\", 0),  # {self.registers[reg].width}\n"
                cfg_dump.write(write_line)
        with open("mu2f_iocorerv_synth.txt", "w+") as cfg_dump:
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

        if 'sparse_mode' in config_kwargs:
            configs_pre = []
        else:
            configs_pre = [
            ]
        dense_bypass = 0
        configs = []
        # add valid high reg sel

       # sub_dict = {'dense_bypass': dense_bypass}
        tile_config = self.dut.get_bitstream(sub_dict)
        for name, v in configs_pre:
            configs = [self.get_config_data(name, v)] + configs
        for name, v in tile_config:
            configs = [self.get_config_data(name, v)] + configs
        #return configs
        return []

    def pnr_info(self):
        return [PnRTag("U", 2, self.DEFAULT_PRIORITY),
                PnRTag("u", 1, self.DEFAULT_PRIORITY),
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
    mu2f_rviocore = MU2F_IOCoreReadyValid()
