import argparse
import pytest
from memory_core.memory_core_magma import MemCore
from lake.utils.test_infra import lake_test_app_args
from lake.utils.parse_clkwork_csv import generate_data_lists
from gemstone.common.testers import ResetTester
from gemstone.common.testers import BasicTester
from gemstone.common.util import compress_config_data
from cgra.util import create_cgra
from canal.util import IOSide
from memory_core.memory_core_magma import config_mem_tile
from archipelago import pnr


def io_sides():
    return IOSide.North | IOSide.East | IOSide.South | IOSide.West


def make_memory_core():
    mem_core = MemCore()
    return mem_core


class MemoryCoreTester(BasicTester):

    def configure(self, addr, data, feature=0):
        self.poke(self.clock, 0)
        self.poke(self.reset_port, 0)
        if (feature == 0):
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

    placement, routing, _ = pnr(interconnect, (netlist, bus))
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
@pytest.mark.parametrize("args", [lake_test_app_args("conv_3_3")])
@pytest.mark.skip
def test_lake_garnet(args, run_tb):
    basic_tb(config_path=args[0],
             stream_path=args[1],
             in_file_name=args[2],
             out_file_name=args[3],
             run_tb=run_tb)


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

    basic_tb(config_path=args.config_path,
             stream_path=args.stream_path,
             in_file_name=args.in_file_name,
             out_file_name=args.out_file_name,
             cwd=args.tempdir_override,
             trace=args.trace,
             run_tb=run_tb_fn)
