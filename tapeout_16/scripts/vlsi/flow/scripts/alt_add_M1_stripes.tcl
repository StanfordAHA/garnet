# Designed to be used in floorplanning, see "gen_floorplan.tcl"
# set ::USE_ALTERNATIVE_M1_STRIPE_GENERATION 0
# source ../../scripts/alt_add_M1_stripes.tcl

proc alt_add_M1_stripes {} {
##############################################################################
##############################################################################
##############################################################################
# ADD_STRIPE EXPERIMENTS


#     puts "@file_info gen_floorplan.tcl/gen_power: add_stripes M1"
#     # standard cell rails in M1
#     # [stevo]: no vias
#     set_db add_stripes_stacked_via_bottom_layer M2
#     set_db add_stripes_stacked_via_top_layer M2
#     add_stripes \
#       -pin_layer M1   \
#       -over_pins 1   \
#       -block_ring_top_layer_limit M1   \
#       -max_same_layer_jog_length 3.6   \
#       -pad_core_ring_bottom_layer_limit M1   \
#       -pad_core_ring_top_layer_limit M1   \
#       -spacing 1.8   \
#       -master "TAPCELL* BOUNDARY*"   \
#       -merge_stripes_value 0.045   \
#       -direction horizontal   \
#       -layer M1   \
#       -area {} \
#       -block_ring_bottom_layer_limit M1   \
#       -width pin_width   \
#       -nets {VSS VDD}
#     echo M1 Stripes Complete


    ########################################################################
    # Tap cells take forever (6 hours +)
    # There are about 2.5M of them.
    # [09/20 10:21:20 380s] Inserted 2,437,965 well-taps <TAPCELLBWP16P90>
    #                       cells (prefix WELLTAP).
    #
    # What if we try multiple vertical strips of stripes?
    # Die goes from 0,0 (BL) to 4900,4900 (TR)
    # Let's try horiz strips 0-2000 (cgra), 2000-4000 (gb/icovl), 4000-4900 (butterphy)
    #
    # floorplan.tcl: create_floorplan -die_size 4900.0 4900.0 100 100 100 100
    # - I think this means the die is 4900x4900 with 100u margins all round
    #   the inside. So design boundary would be ? 100 100   4800 4800 ?

    puts "@file_info gen_floorplan.tcl/gen_power: add_stripes M1 - TAPCELL"
    #
    puts "@file_info top strip: butterphy"
    # standard cell rails in M1
    # [stevo]: no vias
    set_db add_stripes_stacked_via_bottom_layer M2
    set_db add_stripes_stacked_via_top_layer M2
    add_stripes \
      -pin_layer M1   \
      -over_pins 1   \
      -block_ring_top_layer_limit M1   \
      -max_same_layer_jog_length 3.6   \
      -pad_core_ring_bottom_layer_limit M1   \
      -pad_core_ring_top_layer_limit M1   \
      -spacing 1.8   \
      -master "TAPCELL*"   \
      -merge_stripes_value 0.045   \
      -direction horizontal   \
      -layer M1   \
      -area { 100 4000    4800 4800 } \
      -block_ring_bottom_layer_limit M1   \
      -width pin_width   \
      -nets {VSS VDD}
    echo M1 TAPCELL Stripes Complete - top strip


# **ERROR: (IMPPP-209): The edge (4900.000000 0.000000 0.000000
# 4000.000000) in the rectilinear region in -area option is
# slanted. will ignore it.


# [09/22 12:22:37 545s] Use option
# add_stripes_extend_to_closest_target {area_boundary} if stripes must
# be generated in specified area.
# 
# -extend_to design_boundary

# -area and -extend_to design_boundary are mutually exclusive. The
# following error is issued on them being used together:
# 
# You cannot specify stripes over design boundary and set an area
# constraint. Instead, specify area to cover design boundary.
# 


    #
    puts "@file_info: middle strip: gb, icovl"
    # standard cell rails in M1
    # [stevo]: no vias
    set_db add_stripes_stacked_via_bottom_layer M2
    set_db add_stripes_stacked_via_top_layer M2
    add_stripes \
      -pin_layer M1   \
      -over_pins 1   \
      -block_ring_top_layer_limit M1   \
      -max_same_layer_jog_length 3.6   \
      -pad_core_ring_bottom_layer_limit M1   \
      -pad_core_ring_top_layer_limit M1   \
      -spacing 1.8   \
      -master "TAPCELL*"   \
      -merge_stripes_value 0.045   \
      -direction horizontal   \
      -layer M1   \
      -area { 100 2000    4800 4000 } \
      -block_ring_bottom_layer_limit M1   \
      -width pin_width   \
      -nets {VSS VDD}
    echo M1 TAPCELL Stripes Complete - middle strip
    #
    puts "@file_info: bottom strip: cgra"
    # standard cell rails in M1
    # [stevo]: no vias
    set_db add_stripes_stacked_via_bottom_layer M2
    set_db add_stripes_stacked_via_top_layer M2
    add_stripes \
      -pin_layer M1   \
      -over_pins 1   \
      -block_ring_top_layer_limit M1   \
      -max_same_layer_jog_length 3.6   \
      -pad_core_ring_bottom_layer_limit M1   \
      -pad_core_ring_top_layer_limit M1   \
      -spacing 1.8   \
      -master "TAPCELL*"   \
      -merge_stripes_value 0.045   \
      -direction horizontal   \
      -layer M1   \
      -area { 100    100    4800 2000 } \
      -block_ring_bottom_layer_limit M1   \
      -width pin_width   \
      -nets {VSS VDD}
    echo M1 TAPCELL Stripes Complete - bottom strip


    # Boundary cells are fast ish (15m)
    # [09/22 08:57:46    530s] @file_info gen_floorplan.tcl/gen_power: add_stripes M1 - BOUNDARY
    # [09/22 09:12:58   1444s] M1 BOUNDARY Stripes Complete
    #
    puts "@file_info gen_floorplan.tcl/gen_power: add_stripes M1 - BOUNDARY"
    # standard cell rails in M1
    # [stevo]: no vias
    set_db add_stripes_stacked_via_bottom_layer M2
    set_db add_stripes_stacked_via_top_layer M2
    add_stripes \
      -pin_layer M1   \
      -over_pins 1   \
      -block_ring_top_layer_limit M1   \
      -max_same_layer_jog_length 3.6   \
      -pad_core_ring_bottom_layer_limit M1   \
      -pad_core_ring_top_layer_limit M1   \
      -spacing 1.8   \
      -master "BOUNDARY*"   \
      -merge_stripes_value 0.045   \
      -direction horizontal   \
      -layer M1   \
      -area {} \
      -block_ring_bottom_layer_limit M1   \
      -width pin_width   \
      -nets {VSS VDD}
    echo M1 BOUNDARY Stripes Complete
}