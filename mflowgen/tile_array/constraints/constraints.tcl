#=========================================================================
# Design Constraints File
#=========================================================================

# This constraint sets the target clock period for the chip in
# nanoseconds. Note that the first parameter is the name of the clock
# signal in your verlog design. If you called it something different than
# clk you will need to change this. You should set this constraint
# carefully. If the period is unrealistically small then the tools will
# spend forever trying to meet timing and ultimately fail. If the period
# is too large the tools will have no trouble but you will get a very
# conservative implementation.

set clock_net  clk
set clock_name ideal_clock

create_clock -name ${clock_name} \
             -period ${clock_period} \
             [get_ports ${clock_net}]

# This constraint sets the load capacitance in picofarads of the
# output pins of your design.

set_load -pin_load $ADK_TYPICAL_ON_CHIP_LOAD [all_outputs]

# This constraint sets the input drive strength of the input pins of
# your design. We specifiy a specific standard cell which models what
# would be driving the inputs. This should usually be a small inverter
# which is reasonable if another block of on-chip logic is driving
# your inputs.

set_driving_cell -no_design_rule \
  -lib_cell $ADK_DRIVING_CELL [all_inputs]

# set_input_delay constraints for input ports
#
# - make this non-zero to avoid hold buffers on input-registered designs

set_input_delay -clock ${clock_name} [expr ${clock_period} * 0.2] [all_inputs]

# set_output_delay constraints for output ports

set_output_delay -clock ${clock_name} 0 [all_outputs]

set_output_delay -clock ${clock_name} [expr 0.7 * ${clock_period}] [get_ports io2glb*]

# Make all signals limit their fanout

set_max_fanout 20 $design_name

# Make all signals meet good slew

set_max_transition [expr 0.1*${clock_period}] $design_name

#set_input_transition 1 [all_inputs]
#set_max_transition 10 [all_outputs]

# Ensure that no buffers get inserted on abutted nets
# First get all nets connected to CGRA tiles
set tile_nets [get_nets -of_objects [get_cells -filter {ref_name =~ *Tile*}]]
# Now iterate over collection and check if net connects > 1
# CGRA tile and no other cells. If this is true, don't try to route it.
foreach_in_collection net $tile_nets {
  set connected_cells [get_cells -of_object $net]
  set connected_tiles [filter_collection $connected_cells {ref_name =~ *Tile*}]
  set num_connected_tiles [sizeof_collection $connected_tiles]
  if {($num_connected_tiles > 1) && ([compare_collections $connected_cells $connected_tiles] == 0)} {
    set_dont_touch $net true
  }
}

# This can catch nets connected to external ports of tile_array.
# We must ensure that these nets can be touched
set ext_port_nets [get_nets -of_objects [get_ports]]
set_dont_touch $ext_port_nets false

# This can catch nets connected to IO tiles, which should be touched
set io_tile_nets [get_nets -of_objects [get_cells -filter {ref_name =~ Tile_io*}]]
set_dont_touch $io_tile_nets false

# Relax read_config_data timing path
set_multicycle_path 10 -to [get_ports read_config_data] -setup
set_multicycle_path 9 -to [get_ports read_config_data] -hold

# Don't ungroup references to *mantle_wire* because doing so 
# causes hi,lo -> tile_id connections on cgra tiles to be
# optimized away and replaced with tie cells.
#set_dont_touch [get_references *mantle_wire*]
