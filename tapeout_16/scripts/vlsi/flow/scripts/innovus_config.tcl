# Flowkit v0.2
################################################################################
# Tool attributes
#
#  Attributes used to drive tool behavior.  Most typically these are root level
#  attributes.  All root attributes can be listed by using 'report_obj -all' or
#  by category using 'report_obj -all -verbose'
#
#  Further attribute help can be obtained by using the command 'help <ATTRIBUTE>'
#
################################################################################

if {[get_db flow_step_current] ne ""} {
  puts "INFO: (FLOW-102) : Loading [file tail [info script]] with [get_db flow_step_current]"
} else {
  puts "INFO: (FLOW-102) : Loading [file tail [info script]]"
}

################################################################################
# ATTRIBUTES APPLIED BEFORE LOADING A LIBRARY OR DATABASE
################################################################################

##########################################################
# General attributes  [get_db -category init]
##########################################################
#-------------------------------------------------------------------------------

set_multi_cpu_usage -local_cpu  16

set_message -id  IMPSP-9099 -severity warn
################################################################################
# ATTRIBUTES APPLIED AFTER LOADING A LIBRARY OR DATABASE
################################################################################
if {[get_db current_design] eq ""} {return}

# Design attributes  [get_db -category design]
#-------------------------------------------------------------------------------
set_db design_process_node          16 
#set_db design_flow_effort           medium

##########################################################
# Timing attributes  [get_db -category timing && delaycalc]
##########################################################
#-------------------------------------------------------------------------------
set_db timing_analysis_cppr           both
set_db timing_analysis_type           ocv

#tsmc set_db timing_analysis_type           aocv

#tsmc  set_db delaycal_equivalent_waveform_model_type ecsm
#tsmc set_db delaycal_equivalent_waveform_model_propagation true
#set_db timing_analysis_aocv   true

set_db timing_enable_preset_clear_arcs true

##########################################################
# Extraction attributes  [get_db -category extract_rc]
##########################################################
#-------------------------------------------------------------------------------
if [is_flow -after_history flow:route] {
  set_db delaycal_enable_si           true
  set_db extract_rc_engine            post_route
}

##########################################################
# Placement attributes  [get_db -category place]
##########################################################
#-------------------------------------------------------------------------------
set_db place_global_place_io_pins  true

set_db opt_honor_fences true
set_db place_detail_dpt_flow true
set_db place_detail_color_aware_legal true
set_db place_global_solver_effort high
set_db place_detail_check_cut_spacing true
set_db place_global_cong_effort high

# M3 straps fix
set_db place_detail_m3_stripe_shrink 0
set_db place_detail_preroute_as_obs 3


# Tieoff attributes  [get_db -category add_tieoffs]
#-------------------------------------------------------------------------------
set_db add_tieoffs_cells              {TIEHBWP16P90 TIELBWP16P90}


##########################################################
# Optimization attributes  [get_db -category opt]
##########################################################
#-------------------------------------------------------------------------------

set_db opt_fix_fanout_load true
set_db opt_clock_gate_aware false
set_db opt_area_recovery true
set_db opt_post_route_area_reclaim setup_aware
set_db opt_fix_hold_verbose true


set_db opt_new_inst_prefix            "[get_db flow_report_name]_"

set_db opt_fix_hold_lib_cells "BUFFD1BWP16P90 BUFFD2BWP16P90 BUFFD3BWP16P90 BUFFD4BWP16P90 DEL025D1BWP16P90 DEL050D1BWP16P90 DEL075D1BWP16P90 DEL100D1BWP16P90 DEL200D1BWP16P90"

##########################################################
# Clock attributes  [get_db -category cts]
##########################################################
#-------------------------------------------------------------------------------
set_db cts_target_skew                .15
set_db cts_target_max_transition_time .15
set_db cts_update_io_latency false

set_db cts_use_inverters true
set_db cts_buffer_cells               "CKBD4BWP16P90LVT CKBD6BWP16P90LVT CKBD8BWP16P90LVT CKBD12BWP16P90LVT CKBD4BWP16P90LVT CKBD6BWP16P90LVT CKBD8BWP16P90LVT CKBD12BWP16P90LVT"
set_db cts_inverter_cells             "CKND4BWP16P90LVT CKND6BWP16P90LVT CKND8BWP16P90LVT CKND12BWP16P90LVT CKND4BWP16P90LVT CKND6BWP16P90LVT CKND8BWP16P90LVT CKND12BWP16P90LVT"
set_db cts_clock_gating_cells         "CKLHQD1BWP16P90LVT CKLHQD1BWP16P90LVT CKLNQD4BWP16P90LVT CKLNQD6BWP16P90LVT CKLNQD8BWP16P90LVT CKLNQD12BWP16P90LVT CKLNQD4BWP16P90LVT CKLNQD6BWP16P90LVT CKLNQD8BWP16P90LVT CKLNQD12BWP16P90LVT"


##########################################################
#- Route types definitions occur during the "init_floorplan" flow_step
##########################################################
if {[get_db route_types] ne ""} {
  set_db cts_route_type_leaf          leaf
  set_db cts_route_type_trunk         trunk
  set_db cts_route_type_top           top
}

### ENDCAPS
# parameters of FE_ADD_ENDCAPS
   set_db add_endcaps_boundary_tap               true
   set_db add_endcaps_left_top_corner     BOUNDARY_PCORNERBWP16P90
   set_db add_endcaps_left_top_edge       BOUNDARY_RIGHTBWP16P90
   set_db add_endcaps_top_edge           "BOUNDARY_PROW4BWP16P90 BOUNDARY_PROW3BWP16P90 BOUNDARY_PROW2BWP16P90 BOUNDARY_PROW1BWP16P90"
   set_db add_endcaps_right_top_edge      BOUNDARY_LEFTBWP16P90
   set_db add_endcaps_right_edge         BOUNDARY_LEFTBWP16P90
   set_db add_endcaps_right_bottom_edge   BOUNDARY_LEFTBWP16P90
   set_db add_endcaps_bottom_edge        "BOUNDARY_NROW4BWP16P90 BOUNDARY_NROW3BWP16P90 BOUNDARY_NROW2BWP16P90 BOUNDARY_NROW1BWP16P90"
   set_db add_endcaps_left_bottom_edge    BOUNDARY_RIGHTBWP16P90
   set_db add_endcaps_left_bottom_corner  BOUNDARY_NCORNERBWP16P90
   set_db add_endcaps_left_edge          BOUNDARY_RIGHTBWP16P90
   set_db add_endcaps_flip_y                      false


set_db TSMC_wellTapInterval 49.95
set_db add_well_taps_rule 24.975
set_db add_well_taps_bottom_tap_cell BOUNDARY_NTAPBWP16P90
set_db add_well_taps_top_tap_cell  BOUNDARY_PTAPBWP16P90
set_db add_well_taps_cell  TAPCELLBWP16P90
set_db add_well_taps_site_offset 32

set_db assign_pins_max_layer  7
set_db assign_pins_min_layer  2


# Filler attributes  [get_db -category add_fillers]
### changed the cell type from P20P90 to P16P90
#-------------------------------------------------------------------------------
set_db add_fillers_cells "DCAP64BWP16P90 DCAP64BWP16P90LVT DCAP64BWP16P90ULVT DCAP32BWP16P90 DCAP32BWP16P90LVT DCAP32BWP16P90ULVT DCAP16BWP16P90 DCAP16BWP16P90LVT DCAP16BWP16P90ULVT DCAP8BWP16P90 DCAP8BWP16P90LVT DCAP8BWP16P90ULVT DCAP4BWP16P90 DCAP4BWP16P90LVT DCAP4BWP16P90ULVT FILL3BWP16P90 FILL3BWP16P90LVT FILL3BWP16P90ULVT FILL2BWP16P90 FILL2BWP16P90LVT FILL2BWP16P90ULVT FILL1BWP16P90 FILL1BWP16P90LVT FILL1BWP16P90ULVT"             

##########################################################
# Routing attributes  [get_db -category route]
##########################################################
#-------------------------------------------------------------------------------
set_db route_design_bottom_routing_layer 2
set_db route_design_top_routing_layer 8

set_db route_design_antenna_diode_insertion true
set_db route_design_antenna_cell_name ANTENNABWP16P90 

# [stevo]: copied from NGC
### Don't use DFM-vias
set_db route_design_via_weight "*FBDS7_P1_* -1, *FBDS3_P2_* -1, *PBDS3B_P3_* -1, *FBR17_P4_* -1, *PBR7_P6_* -1, *FBS22_P7_* -1"
### Mx(a)+1/VIAx(a)/Mx(a)
set_db route_design_via_weight "*FBDS3B_P1_* 10, *FBDS25B_P2_* 9, *PBDS25B_P3_* 8, *FBR16_P4_* 7, *FBR7_P5_* 6, *PBR7U_P6_* 5, *FBS16_P7_* 4, *FBS3_P8_* 3, *PBS3B_P9_* 2, *_FAT_* 1"
### Mxd+1/VIAxd/Mx(a)
set_db route_design_via_weight "*FBDS14_P1_* 10, *FBDS4_P2_* 9, *FBR25B_P3_* 8, *FBR14_P4_* 7, *PBR3B_P5_* 6, *FBS24_P6_* 5, *FBS14_P7_* 4, *FBS4_P8_* 3, *FBR24_P3_* -1"
### Mxe+1/VIAxe/Mxe(d)
set_db route_design_via_weight "*FBDS10_P1_* 10, *PBDS40B_P2_* 9, *FBR20_P3_* 8, *PBR20B_P4_* 7, *PBR10B_P5_* 6, *PBR20_P6_* 5, *FBS10_P7_* 4, *PBS10U_P8_* 3, *PBS10B_P9_* 2, *FBR40_P3_* -1, *FBR10_P4_* -1"
### Mxc+1/VIAxc/Mx(a)
set_db route_design_via_weight "*FBR20_P1_* 10, *FBR40_P2_* 9, *FBS23_P3_* 8, *FBS12_P4_* 7, *PBS3B_P5_* 6"
## Mxy+1/VIAxy/Mx(a)
set_db route_design_via_weight "*FBR20_P1_* 10, *FBR30_P2_* 9, *PBR20B_P3_* 8, *PBR20U_P4_* 7, *PBRE_P5_* 6, *FBS23_P6_* 5, *PBS10B_P7_* 4, *PBS10U_P8_* 3"
## Mxy+1/VIAxy/Mxy,Mxc
set_db route_design_via_weight "*FBR20_P1_* 10, *FBR30_P2_* 9, *PBR20B_P3_* 8, *PBRE_P4_* 7, *FBS23_P5_* 6, *PBS10B_P6_* 5"
## My+1/VIAy/My
set_db route_design_via_weight "*FBDS27_P1_* 10, *FBS27_P2_* 9, *PBDS27_P3_* 8, *PBS27_P4_* 7, *PBDS27U_P5_* 6, *PBDS27B_1_P6_* 5, *PBDS27B_3_P7_* 4"
## My+1/VIAy/Mxy
set_db route_design_via_weight "*FBDS27_P1_* 10, *FBS27_P2_* 9, *FBDS10B_P3_* 8, *FBS10B_P4_* 7, *PBDS27_P5_* 6, *PBDS27B_1_P6_* 5, *PBDS27B_3_P7_* 4, *PBS10B_P8_* 3"
## My+1/VIAy/Mxe
set_db route_design_via_weight "*FBDS27_P1_* 10, *FBS27_P2_* 9, *FBDS29B_P3_* 8, *FBS20B_P4_* 7, *PBDS27_P5_* 6, *PBDS29B_1_P6_* 5, *PBDS29B_3_P7_* 4, *PBS20B_P8_* 3"

#set_db route_design_detail_on_grid_only {wire 4:7 via 3:6}
set_db route_design_detail_on_grid_only false
set_db route_design_with_via_in_pin {1:1}
set_db route_design_bottom_routing_layer 2
set_db route_design_detail_post_route_spread_wire false
#set_db route_design_via_weight {*_P* -1} 
# MANUALLY TRANSLATE (ERROR-11): Argument '-routeExpAdvancedTechnology' for command 'setNanoRouteMode' has no Novus defination and is removed, contact Cadence for support.

set_db route_design_reserve_space_for_multi_cut false
set_db route_design_with_si_driven false
set_db route_design_with_timing_driven true
# MANUALLY TRANSLATE (ERROR-11): Argument '-routeAutoPinAccessForBlockPin' for command 'setNanoRouteMode' has no Novus defination and is removed, contact Cadence for support.

set_db route_design_concurrent_minimize_via_count_effort high
set_db route_design_detail_post_route_swap_via true

set_db opt_consider_routing_congestion true



##########################################################
# power attributes  [get_db -category power]
##########################################################
#-------------------------------------------------------------------------------
## need to move this to mmmmc 
set_db  power_dynamic_power_view func-0p72v125c.setup_cworst_CCworst
set_db  power_leakage_power_view func-0p72v125c.setup_cworst_CCworst


proc write_lvs_netlist {} {
  set out_dir [file join [get_db flow_database_directory] [get_db flow_report_name]]
  set design  [get_db [current_design] .name]

  if {![file exists $out_dir]} {
    file mkdir $out_dir
  }

  # [stevo]: fix name issue, LVS doesn't like /
  update_names -map {{"/" "_"}}

  # [stevo]: write out netlist for LVS
  # [stevo]: might need to add pad frame endcap if we cut the corner cell
  # [stevo]: also, last time we added -flat option because SRAMs were messed up
  write_netlist \
    [file join $out_dir $design.lvs.v] \
    -top_module_first \
    -top_module $design \
    -exclude_leaf_cells \
    -phys \
    -exclude_insts_of_cells " \
      ICOVL_CODH_OD_20140702 \
      ICOVL_CODV_OD_20140702 \
      ICOVL_IMP1_OD_20140702 \
      ICOVL_IMP2_OD_20140702 \
      ICOVL_IMP3_OD_20140702 \
      ICOVL_PMET_OD_20140702 \
      ICOVL_VT2_OD_20140702 \
      ICOVL_PO_OD_20140702 \
      ICOVL_CPO_OD_20140702 \
      ICOVL_CMD_OD_20140702 \
      ICOVL_M0OD_OD_20140702 \
      ICOVL_M0OD_PO_20140702 \
      ICOVL_M0PO_CMD_20140702 \
      ICOVL_M0PO_M0OD_20140702 \
      ICOVL_M0PO_PO_20140702 \
      ICOVL_M1L1_M0OD_20140702 \
      ICOVL_M1L2_M1L1_20140702 \
      ICOVL_M2L1_M1L1_20140702 \
      ICOVL_M2L2_M2L1_20140702 \
      ICOVL_M3L1_M2L1_20140702 \
      ICOVL_M3L2_M3L1_20140702 \
      ICOVL_M4L1_M3L1_20140702 \
      ICOVL_M5L1_M4L1_20140702 \
      ICOVL_M6L1_M5L1_20140702 \
      ICOVL_M7L1_M6L1_20140702 \
      ICOVL_V0H1_M0OD_20140702 \
      ICOVL_V0H1_M1L1_20140702 \
      ICOVL_V0H2_M1L1_20140702 \
      ICOVL_V0H2_M1L2_20140702 \
      ICOVL_V1H1_M1L1_20140702 \
      ICOVL_V1H1_M2L1_20140702 \
      ICOVL_V2H1_M2L1_20140702 \
      ICOVL_V2H1_M3L1_20140702 \
      ICOVL_V3H1_M3L1_20140702 \
      ICOVL_V3H1_M3L2_20140702 \
      ICOVL_V4H1_M4L1_20140702 \
      ICOVL_V4H1_M5L1_20140702 \
      ICOVL_V5H1_M5L1_20140702 \
      ICOVL_V5H1_M6L1_20140702 \
      ICOVL_V6H1_M6L1_20140702 \
      ICOVL_V6H1_M7L1_20140702 \
      ICOVL_PO_CPODE_20140702 \
      ICOVL_CPODE_OD_20140702 \
      N16_DTCD_FEOL_20140707 \
      N16_DTCD_BEOL_M1_20140707 \
      N16_DTCD_BEOL_M2_20140707 \
      N16_DTCD_BEOL_M3_20140707 \
      N16_DTCD_BEOL_M4_20140707 \
      N16_DTCD_BEOL_M5_20140707 \
      N16_DTCD_BEOL_M6_20140707 \
      N16_DTCD_BEOL_M7_20140707 \
      N16_DTCD_BEOL_V1_20140707 \
      N16_DTCD_BEOL_V2_20140707 \
      N16_DTCD_BEOL_V3_20140707 \
      N16_DTCD_BEOL_V4_20140707 \
      N16_DTCD_BEOL_V5_20140707 \
      N16_DTCD_BEOL_V6_20140707 \
      PFILLER10080 \
      PFILLER01008 \
      PFILLER00048 \
      PFILLER00001 \
      PCORNER \
      BOUNDARY_PCORNERBWP16P90 \
      BOUNDARY_PROW4BWP16P90 \
      BOUNDARY_PROW3BWP16P90 \
      BOUNDARY_PROW2BWP16P90 \
      BOUNDARY_PROW1BWP16P90 \
      BOUNDARY_LEFTBWP16P90 \
      BOUNDARY_NROW4BWP16P90 \
      BOUNDARY_NROW3BWP16P90 \
      BOUNDARY_NROW2BWP16P90 \
      BOUNDARY_NROW1BWP16P90 \
      BOUNDARY_NCORNERBWP16P90 \
      BOUNDARY_RIGHTBWP16P90 \
      DCAP64BWP16P90 \
      DCAP64BWP16P90LVT \
      DCAP64BWP16P90ULVT \
      DCAP32BWP16P90 \
      DCAP32BWP16P90LVT \
      DCAP32BWP16P90ULVT \
      DCAP16BWP16P90 \
      DCAP16BWP16P90LVT \
      DCAP16BWP16P90ULVT \
      DCAP8BWP16P90 \
      DCAP8BWP16P90LVT \
      DCAP8BWP16P90ULVT \
      DCAP4BWP16P90 \
      DCAP4BWP16P90LVT \
      DCAP4BWP16P90ULVT \
      FILL3BWP16P90 \
      FILL3BWP16P90LVT \
      FILL3BWP16P90ULVT \
      FILL2BWP16P90 \
      FILL2BWP16P90LVT \
      FILL2BWP16P90ULVT \
      FILL1BWP16P90 \
      FILL1BWP16P90LVT \
      FILL1BWP16P90ULVT \
  " 
}
