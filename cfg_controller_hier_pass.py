from global_buffer.magma.cfg_controller_magma import CfgController
from hierarchy_passes.ungroup import ungroup
from hierarchy_passes.group import group
import magma as m

cfg_ctrl = CfgController(32,8)
cfg_ctrl_channel_Wrappers = []
for channel_num, channel_inst_list in enumerate(cfg_ctrl.channel_insts):
    group(cfg_ctrl, "Wrapper", *channel_inst_list)
#ungroup(cfg_ctrl)
m.compile("cfg_controller", cfg_ctrl.circuit(), output="coreir-verilog")
