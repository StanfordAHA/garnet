from global_buffer.magma.global_buffer_magma import GlobalBuffer
from hierarchy_passes.ungroup import ungroup
from hierarchy_passes.group import group
import magma as m

# Instantiate a global buffer and manipulates the hierarchy
# to create a "tiled" global buffer for physical design
global_buffer = GlobalBuffer(32,8,8)
io_ctrl_channel_wrappers = []
# First within the io_controller, group all of the instances into their proper tiles
for channel_inst_list in global_buffer.io_ctrl.channel_insts:
    io_ctrl_channel_wrappers.append(group(global_buffer.io_ctrl, "Wrapper", *channel_inst_list))
cfg_ctrl_channel_wrappers = []
# First within the cfg_controller, group all of the instances into their proper tiles
for channel_inst_list in global_buffer.cfg_ctrl.channel_insts:
    cfg_ctrl_channel_wrappers.append(group(global_buffer.cfg_ctrl, "Wrapper", *channel_inst_list))

# Now ungroup the controllers
ungroup(global_buffer, global_buffer.io_ctrl)
ungroup(global_buffer, global_buffer.cfg_ctrl)
assert(len(cfg_ctrl_channel_wrappers) == len(io_ctrl_channel_wrappers))

final_tiles = []
# Finally group the wrappers and corresponding memory banks into tiles
for channel_num, (io_channel, cfg_channel) in enumerate(zip(io_ctrl_channel_wrappers, cfg_ctrl_channel_wrappers)):
    mem_start = channel_num * global_buffer.banks_per_io
    mem_finish = (channel_num + 1) * global_buffer.banks_per_io
    mems = global_buffer.memory_bank[mem_start : mem_finish]
    final_tiles.append(group(global_buffer, "Wrapper", io_channel, cfg_channel, *mems))

m.compile("global_buffer", global_buffer.circuit(), output="coreir-verilog")
