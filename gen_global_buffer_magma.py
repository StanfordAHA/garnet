from global_buffer.magma.global_buffer_magma import GlobalBuffer
import magma as m

global_buffer = GlobalBuffer(32, 8, 8)
m.compile("global_buffer", global_buffer.circuit(), output="coreir-verilog")
