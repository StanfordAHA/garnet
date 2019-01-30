import magma
from top.top_magma_pd import CGRA_PD
from top.top_magma_pd import PDCGRAConfig


def test_top_magma():
    cgra_pd = CGRA_PD(4, 4, PDCGRAConfig)
    cgra_pd_circ = cgra_pd.circuit()
    magma.compile("cgra_pd", cgra_pd_circ, output="coreir-verilog")
