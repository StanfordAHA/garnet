import magma
from top.top_magma import CGRA


def test_top_magma():
    cgra = CGRA(2, 2)
    cgra_circ = cgra.circuit()
    magma.compile("cgra", cgra_circ, output="coreir-verilog")
