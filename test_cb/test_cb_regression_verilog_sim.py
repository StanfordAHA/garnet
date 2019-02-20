import magma as m
from cb.cb_magma import define_cb
from gemstone.common.genesis_wrapper import run_genesis
from gemstone.common.run_verilog_sim import run_verilog_sim, verilog_sim_available
import pytest


def run_verilog_regression(params):
    # Magma version.
    magma_cb = define_cb(**params)
    m.compile(f"./{magma_cb.name}", magma_cb, output="coreir-verilog")

    # Genesis version.
    genesis_outfile = run_genesis("cb", "cb/genesis/cb.vp", params)

    files = [f"test_cb/{magma_cb.name}_tb.v",  # test bench file
             genesis_outfile,
             f"{magma_cb.name}.v"]
    return run_verilog_sim(files, cleanup=True)


@pytest.mark.skipif(not verilog_sim_available(),
                    reason="verilog simulator not available")
@pytest.mark.parametrize('params', [
    {
        "width": 7,
        "num_tracks": 8,
        "feedthrough_outputs": "11111111",
        "has_constant": 0,
        "default_value": 0,
    }, {
        "width": 16,
        "num_tracks": 10,
        "feedthrough_outputs": "1111101111",
        "has_constant": 1,
        "default_value": 7,
    }
])
def test_cb_verilog_sim(params):
    assert run_verilog_regression(params)
