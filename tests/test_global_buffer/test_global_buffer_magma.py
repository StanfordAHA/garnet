import magma
from global_buffer.global_buffer_magma import GlobalBuffer

def test_compile():
    global_buffer = GlobalBuffer(16, 32)
    global_buffer_circ = global_buffer.circuit()
    magma.compile("global_buffer", global_buffer_circ, output="coreir-verilog")
