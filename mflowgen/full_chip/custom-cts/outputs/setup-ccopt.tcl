#=========================================================================
# setup-ccopt.tcl
#=========================================================================
# Author : Christopher Torng
# Date   : March 26, 2018

# # Add non-default rules for route types

# add_ndr -name CTS_2W1S \
#         -width_multiplier {8:10 2} \
#         -generate_via
#         # -min_cut {M4:M5 2}

# add_ndr -name CTS_2W2S \
#         -width_multiplier {11:13 2} \
#         -spacing_multiplier {11:13 2} \
#         -generate_via
#         # -min_cut {M6:M9 2}

# # Define route types (from Quick Start Example)

# create_route_type -name leaf_rule \
#                   -non_default_rule CTS_2W1S \
#                   -top_preferred_layer 9 \
#                   -bottom_preferred_layer 8 \
#                   -prefer_multi_cut_via \
#                   -preferred_routing_layer_effort medium

# create_route_type -name trunk_rule \
#                   -non_default_rule CTS_2W2S \
#                   -top_preferred_layer 11 \
#                   -bottom_preferred_layer 10 \
#                   -shield_net VSS \
#                   -shield_side both_side \
#                   -prefer_multi_cut_via \
#                   -preferred_routing_layer_effort medium

# create_route_type -name top_rule \
#                   -non_default_rule CTS_2W2S \
#                   -top_preferred_layer 13 \
#                   -bottom_preferred_layer 12 \
#                   -shield_net VSS \
#                   -shield_side both_side \
#                   -prefer_multi_cut_via \
#                   -preferred_routing_layer_effort medium

# # Specify the route types will be used for leaf, trunk, and top nets,
# # respectively

# set_ccopt_property -net_type leaf route_type leaf_rule
# set_ccopt_property -net_type trunk route_type trunk_rule
# set_ccopt_property -net_type top route_type top_rule

# Setting top

# set_ccopt_property routing_top_min_fanout 10000

# set_ccopt_property buffer_cells ${ADK_CTS_BUFFER_CELLS}

# set_ccopt_property inverter_cells ${ADK_CTS_INVERTER_CELLS}

# Allow clock gate cloning and merging

set_ccopt_property clone_clock_gates true
set_ccopt_property clone_clock_logic true
set_ccopt_property ccopt_merge_clock_gates true
set_ccopt_property ccopt_merge_clock_logic true
set_ccopt_property cts_merge_clock_gates true
set_ccopt_property cts_merge_clock_logic true

# Useful skew
#
# setOptMode -usefulSkew [ true | false ]
#
# - This enables/disables all other -usefulSkew* options (e.g.,
#   -usefulSkewCCOpt, -usefulSkewPostRoute, and -usefulSkewPreCTS)
#
# setOptMode -usefulSkewCCOpt [ none | standard | medium | extreme ]
#
# - If setOptMode -usefulSkew is false, then this entire option is ignored
#
# - Connection to "set_ccopt_effort" .. these are the same:
#   - "set_ccopt_effort -low"    and "setOptMode -usefulSkewCCOpt standard"
#   - "set_ccopt_effort -medium" and "setOptMode -usefulSkewCCOpt medium"
#   - "set_ccopt_effort -high"   and "setOptMode -usefulSkewCCOpt extreme"
#

puts "Info: Useful skew = $::env(useful_skew)"
puts "Info: Useful skew ccopt effort = $::env(useful_skew_ccopt_effort)"

if { $::env(useful_skew) } {
  setOptMode -usefulSkew      true
  setOptMode -usefulSkewCCOpt $::env(useful_skew_ccopt_effort)
} else {
  setOptMode -usefulSkew      false
}

# Specify clock tree synthesis cells and slew
set_ccopt_mode \
  -integration "native" \
  -cts_inverter_cells ${ADK_CTS_INVERTER_CELLS} \
  -cts_buffer_cells ${ADK_CTS_BUFFER_CELLS} \
  -cts_clock_gating_cells ${ADK_CTS_CLOCK_GATING_CELLS} \
  -cts_logic_cells ${ADK_CTS_LOGIC_CELLS} \
  -ccopt_modify_clock_latency true \
  -cts_target_slew ${ADK_CTS_TARGET_SLEW}

# Enable the use of clock gating cells
foreach cell ${ADK_CTS_CLOCK_GATING_CELLS} {
  setDontUse ${cell} false
}


if { $::env(set_cts_insertion_delay) } {
  # Prevent -200 insertion delay on glb clk
  set_ccopt_property insertion_delay -pin [get_object_name [get_pin -hier global_buffer/clk]] 850ps
  set_ccopt_property insertion_delay -pin [get_object_name [get_pin -hier Interconnect_inst0/clk]] 500ps
}
