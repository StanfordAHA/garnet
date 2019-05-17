from global_buffer import global_buffer_genesis2
import glob
import os


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")


def test_global_buffer_genesis2(capsys):
    argv = [
        "--num_banks", "32",
        "--num_io", "8",
        "--num_cfg", "8",
        "--bank_addr_width", "17",
        "--glb_addr_width", "32",
        "--bank_data_width", "64",
        "--cgra_data_width", "16",
        "--glb_config_reg_width", "8",
        "--glb_config_feature_width", "8",
        "--glb_config_tile_width", "8",
        "--cfg_addr_width", "32",
        "--cfg_data_width", "32"
    ]
    param_mapping = global_buffer_genesis2.param_mapping
    global_buffer_genesis2.glb_wrapper.main(argv=argv,
                                            param_mapping=param_mapping)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top global_buffer -input global_buffer/genesis/global_buffer.svp global_buffer/genesis/global_buffer_int.svp global_buffer/genesis/memory_bank.svp global_buffer/genesis/cfg_address_generator.svp global_buffer/genesis/cfg_controller.svp global_buffer/genesis/bank_controller.svp global_buffer/genesis/host_bank_interconnect.svp global_buffer/genesis/io_controller.svp global_buffer/genesis/io_address_generator.svp global_buffer/genesis/glbuf_memory_core.svp global_buffer/genesis/memory.svp global_buffer/genesis/sram_gen.svp global_buffer/genesis/sram_controller.svp -parameter global_buffer.num_banks='32' -parameter global_buffer.num_io_channels='8' -parameter global_buffer.num_cfg_channels='8' -parameter global_buffer.bank_addr_width='17' -parameter global_buffer.glb_addr_width='32' -parameter global_buffer.bank_data_width='64' -parameter global_buffer.cgra_data_width='16' -parameter global_buffer.glb_config_reg_width='8' -parameter global_buffer.glb_config_tile_width='8' -parameter global_buffer.glb_config_feature_width='8' -parameter global_buffer.config_addr_width='32' -parameter global_buffer.config_data_width='32''
global_buffer(clk: In(Clock), reset: In(AsyncReset), host_wr_en: In(Bit), host_wr_data: In(Bits[64]), host_wr_addr: In(Bits[32]), host_rd_en: In(Bit), host_rd_data: Out(Bits[64]), host_rd_addr: In(Bits[32]), cgra_to_io_wr_en: In(Bits[8]), cgra_to_io_rd_en: In(Bits[8]), io_to_cgra_rd_data_valid: Out(Bits[8]), cgra_to_io_wr_data: In(Bits[128]), io_to_cgra_rd_data: Out(Bits[128]), cgra_to_io_addr_high: In(Bits[128]), cgra_to_io_addr_low: In(Bits[128]), glb_to_cgra_cfg_wr: Out(Bits[8]), glb_to_cgra_cfg_rd: Out(Bits[8]), glb_to_cgra_cfg_addr: Out(Bits[256]), glb_to_cgra_cfg_data: Out(Bits[256]), glc_to_io_stall: In(Bit), glc_to_cgra_cfg_wr: In(Bit), glc_to_cgra_cfg_rd: In(Bit), glc_to_cgra_cfg_addr: In(Bits[32]), glc_to_cgra_cfg_data: In(Bits[32]), cgra_start_pulse: In(Bit), cgra_done_pulse: Out(Bit), config_start_pulse: In(Bit), config_done_pulse: Out(Bit), glb_config_wr: In(Bit), glb_config_rd: In(Bit), glb_config_addr: In(Bits[32]), glb_config_wr_data: In(Bits[32]), glb_config_rd_data: Out(Bits[32]), glb_sram_config_wr: In(Bit), glb_sram_config_rd: In(Bit), glb_sram_config_addr: In(Bits[32]), glb_sram_config_wr_data: In(Bits[32]), glb_sram_config_rd_data: Out(Bits[32]))
"""  # nopep8
