from memory_core.memory_core_magma import get_pond
import glob
import tempfile
import shutil
import fault
import random
import magma
from gemstone.common.testers import ResetTester
from gemstone.common.testers import BasicTester
import pytest


# Simply generate the coreir-verilog output target for pond core
# Skipping for now - until we get updated pond core
@pytest.mark.skip
def test_pond_verilog_generation():
    pond_core = get_pond(use_sram_stub=1)
    magma.compile("PondCore", pond_core.circuit(), output="coreir-verilog")
