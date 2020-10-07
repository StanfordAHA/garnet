import os
from gemstone.common.util import ip_available
from gemstone.common.run_verilog_sim import verilog_sim_available
import pytest


@pytest.mark.skipif(not verilog_sim_available(),
                    reason="verilog simulator not available")
@pytest.mark.skipif(not ip_available("CW_tap.v",
                                     ["/cad/cadence/GENUS_19.10.000_lnx86/"
                                      "share/synth/lib/chipware/sim/verilog/CW"]),
                    reason="TAP IP not available")
def test_global_controller_verilog_sim():
    result = os.system("make -C global_controller sim")
    assert result == 0
