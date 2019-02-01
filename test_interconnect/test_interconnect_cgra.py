import tempfile
import glob
import shutil
from common.testers import BasicTester
from interconnect.circuit import create_name
from interconnect.global_signal import apply_global_meso_wiring
from interconnect.interconnect import Interconnect
from interconnect.util import create_uniform_interconnect, SwitchBoxType
from memory_core.memory_core_magma import MemCore
from pe_core.pe_core_magma import PECore
from interconnect.cyclone import SwitchBoxSide, SwitchBoxIO
import pytest
import random


@pytest.mark.parametrize("batch_size", [100])
def test_interconnect_cgra(batch_size: int):
    # we test a simple point-wise multiplier function
    # to account for different CGRA size, we feed in data to the very top-left
    # SB and route through horizontally to reach very top-right SB
    # we configure the top-left PE as multiplier
    chip_size = 2
    num_tracks = 2
    reg_mode = True

    addr_width = 8
    data_width = 32
    bit_widths = [1, 16]

    tile_id_width = 16

    track_length = 1

    # creates all the cores here
    # we don't want duplicated cores when snapping into different interconnect
    # graphs
    cores = {}
    for x in range(chip_size):
        for y in range(chip_size):
            core = MemCore(16, 1024) if (x % 4 == 3) else PECore()
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
    for bit_width in bit_widths:
        ic = create_uniform_interconnect(chip_size, chip_size, bit_width,
                                         create_core,
                                         port_conns,
                                         {track_length: num_tracks},
                                         SwitchBoxType.Disjoint,
                                         pipeline_regs)
        ics[bit_width] = ic

    interconnect = Interconnect(ics, addr_width, data_width, tile_id_width,
                                lift_ports=True)

    apply_global_meso_wiring(interconnect)

    config_data = []
    test_data = []

    graph_16 = interconnect.get_graph(16)
    sb_data0 = graph_16[0, 0].get_sb(SwitchBoxSide.WEST,
                                     0,
                                     SwitchBoxIO.SB_IN)
    sb_data1 = graph_16[0, 0].get_sb(SwitchBoxSide.NORTH,
                                     0,
                                     SwitchBoxIO.SB_IN)
    port_data0 = graph_16[0, 0].ports["data0"]
    port_data1 = graph_16[0, 0].ports["data1"]
    config_data.append(interconnect.get_route_bitstream_config(sb_data0,
                                                               port_data0))
    config_data.append(interconnect.get_route_bitstream_config(sb_data1,
                                                               port_data1))
    output_port = graph_16[0, 0].ports["res"]
    output_sb = graph_16[0, 0].get_sb(SwitchBoxSide.EAST,
                                      0,
                                      SwitchBoxIO.SB_OUT)
    config_data.append(interconnect.get_route_bitstream_config(output_port,
                                                               output_sb))

    next_node = None
    # route all the way to the end
    for x in range(1, chip_size):
        pre_node = graph_16[x, 0].get_sb(SwitchBoxSide.WEST,
                                         0,
                                         SwitchBoxIO.SB_IN)
        next_node = graph_16[x, 0].get_sb(SwitchBoxSide.EAST,
                                          0,
                                          SwitchBoxIO.SB_OUT)
        config = interconnect.get_route_bitstream_config(pre_node,
                                                         next_node)
        assert config is not None
        config_data.append(config)

    # config the top-left PE
    config_data.append((0xFF000000, 0x000AF00B))

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    # set the PE core
    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    src_name0 = create_name(str(sb_data0)) + f"_X{sb_data0.x}_Y{sb_data0.y}"
    src_name1 = create_name(str(sb_data1)) + f"_X{sb_data1.x}_Y{sb_data1.y}"
    assert next_node is not None
    dst_name = create_name(str(next_node)) + f"_X{next_node.x}_Y{next_node.y}"
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
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal", "--trace"])
