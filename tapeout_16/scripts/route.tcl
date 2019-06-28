source ../../scripts/tool_settings.tcl
#No need to route bump to pad nets (routed during fplan step)
foreach_in_collection x [get_nets pad_*] {set cmd "setAttribute -net [get_property $x full_name] -skip_routing true"; puts $cmd; eval_legacy $cmd}

#Fixes for ICOVL DRCs
create_route_blockage -all {route cut} -rects {{2332 2684 2414 2733}{2331 3505 2414 3561}}       
set_db [get_db insts ifid_icovl*] .route_halo_size 4
set_db [get_db insts ifid_icovl*] .route_halo_bottom_layer M1
set_db [get_db insts ifid_icovl*] .route_halo_top_layer AP

#### Route Design
routeDesign
setAnalysisMode -aocv true
saveDesign init_route.enc -def -tcon -verilog
optDesign -postRoute -hold -setup
