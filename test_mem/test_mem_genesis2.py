from mem import mem_genesis2
import glob
import os
import shutil
import fault
from magma.testing.verilator import compile, run_verilator_test


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")
    os.system(f"rm MEMmemory_core")


def test_main(capsys):
    parser = mem_genesis2.create_parser()
    args = parser.parse_args([
        "--data-width", "16",
        "--data-depth", "1024",
        "mem/genesis/input_sr.vp",
        "mem/genesis/output_sr.vp",
        "mem/genesis/linebuffer_control.vp",
        "mem/genesis/fifo_control.vp",
        "mem/genesis/mem.vp",
        "mem/genesis/memory_core.vp"
    ])

    mem_genesis2.main(args)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top memory_core -input mem/genesis/input_sr.vp mem/genesis/output_sr.vp mem/genesis/linebuffer_control.vp mem/genesis/fifo_control.vp mem/genesis/mem.vp mem/genesis/memory_core.vp -parameter memory_core.dwidth='16' -parameter memory_core.ddepth='1024''
memory_core(clk_in: In(Bit), clk_en: In(Bit), reset: In(Bit), config_addr: Array(32,In(Bit)), config_data: Array(32,In(Bit)), config_read: In(Bit), config_write: In(Bit), config_en: In(Bit), config_en_sram: Array(4,In(Bit)), config_en_linebuf: In(Bit), data_in: Array(16,In(Bit)), data_out: Array(16,Out(Bit)), wen_in: In(Bit), ren_in: In(Bit), valid_out: Out(Bit), chain_in: Array(16,In(Bit)), chain_out: Array(16,Out(Bit)), chain_wen_in: In(Bit), chain_valid_out: Out(Bit), almost_full: Out(Bit), almost_empty: Out(Bit), addr_in: Array(16,In(Bit)), read_data: Array(32,Out(Bit)), read_data_sram: Array(32,Out(Bit)), read_data_linebuf: Array(32,Out(Bit)), flush: In(Bit))
"""  # nopep8


def test_sram_basic():
    Mem = mem_genesis2.define_mem_genesis2()  # Using default params
    for genesis_verilog in glob.glob("genesis_verif/*.v"):
        shutil.copy(genesis_verilog, "test_mem/build")

    # FIXME: HACK from old CGRA, copy sram stub
    shutil.copy("test_mem/sram_stub.v", "test_mem/build/sram_512w_16b.v")

    tester = fault.Tester(Mem, clock=Mem.clk_in)
    # Initialize all inputs to 0
    # TODO: Make this a convenience function in Tester?
    # We have to get the `outputs` because the ports are flipped to use the
    # polarity for definitions. TODO: This is a confusing wart
    for port in Mem.interface.outputs():
        tester.poke(getattr(Mem, str(port)), 0)

    # Expect all outputs to be 0
    for port in Mem.interface.inputs():
        tester.expect(getattr(Mem, str(port)), 0)

    tester.eval()

    compile(f"test_mem/build/test_{Mem.name}.cpp", Mem, tester.test_vectors)
    run_verilator_test(Mem.name, f"test_{Mem.name}", Mem.name, ["-Wno-fatal"],
                       build_dir="test_mem/build")
