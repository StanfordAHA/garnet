import glob
import pytest
import os
from gemstone.common.run_genesis import run_genesis
from verilator_sim import run_verilator, verilator_available


def run_verilator_regression(top, test_driver, genesis_params={},
                             verilog_params={}):
    run_genesis(f"{top}",
                ["global_buffer/genesis/bank_controller.svp",
                 "global_buffer/genesis/cfg_address_generator.svp",
                 "global_buffer/genesis/cfg_controller.svp",
                 "global_buffer/genesis/glbuf_memory_core.svp",
                 "global_buffer/genesis/global_buffer_int.svp",
                 "global_buffer/genesis/host_bank_interconnect.svp",
                 "global_buffer/genesis/io_address_generator.svp",
                 "global_buffer/genesis/io_controller.svp",
                 "global_buffer/genesis/memory_bank.svp",
                 "global_buffer/genesis/memory.svp",
                 "global_buffer/genesis/sram_controller.svp",
                 "global_buffer/genesis/sram_gen.svp"],
                genesis_params)
    files = ["genesis_verif/bank_controller.sv",
             "genesis_verif/cfg_address_generator.sv",
             "genesis_verif/cfg_controller.sv",
             "genesis_verif/glbuf_memory_core.sv",
             "genesis_verif/global_buffer_int.sv",
             "genesis_verif/host_bank_interconnect.sv",
             "genesis_verif/io_address_generator.sv",
             "genesis_verif/io_controller.sv",
             "genesis_verif/memory_bank.sv",
             "genesis_verif/memory.sv",
             "genesis_verif/sram_controller.sv",
             "genesis_verif/sram_gen.sv",
             "global_buffer/genesis/TS1N16FFCLLSBLVTC2048X64M8SW.sv"]
    return run_verilator(verilog_params, top, files, test_driver)


@pytest.mark.skipif(not verilator_available(),
                    reason="verilator not available")
@pytest.mark.parametrize('verilog_params', [
    {
        "BANK_DATA_WIDTH": 64,
        "GLB_ADDR_WIDTH": 32,
        "CGRA_DATA_WIDTH": 16
    }
])
def test_global_buffer_int_verilator(verilog_params):
    test_driver = f"tests/test_global_buffer/verilator/"\
                  f"test_global_buffer_int.cpp"
    res = run_verilator_regression("global_buffer_int", test_driver,
                                   {}, verilog_params)
    assert res == 1
