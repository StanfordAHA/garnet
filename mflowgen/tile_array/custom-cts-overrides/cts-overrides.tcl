for {set x 0} {$x < ${array_width}} {incr x} {
  set x_hex [format "%02X" $x] 
  set pin_name Tile_X${x_hex}_Y01/clk
  set_ccopt_property -pin $pin_name sink_type stop
  set_ccopt_property -pin ${pin_name}_pass_through sink_type stop
}
