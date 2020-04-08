import magma as m
from gemstone.common.run_genesis import run_genesis
from gemstone.common.util import ip_available
from gemstone.common.run_verilog_sim import run_verilog_sim, \
    verilog_sim_available
import pytest
import glob


def run_verilog_regression(params):
    # Genesis version of global_controller
    genesis_outfile = run_genesis("top",
                                  ["tests/test_global_controller/"
                                   "genesis/top.svp",
                                   "tests/test_global_controller/"
                                   "genesis/test.svp",
                                   "tests/test_global_controller/genesis/"
                                   "JTAGDriver.svp",
                                   "tests/test_global_controller/genesis/"
                                   "axi_driver.svp",
                                   "tests/test_global_controller/genesis/"
                                   "clocker.svp",
                                   "tests/test_global_controller/genesis/"
                                   "template_ifc.svp",
                                   "tests/test_global_controller/genesis/"
                                   "cfg_ifc.svp",
                                   "global_controller/genesis/"
                                   "global_controller.svp",
                                   "global_controller/genesis/jtag.svp",
                                   "global_controller/genesis/axi_ctrl.svp",
                                   "global_controller/genesis/tap.svp",
                                   "global_controller/genesis/cfg_and_dbg.svp",
                                   "global_controller/genesis/flop.svp"],
                                  params)
    files = glob.glob('genesis_verif/*')
    # append path to TAP IP on kiwi
    files += ["/cad/synopsys/syn/P-2019.03/dw/sim_ver/DW_tap.v"]
    return run_verilog_sim(files, cleanup=True)


@pytest.mark.skipif(not verilog_sim_available(),
                    reason="verilog simulator not available")
@pytest.mark.skipif(not ip_available("DW_tap.v",
                                     ["/cad/synopsys/syn/"
                                      "P-2019.03/dw/sim_ver"]),
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
    assert res == 1
