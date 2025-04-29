from gemstone.generator.from_magma import FromMagma
from lake.top.extract_tile_info import *
import kratos as kts
from gemstone.generator.from_magma import FromMagma
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
        mem_width_default = 16
    else:
        mem_width_default = 64

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
                 ready_valid=True,
                 mem_width=mem_width_default,
                 mem_depth=512):

        self.pnr_tag = pnr_tag
        self.input_prefix = input_prefix

        self.dual_port = dual_port
        self.rf = rf
        self.mem_width = mem_width
        self.mem_depth = mem_depth

        self.fw = mem_width // data_width

        self.ready_valid = ready_valid

        self.read_delay = 1
        if self.rf:
            self.read_delay = 0

        cc_core_name = "CoreCombiner"

        # assert controllers_list is not None and len(controllers_list) > 0
        for controller in controllers_list:
            cc_core_name += f"_{str(controller)}"

        if name is not None:
            cc_core_name = name

        super().__init__(config_data_width=config_data_width,
                         config_addr_width=config_addr_width,
                         data_width=data_width,
                         name=cc_core_name,
                         ready_valid=self.ready_valid)

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
                                   tech_map_name=tech_map_name,
                                   ready_valid=self.ready_valid)

            self.dut = self.CC.dut

            # print(self.dut)

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

    def get_config_bitstream(self, config_tuple, active_core_ports=None):
        # print(self.runtime_mode)
        # assert self.runtime_mode is not None
        configs = []

        print("CORE_COMBINER_CORE_CONFIG")
        print(self.instance_name)
        print(config_tuple)

        # Check if PE, ready_valid, and dict
        use_pe_rv_config = self.ready_valid and isinstance(config_tuple, dict) and self.pnr_tag == "p"

        # Basically this means we are doing a dense app
        if isinstance(config_tuple, dict) and not use_pe_rv_config:
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
                    # config_extra_rom = [(f"{self.get_port_remap()['ROM']['wen']}_reg_sel", 1)]
                    config_extra_rom = []
                    for name, v in config_extra_rom:
                        configs = [self.get_config_data(name, v)] + configs
                elif 'mode' not in instr and 'stencil_valid' in instr:
                    instr['mode'] = 'stencil_valid'
                else:
                    # Default to UB mode since we get varying consistency in controller indication
                    instr['mode'] = 'UB'

                config_pre = self.dut.get_bitstream(instr)

                # Add the runtime configuration to the final config
                for name, v in config_pre:
                    configs = [self.get_config_data(name, v)] + configs

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
                # print(configs)
                return configs
            elif self.pnr_tag == 'p':
                instr['mode'] = 'alu'
                config_pre = self.dut.get_bitstream(instr)
                for name, v in config_pre:
                    configs = [self.get_config_data(name, v)] + configs
                # print(configs)
                return configs
        elif not isinstance(config_tuple, tuple) or use_pe_rv_config:
            dense_ready_valid = "DENSE_READY_VALID" in os.environ and os.environ.get("DENSE_READY_VALID") == "1"
            # It's a PE then...
            if active_core_ports is None:
                raise ValueError("Error: 'active_core_ports' cannot be None for a PE.")
            active_inputs = list("000")
            active_bit_inputs = list("000")
            active_16b_output = 0
            active_1b_output = 0
            is_constant_pe = 0

            input_count = 0
            input_bit_count = 0
            output_count = 0
            output_bit_count = 0

            for port_name in active_core_ports:
                port_width = int(port_name.split("width_")[1].split("_")[0])
                if 'input' in port_name:
                    input_num = port_name.split('num_')[1]

                    if port_width > 1:
                        input_count += 1
                        active_inputs[2 - int(input_num)] = '1'
                    else:
                        input_bit_count += 1
                        active_bit_inputs[2 - int(input_num)] = '1'

                if 'output' in port_name:
                    if port_width > 1:
                        output_count += 1
                        active_16b_output = 1
                    else:
                        output_bit_count += 1
                        active_1b_output = 1

            active_inputs = int("".join(active_inputs), 2)
            active_bit_inputs = int("".join(active_bit_inputs), 2)
            # print(f"active_inputs: {active_inputs}, active_bit_inputs: {active_bit_inputs},
            #       active_16b_output: {active_16b_output}, active_1b_output: {active_1b_output}")

            if not (dense_ready_valid):
                active_inputs = 0
                active_bit_inputs = 0
                active_16b_output = 0
                active_1b_output = 0

            if input_bit_count == 0 and input_count == 0 and ((output_count > 0) or (output_bit_count)):
                is_constant_pe = 1
                print("CONSTANT PE")

            # These should be maps from a port to how much data it needs...
            input_bogus = {}
            output_bogus = 0
            p_remap = self.get_port_remap()
            if self.ready_valid:
                pe_op = None
                # parse the pe instruction out...
                if isinstance(config_tuple, dict):
                    pe_op = int(config_tuple["pe_inst"])
                    # Check for num_input_fifo, num_output_fifo to load them in...
                    # For now, should be safe to add any input fifo stuff to all input fifos since we already
                    # check that there are no real streams joining here (should be a constant)

                    # The rest is ports that have fifo
                    # print("PRINT PE REMAP")
                    # print(p_remap)

                    # for port_name_with_p, fifo_info in config_tuple[0].items():
                    for port_name_with_p, fifo_info in config_tuple.items():
                        if port_name_with_p == "pe_inst":
                            continue
                        port_name_stripped = port_name_with_p.strip(".")
                        port_name_remapped = p_remap['alu'][port_name_stripped]
                        # print(f"{port_name_with_p} remapped to {port_name_remapped}")
                        if "data" in port_name_stripped:
                            print("ADDING BOGUS DATA")
                            input_bogus[port_name_remapped] = int(fifo_info["num_input_fifo"])
                            output_bogus = int(fifo_info["num_output_fifo"])
                else:
                    pe_op = int(config_tuple)

                assert pe_op is not None, "PE op must be set either through a metadata dictionary or a list"

                config_kwargs = {
                    'mode': 'alu',
                    'bypass_rv': not (dense_ready_valid),
                    'active_inputs': active_inputs,
                    'op': pe_op,
                    'active_bit_inputs': active_bit_inputs,
                    'active_16b_output': active_16b_output,
                    'active_1b_output': active_1b_output,
                    # pe in dense mode always accept inputs that are external
                    # to the cluster
                    'pe_in_external': 1,
                    'is_constant_pe': is_constant_pe,
                    # only configure pe within the cluster
                    'pe_only': True
                }
            else:
                config_kwargs = {
                    'mode': 'alu',
                    'op': int(config_tuple)
                }
            instr = config_kwargs
            config_pre = self.dut.get_bitstream(instr)
            for name, v in config_pre:
                configs = [self.get_config_data(name, v)] + configs

            # BEGIN BLOCK COMMENT
            # TODO: Fix this and name it better. ready_valid really means include RV interconnect in this context
            if self.ready_valid:
                rv_bypass_value = 0 if dense_ready_valid else 1
                config_rv_bypass = [(f"{self.get_port_remap()['alu']['data0']}_bypass_rv", rv_bypass_value),
                                    (f"{self.get_port_remap()['alu']['data1']}_bypass_rv", rv_bypass_value),
                                    (f"{self.get_port_remap()['alu']['data2']}_bypass_rv", rv_bypass_value),
                                    (f"{self.get_port_remap()['alu']['res']}_bypass_rv", rv_bypass_value)]
                for name, v in config_rv_bypass:
                    configs = [self.get_config_data(name, v)] + configs

                input_bogus_init_num = [0, 0, 0, 0]

                # Iterate through the active core ports (inputs) and assign them the input_bogus
                for port_name, num_in in input_bogus.items():
                    input_num = int(port_name.split('_num_')[1])
                    input_bogus_init_num[input_num] = num_in

                assert all(0 <= num <= 2 for num in input_bogus_init_num), \
                    "All elements in input_bogus_init_num must be between 0 and 2 inclusive"
                config_input_bogus_init = [(f"PE_input_width_17_num_0_fifo_bogus_init_num", input_bogus_init_num[0]),
                                           (f"PE_input_width_17_num_1_fifo_bogus_init_num", input_bogus_init_num[1]),
                                           (f"PE_input_width_17_num_2_fifo_bogus_init_num", input_bogus_init_num[2]),
                                           (f"PE_input_width_17_num_3_fifo_bogus_init_num", input_bogus_init_num[3])]
                for name, v in config_input_bogus_init:
                    configs = [self.get_config_data(name, v)] + configs

                output_bogus_init_num = [0, 0, 0]
                # Iterate through the active core ports (inputs) and assign them the output_bogus
                # Currently assume only one output - which has to be true given that the ALU has only one data output...
                # If we are putting data in the output fifo, assert that we are using a single 16b output...
                if output_bogus > 0:
                    assert output_count == 1, "Must be one output for bogus data fifos..."
                for port_name in active_core_ports:
                    if "output" in port_name:
                        output_num = int(port_name.split('_num_')[1])
                        output_bogus_init_num[output_num] = output_bogus

                assert all(0 <= num <= 2 for num in output_bogus_init_num), \
                    "All elements in output_bogus_init_num must be between 0 and 2 inclusive"
                config_output_bogus_init = [(f"PE_output_width_17_num_0_fifo_bogus_init_num", output_bogus_init_num[0]),
                                            (f"PE_output_width_17_num_1_fifo_bogus_init_num", output_bogus_init_num[1]),
                                            (f"PE_output_width_17_num_2_fifo_bogus_init_num", output_bogus_init_num[2])]

                print("PE bogus init...")
                for it_ in config_input_bogus_init:
                    print(it_)
                for it_ in config_output_bogus_init:
                    print(it_)
                print("PE bogus init end...")

                for name, v in config_output_bogus_init:
                    configs = [self.get_config_data(name, v)] + configs

                config_rv_bypass_bit = [(f"{self.get_port_remap()['alu']['bit0']}_bypass_rv", rv_bypass_value),
                                        (f"{self.get_port_remap()['alu']['bit1']}_bypass_rv", rv_bypass_value),
                                        (f"{self.get_port_remap()['alu']['bit2']}_bypass_rv", rv_bypass_value),
                                        (f"{self.get_port_remap()['alu']['res_p']}_bypass_rv", rv_bypass_value)]
                for name, v in config_rv_bypass_bit:
                    configs = [self.get_config_data(name, v)] + configs

                fine_grained_input_fifo_bypass = [0, 0, 0]
                fine_grained_output_fifo_bypass = 0

                config_fine_grained_input_fifo_bypass = [
                    (f"{self.get_port_remap()['alu']['data0']}_fine_grain_fifo_bypass",
                     fine_grained_input_fifo_bypass[0]),
                    (f"{self.get_port_remap()['alu']['data1']}_fine_grain_fifo_bypass",
                     fine_grained_input_fifo_bypass[1]),
                    (f"{self.get_port_remap()['alu']['data2']}_fine_grain_fifo_bypass",
                     fine_grained_input_fifo_bypass[2]),
                    (f"{self.get_port_remap()['alu']['res']}_fine_grain_fifo_bypass",
                     fine_grained_output_fifo_bypass)]
                for name, v in config_fine_grained_input_fifo_bypass:
                    configs = [self.get_config_data(name, v)] + configs
            # END BLOCK COMMENT
            # print(configs)
            return configs
        else:
            _, config_kwargs = config_tuple
        assert 'mode' in config_kwargs
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
