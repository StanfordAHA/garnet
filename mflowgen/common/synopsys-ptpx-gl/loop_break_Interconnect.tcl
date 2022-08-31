# Loop break constraints
foreach_in_collection tile [get_cells -hier Tile* ] {
  current_instance $tile
  set rmuxes [get_cells -hier -regexp .*RMUX_.*_sel_(inst0|value)]
  set rmux_outputs [get_pins -of_objects $rmuxes -filter "direction==out"]
  set_case_analysis 1 $rmux_outputs
  current_instance
}
