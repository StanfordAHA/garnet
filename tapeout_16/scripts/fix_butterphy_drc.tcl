set bad_butterphy_nets [get_nets -of_objects [get_pins iphy/ext*]]
set bad_butterphy_nets [remove_from_collection $bad_butterphy_nets [get_nets ext_*]]
set bad_butterphy_nets [get_property $bad_butterphy_nets hierarchical_name]
foreach bad_net $bad_butterphy_nets {
  delete_nets $bad_net
  set bad_cells [get_cells -of_objects [get_net $bad_net]]
  set bad_cells [remove_from_collection $bad_cells [get_cells -hier iphy]]
  set bad_nets [get_nets -of_objects $bad_cells]
  delete_inst -inst [get_property $bad_cells hierarchical_name]
  foreach_in_collection bad_nets $bad_nets {
    delete_nets [get_property $bad_net name]
  }
}

#set bad_rte_nets [get_nets -of_objects [get_pins */RTE]]
#set bad_rte_nets [get_property $bad_rte_nets hierarchical_name]
#foreach bad_net $bad_rte_nets {
#  delete_nets $bad_net
#}
