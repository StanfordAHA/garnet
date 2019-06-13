import glob
import pytest
import os
import subprocess

GARNET_VERILOG_FILENAME = os.path.join(os.path.dirname(__file__),
                                       os.path.pardir, os.path.pardir,
                                       "garnet.v")

PROBLEM_FILENAME = os.path.join(os.path.dirname(__file__),
                                "problem.txt")


def test_pe_tile_interconnect():
    pytest.skip("yosys takes forever to download")
    if not os.path.isfile(GARNET_VERILOG_FILENAME):
        garnet_root = os.path.dirname(GARNET_VERILOG_FILENAME)
        subprocess.check_call(["python", 'garnet.py', "-v"], cwd=garnet_root)
    assert os.path.isfile(GARNET_VERILOG_FILENAME)
    subprocess.check_call(["CoSA", "--problems", PROBLEM_FILENAME])


if __name__ == "__main__":
    test_pe_tile_interconnect()
