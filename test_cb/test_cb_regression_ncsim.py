import os
from cb.cb_magma import define_cb
from common.genesis_wrapper import run_genesis
from common.util import compile_to_verilog, skip_unless_irun_available


def run_ncsim_regression(params):
    # Magma version.
    magma_cb = define_cb(**params)
    res = compile_to_verilog(magma_cb, magma_cb.name, "./")
    assert res

    # Genesis version.
    genesis_outfile = run_genesis("cb", "cb/genesis/cb.vp", params)
    assert genesis_outfile is not None

    # Run ncsim.
    TCL_FILE = "test_cb/cmd.tcl"
    tb_file = f"test_cb/{magma_cb.name}_tb.v"
    res = os.system("rm -rf INCA_libs irun.*")
    assert res == 0
    irun_cmd = f"irun -sv -top top -timescale 1ns/1ps -l irun.log -access " \
        f"+rwc -notimingchecks -input {TCL_FILE} {tb_file} " \
        f"{genesis_outfile} {magma_cb.name}.v"
    print(f"Running irun cmd: {irun_cmd}")
    res = os.system(irun_cmd)
    assert res == 0


@skip_unless_irun_available
def test_16_10_111110111_1_7():
    params = {
        "width": 16,
        "num_tracks": 10,
        "feedthrough_outputs": "1111101111",
        "has_constant": 1,
        "default_value": 7,
    }
    run_ncsim_regression(params)


@skip_unless_irun_available
def test_7_8_11111111_0_0():
    params = {
        "width": 7,
        "num_tracks": 8,
        "feedthrough_outputs": "11111111",
        "has_constant": 0,
        "default_value": 0,
    }
    run_ncsim_regression(params)
