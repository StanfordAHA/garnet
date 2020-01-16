from global_buffer.magma.cfg_controller_magma import CfgController
from gemstone.common.ungroup import ungroup
from gemstone.common.group import group
import magma as m

cfg_ctrl = CfgController(32,8)
cfg_ctrl_channel_wrappers = []
for channel_num, channel_inst_list in enumerate(cfg_ctrl.channel_insts):
    cfg_ctrl_channel_wrappers.append(group(cfg_ctrl, "cfg_ctrl_tile", *channel_inst_list))
#ungroup(cfg_ctrl)
for sink in cfg_ctrl.sinks:
    for port in sink.ports.sink_in._connections:
        cfg_ctrl.remove_wire(sink.ports.sink_in, port)
left = cfg_ctrl_channel_wrappers[0]
mid = cfg_ctrl_channel_wrappers[1]
right = cfg_ctrl_channel_wrappers[-1]
print(f"left: {len(left.children())} children, {len(left.ports)} ports")
print(f"mid: {len(mid.children())} children, {len(mid.ports)} ports")
print(f"right: {len(right.children())} children, {len(right.ports)} ports")
m.compile("cfg_controller", cfg_ctrl.circuit(), output="coreir-verilog")
