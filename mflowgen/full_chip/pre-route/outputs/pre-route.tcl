foreach_in_collection x [get_nets pad_*] {
  setAttribute -net [get_property $x full_name] -skip_routing true
}
