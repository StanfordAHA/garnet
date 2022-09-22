#=========================================================================
# setup-ccopt.tcl
#=========================================================================
# Author : Christopher Torng
# Date   : March 26, 2018

# Add non-default rules for route types

#add_ndr -name CTS_2W1S \
#        -width_multiplier {7:9 2} \
#        -generate_via
#        # -min_cut {M4:M5 2}
#
#add_ndr -name CTS_2W2S \
#        -width_multiplier {10:12 2} \
#        -spacing_multiplier {10:12 2} \
#        -generate_via
#        # -min_cut {M6:M9 2}
#
## Define route types (from Quick Start Example)
#
#create_route_type -name leaf_rule \
#                  -non_default_rule CTS_2W1S \
#                  -top_preferred_layer 8 \
#                  -bottom_preferred_layer 7 \
#                  -prefer_multi_cut_via \
#                  -preferred_routing_layer_effort medium
#
#create_route_type -name trunk_rule \
#                  -non_default_rule CTS_2W2S \
#                  -top_preferred_layer 10 \
#                  -bottom_preferred_layer 9 \
#                  -shield_net VSS \
#                  -shield_side both_side \
#                  -prefer_multi_cut_via \
#                  -preferred_routing_layer_effort medium
#
#create_route_type -name top_rule \
#                  -non_default_rule CTS_2W2S \
#                  -top_preferred_layer 12 \
#                  -bottom_preferred_layer 11 \
#                  -shield_net VSS \
#                  -shield_side both_side \
#                  -prefer_multi_cut_via \
#                  -preferred_routing_layer_effort medium
#
## Specify the route types will be used for leaf, trunk, and top nets,
## respectively
#
#set_ccopt_property -net_type leaf route_type leaf_rule
#set_ccopt_property -net_type trunk route_type trunk_rule
#set_ccopt_property -net_type top route_type top_rule
#
## Setting top
#
#set_ccopt_property routing_top_min_fanout 10000

set_ccopt_property buffer_cells {SC7P5T_CKBUFX1_SSC14SL SC7P5T_CKBUFX0P5_SSC14SL SC7P5T_CKBUFX10_SSC14SL SC7P5T_CKBUFX12_SSC14SL SC7P5T_CKBUFX14_SSC14SL SC7P5T_CKBUFX16_SSC14SL SC7P5T_CKBUFX20_SSC14SL SC7P5T_CKBUFX24_SSC14SL SC7P5T_CKBUFX2_SSC14SL SC7P5T_CKBUFX3_SSC14SL  SC7P5T_CKBUFX4_SSC14SL SC7P5T_CKBUFX5_SSC14SL SC7P5T_CKBUFX6_SSC14SL SC7P5T_CKBUFX8_SSC14SL SC7P5T_CKBUFX1_SSC14L SC7P5T_CKBUFX0P5_SSC14L SC7P5T_CKBUFX10_SSC14L SC7P5T_CKBUFX12_SSC14L SC7P5T_CKBUFX14_SSC14L SC7P5T_CKBUFX16_SSC14L SC7P5T_CKBUFX20_SSC14L SC7P5T_CKBUFX24_SSC14L SC7P5T_CKBUFX2_SSC14L SC7P5T_CKBUFX3_SSC14L  SC7P5T_CKBUFX4_SSC14L SC7P5T_CKBUFX5_SSC14L SC7P5T_CKBUFX6_SSC14L SC7P5T_CKBUFX8_SSC14L SC7P5T_CKBUFX1_SSC14R SC7P5T_CKBUFX0P5_SSC14R SC7P5T_CKBUFX10_SSC14R SC7P5T_CKBUFX12_SSC14R SC7P5T_CKBUFX14_SSC14R SC7P5T_CKBUFX16_SSC14R SC7P5T_CKBUFX20_SSC14R SC7P5T_CKBUFX24_SSC14R SC7P5T_CKBUFX2_SSC14R SC7P5T_CKBUFX3_SSC14R  SC7P5T_CKBUFX4_SSC14R SC7P5T_CKBUFX5_SSC14R SC7P5T_CKBUFX6_SSC14R SC7P5T_CKBUFX8_SSC14R}

set_ccopt_property inverter_cells {SC7P5T_CKINVX1_SSC14SL SC7P5T_CKINVX2_SSC14SL SC7P5T_CKINVX3_SSC14SL SC7P5T_CKINVX0P5_SSC14SL SC7P5T_CKINVX10_SSC14SL SC7P5T_CKINVX12_SSC14SL SC7P5T_CKINVX14_SSC14SL SC7P5T_CKINVX16_SSC14SL SC7P5T_CKINVX20_SSC14SL SC7P5T_CKINVX24_SSC14SL  SC7P5T_CKINVX4_SSC14SL SC7P5T_CKINVX5_SSC14SL SC7P5T_CKINVX6_SSC14SL SC7P5T_CKINVX8_SSC14SL SC7P5T_CKINVX1_SSC14L SC7P5T_CKINVX2_SSC14L SC7P5T_CKINVX3_SSC14L SC7P5T_CKINVX0P5_SSC14L SC7P5T_CKINVX10_SSC14L SC7P5T_CKINVX12_SSC14L SC7P5T_CKINVX14_SSC14L SC7P5T_CKINVX16_SSC14L SC7P5T_CKINVX20_SSC14L SC7P5T_CKINVX24_SSC14L  SC7P5T_CKINVX4_SSC14L SC7P5T_CKINVX5_SSC14L SC7P5T_CKINVX6_SSC14L SC7P5T_CKINVX8_SSC14L SC7P5T_CKINVX1_SSC14R SC7P5T_CKINVX2_SSC14R SC7P5T_CKINVX3_SSC14R SC7P5T_CKINVX0P5_SSC14R SC7P5T_CKINVX10_SSC14R SC7P5T_CKINVX12_SSC14R SC7P5T_CKINVX14_SSC14R SC7P5T_CKINVX16_SSC14R SC7P5T_CKINVX20_SSC14R SC7P5T_CKINVX24_SSC14R  SC7P5T_CKINVX4_SSC14R SC7P5T_CKINVX5_SSC14R SC7P5T_CKINVX6_SSC14R SC7P5T_CKINVX8_SSC14R}

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


