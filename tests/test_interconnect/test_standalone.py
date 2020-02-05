import glob
import os
import pytest
import shutil
import tempfile
from canal.cyclone import SwitchBoxSide, SwitchBoxIO
from canal.util import IOSide
from gemstone.common.testers import BasicTester
import hwtypes
import lassen.asm
from cgra import create_cgra


@pytest.fixture(scope="module")
def dw_files():
    filenames = ["DW_fp_add.v", "DW_fp_mult.v"]
    dirname = "peak_core"
    result_filenames = []
    for name in filenames:
        filename = os.path.join(dirname, name)
        assert os.path.isfile(filename)
        result_filenames.append(filename)
    return result_filenames


@pytest.mark.parametrize("batch_size", [100])
def test_interconnect_point_wise(batch_size: int, dw_files):
    """
    Pointwise multiply test on 2x2 fabric, without IO tiles. Routing and
    placement is hand-crafted.
    """
    # Create cgra generator object. Note that we set standalone=True,
    # io_sides=IOSide.None_, and mem_ratio=(1, 100). These options specify that
    # interconnect ports are lifted to the top, IO tiles are not included, and
    # that there are no Mem tiles (for a 2x2).
    chip_size = 2
    interconnect = create_cgra(width=chip_size, height=chip_size,
                               io_sides=IOSide.None_, num_tracks=5,
                               standalone=True, add_pd=True, mem_ratio=(1, 100))

    # Use canal API to get the bitstream for the following route:
    #   * Tile(0, 0).SB.WEST.0.IN -> Tile(0, 0).PE.data0
    #   * Tile(0, 0).SB.NORTH.0.IN -> Tile(0, 0).PE.data1
    #   * Tile(0, 0).PE.alu_res -> Tile(0, 0).SB.EAST.0.OUT
    config_data = []
    graph_16 = interconnect.get_graph(16)
    sb_data0 = graph_16[0, 0].get_sb(SwitchBoxSide.WEST, 0, SwitchBoxIO.SB_IN)
    sb_data1 = graph_16[0, 0].get_sb(SwitchBoxSide.NORTH, 0, SwitchBoxIO.SB_IN)
    port_data0 = graph_16[0, 0].ports["data0"]
    port_data1 = graph_16[0, 0].ports["data1"]
    config_data.append(interconnect.get_node_bitstream_config(sb_data0, port_data0))
    config_data.append(interconnect.get_node_bitstream_config(sb_data1, port_data1))
    output_port = graph_16[0, 0].ports["alu_res"]
    output_sb = graph_16[0, 0].get_sb(SwitchBoxSide.EAST, 0, SwitchBoxIO.SB_OUT)
    config_data.append(interconnect.get_node_bitstream_config(output_port, output_sb))

    # Now, route from Tile(0, 0).SB.EAST.0.OUT all the way to the east edge of
    # the CGRA, which is Tile(w, 0).SB.EAST.0.OUT.
    for x in range(1, chip_size):
        pre_node = graph_16[x, 0].get_sb(SwitchBoxSide.WEST, 0, SwitchBoxIO.SB_IN)
        next_node = graph_16[x, 0].get_sb(SwitchBoxSide.EAST, 0, SwitchBoxIO.SB_OUT)
        config = interconnect.get_node_bitstream_config(pre_node, next_node)
        assert config is not None
        config_data.append(config)

    # Now need to configure Tile(0, 0).PE to be umult0.
    pe_tile = interconnect.tile_circuits[(0, 0)]
    mul_conifg_data = pe_tile.core.get_config_bitstream(lassen.asm.umult0())
    for addr, data in mul_conifg_data:
        full_addr = interconnect.get_config_addr(addr, 0, 0, 0)
        config_data.append((full_addr, data))

    # Construct circuit and setup fault tester.
    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.circuit.clk = 0
    tester.reset()

    # Run configuration sequence and check the configuration output bus.
    for addr, data in config_data:
        tester.configure(addr, data)
        tester.config_read(addr)
        tester.eval()
        tester.print(f"Doing config {(addr, data)}\n")
        tester.expect(circuit.read_config_data, data)
    tester.done_config()

    # Drive a bunch of random values and check the output against the expected
    # value.
    for _ in range(batch_size):
        x = hwtypes.BitVector.random(16)
        y = hwtypes.BitVector.random(16)
        tester.circuit.SB_T0_WEST_SB_IN_B16_X0_Y0 = x
        tester.circuit.SB_T0_NORTH_SB_IN_B16_X0_Y0 = y
        tester.eval()
        tester.circuit.SB_T0_EAST_SB_OUT_B16_X1_Y0.expect(x * y)

    # Compile and run the test using a verilator backend.
    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        for filename in dw_files:
            shutil.copy(filename, tempdir)
        shutil.copy(os.path.join("tests", "test_memory_core",
                                 "sram_stub.v"),
                    os.path.join(tempdir, "sram_512w_16b.v"))
        for aoi_mux in glob.glob("tests/*.sv"):
            shutil.copy(aoi_mux, tempdir)
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               magma_opts={"coreir_libs": {"float_DW"}},
                               directory=tempdir,
                               flags=["-Wno-fatal"])
