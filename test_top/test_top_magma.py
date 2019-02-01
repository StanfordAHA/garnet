import magma
from top.top_magma import CGRA


def test_top_magma():
    cgra = CGRA(width=4, height=4)
    cgra_circ = cgra.circuit()
    magma.compile("cgra", cgra_circ, output="coreir-verilog")
