set bad_butterphy_nets [get_nets -of_objects [get_pins iphy/ext*]]
set bad_butterphy_nets [remove_from_collection $bad_butterphy_nets [get_nets ext_*]]
set bad_butterphy_nets [get_property $bad_butterphy_nets hierarchical_name]
foreach_in_collection bad_net $bad_butterphy_nets {
  delete_net $bad_net
}
