import os
from cb.cb_magma import define_cb
from common.genesis_wrapper import run_genesis
from common.util import compile_to_verilog, skip_unless_irun_available
from common.irun import irun


def run_ncsim_regression(params):
    # Magma version.
    magma_cb = define_cb(**params)
    res = compile_to_verilog(magma_cb, magma_cb.name, "./")
    assert res

    # Genesis version.
    genesis_outfile = run_genesis("cb", "cb/genesis/cb.vp", params)

    # Run ncsim.
    files = [f"test_cb/{magma_cb.name}_tb.v",  # test bench file
             genesis_outfile,
             f"{magma_cb.name}.v"]
    res = irun(files)
    assert res


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
