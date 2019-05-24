import tempfile
import os
import json
from cgra.util import create_cgra, IOSide, GlobalSignalWiring
from collateral_pass.config_register import get_interconnect_regs


def test_config_register():
    sides = IOSide.North
    ic = create_cgra(2, 2, sides, global_signal_wiring=GlobalSignalWiring.Meso)

    with tempfile.TemporaryDirectory() as tempdir:
        filename = os.path.join(tempdir, "config.json")
        result = get_interconnect_regs(ic)
        with open(filename, "w+") as f:
            json.dump(result, f)
