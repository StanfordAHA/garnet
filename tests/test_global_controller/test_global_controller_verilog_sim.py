import os
from gemstone.common.util import ip_available
from gemstone.common.run_verilog_sim import verilog_sim_available
import pytest


@pytest.mark.skipif(not verilog_sim_available(),
                    reason="verilog simulator not available")
@pytest.mark.skipif(not ip_available("DW_tap.v",
                                     ["/cad/synopsys/syn/"
                                      "P-2019.03/dw/sim_ver"]),
                    reason="TAP IP not available")
def test_global_controller_verilog_sim():
    result = os.system("make -C global_controller tb_compile")
    assert result == 0
