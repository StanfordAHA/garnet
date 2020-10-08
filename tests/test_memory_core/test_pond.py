from memory_core.pond_core import PondCore
from lake.utils.util import transform_strides_and_ranges, trim_config
import glob
import tempfile
import shutil
import fault
import random
import magma
import os
from gemstone.common.testers import ResetTester
from gemstone.common.testers import BasicTester
import pytest
from gemstone.generator import Const
from cgra.util import create_cgra, compress_config_data
from canal.util import IOSide
from memory_core.memory_core_magma import config_mem_tile
from archipelago import pnr
import kratos as kts
from _kratos import create_wrapper_flatten


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


class PondCoreTester(BasicTester):

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


def make_pond_core():
    pond_core = PondCore()
    pond_circ = pond_core.circuit()

    tester = PondCoreTester(pond_circ, pond_circ.clk, pond_circ.reset)
    tester.poke(pond_circ.clk, 0)
    tester.poke(pond_circ.reset, 0)
    tester.step(1)
    tester.poke(pond_circ.reset, 1)
    tester.step(1)
    return [pond_circ, tester, pond_core]


def generate_pond_api(interconnect, pondcore, ctrl_rd, ctrl_wr, pe_x, pe_y, config_data):
    flattened = create_wrapper_flatten(pondcore.dut.internal_generator.clone(),
                                       pondcore.dut.name)

    (tform_ranges_rd, tform_strides_rd) = transform_strides_and_ranges(ctrl_rd[0], ctrl_rd[1], ctrl_rd[2])
    (tform_ranges_wr, tform_strides_wr) = transform_strides_and_ranges(ctrl_wr[0], ctrl_wr[1], ctrl_wr[2])

    name_out, val_out = trim_config(flattened, "tile_en", 1)
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    name_out, val_out = trim_config(flattened, "rf_read_iter_0_dimensionality", ctrl_rd[2])
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    name_out, val_out = trim_config(flattened, "rf_read_addr_0_starting_addr", ctrl_rd[3])
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    name_out, val_out = trim_config(flattened, "rf_read_addr_0_strides_0", tform_strides_rd[0])
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    name_out, val_out = trim_config(flattened, "rf_read_addr_0_strides_1", tform_strides_rd[1])
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    name_out, val_out = trim_config(flattened, "rf_read_iter_0_ranges_0", tform_ranges_rd[0])
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    name_out, val_out = trim_config(flattened, "rf_read_iter_0_ranges_1", tform_ranges_rd[1])
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    name_out, val_out = trim_config(flattened, "rf_read_sched_0_sched_addr_gen_starting_addr", ctrl_rd[4])
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    name_out, val_out = trim_config(flattened, "rf_read_sched_0_sched_addr_gen_strides_0", tform_strides_rd[0])
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    name_out, val_out = trim_config(flattened, "rf_read_sched_0_sched_addr_gen_strides_1", tform_strides_rd[1])
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    name_out, val_out = trim_config(flattened, "rf_write_iter_0_dimensionality", ctrl_wr[2])
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    name_out, val_out = trim_config(flattened, "rf_write_addr_0_starting_addr", ctrl_wr[3])
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    name_out, val_out = trim_config(flattened, "rf_write_addr_0_strides_0", tform_strides_wr[0])
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    name_out, val_out = trim_config(flattened, "rf_write_addr_0_strides_1", tform_strides_wr[1])
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    name_out, val_out = trim_config(flattened, "rf_write_iter_0_ranges_0", tform_ranges_wr[0])
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    name_out, val_out = trim_config(flattened, "rf_write_iter_0_ranges_1", tform_ranges_wr[1])
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    name_out, val_out = trim_config(flattened, "rf_write_sched_0_sched_addr_gen_starting_addr", ctrl_wr[4])
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    name_out, val_out = trim_config(flattened, "rf_write_sched_0_sched_addr_gen_strides_0", tform_strides_wr[0])
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))

    name_out, val_out = trim_config(flattened, "rf_write_sched_0_sched_addr_gen_strides_1", tform_strides_wr[1])
    idx, value = pondcore.get_config_data(name_out, val_out)
    config_data.append((interconnect.get_config_addr(idx, 1, pe_x, pe_y), value))


def basic_tb(verilator=True):

    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides(),
                               num_tracks=3,
                               add_pd=True,
                               add_pond=True,
                               mem_ratio=(1, 2))

    netlist = {
        "e0": [("I0", "io2f_16"), ("p0", "data_in_pond")],
        "e1": [("I1", "io2f_16"), ("p0", "data1")],
        "e2": [("p0", "data_out_pond"), ("I2", "f2io_16")]
    }
    bus = {"e0": 16, "e1": 16, "e2": 16}

    placement, routing = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    [circuit, tester, PCore] = make_pond_core()

    pe_x, pe_y = placement["p0"]

    petile = interconnect.tile_circuits[(pe_x, pe_y)]

    pondcore = PondCore()  # petile.additional_core[0][0]

    # Ranges, Strides, Dimensionality, Starting Addr, Starting Addr - Schedule
    ctrl_rd = [[16, 1], [1, 1], 2, 0, 16]
    ctrl_wr = [[16, 1], [1, 1], 2, 0, 0]

    generate_pond_api(interconnect, pondcore, ctrl_rd, ctrl_wr, pe_x, pe_y, config_data)

    config_data = compress_config_data(config_data)

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)

    tester.poke(circuit.interface["stall"], 1)

    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    tester.done_config()
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    src_x0, src_y0 = placement["I0"]
    src_x1, src_y1 = placement["I1"]
    src_name0 = f"glb2io_16_X{src_x0:02X}_Y{src_y0:02X}"
    src_name1 = f"glb2io_16_X{src_x1:02X}_Y{src_y1:02X}"
    dst_x, dst_y = placement["I2"]
    dst_name = f"io2glb_16_X{dst_x:02X}_Y{dst_y:02X}"
    random.seed(0)

    for i in range(32):
        tester.poke(circuit.interface[src_name0], i)
        tester.poke(circuit.interface[src_name1], i + 1)
        tester.eval()
        if i >= 16:
            tester.expect(circuit.interface[dst_name], i - 16)
        tester.step(2)
        tester.eval()

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


def test_pond_rd_wr():
    # pond rd wr test
    basic_tb()


if __name__ == "__main__":
    test_pond_rd_wr()
