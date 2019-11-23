from global_buffer.magma.global_buffer_magma import GlobalBuffer
from hierarchy_passes.ungroup import ungroup
import magma as m

# Instantiate a global buffer and manipulates the hierarchy
# to create a "tiled" global buffer for physical design
global_buffer = GlobalBuffer(32,8,8)
io_ctrl_channel_Wrappers = []
# First within the io_controller, group all of the instances into their proper tiles
for channel_inst_list in io_ctrl.channel_insts:
    group(io_ctrl, *channel_inst_list)
ungroup(global_buffer, global_buffer.io_ctrl)
ungroup(global_buffer, global_buffer.cfg_ctrl)
m.compile("global_buffer", global_buffer.circuit(), output="coreir-verilog")
