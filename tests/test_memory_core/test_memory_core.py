from memory_core.memory_core import gen_memory_core, Mode
from memory_core.memory_core_magma import MemCore
from lake.utils.parse_clkwork_csv import generate_data_lists
import glob
import tempfile
import shutil
import fault
import random
import magma
import os
from gemstone.common.testers import ResetTester
from gemstone.common.testers import BasicTester
from gemstone.common.util import compress_config_data
import pytest
from gemstone.generator import Const
from cgra.util import create_cgra
from canal.util import IOSide
from memory_core.memory_core_magma import config_mem_tile
from archipelago import pnr


# @pytest.fixture()
def io_sides():
    return IOSide.North | IOSide.East | IOSide.South | IOSide.West


# @pytest.fixture(scope="module")
def dw_files():
    filenames = ["DW_fp_add.v", "DW_fp_mult.v"]
    dirname = "peak_core"
    result_filenames = []
    for name in filenames:
        filename = os.path.join(dirname, name)
        assert os.path.isfile(filename)
        result_filenames.append(filename)
    return result_filenames


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

    def configure(self, addr, data, feature=0):
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


# No longer applicable w/ Diet Lake
@pytest.mark.skip
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

    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_input_port_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_output_port_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_output_port_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_read_depth_0", 3 * chunk * 4))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_write_depth_wo_0", 256 * 4))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_write_depth_ss_0", 256 * 4))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_read_depth_0", int(3 * chunk)))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_write_depth_wo_0", 256))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_write_depth_ss_0", 256))

    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_dimensionality", 2))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_0", 256))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_1", 100))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_1", 256))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_5", 0))

    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_dimensionality", 3))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_0", 128))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_1", 3))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_2", 100))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_5", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_1", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_2", 256))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_5", 0))

    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_range_outer", chunk))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_stride", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_dimensionality", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_indices_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_range_inner", 2))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_tb_height", 1))

    config_data.append(MCore.get_config_data("strg_ub_sync_grp_sync_group_0", 1))
    config_data.append(MCore.get_config_data("tile_en", 1))
    config_data.append(MCore.get_config_data("fifo_ctrl_fifo_depth", 0))
    config_data.append(MCore.get_config_data("mode", 0))
    config_data.append(MCore.get_config_data("flush_reg_sel", 1))
    config_data.append(MCore.get_config_data("wen_in_1_reg_sel", 1))
    config_data.append(MCore.get_config_data("strg_ub_pre_fetch_0_input_latency", 4))

    config_data.append(MCore.get_config_data("enable_chain_output", 0))
    config_data.append(MCore.get_config_data("enable_chain_input", 0))
    config_data.append(MCore.get_config_data("chain_idx_input", 0))
    config_data.append(MCore.get_config_data("chain_idx_output", 0))

    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_input_port_1", 0))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_read_depth_1", 3 * chunk * 4))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_read_depth_1", 3 * chunk))

    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_dimensionality", 3))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_0", 128))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_1", 3))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_2", 100))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_5", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_starting_addr", 128))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_1", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_2", 256))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_5", 0))

    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_range_outer", chunk))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_stride", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_dimensionality", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_indices_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_range_inner", 2))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_tb_height", 1))

    config_data.append(MCore.get_config_data("strg_ub_sync_grp_sync_group_1", 1))
    config_data.append(MCore.get_config_data("strg_ub_pre_fetch_1_input_latency", 4))

    config_data = compress_config_data(config_data)

    # Configure
    for addr, data in config_data:
        tester.configure(addr, data)

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


# No longer applicable w/ Diet Lake
@pytest.mark.skip
def test_multiple_output_ports_conv():
    # Regular Bootstrap
    [circuit, tester, MCore] = make_memory_core()

    tester.poke(circuit.stall, 1)

    tile_en = 1
    depth = 1024
    chunk = 128
    startup_delay = 4
    num_outputs = 6 * 6 * 3 * 3 * 2 * 4
    mode = Mode.DB

    config_data = []

    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_input_port_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_output_port_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_output_port_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_read_depth_0", num_outputs))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_write_depth_wo_0", 256 * 4))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_write_depth_ss_0", 256 * 4))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_read_depth_0", int(num_outputs / 4)))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_write_depth_wo_0", 256))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_write_depth_ss_0", 256))

    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_dimensionality", 2))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_0", 256))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_1", 100))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_1", 256))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_5", 0))

    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_dimensionality", 6))
    # channel
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_0", 2))
    # window x
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_1", 3))
    # window y
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_2", 3))
    # chunk x
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_3", 6))
    # cuhnk y
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_4", 6))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_5", 100))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_1", 2))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_2", 16))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_3", 2))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_4", 16))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_5", 0))

    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_range_outer", chunk))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_stride", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_dimensionality", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_indices_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_range_inner", 2))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_tb_height", 1))

    config_data.append(MCore.get_config_data("strg_ub_sync_grp_sync_group_0", 1))
    config_data.append(MCore.get_config_data("tile_en", 1))
    config_data.append(MCore.get_config_data("fifo_ctrl_fifo_depth", 0))
    config_data.append(MCore.get_config_data("mode", 0))
    config_data.append(MCore.get_config_data("flush_reg_sel", 1))
    config_data.append(MCore.get_config_data("wen_in_1_reg_sel", 1))
    config_data.append(MCore.get_config_data("strg_ub_pre_fetch_0_input_latency", 4))

    config_data.append(MCore.get_config_data("enable_chain_output", 0))
    config_data.append(MCore.get_config_data("enable_chain_input", 0))
    config_data.append(MCore.get_config_data("chain_idx_input", 0))
    config_data.append(MCore.get_config_data("chain_idx_output", 0))

    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_input_port_1", 0))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_read_depth_1", num_outputs))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_read_depth_1", int(num_outputs / 4)))

    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_dimensionality", 6))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_0", 2))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_1", 3))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_2", 3))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_3", 6))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_4", 6))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_5", 100))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_starting_addr", 128))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_1", 2))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_2", 16))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_3", 2))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_4", 16))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_5", 0))

    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_range_outer", chunk))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_stride", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_dimensionality", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_indices_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_range_inner", 2))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_tb_height", 1))

    config_data.append(MCore.get_config_data("strg_ub_sync_grp_sync_group_1", 1))
    config_data.append(MCore.get_config_data("strg_ub_pre_fetch_1_input_latency", 4))

    config_data = compress_config_data(config_data)

    # Configure
    for addr, data in config_data:
        tester.configure(addr, data)

    tester.poke(circuit.stall, 0)
    tester.eval()

    inputs = []
    for z in range(6):
        for i in range(depth):
            inputs.append(i)

    output_index = []
    output1_index = []
    for y in range(6):
        for x in range(6):
            for wy in range(3):
                for wx in range(3):
                    for ch in range(2):
                        offset = y * 16 + x * 2 + wy * 16 + wx * 2 + ch * 1
                        output1 = 128 + offset
                        for i in range(4):
                            output_index.append((offset * 4 + i) % len(inputs))
                            output1_index.append((output1 * 4 + i) % len(inputs))

    tester.poke(circuit.ren_in_0, 1)
    tester.poke(circuit.ren_in_1, 1)

    output_idx = 0

    for i in range(depth + startup_delay + num_outputs):
        # We are just writing sequentially for this sample
        if (i < 2 * depth):
            tester.poke(circuit.wen_in_0, 1)
            tester.poke(circuit.data_in_0, inputs[i])
        else:
            tester.poke(circuit.wen_in_0, 0)

        tester.eval()

        if (i > depth + startup_delay):
            tester.expect(circuit.valid_out_0, 1)
            tester.expect(circuit.valid_out_1, 1)

            idx0 = output_index[output_idx]
            idx1 = output1_index[output_idx]

            tester.expect(circuit.data_out_0, inputs[idx0])
            tester.expect(circuit.data_out_1, inputs[idx1])

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


# No longer applicable w/ Diet Lake
@pytest.mark.skip
def test_mult_ports_mult_aggs_double_buffer_conv():
    # Regular Bootstrap
    [circuit, tester, MCore] = make_memory_core()

    tester.poke(circuit.stall, 1)

    tile_en = 1
    depth = 128 * 4

    # 4 is normal start up delay, 1 is due to mult input port agg scheduling
    startup_delay = 4 + 1
    num_outputs = 6 * 6 * 3 * 3 * 2 * 4
    mode = Mode.DB

    config_data = []

    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_input_port_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_output_port_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_output_port_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_read_depth_0", num_outputs))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_write_depth_wo_0", depth))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_write_depth_ss_0", depth))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_read_depth_0", int(num_outputs / 4)))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_write_depth_wo_0", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_write_depth_ss_0", int(depth / 4)))

    config_data.append(MCore.get_config_data("strg_ub_agg_in_0_in_period", 2))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_0_in_sched_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_0_in_sched_1", 1))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_0_out_period", 2))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_0_out_sched_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_0_out_sched_1", 1))

    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_dimensionality", 2))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_0", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_1", 100))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_1", 256))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_5", 0))

    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_dimensionality", 6))
    # channel
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_0", 2))
    # window x
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_1", 3))
    # window y
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_2", 3))
    # chunk x
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_3", 6))
    # cuhnk y
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_4", 6))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_5", 100))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_1", 2))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_2", 16))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_3", 2))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_4", 16))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_5", 0))

    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_range_outer", depth))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_stride", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_dimensionality", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_indices_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_range_inner", 2))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_tb_height", 1))

    config_data.append(MCore.get_config_data("strg_ub_sync_grp_sync_group_0", 1))
    config_data.append(MCore.get_config_data("tile_en", 1))
    config_data.append(MCore.get_config_data("fifo_ctrl_fifo_depth", 0))
    config_data.append(MCore.get_config_data("mode", 0))
    config_data.append(MCore.get_config_data("flush_reg_sel", 1))
    config_data.append(MCore.get_config_data("strg_ub_pre_fetch_0_input_latency", 4))

    config_data.append(MCore.get_config_data("enable_chain_output", 0))
    config_data.append(MCore.get_config_data("enable_chain_input", 0))
    config_data.append(MCore.get_config_data("chain_idx_input", 0))
    config_data.append(MCore.get_config_data("chain_idx_output", 0))

    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_input_port_1", 1))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_read_depth_1", num_outputs))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_write_depth_wo_1", depth))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_write_depth_ss_1", depth))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_read_depth_1", int(num_outputs / 4)))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_write_depth_wo_1", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_write_depth_ss_1", int(depth / 4)))

    config_data.append(MCore.get_config_data("strg_ub_agg_in_1_in_period", 2))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_1_in_sched_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_1_in_sched_1", 1))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_1_out_period", 2))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_1_out_sched_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_1_out_sched_1", 1))

    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_dimensionality", 2))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_ranges_0", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_ranges_1", 100))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_ranges_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_ranges_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_starting_addr", 128))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_strides_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_strides_1", 256))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_strides_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_strides_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_strides_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_strides_5", 0))

    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_dimensionality", 6))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_0", 2))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_1", 3))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_2", 3))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_3", 6))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_4", 6))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_5", 100))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_starting_addr", 128))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_1", 2))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_2", 16))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_3", 2))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_4", 16))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_5", 0))

    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_range_outer", depth))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_stride", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_dimensionality", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_indices_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_range_inner", 2))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_tb_height", 1))

    config_data.append(MCore.get_config_data("strg_ub_sync_grp_sync_group_1", 1))
    config_data.append(MCore.get_config_data("strg_ub_pre_fetch_1_input_latency", 4))

    config_data = compress_config_data(config_data)

    # Configure
    for addr, data in config_data:
        tester.configure(addr, data)

    tester.poke(circuit.stall, 0)
    tester.eval()

    inputs = []
    inputs1 = []
    for j in range(3):
        for i in range(depth):
            inputs.append(i + (j + 1) * 16)
            inputs1.append((i + 16) + (j + 1) * 16)

    output_index = []
    output1_index = []
    for y in range(6):
        for x in range(6):
            for wy in range(3):
                for wx in range(3):
                    for ch in range(2):
                        offset = y * 16 + x * 2 + wy * 16 + wx * 2 + ch * 1
                        output1 = 128 + offset
                        for i in range(4):
                            output_index.append((offset * 4 + i) % len(inputs))
                            output1_index.append((output1 * 4 + i) % len(inputs))

    tester.poke(circuit.ren_in_0, 1)
    tester.poke(circuit.ren_in_1, 1)

    output_idx = 0

    for i in range(depth + startup_delay + num_outputs):
        if(i >= 3 * depth):
            tester.poke(circuit.wen_in_0, 0)
            tester.poke(circuit.wen_in_1, 0)
        else:
            tester.poke(circuit.wen_in_0, 1)
            tester.poke(circuit.data_in_0, inputs[i])
            tester.poke(circuit.wen_in_1, 1)
            tester.poke(circuit.data_in_1, inputs1[i])

        tester.eval()

        if (i > depth + startup_delay):
            tester.expect(circuit.valid_out_0, 1)
            tester.expect(circuit.valid_out_1, 1)

            idx0 = output_index[output_idx]
            idx1 = output1_index[output_idx]

            tester.expect(circuit.data_out_0, inputs[idx0])
            tester.expect(circuit.data_out_1, inputs[idx1])

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


# No longer applicable w/ Diet Lake
@pytest.mark.skip
def test_mult_ports_mult_aggs_double_buffer():
    # Regular Bootstrap
    [circuit, tester, MCore] = make_memory_core()

    tester.poke(circuit.stall, 1)

    tile_en = 1
    depth = 128 * 4

    # 4 is normal start up delay, 1 is due to mult input port agg scheduling
    startup_delay = 4 + 1
    num_outputs = 6 * 6 * 3 * 3 * 2 * 4
    mode = Mode.DB

    config_data = []

    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_input_port_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_output_port_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_output_port_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_read_depth_0", depth))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_write_depth_wo_0", depth))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_write_depth_ss_0", depth))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_read_depth_0", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_write_depth_wo_0", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_write_depth_ss_0", int(depth / 4)))

    config_data.append(MCore.get_config_data("strg_ub_agg_in_0_in_period", 2))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_0_in_sched_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_0_in_sched_1", 1))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_0_out_period", 2))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_0_out_sched_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_0_out_sched_1", 1))

    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_dimensionality", 2))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_0", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_1", 100))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_1", 256))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_5", 0))

    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_dimensionality", 2))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_0", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_1", 100))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_5", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_1", 256))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_5", 0))

    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_range_outer", depth))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_stride", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_dimensionality", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_indices_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_range_inner", 2))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_tb_height", 1))

    config_data.append(MCore.get_config_data("strg_ub_sync_grp_sync_group_0", 1))
    config_data.append(MCore.get_config_data("tile_en", 1))
    config_data.append(MCore.get_config_data("fifo_ctrl_fifo_depth", 0))
    config_data.append(MCore.get_config_data("mode", 0))
    config_data.append(MCore.get_config_data("flush_reg_sel", 1))
    config_data.append(MCore.get_config_data("strg_ub_pre_fetch_0_input_latency", 4))

    config_data.append(MCore.get_config_data("enable_chain_output", 0))
    config_data.append(MCore.get_config_data("enable_chain_input", 0))
    config_data.append(MCore.get_config_data("chain_idx_input", 0))
    config_data.append(MCore.get_config_data("chain_idx_output", 0))

    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_input_port_1", 1))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_read_depth_1", depth))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_write_depth_wo_1", depth))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_write_depth_ss_1", depth))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_read_depth_1", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_write_depth_wo_1", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_write_depth_ss_1", int(depth / 4)))

    config_data.append(MCore.get_config_data("strg_ub_agg_in_1_in_period", 2))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_1_in_sched_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_1_in_sched_1", 1))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_1_out_period", 2))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_1_out_sched_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_1_out_sched_1", 1))

    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_dimensionality", 2))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_ranges_0", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_ranges_1", 100))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_ranges_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_ranges_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_starting_addr", 128))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_strides_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_strides_1", 256))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_strides_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_strides_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_strides_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_strides_5", 0))

    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_dimensionality", 2))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_0", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_1", 100))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_5", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_starting_addr", 128))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_1", 256))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_5", 0))

    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_range_outer", depth))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_stride", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_dimensionality", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_indices_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_range_inner", 2))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_tb_height", 1))

    config_data.append(MCore.get_config_data("strg_ub_sync_grp_sync_group_1", 1))
    config_data.append(MCore.get_config_data("strg_ub_pre_fetch_1_input_latency", 4))

    config_data = compress_config_data(config_data)

    # Configure
    for addr, data in config_data:
        tester.configure(addr, data)

    tester.poke(circuit.stall, 0)
    tester.eval()

    inputs = []
    inputs1 = []
    for j in range(3):
        for i in range(depth):
            inputs.append(i + (j + 1) * 16)
            inputs1.append((i + 16) + (j + 1) * 16)

    outputs = []
    outputs1 = []
    for j in range(2):
        for i in range(depth):
            outputs.append(i + (j + 1) * 16)
            outputs1.append((i + 16) + (j + 1) * 16)

    tester.poke(circuit.ren_in_0, 1)
    tester.poke(circuit.ren_in_1, 1)

    output_idx = 0

    for i in range(4 * depth):
        if(i >= 3 * depth):
            tester.poke(circuit.wen_in_0, 0)
            tester.poke(circuit.wen_in_1, 0)
        else:
            tester.poke(circuit.wen_in_0, 1)
            tester.poke(circuit.data_in_0, inputs[i])
            tester.poke(circuit.wen_in_1, 1)
            tester.poke(circuit.data_in_1, inputs1[i])

        if i >= 3 * depth + startup_delay:
            tester.poke(circuit.ren_in_0, 0)
            tester.poke(circuit.ren_in_1, 0)

        tester.eval()

        if (i > depth + startup_delay) and (i < 3 * depth + startup_delay):
            tester.expect(circuit.valid_out_0, 1)
            tester.expect(circuit.valid_out_1, 1)
            tester.expect(circuit.data_out_0, outputs[output_idx])
            tester.expect(circuit.data_out_1, outputs1[output_idx])

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


# No longer applicable w/ Diet Lake
@pytest.mark.skip
def test_multiple_input_ports_identity_stream_mult_aggs():
    # Regular Bootstrap
    [circuit, tester, MCore] = make_memory_core()

    tester.poke(circuit.stall, 1)

    tile_en = 1
    depth = 256

    # 4 is normal start up delay, 1 is due to mult input port agg scheduling
    startup_delay = 4 + 1
    mode = Mode.DB

    config_data = []

    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_input_port_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_output_port_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_read_depth_0", depth))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_write_depth_wo_0", depth))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_write_depth_ss_0", depth))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_read_depth_0", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_write_depth_wo_0", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_write_depth_ss_0", int(depth / 4)))

    config_data.append(MCore.get_config_data("strg_ub_agg_in_0_in_period", 2))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_0_in_sched_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_0_in_sched_1", 1))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_0_out_period", 2))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_0_out_sched_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_0_out_sched_1", 1))

    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_dimensionality", 2))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_0", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_1", 100))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_ranges_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_1", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_0_strides_5", 0))

    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_dimensionality", 2))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_0", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_1", 100))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_ranges_5", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_1", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_0_strides_5", 0))

    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_range_outer", depth))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_stride", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_dimensionality", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_indices_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_range_inner", 2))
    config_data.append(MCore.get_config_data("strg_ub_tba_0_tb_0_tb_height", 1))

    config_data.append(MCore.get_config_data("strg_ub_sync_grp_sync_group_0", 1))
    config_data.append(MCore.get_config_data("tile_en", 1))
    config_data.append(MCore.get_config_data("fifo_ctrl_fifo_depth", 0))
    config_data.append(MCore.get_config_data("mode", 0))
    config_data.append(MCore.get_config_data("flush_reg_sel", 1))
    config_data.append(MCore.get_config_data("strg_ub_pre_fetch_0_input_latency", 4))

    config_data.append(MCore.get_config_data("enable_chain_output", 0))
    config_data.append(MCore.get_config_data("enable_chain_input", 0))
    config_data.append(MCore.get_config_data("chain_idx_input", 0))
    config_data.append(MCore.get_config_data("chain_idx_output", 0))

    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_input_port_1", 1))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_read_depth_1", depth))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_write_depth_wo_1", depth))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_write_depth_ss_1", depth))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_read_depth_1", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_write_depth_wo_1", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_app_ctrl_coarse_write_depth_ss_1", int(depth / 4)))

    config_data.append(MCore.get_config_data("strg_ub_agg_in_1_in_period", 2))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_1_in_sched_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_1_in_sched_1", 1))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_1_out_period", 2))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_1_out_sched_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_agg_in_1_out_sched_1", 1))

    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_dimensionality", 2))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_ranges_0", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_ranges_1", 100))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_ranges_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_ranges_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_starting_addr", 64))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_strides_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_strides_1", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_strides_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_strides_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_strides_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_input_addr_ctrl_address_gen_1_strides_5", 0))

    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_dimensionality", 2))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_0", int(depth / 4)))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_1", 100))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_ranges_5", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_starting_addr", 64))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_0", 1))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_1", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_2", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_3", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_4", 0))
    config_data.append(MCore.get_config_data("strg_ub_output_addr_ctrl_address_gen_1_strides_5", 0))

    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_range_outer", depth))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_starting_addr", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_stride", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_dimensionality", 1))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_indices_0", 0))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_range_inner", 2))
    config_data.append(MCore.get_config_data("strg_ub_tba_1_tb_0_tb_height", 1))

    config_data.append(MCore.get_config_data("strg_ub_sync_grp_sync_group_1", 1))
    config_data.append(MCore.get_config_data("strg_ub_pre_fetch_1_input_latency", 4))

    config_data = compress_config_data(config_data)

    # Configure
    for addr, data in config_data:
        tester.configure(addr, data)

    tester.poke(circuit.stall, 0)
    tester.eval()

    inputs = []
    inputs1 = []
    for z in range(2):
        for i in range(depth):
            inputs.append(i)
            inputs1.append(i + 16)

    outputs = []
    outputs1 = []
    for z in range(2):
        for i in range(depth):
            outputs.append(i)
            outputs1.append(i + 16)

    tester.poke(circuit.ren_in_0, 1)
    tester.poke(circuit.ren_in_1, 1)

    output_idx = 0

    for i in range(4 * depth):
        if(i >= 2 * depth):
            tester.poke(circuit.wen_in_0, 0)
            tester.poke(circuit.wen_in_1, 0)
        else:
            tester.poke(circuit.wen_in_0, 1)
            tester.poke(circuit.data_in_0, inputs[i])
            tester.poke(circuit.wen_in_1, 1)
            tester.poke(circuit.data_in_1, inputs1[i])

        if i >= 2 * depth + startup_delay:
            tester.poke(circuit.ren_in_0, 0)
            tester.poke(circuit.ren_in_1, 0)

        tester.eval()

        if (i > depth + startup_delay) and (i < 2 * depth + startup_delay):
            tester.expect(circuit.valid_out_0, 1)
            tester.expect(circuit.valid_out_1, 1)
            tester.expect(circuit.data_out_0, outputs[output_idx])
            tester.expect(circuit.data_out_1, outputs1[output_idx])

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


def basic_tb(config_path,
             stream_path,
             in_file_name="input",
             out_file_name="output",
             verilator=True):

    # These need to be set to refer to certain csvs....
    lake_controller_path = os.getenv("LAKE_CONTROLLERS")
    lake_stream_path = os.getenv("LAKE_STREAM")

    assert lake_controller_path is not None and lake_stream_path is not None,\
        f"Please check env vars:\nLAKE_CONTROLLERS: {lake_controller_path}\nLAKE_STREAM: {lake_stream_path}"

    config_path = lake_controller_path + "/" + config_path
    stream_path = lake_stream_path + "/" + stream_path

    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2))

    netlist = {
        "e0": [("I0", "io2f_16"), ("m0", "data_in_0")],
        "e1": [("m0", "data_out_0"), ("I1", "f2io_16")]
    }
    bus = {"e0": 16, "e1": 16}

    placement, routing = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    # Regular Bootstrap
    [circuit, tester, MCore] = make_memory_core()
    # Get configuration
    configs_mem = MCore.get_static_bitstream(config_path=config_path,
                                             in_file_name=in_file_name,
                                             out_file_name=out_file_name)

    config_final = []
    for (f1, f2) in configs_mem:
        config_final.append((f1, f2, 0))
    mem_x, mem_y = placement["m0"]
    memtile = interconnect.tile_circuits[(mem_x, mem_y)]
    mcore = memtile.core
    config_mem_tile(interconnect, config_data, config_final, mem_x, mem_y, mcore)

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    tester.zero_inputs()

    tester.poke(circuit.interface["stall"], 1)

    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
    #    tester.expect(circuit.read_config_data, index)

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    in_data, out_data, valids = generate_data_lists(csv_file_name=stream_path,
                                                    data_in_width=MCore.num_data_inputs(),
                                                    data_out_width=MCore.num_data_outputs())

    num_in_data = 1
    num_out_data = 2

    data_in_x, data_in_y = placement["I0"]
    data_in = f"glb2io_16_X{data_in_x:02X}_Y{data_in_y:02X}"
    data_out_x, data_out_y = placement["I1"]
    data_out = f"io2glb_16_X{data_out_x:02X}_Y{data_out_y:02X}"

    for i in range(len(out_data)):
        tester.poke(circuit.interface[data_in], in_data[0][i])
        tester.eval()
        tester.expect(circuit.interface[data_out], out_data[0][i])
        # toggle the clock
        tester.step(2)

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        for filename in dw_files():
            shutil.copy(filename, tempdir)
        shutil.copy(os.path.join("tests", "test_memory_core",
                                 "sram_stub.v"),
                    os.path.join(tempdir, "sram_512w_16b.v"))
        for aoi_mux in glob.glob("tests/*.sv"):
            shutil.copy(aoi_mux, tempdir)

        target = "verilator"
        runtime_kwargs = {"magma_output": "coreir-verilog",
                          "magma_opts": {"coreir_libs": {"float_DW"}},
                          "directory": tempdir,
                          "flags": ["-Wno-fatal"]}
        if verilator is False:
            target = "system-verilog"
            runtime_kwargs["simulator"] = "vcs"

        tester.compile_and_run(target=target,
                               tmp_dir=False,
                               **runtime_kwargs)


def test_conv_3_3():
    # conv_3_3
    config_path = "conv_3_3_recipe/buf_inst_input_10_to_buf_inst_output_3_ubuf"
    stream_path = "conv_3_3_recipe/buf_inst_input_10_to_buf_inst_output_3_ubuf_0_top_SMT.csv"
    basic_tb(config_path=config_path,
             stream_path=stream_path,
             in_file_name="input",
             out_file_name="output")


if __name__ == "__main__":
    test_conv_3_3()
