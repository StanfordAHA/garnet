

#------------------------------------------------------------------------
# Load UPF 
# ------------------------------------------------------------------------


read_power_intent -1801 inputs/upf_Tile_MemCore.tcl
commit_power_intent
write_power_intent -1801 upf.out

