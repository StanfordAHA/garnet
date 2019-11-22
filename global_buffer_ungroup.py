from global_buffer.magma.global_buffer_magma import GlobalBuffer
from hierarchy_passes.ungroup import ungroup
import magma as m

global_buffer = GlobalBuffer(32,8,8)
ungroup(global_buffer, global_buffer.io_ctrl)
m.compile("global_buffer", global_buffer.circuit(), output="coreir-verilog")
