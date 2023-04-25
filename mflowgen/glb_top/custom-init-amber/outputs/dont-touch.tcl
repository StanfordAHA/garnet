set num_glb_tiles $env(num_glb_tiles)
for {set i 1} {$i < $num_glb_tiles} {incr i} {
  # only need to set west since east pins are connected to same nets
  set nets [get_nets -of_objects [get_pins -of_objects [get_cells *glb_tile_gen_$i*] -filter {name =~ *_wst*}]]
  query_objects $nets
  set_dont_touch $nets true
}

