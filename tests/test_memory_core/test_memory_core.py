from memory_core.memory_core import gen_memory_core, Mode
from memory_core.memory_core_magma import MemCore
import glob
import tempfile
import shutil
import fault
import random
import magma
from gemstone.common.testers import ResetTester
from gemstone.common.testers import BasicTester
import pytest
from gemstone.generator import Const


def make_memory_core():
    mem_core = MemCore()
    mem_circ = mem_core.circuit()

    tester = MemoryCoreTester(mem_circ, mem_circ.clk, mem_circ.reset)
    tester.poke(mem_circ.clk, 0)
    tester.poke(mem_circ.reset, 0)
    tester.step(1)
    tester.poke(mem_circ.reset, 1)
    tester.step(1)
    tester.reset()
    return [mem_circ, tester, mem_core]


class MemoryCoreTester(BasicTester):

    def configure(self, addr, data, feature):
        self.poke(self.clock, 0)
        self.poke(self.reset_port, 0)
        if(feature == 0):
            exec(f"self.poke(self._circuit.config.config_addr, addr)")
            exec(f"self.poke(self._circuit.config.config_data, data)")
            exec(f"self.poke(self._circuit.config.write, 1)")
            self.step(1)
            exec(f"self.poke(self._circuit.config.write, 0)")
            exec(f"self.poke(self._circuit.config.config_data, 0)")
        else:
            exec(f"self.poke(self._circuit.config_{feature}.config_addr, addr)")
            exec(f"self.poke(self._circuit.config_{feature}.config_data, data)")
            exec(f"self.poke(self._circuit.config_{feature}.write, 1)")
            self.step(1)
            exec(f"self.poke(self._circuit.config_{feature}.write, 0)")
            exec(f"self.poke(self._circuit.config_{feature}.config_data, 0)")


def test_multiple_output_ports():
    # Regular Bootstrap
    [circuit, tester, MCore] = make_memory_core()

    tester.poke(circuit.stall, 1)

    tile_en = 1
    depth = 1024
    chunk = 128
    startup_delay = 4
    mode = Mode.DB

    config_data = []

    config_data.append((MCore.get_reg_index("strg_ub_app_ctrl_input_port_0"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_app_ctrl_output_port_0"), 1, 0))
    config_data.append((MCore.get_reg_index("strg_ub_app_ctrl_coarse_output_port_0"), 1, 0))
    config_data.append((MCore.get_reg_index("strg_ub_app_ctrl_read_depth_0"), 3 * chunk * 4, 0))
    config_data.append((MCore.get_reg_index("strg_ub_app_ctrl_write_depth_wo_0"), 256 * 4, 0))
    config_data.append((MCore.get_reg_index("strg_ub_app_ctrl_write_depth_ss_0"), 256 * 4, 0))
    config_data.append((MCore.get_reg_index("strg_ub_app_ctrl_coarse_read_depth_0"), int(3 * chunk), 0))
    config_data.append((MCore.get_reg_index("strg_ub_app_ctrl_coarse_write_depth_wo_0"), 256, 0))
    config_data.append((MCore.get_reg_index("strg_ub_app_ctrl_coarse_write_depth_ss_0"), 256, 0))

    config_data.append((MCore.get_reg_index("strg_ub_input_addr_ctrl_address_gen_0_dimensionality"), 2, 0))
    config_data.append((MCore.get_reg_index("strg_ub_input_addr_ctrl_address_gen_0_ranges_0"), 256, 0))
    config_data.append((MCore.get_reg_index("strg_ub_input_addr_ctrl_address_gen_0_ranges_1"), 100, 0))
    config_data.append((MCore.get_reg_index("strg_ub_input_addr_ctrl_address_gen_0_ranges_2"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_input_addr_ctrl_address_gen_0_ranges_3"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_input_addr_ctrl_address_gen_0_starting_addr"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_input_addr_ctrl_address_gen_0_strides_0"), 1, 0))
    config_data.append((MCore.get_reg_index("strg_ub_input_addr_ctrl_address_gen_0_strides_1"), 256, 0))
    config_data.append((MCore.get_reg_index("strg_ub_input_addr_ctrl_address_gen_0_strides_2"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_input_addr_ctrl_address_gen_0_strides_3"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_input_addr_ctrl_address_gen_0_strides_4"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_input_addr_ctrl_address_gen_0_strides_5"), 0, 0))

    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_0_dimensionality"), 3, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_0_ranges_0"), 128, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_0_ranges_1"), 3, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_0_ranges_2"), 100, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_0_ranges_3"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_0_ranges_4"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_0_ranges_5"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_0_starting_addr"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_0_strides_0"), 1, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_0_strides_1"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_0_strides_2"), 256, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_0_strides_3"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_0_strides_4"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_0_strides_5"), 0, 0))

    config_data.append((MCore.get_reg_index("strg_ub_tba_0_tb_0_range_outer"), chunk, 0))
    config_data.append((MCore.get_reg_index("strg_ub_tba_0_tb_0_starting_addr"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_tba_0_tb_0_stride"), 1, 0))
    config_data.append((MCore.get_reg_index("strg_ub_tba_0_tb_0_dimensionality"), 1, 0))
    config_data.append((MCore.get_reg_index("strg_ub_tba_0_tb_0_indices_merged_0"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_tba_0_tb_0_range_inner"), 2, 0))
    config_data.append((MCore.get_reg_index("strg_ub_tba_0_tb_0_tb_height"), 1, 0))

    config_data.append((MCore.get_reg_index("strg_ub_sync_grp_sync_group_0"), 1, 0))
    config_data.append((MCore.get_reg_index("tile_en"), 1, 0))
    config_data.append((MCore.get_reg_index("fifo_ctrl_fifo_depth"), 0, 0))
    config_data.append((MCore.get_reg_index("mode"), 0, 0))
    config_data.append((MCore.get_reg_index("flush_reg_sel"), 1, 0))
    config_data.append((MCore.get_reg_index("wen_in_1_reg_sel"), 1, 0))
    config_data.append((MCore.get_reg_index("strg_ub_pre_fetch_0_input_latency"), 4, 0))

    config_data.append((MCore.get_reg_index("enable_chain_output"), 0, 0))
    config_data.append((MCore.get_reg_index("enable_chain_input"), 0, 0))
    config_data.append((MCore.get_reg_index("chain_idx_input"), 0, 0))
    config_data.append((MCore.get_reg_index("chain_idx_output"), 0, 0))

    config_data.append((MCore.get_reg_index("strg_ub_app_ctrl_input_port_1"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_app_ctrl_read_depth_1"), 3 * chunk * 4, 0))
    config_data.append((MCore.get_reg_index("strg_ub_app_ctrl_coarse_read_depth_1"), 3 * chunk, 0))

    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_1_dimensionality"), 3, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_1_ranges_0"), 128, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_1_ranges_1"), 3, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_1_ranges_2"), 100, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_1_ranges_3"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_1_ranges_4"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_1_ranges_5"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_1_starting_addr"), 128, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_1_strides_0"), 1, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_1_strides_1"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_1_strides_2"), 256, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_1_strides_3"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_1_strides_4"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_output_addr_ctrl_address_gen_1_strides_5"), 0, 0))

    config_data.append((MCore.get_reg_index("strg_ub_tba_1_tb_0_range_outer"), chunk, 0))
    config_data.append((MCore.get_reg_index("strg_ub_tba_1_tb_0_starting_addr"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_tba_1_tb_0_stride"), 1, 0))
    config_data.append((MCore.get_reg_index("strg_ub_tba_1_tb_0_dimensionality"), 1, 0))
    config_data.append((MCore.get_reg_index("strg_ub_tba_1_tb_0_indices_merged_0"), 0, 0))
    config_data.append((MCore.get_reg_index("strg_ub_tba_1_tb_0_range_inner"), 2, 0))
    config_data.append((MCore.get_reg_index("strg_ub_tba_1_tb_0_tb_height"), 1, 0))

    config_data.append((MCore.get_reg_index("strg_ub_sync_grp_sync_group_1"), 1, 0))
    config_data.append((MCore.get_reg_index("strg_ub_pre_fetch_1_input_latency"), 4, 0))

    # Configure
    for addr, data, feat in config_data:
        tester.configure(addr, data, feat)

    tester.poke(circuit.stall, 0)
    tester.eval()

    inputs = []
    for z in range(6):
        for i in range(depth):
            inputs.append(i)

    outputs_0 = []
    outputs_1 = []
    for z in range(6):
        for i in range(depth // 2):
            outputs_0.append(i)
            outputs_1.append(i + 512)

    tester.poke(circuit.ren_in_0, 1)
    tester.poke(circuit.ren_in_1, 1)

    output_idx = 0

    for i in range(4 * depth):
        # We are just writing sequentially for this sample
        if(i >= 2 * depth + 4 * chunk):
            tester.poke(circuit.wen_in_0, 1)
        elif(i >= 2 * depth):
            # Write for two rounds
            tester.poke(circuit.wen_in_0, 0)
        else:
            tester.poke(circuit.wen_in_0, 1)
            tester.poke(circuit.data_in_0, inputs[i])

        tester.eval()

        if (i > depth + startup_delay):
            tester.expect(circuit.valid_out_0, 1)
            tester.expect(circuit.valid_out_1, 1)
            tester.expect(circuit.data_out_0, outputs_0[output_idx])
            tester.expect(circuit.data_out_1, outputs_1[output_idx])
            output_idx += 1
        else:
            tester.expect(circuit.valid_out_0, 0)
            tester.expect(circuit.valid_out_1, 0)

        tester.step(2)

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               target="verilator",
                               flags=["-Wno-fatal"])
