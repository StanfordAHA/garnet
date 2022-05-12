import tempfile
import glob
import shutil
import os
from gemstone.common.testers import BasicTester
from canal.util import IOSide
import lassen.asm as asm
from archipelago import pnr
import pytest
from cgra import create_cgra, compress_config_data
from memory_core.memory_core_magma import config_mem_tile


@pytest.fixture()
def io_sides():
    return IOSide.North | IOSide.East | IOSide.South | IOSide.West


# Skipping since config is totally out of date - we need another way to test stall
@pytest.mark.skip
def test_stall(run_tb, io_sides):
    chip_size = 2
    depth = 10
    interconnect = create_cgra(chip_size, chip_size, io_sides,
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2))

    netlist = {
        "e0": [("I0", "io2f_16"), ("r1", "reg")],
        "e2": [("r1", "reg"), ("m0", "data_in_0"), ("p0", "data0")],
        "e1": [("m0", "data_out_0"), ("p0", "data1")],
        "e3": [("p0", "res"), ("I1", "f2io_16")],
        "e4": [("i3", "io2f_1"), ("m0", "wen_in_0"), ("m0", "ren_in_0")],
        "e5": [("m0", "valid_out_0"), ("i4", "f2io_1")]
    }
    bus = {"e0": 16, "e2": 16, "e1": 16, "e3": 16, "e4": 1, "e5": 1}

    placement, routing, _ = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    x, y = placement["p0"]

    tile = interconnect.tile_circuits[(x, y)]
    add_bs = tile.core.get_config_bitstream(asm.add(ra_mode=asm.Mode_t.DELAY))
    for addr, data in add_bs:
        config_data.append((interconnect.get_config_addr(addr, 0, x, y), data))

    tile_en = 1

    mem_x, mem_y = placement["m0"]
    memtile = interconnect.tile_circuits[(mem_x, mem_y)]
    mcore = memtile.core

    configs_mem = [("strg_ub_app_ctrl_input_port_0", 0, 0),
                   ("strg_ub_app_ctrl_output_port_0", 0, 0),
                   ("strg_ub_app_ctrl_read_depth_0", depth, 0),
                   ("strg_ub_app_ctrl_write_depth_wo_0", depth, 0),
                   ("strg_ub_app_ctrl_write_depth_ss_0", depth, 0),
                   ("strg_ub_app_ctrl_coarse_input_port_0", 0, 0),
                   ("strg_ub_app_ctrl_coarse_read_depth_0", 1, 0),
                   ("strg_ub_app_ctrl_coarse_write_depth_wo_0", 1, 0),
                   ("strg_ub_app_ctrl_coarse_write_depth_ss_0", 1, 0),
                   ("strg_ub_input_addr_ctrl_address_gen_0_dimensionality", 2, 0),
                   ("strg_ub_input_addr_ctrl_address_gen_0_ranges_0", 512, 0),
                   ("strg_ub_input_addr_ctrl_address_gen_0_ranges_1", 512, 0),
                   ("strg_ub_input_addr_ctrl_address_gen_0_starting_addr", 0, 0),
                   ("strg_ub_input_addr_ctrl_address_gen_0_strides_0", 1, 0),
                   ("strg_ub_input_addr_ctrl_address_gen_0_strides_1", 512, 0),
                   ("strg_ub_input_addr_ctrl_address_gen_0_strides_2", 0, 0),
                   ("strg_ub_input_addr_ctrl_address_gen_0_strides_3", 0, 0),
                   ("strg_ub_output_addr_ctrl_address_gen_0_dimensionality", 2, 0),
                   ("strg_ub_output_addr_ctrl_address_gen_0_ranges_0", 512, 0),
                   ("strg_ub_output_addr_ctrl_address_gen_0_ranges_1", 512, 0),
                   ("strg_ub_output_addr_ctrl_address_gen_0_starting_addr", 0, 0),
                   ("strg_ub_output_addr_ctrl_address_gen_0_strides_0", 1, 0),
                   ("strg_ub_output_addr_ctrl_address_gen_0_strides_1", 512, 0),
                   ("strg_ub_sync_grp_sync_group_0", 1, 0),
                   ("strg_ub_tba_0_tb_0_range_outer", depth, 0),
                   ("strg_ub_tba_0_tb_0_starting_addr", 0, 0),
                   ("strg_ub_tba_0_tb_0_stride", 1, 0),
                   ("strg_ub_tba_0_tb_0_dimensionality", 1, 0),
                   ("strg_ub_agg_align_0_line_length", depth, 0),
                   ("strg_ub_tba_0_tb_0_indices_0", 0, 0),
                   ("strg_ub_tba_0_tb_0_indices_1", 1, 0),
                   ("strg_ub_tba_0_tb_0_indices_2", 2, 0),
                   ("strg_ub_tba_0_tb_0_indices_3", 3, 0),
                   ("strg_ub_tba_0_tb_0_range_inner", 4, 0),
                   ("strg_ub_tba_0_tb_0_tb_height", 1, 0),
                   ("tile_en", tile_en, 0),
                   ("mode", 0, 0),
                   ("flush_reg_sel", 1, 0),
                   ("wen_in_1_reg_sel", 1, 0),
                   ("ren_in_1_reg_sel", 1, 0)]
    config_mem_tile(interconnect, config_data, configs_mem, mem_x, mem_y, mcore)
    config_data = compress_config_data(config_data)

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()

    # stall the chip
    tester.poke(circuit.interface["stall"], 1)
    tester.eval()

    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    # un-stall the chp
    # stall the chip
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    src_x, src_y = placement["I0"]
    src = f"glb2io_16_X{src_x:02X}_Y{src_y:02X}"
    dst_x, dst_y = placement["I1"]
    dst = f"io2glb_16_X{dst_x:02X}_Y{dst_y:02X}"
    wen_x, wen_y = placement["i3"]
    wen = f"glb2io_1_X{wen_x:02X}_Y{wen_y:02X}"
    valid_x, valid_y = placement["i4"]
    valid = f"io2glb_1_X{valid_x:02X}_Y{valid_y:02X}"

    tester.poke(circuit.interface[wen], 1)

    for i in range(20):
        tester.poke(circuit.interface[src], i)
        tester.eval()
        if i >= 10 + 1:
            # data0 of PE: i - 1 - 1
            # data1 of PE: i - 1 - depth
            tester.expect(circuit.interface[dst], i * 2 - 3 - depth)
            tester.expect(circuit.interface[valid], 1)
        elif i < depth:
            tester.expect(circuit.interface[valid], 0)
        if i == 19:
            # now stall everything
            tester.poke(circuit.interface["stall"], 1)
            tester.eval()
        tester.step(2)

    for i in range(20):
        # poke random numbers. it shouldn't matter
        tester.poke(circuit.interface[src], i * 20)
        tester.expect(circuit.interface[dst], 19 * 2 - 3 - depth)
        tester.step(2)

    # un-stall again
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    for i in range(19, 30):
        tester.poke(circuit.interface[src], i)
        tester.eval()
        tester.expect(circuit.interface[dst], i * 2 - 3 - depth)
        tester.expect(circuit.interface[valid], 1)
        tester.step(2)

    run_tb(tester)
