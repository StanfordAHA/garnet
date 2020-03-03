# NOTE(rsetaluri): Some hacks to get relative imports working.
PACKAGE_PARENT = '../..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(
    os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

import os  # noqa
import sys  # noqa
from canal.util import IOSide  # noqa
from gemstone.common.testers import BasicTester  # noqa
import common  # noqa
from cgra import create_cgra  # noqa


def _usage():
    return "Usage: python tests/test_timing/generate_testbench.py <directory>"


def _run(directory):
    """Generates and writes SV testbench in @directory"""
    # Create cgra generator object.
    chip_size = 2
    interconnect = create_cgra(width=chip_size, height=chip_size,
                               io_sides=IOSide.North, num_tracks=5, add_pd=True)
    # Poke the circuit with a reset sequence and short configuration sequence.
    sequence = common.basic_sequence(interconnect)
    sequence = sequence[:2]  # limit to 2 addr's
    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    common.configure(tester, sequence, check_read_data=True)
    common.generate_testbench(tester, directory)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(_usage())
        exit()
    _run(sys.argv[1])
