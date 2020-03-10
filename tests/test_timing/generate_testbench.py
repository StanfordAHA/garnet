import argparse
import os  # noqa
import sys  # noqa

# NOTE(rsetaluri): Some hacks to get relative imports working.
PACKAGE_PARENT = '../..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(
    os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from canal.util import IOSide  # noqa
from gemstone.common.testers import BasicTester  # noqa
import common  # noqa
from cgra import create_cgra  # noqa


def _run(directory, width=2, height=2):
    """Generates and writes SV testbench in @directory"""
    # Create cgra generator object.
    interconnect = create_cgra(width=width, height=height,
                               io_sides=IOSide.North, num_tracks=5, add_pd=True)
    # Poke the circuit with a reset sequence and short configuration sequence.
    sequence = common.basic_sequence(interconnect)
    sequence = sequence[:2]  # limit to 2 addr's
    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    common.configure(tester, sequence, check_read_data=True)
    common.generate_testbench(tester, directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory")
    parser.add_argument("--width", type=int, default=2)
    parser.add_argument("--height", type=int, default=2)
    args = parser.parse_args()
    _run(directory=args.directory,
         width=args.width,
         height=args.height)
