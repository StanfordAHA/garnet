import glob
import pytest
import os
from gemstone.common.run_genesis import run_genesis
from verilator_sim import run_verilator, verilator_available

def run_verilator_regression(top, test_driver, genesis_params={},
                             verilog_params={}):
    files = ["genesis_verif/bank_controller.sv",
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
                  f"test_global_buffer.cpp"
    res = run_verilator_regression("global_buffer", test_driver,
                                   {}, verilog_params)
    assert res == 1
