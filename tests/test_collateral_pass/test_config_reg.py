import tempfile
import os
import json
import cgra
from cgra.util import create_cgra, IOSide, GlobalSignalWiring
from collateral_pass.config_register import get_interconnect_regs, \
    get_core_registers


@pytest.fixture()
def test_config_register(width=2, height=2):
    sides = IOSide.North
    ic = create_cgra(width, height, sides, global_signal_wiring=GlobalSignalWiring.Meso)

    with tempfile.TemporaryDirectory() as tempdir:
        filename = os.path.join(tempdir, "config.json")
        ic_result = get_interconnect_regs(ic)
        core_result = get_core_registers(ic)
        result = ic_result + core_result

        with open(filename, "w+") as f:
            json.dump(result, f)


def main():
    parser = argparse.ArgumentParser(description="""
    Generates collateral describing configuration space of the CGRA.
    """)

    parser.add_argument('--width', type=int, default=4)
    parser.add_argument('--height', type=int, default=2)
    args = parser.parse_args()

    test_config_register(args.width, args.height)


if __name__ == "__main__":
    main()
