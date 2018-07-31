import magma as m
from common.genesis_wrapper import run_genesis
from common.util import verilog_sim_available, ip_available
from common.run_verilog_sim import irun, iverilog, run_verilog_sim
import pytest
import glob


def run_verilog_regression(params):
    # Genesis version of global_controller
    genesis_outfile = run_genesis("top",
                                  ["test_global_controller/genesis/top.svp",
                                   "test_global_controller/genesis/test.svp",
                                   "test_global_controller/genesis/"
                                   "JTAGDriver.svp",
                                   "test_global_controller/genesis/"
                                   "clocker.svp",
                                   "test_global_controller/genesis/"
                                   "template_ifc.svp",
                                   "test_global_controller/genesis/"
                                   "cfg_ifc.svp",
                                   "global_controller/genesis/"
                                   "global_controller.vp",
                                   "global_controller/genesis/jtag.vp",
                                   "global_controller/genesis/tap.vp",
                                   "global_controller/genesis/cfg_and_dbg.vp",
                                   "global_controller/genesis/"
                                   "analog_regfile.vp",
                                   "global_controller/genesis/flop.vp"],
                                  params)
    files = glob.glob('genesis_verif/*')
    # append path to TAP IP on kiwi
    files += ["/cad/synopsys/syn/M-2017.06-SP3/dw/sim_ver/DW_tap.v"]
    return run_verilog_sim(files)


@pytest.mark.skipif(not verilog_sim_available(),
                    reason="verilog simulator not available")
@pytest.mark.skipif(not ip_available("DW_tap.v", ["/cad/synopsys/syn/"
                                     "M-2017.06-SP3/dw/sim_ver/"]),
                    reason="TAP IP not available")
@pytest.mark.parametrize('params', [
    {
        "cfg_bus_width": 32,
        "cfg_addr_width": 32,
        "cfg_op_width": 5,
    }
])
def test_global_controller_verilog_sim(params):
    res = run_verilog_regression(params)
    assert res == 0
