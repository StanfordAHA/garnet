import pytest
import tempfile
from canal.util import IOSide
from gemstone.common.testers import BasicTester
import magma
from cgra import create_cgra
import common


dw_files = pytest.fixture(scope="module")(common.dw_files)


def test_basic(dw_files):
    """
    Configuration sequence test on 2x2 fabric + IO tiles.
    """
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

    # Compile and run the test using a verilator backend.
    with tempfile.TemporaryDirectory() as tempdir:
        common.generate_scaffolding(tempdir)
        magma.compile(f"{tempdir}/{circuit.name}", circuit,
                      output="coreir-verilog", coreir_libs={"float_DW"},
                      inline=False)
        tester.compile_and_run(skip_compile=True, target="verilator",
                               directory=tempdir, flags=["-Wno-fatal"])
