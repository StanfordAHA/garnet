from global_buffer.magma.io_controller_magma import IoController
from gemstone.common.ungroup import ungroup
from gemstone.common.group import group
import magma as m

io_ctrl = IoController(32,8)
io_ctrl_channel_Wrappers = []
for channel_inst_list in io_ctrl.channel_insts:
    print(f"GROUPING {len(channel_inst_list)} channel insts")
    group(io_ctrl, "IoCtrlTile", *channel_inst_list)
#ungroup(io_ctrl)
m.compile("io_controller", io_ctrl.circuit(), output="coreir-verilog")
