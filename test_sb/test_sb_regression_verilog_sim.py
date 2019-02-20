import magma as m
from common.genesis_wrapper import run_genesis
from common.run_verilog_sim import run_verilog_sim, verilog_sim_available
import pytest


def run_verilog_regression(params):
    # Genesis version.
    genesis_outfile = run_genesis("sb", "sb/genesis/sb.vp", params)
    files = ["test_sb/sb_tb.v", genesis_outfile]
    return run_verilog_sim(files, cleanup=True)


@pytest.mark.skipif(not verilog_sim_available(),
                    reason="verilog simulator not available")
@pytest.mark.parametrize('params', [
    {
        "width": 16,
        "num_tracks": 2,
        "sides": 4,
        "feedthrough_outputs": "00",
        "registered_outputs": "11",
        "pe_output_count": 1,
        "is_bidi": 0,
        "sb_fs": "101010",
    }
])
def test_sb_verilog_sim(params):
    assert run_verilog_regression(params)
