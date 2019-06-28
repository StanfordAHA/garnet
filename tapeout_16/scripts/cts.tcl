### Clock Tree 
source ../../scripts/tool_settings.tcl
setMultiCpuUsage -localCpu 8


create_ccopt_clock_tree_spec

ccopt_design -cts
write_db cts_only.db
optDesign -postCTS
write_db cts_first_opt.db
optDesign -postCTS -hold
#eval_novus {write_db cts.db -def -sdc -verilog}
