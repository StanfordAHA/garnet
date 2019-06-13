from global_controller import global_controller_genesis2
import glob
import os


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")


def test_global_controller_genesis2(capsys):
    argv = [
        "--cfg_bus_width", "32",
        "--cfg_addr_width", "32",
        "--cfg_op_width", "5",
        "--axi_addr_width", "12"
    ]
    global_controller_genesis2.gc_wrapper.main(argv=argv)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top global_controller -input global_controller/genesis/global_controller.svp global_controller/genesis/jtag.svp global_controller/genesis/axi_ctrl.svp global_controller/genesis/tap.svp global_controller/genesis/flop.svp global_controller/genesis/cfg_and_dbg.svp -parameter global_controller.cfg_bus_width='32' -parameter global_controller.cfg_addr_width='32' -parameter global_controller.cfg_op_width='5' -parameter global_controller.axi_addr_width='12''
global_controller(clk_in: In(Clock), reset_in: In(AsyncReset), clk_out: Out(Clock), reset_out: Out(AsyncReset), cgra_stalled: Out(Bits[1]), glb_stall: Out(Bit), cgra_start_pulse: Out(Bit), cgra_done_pulse: In(Bit), cgra_soft_reset: Out(Bit), config_start_pulse: Out(Bit), config_done_pulse: In(Bit), glb_write: Out(Bit), glb_read: Out(Bit), glb_config_addr_out: Out(Bits[12]), glb_config_data_out: Out(Bits[32]), glb_config_data_in: In(Bits[32]), glb_sram_write: Out(Bit), glb_sram_read: Out(Bit), glb_sram_config_addr_out: Out(Bits[32]), glb_sram_config_data_out: Out(Bits[32]), glb_sram_config_data_in: In(Bits[32]), read: Out(Bit), write: Out(Bit), config_addr_out: Out(Bits[32]), config_data_out: Out(Bits[32]), config_data_in: In(Bits[32]), AWADDR: In(Bits[12]), AWVALID: In(Bit), AWREADY: Out(Bit), WDATA: In(Bits[32]), WVALID: In(Bit), WREADY: Out(Bit), ARADDR: In(Bits[12]), ARVALID: In(Bit), ARREADY: Out(Bit), RDATA: Out(Bits[32]), RRESP: Out(Bits[2]), RVALID: Out(Bit), RREADY: In(Bit), interrupt: Out(Bit), tck: In(Clock), tdi: In(Bit), tms: In(Bit), trst_n: In(AsyncReset), tdo: Out(Bit))
"""  # nopep8
