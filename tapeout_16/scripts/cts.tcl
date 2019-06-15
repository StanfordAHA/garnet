### Clock Tree 

setMultiCpuUsage -localCpu 8


create_ccopt_clock_tree_spec

ccopt_design -cts
optDesign -postCTS -hold
#eval_novus {write_db cts.db -def -sdc -verilog}
