# Copied/translated to common-ui
# Original was in "gen_floorplan.tcl"
# MUST source stylust-compatibility procs!

# source $env(GARNET_HOME)/mflowgen/common/scripts/stylus-compatibility-procs.tcl
proc gen_power {} {

    delete_inst -inst FE_FILLER_*
    delete_inst -inst WELLTAP_*
    delete_inst -inst ENDCAP*

    # eval_legacy {setEndCapMode
    setEndCapMode \
     -rightEdge BOUNDARY_LEFTBWP16P90 \
     -leftEdge BOUNDARY_RIGHTBWP16P90 \
     -leftBottomCorner BOUNDARY_NCORNERBWP16P90 \
     -leftTopCorner BOUNDARY_PCORNERBWP16P90 \
     -rightTopEdge FILL3BWP16P90 \
     -rightBottomEdge FILL3BWP16P90 \
     -topEdge "BOUNDARY_PROW3BWP16P90 BOUNDARY_PROW2BWP16P90" \
     -bottomEdge "BOUNDARY_NROW3BWP16P90 BOUNDARY_NROW2BWP16P90" \
     -fitGap true \
     -boundary_tap true
    
    # eval_legacy {set_well_tap_mode
    set_well_tap_mode \
     -rule 5.04 \
     -bottom_tap_cell BOUNDARY_NTAPBWP16P90 \
     -top_tap_cell BOUNDARY_PTAPBWP16P90 \
     -cell TAPCELLBWP16P90
    
    # How long does this take? Looks like about 3 min, no big.
    # date >> tmp.date; cat tmp.date
    # echo add_endcaps >> tmp.date; cat tmp.date
    # add_endcaps; date >> tmp.date; cat tmp.date
    add_endcaps

    # [stevo]: can't place these close to endcaps
    foreach inst [get_db insts -if {.is_macro == true}] {
      puts [get_db $inst .name]
      create_place_blockage -inst [get_db $inst .name] -outer_ring_by_side {3.5 2.5 3.5 2.5} -name TAPBLOCK
    }
    foreach inst [get_db insts -if {.name == core_clamp*}] {
      puts [get_db $inst .name]
      create_place_blockage -inst [get_db $inst .name] -outer_ring_by_side {3.5 2.5 3.5 2.8} -name TAPBLOCK
    }
    foreach inst [get_db insts -if {.name == ifid_icovl_* || .name == ifid_dtcd_feol_*}] {
      puts [get_db $inst .name]
      create_place_blockage -inst [get_db $inst .name] -outer_ring_by_side {9.5 8.5 9.5 8.5} -name TAPBLOCK
    }
    # This one takes about two minutes
    add_well_taps \
      -cell_interval 10.08 \
      -in_row_offset 5
    # eval_legacy {deletePlaceBlockage  TAPBLOCK}
    deletePlaceBlockage  TAPBLOCK

#     date >> tmp.date; cat tmp.date
#     echo add_welltaps >> tmp.date; cat tmp.date
#     date >> tmp.date; cat tmp.date

    puts "@file_info gen_floorplan.tcl/gen_power: add_rings"
    # [stevo]: add rings around everything in M2/M3
    # set_db add_rings_stacked_via_top_layer M9
    # set_db add_rings_stacked_via_bottom_layer M1
    setAddRingMode -stacked_via_top_layer M9
    setAddRingMode -stacked_via_bottom_layer M1
    add_rings \
      -type core_rings   \
      -jog_distance 0.045   \
      -threshold 0.045   \
      -follow core   \
      -layer {bottom M2 top M2 right M3 left M3}   \
      -width 1.96   \
      -spacing 0.84   \
      -offset 1.4   \
      -nets {VDD VSS VDD VSS VDD VSS}

    #NB add a ring around the mdll block
    #add_rings -nets {VDD VSS VDD VSS VDD VSS} -around user_defined -user_defined_region {93.1435 4337.26 93.1435 4804.371 1174.5765 4804.371 1174.5765 4337.26 93.1435 4337.26} -type block_rings -layer {top M2 bottom M2 left M3 right M3} -width {top 1.96 bottom 1.96 left 1.96 right 1.96} -spacing {top 0.84 bottom 0.84 left 0.84 right 0.84} -offset {top 1.4 bottom 1.4 left 1.4 right 1.4} -center 0 -extend_corners {} -threshold 0 -jog_distance 0 -snap_wire_center_to_grid none

    puts "@file_info gen_floorplan.tcl/gen_power: route_pads 1"
    # [stevo]: route pads to this ring
    route_special -connect {pad_pin}  \
      -layer_change_range { M2(2) M8(8) }  \
      -pad_pin_port_connect {all_port one_geom}  \
      -pad_pin_target {ring}  \
      -delete_existing_routes  \
      -pad_pin_layer_range { M3(3) M4(4) }  \
      -crossover_via_layer_range { M2(2) M8(8) }  \
      -nets { VSS VDD }  \
      -allow_layer_change 1  \
      -target_via_layer_range { M2(2) M8(8) } \
      -inst [get_db [get_db insts *IOPAD*VDD_*] .name]

    # FIXME/NOTE
    # This does NOTHING b/c [get_db insts *IOPAD*VDDANA_*] = NIL
    # "**WARN: (IMPSR-4033):   SRoute cannot perform selected/named blocks because there is no selected/named block indicated."
    puts "@file_info gen_floorplan.tcl/gen_power: route_pads 2"
    # [stevo]: route pads to this ring
    route_special -connect {pad_pin}  \
      -layer_change_range { M2(2) M8(8) }  \
      -pad_pin_port_connect {all_port one_geom}  \
      -pad_pin_target {ring}  \
      -pad_pin_layer_range { M3(3) M4(4) }  \
      -crossover_via_layer_range { M2(2) M8(8) }  \
      -nets { VSS VDD }  \
      -allow_layer_change 1  \
      -target_via_layer_range { M2(2) M8(8) } \
      -inst [get_db [get_db insts *IOPAD*VDDANA_*] .name]

    puts "@file_info: ----------------"
    puts "@file_info: gen_floorplan.tcl/gen_power: add_stripes M1"
    puts "@file_info: - expect this to take like 7 hours"
    puts -nonewline "@file_info: Time now "; date +%H:%M

    puts "@file_info: trying new hack that should shorten the 7 hours significantly"
    puts "@file_info: turning off DRC during M1 stripe generation ONLY"

    # set orig_asid_value [ get_db add_stripes_ignore_drc ]
    set orig_asid_value [ getAddStripeMode -ignore_DRC ]

    #set_db add_stripes_ignore_drc true
    setAddStripeMode -ignore_DRC true

    # set t [ get_db add_stripes_ignore_drc ]
    set t [ getAddStripeMode -ignore_DRC ]
    puts "@file_info: add_stripes_ignore_drc=$orig_asid_value => add_stripes_ignore_drc=$t"

    # standard cell rails in M1
    # [stevo]: no vias

    # set_db add_stripes_stacked_via_bottom_layer M2
    # set_db add_stripes_stacked_via_top_layer M2
    setAddStripeMode  -stacked_via_bottom_layer M2
    setAddStripeMode  -stacked_via_top_layer M2

    date >> tmp.date; cat tmp.date
    echo add_stripes >> tmp.date; cat tmp.date
    # begin 752am 
    # Note this can take 2-3 hours
    add_stripes \
      -pin_layer M1   \
      -over_pins 1   \
      -block_ring_top_layer_limit M1   \
      -max_same_layer_jog_length 3.6   \
      -pad_core_ring_bottom_layer_limit M1   \
      -pad_core_ring_top_layer_limit M1   \
      -spacing 1.8   \
      -master "TAPCELL* BOUNDARY*"   \
      -merge_stripes_value 0.045   \
      -direction horizontal   \
      -layer M1   \
      -area {} \
      -block_ring_bottom_layer_limit M1   \
      -width pin_width   \
      -nets {VSS VDD}
    date >> tmp.date; cat tmp.date
#--BOOKMARK--
    #----------------------------------------------------------------
    echo M1 Stripes Complete
    puts "@file_info: - M1 Stripes Complete"
    puts -nonewline "@file_info: Time now "; date +%H:%M
    puts "@file_info: ----------------"
    # set_db add_stripes_ignore_drc true
    puts "@file_info: restoring add_stripe DRC"

    # set_db add_stripes_ignore_drc $orig_asid_value
    # set t [ get_db add_stripes_ignore_drc ]
    setAddStripeMode -ignore_DRC $orig_asid_value
    set t [ getAddStripeMode -ignore_DRC ]

    puts "@file_info: NOW: add_stripes_ignore_drc=$t"
    puts "@file_info: ----------------"
    #----------------------------------------------------------------

    ####NB DIS# Add M2 horizontal stripes matching M1, but narrower (0.064)
    ####NB DIS# took 5 minutes 9 seconds when DRC checking was off, 5 minutes 55 seconds with DRC checking
    ####NB DISset_db add_stripes_stacked_via_bottom_layer M1
    ####NB DISset_db add_stripes_stacked_via_top_layer M3
    ####NB DISadd_stripes \
    ####NB DIS  -pin_layer M1   \
    ####NB DIS  -over_pins 1   \
    ####NB DIS  -block_ring_top_layer_limit M1   \
    ####NB DIS  -max_same_layer_jog_length 3.6   \
    ####NB DIS  -pad_core_ring_bottom_layer_limit M1   \
    ####NB DIS  -pad_core_ring_top_layer_limit M1   \
    ####NB DIS  -spacing 1.8   \
    ####NB DIS  -master "TAPCELL* BOUNDARY*"   \
    ####NB DIS  -merge_stripes_value 0.045   \
    ####NB DIS  -direction horizontal   \
    ####NB DIS  -layer M2   \
    ####NB DIS  -block_ring_bottom_layer_limit M1   \
    ####NB DIS  -width 0.064   \
    ####NB DIS  -area {}   \
    ####NB DIS  -nets {VSS VDD}
    ####NB DISecho M2 Stripes Complete

    puts "@file_info gen_floorplan.tcl/gen_power: add_rings 2"

    # set_db add_rings_stacked_via_top_layer M9
    # set_db add_rings_stacked_via_bottom_layer M3
    setAddRingMode -stacked_via_top_layer M9
    setAddRingMode -stacked_via_bottom_layer M3
    add_rings \
      -type core_rings   \
      -jog_distance 0.045   \
      -threshold 0.045   \
      -follow core   \
      -layer {bottom M8 top M8 right M9 left M9}   \
      -width 2.1   \
      -spacing 0.77   \
      -offset 1.4   \
      -nets {VDD VSS VDD VSS VDD VSS}

    puts "@file_info gen_floorplan.tcl/gen_power: add_boundary,power_mesh"
    # [stevo]: now place boundary fiducials, avoiding routes between rings and power IO cells
    # if we do this earlier, the M2/3 rings do funky stuff
    add_boundary_fiducials; # See alignment-cells.tcl for proc
    add_power_mesh_colors
}
