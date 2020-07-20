for {set x 0} {$x < $::env(array_width)} {incr x} {
  set x_hex [format "%02X" $x]
  set tile_name Tile_X${x_hex}_Y01
  set tile_type [get_property [get_cells $tile_name] ref_lib_cell_name]
  if { $tile_type eq "Tile_PE" } {
    set pin_name ${tile_name}/clk
    set_ccopt_property -pin $pin_name sink_type stop
    set_ccopt_property -pin ${pin_name}_pass_through sink_type stop
  }
}
