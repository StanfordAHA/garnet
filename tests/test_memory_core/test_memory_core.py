import argparse
from gemstone.common.util import compress_config_data
import pytest
from memory_core.memory_core_magma import MemCore
from memory_core.scanner_core import ScannerCore
from lake.utils.test_infra import lake_test_app_args
from lake.utils.parse_clkwork_csv import generate_data_lists
from gemstone.common.testers import ResetTester
from gemstone.common.testers import BasicTester
from cgra.util import create_cgra
from canal.util import IOSide
from memory_core.memory_core_magma import config_mem_tile
from archipelago import pnr


def io_sides():
    return IOSide.North | IOSide.East | IOSide.South | IOSide.West


def make_memory_core():
    mem_core = MemCore()
    return mem_core


def make_scanner_core():
    scan_core = ScannerCore()
    return scan_core


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


def basic_tb(config_path,
             stream_path,
             run_tb,
             in_file_name="input",
             out_file_name="output",
             cwd=None,
             trace=False):

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
    MCore = make_memory_core()
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

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    in_data, out_data, valids = generate_data_lists(csv_file_name=stream_path,
                                                    data_in_width=MCore.num_data_inputs(),
                                                    data_out_width=MCore.num_data_outputs())

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

    run_tb(tester, cwd=cwd, trace=trace, disable_ndarray=True)


# add more tests with this function by adding args
# @pytest.mark.parametrize("args", [lake_test_app_args("conv_3_3")])
# def test_lake_garnet(args, run_tb):
#     basic_tb(config_path=args[0],
#              stream_path=args[1],
#              in_file_name=args[2],
#              out_file_name=args[3],
#              run_tb=run_tb)


def scanner_test(trace, run_tb, cwd):

    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2))

    netlist = {
        # Scanner to I/O
        "e0": [("s4", "data_out"), ("I0", "f2io_16")],
        "e1": [("s4", "valid_out"), ("i1", "f2io_1")],
        "e2": [("s4", "eos_out"), ("i2", "f2io_1")],
        "e3": [("i3", "io2f_1"), ("s4", "ready_in")],
        # Scanner to Mem
        "e4": [("m5", "data_out_0"), ("s4", "data_in")],
        "e5": [("m5", "valid_out_0"), ("s4", "valid_in")],
        "e6": [("s4", "addr_out"), ("m5", "addr_in_0")],
        "e7": [("s4", "ready_out"), ("m5", "ren_in_0")],
        "e8": [("i6", "io2f_1"), ("s4", "flush")],
        "e9": [("i6", "io2f_1"), ("m5", "flush")]
    }

    bus = {"e0": 16,
           "e1": 1,
           "e2": 1,
           "e3": 1,
           "e4": 16,
           "e5": 1,
           "e6": 16,
           "e7": 1,
           "e8": 1,
           "e9": 1
           }

    placement, routing = pnr(interconnect, (netlist, bus), cwd=cwd)
    config_data = interconnect.get_route_bitstream(routing)

    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    data_len = len(data)

    # Get configuration
    mem_x, mem_y = placement["m5"]
    mem_data = interconnect.configure_placement(mem_x, mem_y, {"config":["mek", {"init": data}]})
    scan_x, scan_y = placement["s4"]
    scan_data = interconnect.configure_placement(scan_x, scan_y, data_len)
    config_data += scan_data
    config_data += mem_data
    config_data = compress_config_data(config_data)

    print("BITSTREAM START")
    for addr, config in config_data:
        print("{0:08X} {1:08X}".format(addr, config))
    print("BITSTREAM END")

    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    tester.zero_inputs()

    tester.poke(circuit.interface["stall"], 1)

    # flush_x, flush_y = placement["i6"]
    # flush = f"glb2io_1_X{flush_x:02X}_Y{flush_y:02X}"

    for addr, index in config_data:
        tester.configure(addr, index)
        #  tester.config_read(addr)
        tester.eval()

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    # Now flush to synchronize everybody
    # tester.poke(circuit.interface[flush], 1)
    # tester.eval()
    # tester.step(2)
    # tester.poke(circuit.interface[flush], 0)
    # tester.eval()

    data_out_x, data_out_y = placement["I0"]
    data_out = f"io2glb_16_X{data_out_x:02X}_Y{data_out_y:02X}"

    valid_x, valid_y = placement["i1"]
    valid = f"io2glb_1_X{valid_x:02X}_Y{valid_y:02X}"
    eos_x, eos_y = placement["i2"]
    eos = f"io2glb_1_X{eos_x:02X}_Y{eos_y:02X}"
    readyin_x, readyin_y = placement["i3"]
    readyin = f"glb2io_1_X{readyin_x:02X}_Y{readyin_y:02X}"

    val = 1
    for i in range(50):
        tester.poke(circuit.interface[readyin], val)
        val = 1 - val
        tester.eval()
        # tester.expect(circuit.interface[data_out], out_data[0][i])
        # toggle the clock
        tester.step(2)

    run_tb(tester, trace=trace, disable_ndarray=True, cwd=cwd)


if __name__ == "__main__":
    # conv_3_3 - default tb - use command line to override
    from conftest import run_tb_fn
    parser = argparse.ArgumentParser(description='Tile_MemCore TB Generator')
    parser.add_argument('--config_path',
                        type=str,
                        default="conv_3_3_recipe/buf_inst_input_10_to_buf_inst_output_3_ubuf")
    parser.add_argument('--stream_path',
                        type=str,
                        default="conv_3_3_recipe/buf_inst_input_10_to_buf_inst_output_3_ubuf_0_top_SMT.csv")
    parser.add_argument('--in_file_name', type=str, default="input")
    parser.add_argument('--out_file_name', type=str, default="output")
    parser.add_argument('--tempdir_override', action="store_true")
    parser.add_argument('--trace', action="store_true")
    args = parser.parse_args()

    scanner_test(trace=args.trace,
                 run_tb=run_tb_fn,
                 cwd="mek_dump")

    # basic_tb(config_path=args.config_path,
    #          stream_path=args.stream_path,
    #          in_file_name=args.in_file_name,
    #          out_file_name=args.out_file_name,
    #          cwd=args.tempdir_override,
    #          trace=args.trace,
    #          run_tb=run_tb_fn)
