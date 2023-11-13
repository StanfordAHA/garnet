#====================================================================
# genlibdb-constraints.tcl
#====================================================================
# These constraints are passed to Primetime for both the PE and
# memory tiles in order to activate all of the pipeline registers
# in the tile interconnect. This prevents all downstream tools
# from analyzing combinational loops that can be realized
# in the interconnect.
#
# Authors: Alex Carsello, Teguh Hofstee
# Date: 1/24/2020

# These SB_IN to SB_OUT combinational paths
# create a loop in the tile_array level
# (dangerous: only disable these during libdb generation)
puts "\[genlibdb-constraints.tcl\] Setting paths from SB-inputs to SB-outputs to be false paths."
set_false_path -from [get_ports SB* -filter {direction == in}] -to [get_ports SB* -filter {direction == out}]

# We don't want to analyze the full combinational path through PE/MEM core in tile_array level 
set PE_core_name PE_inst0
set PE_core_cell [get_cells -quiet $PE_core_name]
if {[string length $PE_core_cell] == 0} {
    puts "\[genlibdb-constraints.tcl\] Warning: PE core ($PE_core_name) not found."
    puts "\[genlibdb-constraints.tcl\]          Possilby because you are running this script on a MEM tile."
} else {
    puts "\[genlibdb-constraints.tcl\] Setting paths through PE core ($PE_core_name) to be false paths."
    set_false_path -through $PE_core_cell
}

set MEM_core_name MemCore_inst0
set Mem_core_cell [get_cells -quiet $MEM_core_name]
if {[string length $Mem_core_cell] == 0} {
    puts "\[genlibdb-constraints.tcl\] Warning: MEM core ($MEM_core_name) not found."
    puts "\[genlibdb-constraints.tcl\]          Possilby because you are running this script on a PE tile."
} else {
    puts "\[genlibdb-constraints.tcl\] Setting paths through MEM core ($MEM_core_name) to be false paths."
    set_false_path -through $Mem_core_cell
}
