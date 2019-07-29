source ../../scripts/tool_settings.tcl
##No need to route bump to pad nets (routed during fplan step)
setMultiCpuUsage -localCpu 8
foreach_in_collection x [get_nets pad_*] {set cmd "setAttribute -net [get_property $x full_name] -skip_routing true"; puts $cmd; eval_legacy $cmd}


##### Route Design
routeDesign
setAnalysisMode -aocv true
saveDesign init_route.enc -def -tcon -verilog
optDesign -postRoute -hold -setup
