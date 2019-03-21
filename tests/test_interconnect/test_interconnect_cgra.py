import tempfile
import glob
import shutil
import os
from gemstone.common.testers import BasicTester
from canal.global_signal import apply_global_meso_wiring
from canal.interconnect import Interconnect
from canal.util import create_uniform_interconnect, SwitchBoxType
from memory_core.memory_core_magma import MemCore
from pe_core.pe_core_magma import PECore
from canal.cyclone import SwitchBoxSide, SwitchBoxIO
from io_core.io16bit_magma import IO16bit
from io_core.io1bit_magma import IO1bit
import pytest
import random


@pytest.mark.parametrize("batch_size", [100])
def test_interconnect_point_wise(batch_size: int):
    # we test a simple point-wise multiplier function
    # to account for different CGRA size, we feed in data to the very top-left
    # SB and route through horizontally to reach very top-right SB
    # we configure the top-left PE as multiplier
    chip_size = 2
    interconnect = create_cgra(chip_size, add_io=True)

    config_data = []

    graph_16 = interconnect.get_graph(16)
    sb_data0 = graph_16[1, 1].get_sb(SwitchBoxSide.WEST,
                                     0,
                                     SwitchBoxIO.SB_IN)
    sb_data1 = graph_16[1, 1].get_sb(SwitchBoxSide.NORTH,
                                     0,
                                     SwitchBoxIO.SB_IN)
    port_data0 = graph_16[1, 1].ports["data0"]
    port_data1 = graph_16[1, 1].ports["data1"]
    config_data.append(interconnect.get_node_bitstream_config(sb_data0,
                                                              port_data0))
    config_data.append(interconnect.get_node_bitstream_config(sb_data1,
                                                              port_data1))
    output_port = graph_16[1, 1].ports["res"]
    output_sb = graph_16[1, 1].get_sb(SwitchBoxSide.EAST,
                                      0,
                                      SwitchBoxIO.SB_OUT)
    config_data.append(interconnect.get_node_bitstream_config(output_port,
                                                              output_sb))

    next_node = None
    # route all the way to the end
    for x in range(2, chip_size + 1):
        pre_node = graph_16[x, 1].get_sb(SwitchBoxSide.WEST,
                                         0,
                                         SwitchBoxIO.SB_IN)
        next_node = graph_16[x, 1].get_sb(SwitchBoxSide.EAST,
                                          0,
                                          SwitchBoxIO.SB_OUT)
        config = interconnect.get_node_bitstream_config(pre_node,
                                                        next_node)
        assert config is not None
        config_data.append(config)

    # config the top-left PE
    config_data.append((0xFF000101, 0x000AF00B))

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    # set the PE core
    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    src_name0 = f"glb2io_X0_Y{sb_data0.y}"
    src_name1 = f"glb2io_X{sb_data1.x}_Y0"
    assert next_node is not None
    dst_name = f"io2glb_X{next_node.x + 1}_Y{next_node.y}"
    random.seed(0)
    for _ in range(batch_size):
        num_1 = random.randrange(0, 256)
        num_2 = random.randrange(0, 256)
        tester.poke(circuit.interface[src_name0], num_1)
        tester.poke(circuit.interface[src_name1], num_2)

        tester.eval()
        tester.expect(circuit.interface[dst_name], num_1 * num_2)

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        shutil.copy(os.path.join("tests", "test_memory_core",
                                 "sram_stub.v"),
                    os.path.join(tempdir, "sram_512w_16b.v"))
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])


def test_interconnect_line_buffer():
    chip_size = 2
    depth = 10
    interconnect = create_cgra(chip_size, add_io=True)
    config_data = []

    graph16 = interconnect.get_graph(16)
    graph1 = interconnect.get_graph(1)
    input_node = graph16.get_sb(2, 1, SwitchBoxSide.EAST, 0, SwitchBoxIO.SB_IN)
    mem_in = graph16.get_port(2, 1, "data_in")
    mem_out = graph16.get_port(2, 1, "data_out")
    config_data.append(interconnect.get_node_bitstream_config(input_node,
                                                              mem_in))
    next_node0 = graph16.get_sb(2, 1, SwitchBoxSide.WEST, 0, SwitchBoxIO.SB_OUT)
    config_data.append(interconnect.get_node_bitstream_config(input_node,
                                                              next_node0))
    # route the line buffer output to the track 1
    next_node1 = graph16.get_sb(2, 1, SwitchBoxSide.WEST, 1, SwitchBoxIO.SB_OUT)
    config_data.append(interconnect.get_node_bitstream_config(mem_out,
                                                              next_node1))
    # route the result to the input
    next_node0 = graph16.get_sb(1, 1, SwitchBoxSide.EAST, 0, SwitchBoxIO.SB_IN)
    # to data 0
    data0 = graph16.get_port(1, 1, "data0")
    config_data.append(interconnect.get_node_bitstream_config(next_node0,
                                                              data0))
    next_node1 = graph16.get_sb(1, 1, SwitchBoxSide.EAST, 1, SwitchBoxIO.SB_IN)
    data1 = graph16.get_port(1, 1, "data1")
    config_data.append(interconnect.get_node_bitstream_config(next_node1,
                                                              data1))

    # route the pe out to the (1, 1) left sb T0
    data_out = graph16.get_port(1, 1, "res")
    output_node = graph16.get_sb(1, 1, SwitchBoxSide.WEST, 0,
                                 SwitchBoxIO.SB_OUT)
    config_data.append(interconnect.get_node_bitstream_config(data_out,
                                                              output_node))

    # in this case we configure (2, 1) as line buffer mode
    config_data.append((0x00000201, 0x00000004 | (depth << 3)))
    # then (1, 1) is configured as add
    config_data.append((0xFF000101, 0x000AF000))

    # also need to wire a constant 1 to wen
    wen_sb = graph1.get_sb(2, 1, SwitchBoxSide.NORTH, 1, SwitchBoxIO.SB_IN)
    wen_port = graph1.get_port(2, 1, "wen_in")
    config_data.append(interconnect.get_node_bitstream_config(wen_sb,
                                                              wen_port))

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    src = f"glb2io_X{input_node.x + 1}_Y{input_node.y}"
    dst = f"io2glb_X{output_node.x - 1}_Y{output_node.y}"
    wen = f"glb2io_X{wen_sb.x}_Y{wen_sb.y - 1}"

    tester.poke(circuit.interface[wen], 1)

    for i in range(200):
        tester.poke(circuit.interface[src], i)
        tester.eval()

        if i > depth + 10:
            tester.expect(circuit.interface[dst], i * 2 - depth)

        # toggle the clock
        tester.step(2)

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        shutil.copy(os.path.join("tests", "test_memory_core",
                                 "sram_stub.v"),
                    os.path.join(tempdir, "sram_512w_16b.v"))
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])


def test_interconnect_sram():
    chip_size = 2
    interconnect = create_cgra(chip_size, add_io=True)
    config_data = []

    graph16 = interconnect.get_graph(16)
    graph1 = interconnect.get_graph(1)
    input_node = graph16.get_sb(2, 1, SwitchBoxSide.EAST, 0, SwitchBoxIO.SB_IN)
    mem_in = graph16.get_port(2, 1, "addr_in")
    mem_out = graph16.get_port(2, 1, "data_out")
    config_data.append(interconnect.get_node_bitstream_config(input_node,
                                                              mem_in))
    next_node0 = graph16.get_sb(2, 1, SwitchBoxSide.WEST, 0, SwitchBoxIO.SB_OUT)
    config_data.append(interconnect.get_node_bitstream_config(mem_out,
                                                              next_node0))
    # route the result to left PE
    next_node0 = graph16.get_sb(1, 1, SwitchBoxSide.EAST, 0, SwitchBoxIO.SB_IN)
    # route to the (0, 0) left sb T0
    output_node = graph16.get_sb(1, 1, SwitchBoxSide.WEST, 0,
                                 SwitchBoxIO.SB_OUT)
    config_data.append(interconnect.get_node_bitstream_config(next_node0,
                                                              output_node))

    # in this case we configure (1, 0) as sram mode
    config_data.append((0x00000201, 0x00000006))

    # also need to wire a constant 1 to ren
    ren_sb = graph1.get_sb(2, 1, SwitchBoxSide.NORTH, 1, SwitchBoxIO.SB_IN)
    ren_port = graph1.get_port(2, 1, "ren_in")
    config_data.append(interconnect.get_node_bitstream_config(ren_sb,
                                                              ren_port))
    sram_data = []
    # add SRAM data
    for i in range(0, 1024, 4):
        feat_addr = i // 256 + 1
        mem_addr = i % 256
        sram_data.append((0x00000201 | mem_addr << 24 | feat_addr << 16,
                          i + 10))

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    for addr, data in sram_data:
        tester.configure(addr, data)
        # currently read back doesn't work
        # tester.config_read(addr)
        # tester.eval()
        # tester.expect(circuit.read_config_data, data)

    src = f"glb2io_X{input_node.x + 1}_Y{input_node.y}"
    dst = f"io2glb_X{output_node.x - 1}_Y{output_node.y}"
    ren = f"glb2io_X{ren_sb.x}_Y{ren_sb.y - 1}"

    tester.step(2)
    tester.poke(circuit.interface[ren], 1)
    tester.eval()

    for i in range(0, 1024, 4):
        tester.poke(circuit.interface[src], i)
        tester.eval()
        tester.step(2)
        tester.eval()
        tester.expect(circuit.interface[dst], i + 10)

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        shutil.copy(os.path.join("tests", "test_memory_core",
                                 "sram_stub.v"),
                    os.path.join(tempdir, "sram_512w_16b.v"))
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])


def create_cgra(chip_size: int, add_io: bool = False):
    # currently only add 16bit io cores
    num_tracks = 2
    reg_mode = True
    addr_width = 8
    data_width = 32
    bit_widths = [1, 16]
    tile_id_width = 16
    track_length = 1
    margin = 0 if not add_io else 1
    chip_size += 2 * margin
    # recalculate the margin
    # creates all the cores here
    # we don't want duplicated cores when snapping into different interconnect
    # graphs
    cores = {}
    for x in range(chip_size):
        for y in range(chip_size):
            # empty corner
            if x in range(margin) and y in range(margin):
                core = None
            elif x in range(margin) and y in range(chip_size - margin,
                                                   chip_size):
                core = None
            elif x in range(chip_size - margin,
                            chip_size) and y in range(margin):
                core = None
            elif x in range(chip_size - margin,
                            chip_size) and y in range(chip_size - margin,
                                                      chip_size):
                core = None
            elif x in range(margin) \
                    or x in range(chip_size - margin, chip_size) \
                    or y in range(margin) \
                    or y in range(chip_size - margin, chip_size):
                if x == margin or y == margin:
                    core = IO16bit()
                else:
                    core = IO1bit()
            else:
                core = MemCore(16, 1024) if ((x - margin) % 2 == 1) else \
                    PECore()
            cores[(x, y)] = core

    def create_core(xx: int, yy: int):
        return cores[(xx, yy)]

    # specify input and output port connections
    inputs = ["data0", "data1", "bit0", "bit1", "bit2", "data_in",
              "addr_in", "flush", "ren_in", "wen_in"]
    outputs = ["res", "res_p", "data_out"]
    # this is slightly different from the chip we tape out
    # here we connect input to every SB_IN and output to every SB_OUT
    port_conns = {}
    in_conn = []
    out_conn = []
    for side in SwitchBoxSide:
        in_conn.append((side, SwitchBoxIO.SB_IN))
        out_conn.append((side, SwitchBoxIO.SB_OUT))
    for input_port in inputs:
        port_conns[input_port] = in_conn
    for output_port in outputs:
        port_conns[output_port] = out_conn
    pipeline_regs = []
    for track in range(num_tracks):
        for side in SwitchBoxSide:
            pipeline_regs.append((track, side))
    # if reg mode is off, reset to empty
    if not reg_mode:
        pipeline_regs = []
    ics = {}

    io_in = {"f2io_1": [1], "f2io_16": [0]}
    io_out = {"io2f_1": [1], "io2f_16": [0]}
    for bit_width in bit_widths:
        if add_io:
            io_conn = {"in": io_in, "out": io_out}
        else:
            io_conn = None
        ic = create_uniform_interconnect(chip_size, chip_size, bit_width,
                                         create_core,
                                         port_conns,
                                         {track_length: num_tracks},
                                         SwitchBoxType.Disjoint,
                                         pipeline_regs,
                                         margin=margin,
                                         io_conn=io_conn)
        ics[bit_width] = ic

    lift_ports = margin == 0
    interconnect = Interconnect(ics, addr_width, data_width, tile_id_width,
                                lift_ports=lift_ports)
    interconnect.finalize()
    apply_global_meso_wiring(interconnect, margin=margin)
    return interconnect


if __name__ == "__main__":
    test_interconnect_point_wise(20)
