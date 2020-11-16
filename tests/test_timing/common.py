import glob
import os
import shutil
import lassen.asm


def dw_files():
    filenames = ["DW_fp_add.v", "DW_fp_mult.v"]
    dirname = "peak_core"
    result_filenames = []
    for name in filenames:
        filename = os.path.join(dirname, name)
        assert os.path.isfile(filename)
        result_filenames.append(filename)
    return result_filenames


def configure(tester, sequence, check_read_data=True):
    tester.zero_inputs()
    tester.circuit.clk = 0
    tester.print(f"Starting reset\n")
    tester.reset()
    tester.print(f"Finished reset\n")

    for i, (addr, data) in enumerate(sequence):
        tester.configure(addr, data)
        tester.config_read(addr)
        tester.eval()
        tester.print(f"Doing config {(addr, data)}\n")
        if check_read_data:
            tester.expect(tester._circuit.read_config_data, data)
    tester.done_config()


def basic_sequence(interconnect):
    sequence = []

    # Configure Tile(1, 1).PE to be umult0.
    pe_tile = interconnect.tile_circuits[(1, 1)]
    mul_conifg_data = pe_tile.core.get_config_bitstream(lassen.asm.umult0())
    for addr, data in mul_conifg_data:
        full_addr = interconnect.get_config_addr(addr, 0, 1, 1)
        sequence.append((full_addr, data))

    return sequence


def generate_scaffolding(directory):
    for genesis_verilog in glob.glob("genesis_verif/*.*"):
        shutil.copy(genesis_verilog, directory)
    for filename in dw_files():
        shutil.copy(filename, directory)
    for aoi_mux in glob.glob("tests/*.sv"):
        shutil.copy(aoi_mux, directory)


def generate_testbench(tester, directory):
    tester.compile_and_run(skip_compile=True, target="system-verilog",
                           simulator="ncsim", directory=directory,
                           ext_model_file=True, skip_run=True)
