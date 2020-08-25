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

    config_simple = [

        # IN 2 AGG

        # In 2 Agg - ADDR
        ("strg_ub_agg_write_addr_gen_0_dimensionality", 2),  # 2
        ("strg_ub_agg_write_addr_gen_0_ranges_0", 4 - 2),  # 2
        ("strg_ub_agg_write_addr_gen_0_ranges_1", 8 - 2),  # 2
        ("strg_ub_agg_write_addr_gen_0_starting_addr", 0),  # 2
        ("strg_ub_agg_write_addr_gen_0_strides_0", 1),  # 2
        ("strg_ub_agg_write_addr_gen_0_strides_1", 4 - (4 - 1) * 1),  # 2
        # In 2 Agg - SCHED
        ("strg_ub_agg_write_sched_gen_0_sched_addr_gen_dimensionality", 2),  # 2
        ("strg_ub_agg_write_sched_gen_0_sched_addr_gen_ranges_0", 4 - 2),  # 2
        ("strg_ub_agg_write_sched_gen_0_sched_addr_gen_ranges_1", 8 - 2),  # 2
        ("strg_ub_agg_write_sched_gen_0_sched_addr_gen_starting_addr", 0),  # 2
        ("strg_ub_agg_write_sched_gen_0_sched_addr_gen_strides_0", 1),  # 2
        ("strg_ub_agg_write_sched_gen_0_sched_addr_gen_strides_1", 5 - (4 - 1) * 1),  # 2

        # AGG 2 SRAM

        # Agg Read Addr
        ("strg_ub_agg_read_addr_gen_0_dimensionality", 1),  # 2
        ("strg_ub_agg_read_addr_gen_0_ranges_0", 8 - 2),  # 2
        ("strg_ub_agg_read_addr_gen_0_ranges_1", 0),  # 2
        ("strg_ub_agg_read_addr_gen_0_starting_addr", 0),  # 2
        ("strg_ub_agg_read_addr_gen_0_strides_0", 1),  # 2
        ("strg_ub_agg_read_addr_gen_0_strides_1", 0),  # 2
        # Agg 2 SRAM - ADDR
        ("strg_ub_input_addr_gen_dimensionality", 1),  # 4
        ("strg_ub_input_addr_gen_ranges_0", 8 - 2),  # 16
        ("strg_ub_input_addr_gen_starting_addr", 0),  # 16
        ("strg_ub_input_addr_gen_strides_0", 1),  # 16
        ("strg_ub_input_addr_gen_strides_1", 0),  # 16
        # Agg 2 SRAM - SCHED
        ("strg_ub_input_sched_gen_sched_addr_gen_dimensionality", 1),  # 4
        ("strg_ub_input_sched_gen_sched_addr_gen_ranges_0", 8 - 2),  # 16
        ("strg_ub_input_sched_gen_sched_addr_gen_ranges_1", 0),  # 16
        ("strg_ub_input_sched_gen_sched_addr_gen_starting_addr", 12),  # 16
        ("strg_ub_input_sched_gen_sched_addr_gen_strides_0", 4),  # 16
        ("strg_ub_input_sched_gen_sched_addr_gen_strides_1", 0),  # 16

        # SRAM 2 TB

        # SRAM 2 TB READ - ADDR
        ("strg_ub_output_addr_gen_dimensionality", 1),  # 4
        ("strg_ub_output_addr_gen_ranges_0", 8 - 2),  # 16
        ("strg_ub_output_addr_gen_starting_addr", 0),  # 16
        ("strg_ub_output_addr_gen_strides_0", 1),  # 16

        # SRAM 2 TB READ - SCHED
        ("strg_ub_output_sched_gen_sched_addr_gen_dimensionality", 1),  # 4
        ("strg_ub_output_sched_gen_sched_addr_gen_ranges_0", 8 - 2),  # 16
        ("strg_ub_output_sched_gen_sched_addr_gen_starting_addr", 15),  # 16
        ("strg_ub_output_sched_gen_sched_addr_gen_strides_0", 4),  # 16

        # SRAM 2 TB WRITE
        ("strg_ub_tb_write_addr_gen_dimensionality", 1),  # 2
        ("strg_ub_tb_write_addr_gen_ranges_0", 8 - 2),  # 2
        ("strg_ub_tb_write_addr_gen_ranges_1", 0),  # 2
        ("strg_ub_tb_write_addr_gen_starting_addr", 0),  # 2
        ("strg_ub_tb_write_addr_gen_strides_0", 1),  # 2
        ("strg_ub_tb_write_addr_gen_strides_1", 0),  # 2

        # TB 2 OUT

        ("strg_ub_tb_read_addr_gen_dimensionality", 2),  # 2
        ("strg_ub_tb_read_addr_gen_ranges_0", 4 - 2),  # 2
        ("strg_ub_tb_read_addr_gen_ranges_1", 8 - 2),  # 2
        ("strg_ub_tb_read_addr_gen_starting_addr", 0),  # 2
        ("strg_ub_tb_read_addr_gen_strides_0", 1),  # 2
        ("strg_ub_tb_read_addr_gen_strides_1", 4 - (4 - 1) * 1),  # 2

        ("strg_ub_tb_read_sched_gen_sched_addr_gen_dimensionality", 2),  # 16
        ("strg_ub_tb_read_sched_gen_sched_addr_gen_ranges_0", 4 - 2),  # 16
        ("strg_ub_tb_read_sched_gen_sched_addr_gen_ranges_1", 8 - 2),  # 16
        ("strg_ub_tb_read_sched_gen_sched_addr_gen_starting_addr", 17),  # 16
        ("strg_ub_tb_read_sched_gen_sched_addr_gen_strides_0", 1),  # 16
        ("strg_ub_tb_read_sched_gen_sched_addr_gen_strides_1", 5 - (4 - 1) * 1),  # 16

        # Other misc registers
        ("tile_en", 1),  # 1
        # ("wen_in_0_reg_sel", 1),  # 1
        # ("wen_in_0_reg_value", 0),  # 1
        # ("wen_in_1_reg_sel", 1),  # 1
        # ("wen_in_1_reg_value", 0),  # 1
        ("chain_idx_input", 0),  # 1
        ("chain_idx_output", 0),  # 1
        ("chain_valid_in_reg_sel", 1),  # 1
        ("chain_valid_in_reg_value", 0),  # 1
        ("enable_chain_input", 0),  # 1
        ("enable_chain_output", 0),  # 1
        ("fifo_ctrl_fifo_depth", 0),  # 16
        ("flush_reg_sel", 1),  # 1
        ("flush_reg_value", 0),  # 1
        ("mode", 0),  # 2
        ("ren_in_reg_sel", 1),  # 1
        ("ren_in_reg_value", 0),  # 1
    ]

    config_data = []
    for cfg_reg, val in config_simple:
        config_data.append((MCore.get_reg_index(cfg_reg), val, 0))

    # Configure
    for addr, data, feat in config_data:
        tester.configure(addr, data, feat)

    tester.poke(circuit.stall, 0)
    tester.eval()

    output_idx = 0

    for i in range(depth + startup_delay + num_outputs):

        tester.poke(circuit.wen_in, 1)
        tester.poke(circuit.data_in, output_idx)
        output_idx += 1

        tester.eval()

        tester.step(2)

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               target="verilator",
                               flags=["-Wno-fatal"])
