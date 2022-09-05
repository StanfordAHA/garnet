from lake.utils.util import transform_strides_and_ranges, trim_config
import random
from gemstone.common.testers import BasicTester
from cgra.util import create_cgra, compress_config_data
from canal.util import IOSide
from archipelago import pnr
from _kratos import create_wrapper_flatten
import lassen.asm as asm


def io_sides():
    return IOSide.North | IOSide.East | IOSide.South | IOSide.West


def test_pond_rd_wr(run_tb, get_mapping):

    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=3,
                               add_pd=True,
                               add_pond=True,
                               ready_valid=True,
                               scgra=True,
                               scgra_combined=True,
                               mem_ratio=(1, 2))

    pe_map, mem_map = get_mapping(interconnect)
    pe_map = pe_map["alu"]

    netlist = {
        "e0": [("I0", "io2f_17"), ("p0", "PondTop_input_width_17_num_2")],
        "e1": [("I1", "io2f_17"), ("p0", pe_map["data1"])],
        "e2": [("p0", "PondTop_output_width_17_num_0"), ("I2", "f2io_17")]
    }
    bus = {"e0": 17, "e1": 17, "e2": 17}

    placement, routing, _ = pnr(interconnect, (netlist, bus), cwd="/aha/garnet")
    config_data = interconnect.get_route_bitstream(routing)

    pe_x, pe_y = placement["p0"]

    petile = interconnect.tile_circuits[(pe_x, pe_y)]

    pondcore = petile.additional_cores[0]

    pond_config = {"mode": "pond",
                   "config": {"in2regfile_0": {"cycle_starting_addr": [1],
                                               "cycle_stride": [1, 1],
                                               "dimensionality": 2,
                                               "extent": [16, 1],
                                               "write_data_starting_addr": [0],
                                               "write_data_stride": [1, 1]},
                              "regfile2out_0": {"cycle_starting_addr": [17],
                                                "cycle_stride": [1, 1],
                                                "dimensionality": 2,
                                                "extent": [16, 1],
                                                "read_data_starting_addr": [0],
                                                "read_data_stride": [1, 1]}}}

    pond_config = pondcore.dut.get_bitstream(config_json=pond_config)
    for name, v in pond_config:
        idx, value = pondcore.get_config_data(name, v)
        config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    src0 = placement["I0"]
    src1 = placement["I1"]
    dst = placement["I2"]

    # Configure IO tiles
    instr = {}
    for place in [src0, src1, dst]:
        iotile = interconnect.tile_circuits[place]
        value = iotile.core.get_config_bitstream(instr)
        for addr, data in value:
            config_data.append((interconnect.get_config_addr(addr, 0, place[0], place[1]), data))

    config_data = compress_config_data(config_data)

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.zero_inputs()
    tester.reset()

    tester.poke(circuit.interface["stall"], 1)

    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()
    
    src_name0 = f"glb2io_17_X{src0[0]:02X}_Y{src0[1]:02X}"
    src_name1 = f"glb2io_17_X{src1[0]:02X}_Y{src1[1]:02X}"
    dst_name = f"io2glb_17_X{dst[0]:02X}_Y{dst[1]:02X}"
    random.seed(0)


    for i in range(34):
        tester.poke(circuit.interface[src_name0], i)
        tester.poke(circuit.interface[src_name1], i + 1)
        tester.eval()
        # 1 cycle delay from pond output to glb
        if i >= 18:
            tester.expect(circuit.interface[dst_name], i - 18)
        tester.step(2)

    run_tb(tester)


def test_pond_pe(run_tb, get_mapping):

    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=3,
                               add_pd=True,
                               add_pond=True,
                               mem_ratio=(1, 2))


    pe_map, mem_map = get_mapping(interconnect)
    pe_map = pe_map["alu"]
    
    netlist = {
        "e0": [("I0", "io2f_17"), ("p0", pe_map["data2"])],
        "e1": [("I1", "io2f_17"), ("p0", pe_map["data1"])],
        "e2": [("p0", pe_map["res"]), ("I2", "f2io_17")],
        #"e3": [("p0", "output_width_17_num_0"), ("p0", pe_map["data0"])]
        # res is incorrect, should it be a pond port?
        "e3": [("p0", pe_map["res"]), ("p0", pe_map["data0"])]
    }
    bus = {"e0": 17, "e1": 17, "e2": 17, "e3": 17}

    placement, routing, _ = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    pe_x, pe_y = placement["p0"]

    petile = interconnect.tile_circuits[(pe_x, pe_y)]

    pondcore = petile.additional_cores[0]

    add_bs = petile.core.get_config_bitstream(asm.umult0())
    for addr, data in add_bs:
        config_data.append((interconnect.get_config_addr(addr, 0, pe_x, pe_y), data))

    pond_config = {"mode": "pond",
                   "config": {"in2regfile_0": {"cycle_starting_addr": [0],
                                               "cycle_stride": [1, 1],
                                               "dimensionality": 2,
                                               "extent": [16, 1],
                                               "write_data_starting_addr": [0],
                                               "write_data_stride": [1, 1]},
                              "regfile2out_0": {"cycle_starting_addr": [16],
                                                "cycle_stride": [1, 1],
                                                "dimensionality": 2,
                                                "extent": [16, 1],
                                                "read_data_starting_addr": [0],
                                                "read_data_stride": [1, 1]}}}

    pond_config = pondcore.dut.get_bitstream(config_json=pond_config)
    for name, v in pond_config:
        idx, value = pondcore.get_config_data(name, v)
        config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))


    src0 = placement["I0"]
    src1 = placement["I1"]
    dst = placement["I2"]

    # Configure IO tiles
    instr = {}
    for place in [src0, src1, dst]:
        iotile = interconnect.tile_circuits[place]
        value = iotile.core.get_config_bitstream(instr)
        for addr, data in value:
            config_data.append((interconnect.get_config_addr(addr, 0, place[0], place[1]), data))

    config_data = compress_config_data(config_data)

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.zero_inputs()
    tester.reset()

    tester.poke(circuit.interface["stall"], 1)

    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    src_name0 = f"glb2io_17_X{src0[0]:02X}_Y{src0[1]:02X}"
    src_name1 = f"glb2io_17_X{src1[0]:02X}_Y{src1[1]:02X}"
    dst_name = f"io2glb_17_X{dst[0]:02X}_Y{dst[1]:02X}"
    random.seed(0)

    for i in range(32):
        if i < 16:
            tester.poke(circuit.interface[src_name0], i)
            tester.eval()
        if i >= 16:
            num = random.randrange(0, 256)
            tester.poke(circuit.interface[src_name1], num)
            tester.eval()
            tester.expect(circuit.interface[dst_name], (i - 16) * num)
        tester.step(2)
        tester.eval()

    run_tb(tester, include_PE=True, trace=True, cwd="/aha/garnet")


def test_pond_pe_acc(run_tb, get_mapping):

    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=3,
                               add_pd=True,
                               add_pond=True,
                               mem_ratio=(1, 2))

    pe_map, mem_map = get_mapping(interconnect)
    pe_map = pe_map["alu"]

    netlist = {
        # definitely incorrect mapping
        "e0": [("I0", "io2f_17"), ("p0", pe_map["data0"])],
        "e1": [("p0", pe_map["res"]), ("p0", pe_map["data1"])],
        "e2": [("p0", pe_map["res"]), ("p0", pe_map["data2"])],
        "e3": [("p0", pe_map["res"]), ("I1", "f2io_17")]
    }
    bus = {"e0": 17, "e1": 17, "e2": 17, "e3": 17}

    placement, routing, _ = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    pe_x, pe_y = placement["p0"]

    petile = interconnect.tile_circuits[(pe_x, pe_y)]

    pondcore = petile.additional_cores[0]

    add_bs = petile.core.get_config_bitstream(asm.add())
    for addr, data in add_bs:
        config_data.append((interconnect.get_config_addr(addr, 0, pe_x, pe_y), data))

    pond_config = {"mode": "pond",
                   "config": {"in2regfile_0": {"cycle_starting_addr": [0],
                                               "cycle_stride": [1, 0],
                                               "dimensionality": 2,
                                               "extent": [18, 1],
                                               "write_data_starting_addr": [8],
                                               "write_data_stride": [0, 0]},
                              "regfile2out_0": {"cycle_starting_addr": [2],
                                                "cycle_stride": [1, 0],
                                                "dimensionality": 2,
                                                "extent": [16, 1],
                                                "read_data_starting_addr": [8],
                                                "read_data_stride": [0, 0]}}}

    pond_config = pondcore.dut.get_bitstream(config_json=pond_config)
    for name, v in pond_config:
        idx, value = pondcore.get_config_data(name, v)
        config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))


    src0 = placement["I0"]
    dst = placement["I2"]

    # Configure IO tiles
    instr = {}
    for place in [src0, dst]:
        iotile = interconnect.tile_circuits[place]
        value = iotile.core.get_config_bitstream(instr)
        for addr, data in value:
            config_data.append((interconnect.get_config_addr(addr, 0, place[0], place[1]), data))

    config_data = compress_config_data(config_data)

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.zero_inputs()
    tester.reset()

    tester.poke(circuit.interface["stall"], 1)

    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    src_name0 = f"glb2io_17_X{src0[0]:02X}_Y{src0[1]:02X}"
    src_name1 = f"glb2io_17_X{src1[0]:02X}_Y{src1[1]:02X}"
    dst_name = f"io2glb_17_X{dst[0]:02X}_Y{dst[1]:02X}"
    random.seed(0)

    total = 0
    # the 2 extra cycle is because refgile2out_0 cycle_starting_addr is at 2
    # cannot be 0 because need to initialize the regfile with 0
    for i in range(2):
        tester.step(2)
        tester.eval()

    for i in range(16):
        tester.poke(circuit.interface[src_name0], i + 1)
        total = total + i
        tester.eval()
        tester.expect(circuit.interface[dst_name], total)
        tester.step(2)
        tester.eval()

    run_tb(tester, include_PE=True)


def test_pond_config(run_tb):
    # 1x1 interconnect with only PE tile
    interconnect = create_cgra(1, 1, IOSide.None_, standalone=True,
                               mem_ratio=(0, 1),
                               add_pond=True)

    # get pond core
    pe_tile = interconnect.tile_circuits[0, 0]
    pond_core = pe_tile.additional_cores[0]
    pond_feat = pe_tile.features().index(pond_core)
    sram_feat = pond_feat + pond_core.num_sram_features

    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.zero_inputs()
    tester.reset()

    config_data = []
    # tile enable
    reg_addr, value = pond_core.get_config_data("tile_en", 1)
    config_data.append((interconnect.get_config_addr(reg_addr, pond_feat, 0, 0), value))

    for i in range(32):
        addr = interconnect.get_config_addr(i, sram_feat, 0, 0)
        config_data.append((addr, i + 1))
    for addr, data in config_data:
        tester.configure(addr, data)

    # read back
    for addr, data in config_data:
        tester.config_read(addr)
        tester.expect(circuit.read_config_data, data)

    run_tb(tester, include_PE=True)
