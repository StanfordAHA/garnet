connect_global_net VDD -type pgpin -pin DVDD -inst iphy -override
connect_global_net VSS -type pgpin -pin DVSS -inst iphy -override


set dx 0.09
set dy 0.576
set phy_width 580.05
set phy_height 700.416
set origin_phy_x  [expr ceil(1813/$dx)*$dx]
set origin_phy_y  4099.584

set DVDD_offset1 3.0
set DVDD_offset2 313.512
set ADC_height [expr 70*$dy]

place_inst iphy $origin_phy_x $origin_phy_y

# M8 blockage covering pad frame bracketing (butter)phy block left, right, top
create_route_blockage -area    0 $origin_phy_y  100 [expr $origin_phy_y+$phy_height] -layer M8
create_route_blockage -area 4800 $origin_phy_y 4900 [expr $origin_phy_y+$phy_height] -layer M8
create_route_blockage -area    0               4800 4900 4900 -layer M8

# M8 stripes across top of chip, from top to about halfway down the analog block
add_stripe -nets {VDD VSS VDD VSS VDD } \
    -layer M8 -direction horizontal -width 2 -spacing 1 \
    -start_offset [expr $origin_phy_y+$DVDD_offset2-100+0.016] \
    -set_to_set_distance $ADC_height -start_from bottom -switch_layer_over_obs false \
    -max_same_layer_jog_length 2 \
    -pad_core_ring_top_layer_limit AP -pad_core_ring_bottom_layer_limit M1 \
    -block_ring_top_layer_limit M8 -block_ring_bottom_layer_limit M1 \
    -use_wire_group 0 -snap_wire_center_to_grid none -extend_to design_boundary

# Hm looks like more M8 stripes in the same region, interleaved with the ones above.
# For the most part, these stripes all match up correctly to phy pins
add_stripe -nets {VDD VSS VDD VSS VDD } \
    -layer M8 -direction horizontal -width 2 -spacing 1 \
    -start_offset [expr $origin_phy_y+$DVDD_offset2-100+0.016+23]  \
    -set_to_set_distance $ADC_height -start_from bottom -switch_layer_over_obs false \
    -max_same_layer_jog_length 2 \
    -pad_core_ring_top_layer_limit AP -pad_core_ring_bottom_layer_limit M1 \
    -block_ring_top_layer_limit M8 -block_ring_bottom_layer_limit M1 \
    -use_wire_group 0 -snap_wire_center_to_grid none -extend_to design_boundary

# Appears to create a blockage area for top half(?) of butterphy
create_route_blockage -area 0 [expr $origin_phy_y+$DVDD_offset2-28] 4900 4900 -layer M8

# More M8 stripes, now finished to bottom of butterphy(?)
add_stripe -nets {VDD VSS} \
    -layer M8 -direction horizontal -width 2 -spacing 1 \
    -start_offset [expr $origin_phy_y+$DVDD_offset1-100+0.016]  \
    -set_to_set_distance 12 -start_from bottom -switch_layer_over_obs false \
    -max_same_layer_jog_length 2 \
    -pad_core_ring_top_layer_limit AP -pad_core_ring_bottom_layer_limit M1 \
    -block_ring_top_layer_limit M8 -block_ring_bottom_layer_limit M1 \
    -use_wire_group 0 -snap_wire_center_to_grid none -extend_to design_boundary

# Hm okay this deletes all the blockages that were added above I guess
# FIXME I think it's supposed to be delete_route_*blockages* (with an 's') not *blockage*
delete_route_blockage -name *

##############################################################################
# (Butter)phy blockages on different layers I guess.
#Some of these look weird to me but okay...

# Block AP over entire phy
create_route_blockage -area $origin_phy_x $origin_phy_y \
    [expr $origin_phy_x+$phy_width] [expr $origin_phy_y+$phy_height] \
    -layer AP

# Block M9 for a little rectangle just below the phy
create_route_blockage -area [expr $origin_phy_x+200] [expr $origin_phy_y] \
    [expr $origin_phy_x+$phy_width-200] [expr $origin_phy_y-80] \
    -layer M9

# Block M7,M9 over entire phy
create_route_blockage -area [expr $origin_phy_x-20] [expr $origin_phy_y] [expr $origin_phy_x] [expr $origin_phy_y+$phy_height] \
    -layer {M9 M7}

# Block M8 across entire top of chip (?? why ??)
create_route_blockage -area 0 [expr $origin_phy_y] 4900 4900 \
    -layer M8

# Vertical strip just off the left edge of the phy block (why?)
create_route_blockage -area [expr $origin_phy_x-180] [expr $origin_phy_y-250] [expr $origin_phy_x-100] [expr $origin_phy_y+$phy_height] \
    -layer {M9}



