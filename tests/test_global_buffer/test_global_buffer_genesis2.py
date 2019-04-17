from global_buffer import global_buffer_genesis2
import glob
import os


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")


def test_global_buffer_genesis2(capsys):
    argv = [
        "--num_banks", "32",
        "--bank_addr_width", "16",
        "--bank_data_width", "64",
        "--top_config_addr_width", "32",
        "--top_config_data_width", "32"
    ]
    global_buffer_genesis2.global_buffer_wrapper.main(argv=argv)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top global_buffer -input global_buffer/genesis/global_buffer.svp global_buffer/genesis/bank_controller.sv global_buffer/genesis/memory_bank.sv global_buffer/genesis/memory_core.sv global_buffer/genesis/sram_controller.sv global_buffer/genesis/memory.v global_buffer/genesis/sram_stub.v -parameter global_buffer.num_banks='32' -parameter global_buffer.bank_addr_width='32' -parameter global_buffer.bank_data_width='64' -parameter global_buffer.top_config_addr_width='32' -parameter global_buffer.top_config_data_width='32''
global_buffer(clk: In(Clock), reset_in: In(AsyncReset), config_data_in: In(Bits[32]), config_addr_out: Out(Bits[32]), config_data_out: Out(Bits[32]), clk_out: Out(Clock), reset_out: Out(AsyncReset), cgra_stalled: Out(Bits[4]), read: Out(Bit), write: Out(Bit), tdi: In(Bit), tdo: Out(Bit), tms: In(Bit), tck: In(Clock), trst_n: In(AsyncReset))
"""  # nopep8
