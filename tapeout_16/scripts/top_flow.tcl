source ../../scripts/floorplan.tcl
eval_legacy {source ../../scripts/place.tcl}
write_db placed.db -def -sdc -verilog
eval_legacy { source ../../scripts/cts.tcl}
eval_legacy { source ../../scripts/route.tcl}
write_db routed_2.db -def -sdc -verilog
eval_legacy { source ../../scripts/chip_finishing.tcl}
write_db final.db -def -sdc -verilog
eval_legacy { source ../../scripts/stream_out.tcl}

