import magma
from top.top_magma import CGRA


def test_top_magma():
    width = 2
    height = 2
    cgra = CGRA(width=width, height=height)
    cgra_circ = cgra.circuit()
    magma.compile("cgra", cgra_circ, output="coreir-verilog")
