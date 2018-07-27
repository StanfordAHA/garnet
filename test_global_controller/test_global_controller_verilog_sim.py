import magma as m
from common.genesis_wrapper import run_genesis
from common.util import verilog_sim_available
from common.run_verilog_sim import irun, iverilog, run_verilog_sim
import pytest


def run_verilog_regression(params):
    # Genesis version of global_controller
    genesis_outfile = run_genesis("top",
                                  ["test_global_controller/genesis/top.svp",
                                  "test_global_controller/genesis/test.svp",
                                  "test_global_controller/genesis/JTAGDriver.svp",
                                  "test_global_controller/genesis/clocker.svp",
                                  "test_global_controller/genesis/template_ifc.svp",
                                  "global_controller/genesis/global_controller.vp",
                                  "global_controller/genesis/jtag.vp",
                                  "global_controller/genesis/tap.vp",
                                  "global_controller/genesis/cfg_and_dbg.vp",
                                  "global_controller/genesis/analog_regfile.vp",
                                  "global_controller/genesis/flop.vp"],
                                  params)

    return run_verilog_sim(genesis_outfile)


@pytest.mark.skipif(not verilog_sim_available(),
                    reason="verilog simulator not available")
@pytest.mark.parametrize('params', [
    {
        "cfg_bus_width": 32,
        "cfg_addr_width": 32,
        "cfg_op_width": 5,
    }
])
def test_global_controller_verilog_sim(params):
    run_verilog_regression(params)
