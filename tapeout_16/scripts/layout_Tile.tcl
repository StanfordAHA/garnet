set lef_file [list /tsmc16/download/TECH16FFC/N16FF_PRTF_Cad_1.2a/PR_tech/Cadence/LefHeader/Standard/VHV/N16_Encounter_9M_2Xa1Xd3Xe2Z_UTRDL_9T_PODE_1.2a.tlef \
/sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/LEF/ts1n16ffcllsblvtc512x16m8s_130a_m4xdh.lef \
/tsmc16/TSMCHOME/digital/Back_End/lef/tcbn16ffcllbwp16p90pm_100a/lef/tcbn16ffcllbwp16p90pm.lef \
/tsmc16/TSMCHOME/digital/Back_End/lef/tcbn16ffcllbwp16p90_100a/lef/tcbn16ffcllbwp16p90.lef ]
 

###################################################################################
source ../../scripts/helper_funcs.tcl
source ../../scripts/params.tcl
set design $::env(DESIGN)

set init_import_mode {-treatUndefinedCellAsBbox 0 -keepEmptyModule 1} 
set init_verilog results_syn/syn_out.v 
set init_design_netlisttype {Verilog}
set init_design_settop {0}
set init_lef_file $lef_file

if $::env(PWR_AWARE) {
} else {
   set init_pwr_net VDD
   set init_gnd_net VSS
}

set init_assign_buffer {0} 
set init_mmmc_file ../../scripts/mmmc.tcl
set delaycal_use_default_delay_limit {1000}
set delaycal_default_net_delay {1000.0ps} 
set delaycal_default_net_load {2.0pf}
set delaycal_input_transition_delay {50ps}

setLibraryUnit -time 1ns

init_design


if $::env(PWR_AWARE) {
   read_power_intent -1801 ../../scripts/upf_$::env(DESIGN).tcl 
   commit_power_intent
   write_power_intent -1801 upf.out
}

if $::env(PWR_AWARE) {
   globalNetConnect VDD_SW -type tiehi -powerdomain TOP
   globalNetConnect VDD    -type tiehi -powerdomain AON
   globalNetConnect VSS -type tielo
   globalNetConnect VDD -type pgpin -pin VPP -inst *
   globalNetConnect VSS -type pgpin -pin VBB -inst *
} else {
   globalNetConnect VDD -type pgpin -pin VDD -inst *
   globalNetConnect VDD -type tiehi
   globalNetConnect VSS -type pgpin -pin VSS -inst *
   globalNetConnect VSS -type tielo
   globalNetConnect VDD -type pgpin -pin VPP -inst *
   globalNetConnect VSS -type pgpin -pin VBB -inst *
}

setNanoRouteMode -routeTopRoutingLayer $max_route_layer($design)
setTrialRouteMode -maxRouteLayer $max_route_layer($design)
setPinAssignMode -maxLayer $max_route_layer($design)
setDesignMode -process 16


set tile_info [calculate_tile_info $Tile_PE_util $Tile_MemCore_util $min_tile_height $min_tile_width $tile_x_grid $tile_y_grid $tile_stripes_array]
set width [dict get $tile_info $design,width]
set height [dict get $tile_info $design,height]

floorPlan -site core -s $width $height 0 0 0 0
createRouteBlk -name cut0 -cutLayer all -box [list 0 [expr $height - 0.5] $width [expr $height + 1]]
createRouteBlk -name cut1 -cutLayer all -box [list 0 -1 $width 0.5]

#createRouteBlk -name cut01M1 -layer M1 -cutLayer all -box [list 0 [expr $height - 0.5] $width [expr $height + 1]]
#createRouteBlk -name cut02M1 -layer M1 -cutLayer all -box [list 0 -1 $width 0.5]
#Prevent M9 vertical strap from getting too close to edge of tile
createRouteBlk -name cutM9 -pgnetonly -layer M9 -cutlayer all -box [list [expr $width - 2] 0 $width $height]

source ../../scripts/tile_io_place.tcl
set ns_io_offset [expr ($width - $ns_io_width) / 2]
set ew_io_offset [expr ($height - $ew_io_width) / 2]
place_ios $width $height $ns_io_offset $ew_io_offset

set tile_id_y_coords [get_property [get_ports {*tile_id* hi* lo*}] y_coordinate]
set tile_id_y_coords [lsort -real $tile_id_y_coords]
set tile_id_min_y [lindex $tile_id_y_coords 0]
set tile_id_max_y [lindex $tile_id_y_coords end]
set tile_id_max_x 0.35

if $::env(PWR_AWARE) {
   ##AON Region Bounding Box
   set offset 4.5 
   set aon_width 14
   set aon_height 11 
   set aon_height_snap [expr ceil($aon_height/$polypitch_y)*$polypitch_y]
   set aon_lx [expr $width/2 - $aon_width/2 + $offset]
   set aon_lx_snap [expr ceil($aon_lx/$polypitch_x)*$polypitch_x]
   set aon_ux [expr $width/2 + $aon_width/2 + $offset - 3]
   set aon_ux_snap [expr ceil($aon_ux/$polypitch_x)*$polypitch_x]
   modifyPowerDomainAttr AON -box $aon_lx_snap  [expr $height - $aon_height_snap - 10*$polypitch_y] $aon_ux_snap [expr $height - 10*$polypitch_y]  -minGaps $polypitch_y $polypitch_y [expr $polypitch_x*6] [expr $polypitch_x*6]
} else {
    # TODO(kongty): I just used same aon_width for block w/o power domain
    set aon_width 14
}


# Place SRAMs, if any
set srams [get_cells -hier * -filter "ref_name=~TS1N*"]
if {$srams != ""} {
  set bank_height 1
  set sram_width 26.195
  set sram_height 69.648
  ### HALO MARGIN CALCULATIONS
  set target_margin 3
  set halo_margin_b [snap_to_grid $target_margin 0.576 0]
  set halo_margin_l [snap_to_grid $target_margin 0.09 0]
  set snapped_height [snap_to_grid $sram_height 0.576 0]
  set height_diff [expr $snapped_height - $sram_height]
  set halo_margin_t [snap_to_grid $target_margin 0.576 $height_diff]
  set snapped_width [snap_to_grid $sram_width 0.09 0]
  set width_diff [expr $snapped_width - $sram_width]
  set halo_margin_r [snap_to_grid $target_margin 0.09 $width_diff]
  ### END HALO MARGIN CALCULATIONS
  set sram_spacing_x_even [snap_to_grid [expr $aon_width + 34] 0.09 $width_diff]
  set sram_spacing_x_odd 0
  set sram_spacing_y 0
  set total_sram_width [expr 2*$sram_width + $sram_spacing_x_even]
  set sram_start_x [snap_to_grid [expr ($width - $total_sram_width) / 2] 0.09 0]
  set sram_start_y [snap_to_grid [expr ($height - $sram_height) / 2] 0.576 0]
  
  glbuf_sram_place $srams $sram_start_x $sram_start_y $sram_spacing_x_even $sram_spacing_x_odd $sram_spacing_y $bank_height $sram_height $sram_width 0 0 1 0
  addHaloToBlock -allMacro $halo_margin_l $halo_margin_b $halo_margin_r $halo_margin_t
}

set bw 0.576
createPlaceBlockage -name botpb -box 0 0 $width $bw
createPlaceBlockage -name toppb -box 0 [expr $height - $bw] $width $height
createPlaceBlockage -name rightpb -box [expr $width - 0.9] 0 $width $height

if $::env(PWR_AWARE) {
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
 -boundary_tap false 

 # For both PE and Mem Tile
 addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst top_endcap_tap_1
 addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst top_endcap_tap_2
 addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst top_endcap_tap_3

 placeInst top_endcap_tap_1 -fixed [expr 2.2 + 1*10.08]  [expr $height - 2*0.576] 
 placeInst top_endcap_tap_2 -fixed [expr 2.2 + 3*10.08]  [expr $height - 2*0.576] 
 placeInst top_endcap_tap_3 -fixed [expr 2.2 + 5*10.08]  [expr $height - 2*0.576] 

 addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst bot_endcap_tap_1
 addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst bot_endcap_tap_2
 addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst bot_endcap_tap_3

 placeInst bot_endcap_tap_1 -fixed [expr 2.2 + 1*10.08]  0.576 
 placeInst bot_endcap_tap_2 -fixed [expr 2.2 + 3*10.08]  0.576 
 placeInst bot_endcap_tap_3 -fixed [expr 2.2 + 5*10.08]  0.576 

  if [regexp Tile_PE  $::env(DESIGN)] {
    addEndCap
    addPowerSwitch -column \-powerDomain TOP  \-leftOffset 10.465  \-horizontalPitch 30.24 \-checkerBoard \-loopBackAtEnd -enableNetOut PSenableNetOut  -noFixedStdCellOverlap
  } else {
    # Mem Tile Only 
    addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst top_endcap_tap_4
    addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst top_endcap_tap_5
    addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst top_endcap_tap_6
    addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst top_endcap_tap_7
    addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst top_endcap_tap_8

    placeInst top_endcap_tap_4 -fixed [expr 2.2 + 7*10.08]  [expr $height - 2*0.576] 
    placeInst top_endcap_tap_5 -fixed [expr 2.2 + 9*10.08]  [expr $height - 2*0.576] 
    placeInst top_endcap_tap_6 -fixed [expr 2.2 + 11*10.08] [expr $height - 2*0.576] 
    placeInst top_endcap_tap_7 -fixed [expr 2.2 + 13*10.08] [expr $height - 2*0.576] 
    placeInst top_endcap_tap_8 -fixed [expr 2.2 + 15*10.08] [expr $height - 2*0.576] 

    addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst bot_endcap_tap_4
    addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst bot_endcap_tap_5
    addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst bot_endcap_tap_6
    addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst bot_endcap_tap_7
    addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst bot_endcap_tap_8

    placeInst bot_endcap_tap_4 -fixed [expr 2.2 + 7*10.08]  0.576
    placeInst bot_endcap_tap_5 -fixed [expr 2.2 + 9*10.08]  0.576
    placeInst bot_endcap_tap_6 -fixed [expr 2.2 + 11*10.08] 0.576
    placeInst bot_endcap_tap_7 -fixed [expr 2.2 + 13*10.08] 0.576
    placeInst bot_endcap_tap_8 -fixed [expr 2.2 + 15*10.08] 0.576
    
    addEndCap
    addPowerSwitch -column \-powerDomain TOP  \-leftOffset 0.385  \-horizontalPitch 30.24 \-checkerBoard \-loopBackAtEnd -enableNetOut PSenableNetOut  -noFixedStdCellOverlap
  }
  
} else {
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

 set_well_tap_mode \
  -rule 6 \
  -bottom_tap_cell BOUNDARY_NTAPBWP16P90 \
  -top_tap_cell BOUNDARY_PTAPBWP16P90 \
  -cell TAPCELLBWP16P90
 addEndCap
}

foreach layer {M7 M8 M9} {
   set power_nets {VDD VSS VDD_SW}
   set aon_power_nets {VDD VSS}
   set sw_nets {VDD_SW}
   set start [dict get $tile_info $layer,start]
   set spacing [dict get $tile_info $layer,spacing]
   set s2s [dict get $tile_info $layer,s2s]
   set stripe_width [dict get $tile_info $layer,width]
   set dir [dict get $tile_info $layer,direction]
   if $::env(PWR_AWARE) {
     addStripe -direction $dir -start $start -create_pins 1 -layer $layer -nets $aon_power_nets -width $stripe_width -spacing $spacing -set_to_set_distance $s2s

     if [regexp M8 $layer] {
        createRouteBlk -name cut_lft -layer $layer -cutLayer all -box [list 0                 0 3      $height]
        createRouteBlk -name cut_rgt -layer $layer -cutLayer all -box [list [expr $width - 3] 0 $width $height]
     } else {
        createRouteBlk -name cut_top -layer $layer -cutLayer all -box [list 0 [expr $height-3] $width $height]
        createRouteBlk -name cut_bot -layer $layer -cutLayer all -box [list 0 0                $width 3      ]
    }
     addStripe -direction $dir -start [expr $start + ($spacing + $stripe_width)*2] -create_pins 0 -layer $layer -nets $sw_nets -width $stripe_width -spacing $spacing -set_to_set_distance $s2s
    if [regexp M8 $layer] {
     deleteRouteBlk -name cut_lft
     deleteRouteBlk -name cut_rgt
    } else {
     deleteRouteBlk -name cut_top
     deleteRouteBlk -name cut_bot
    }
     selectObject Group AON

     addStripe -direction $dir -start $start -create_pins 1 -layer $layer -nets $aon_power_nets -width $stripe_width -spacing $spacing -set_to_set_distance $s2s -over_power_domain 1
     editPowerVia -delete_vias true
   } else {
     addStripe -direction $dir -start $start -create_pins 1 -layer $layer -nets $aon_power_nets -width $stripe_width -spacing $spacing -set_to_set_distance $s2s
     editPowerVia -delete_vias true
   }
}

sroute -allowJogging 0 -allowLayerChange 0 -floatingStripeTarget stripe

editPowerVia -delete_vias true

sroute -allowJogging 0 -allowLayerChange 0 -floatingStripeTarget stripe

editPowerVia -skip_via_on_pin {} -add_vias true -orthogonal_only true -top_layer 9 -bottom_layer 8
editPowerVia -skip_via_on_pin {} -add_vias true -orthogonal_only true -top_layer 8 -bottom_layer 7
editPowerVia -skip_via_on_pin {} -add_vias true -orthogonal_only true -top_layer 7 -bottom_layer 1
sroute -allowJogging 0 -allowLayerChange 0 -connect  {secondaryPowerPin} -secondaryPinNet VDD -powerDomains TOP

deleteRouteBlk -name cut0
deleteRouteBlk -name cut1
#deleteRouteBlk -name cut01M1
#deleteRouteBlk -name cut02M1
deleteRouteBlk -name cutM9

if $::env(PWR_AWARE) {
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
 
 set_well_tap_mode \
  -rule 6 \
  -bottom_tap_cell BOUNDARY_NTAPBWP16P90 \
  -top_tap_cell BOUNDARY_PTAPBWP16P90 \
  -cell TAPCELLBWP16P90

 addEndCap -powerDomain AON
 addWellTap -powerDomain AON -cellInterval 12
} else {
 addWellTap -cellInterval 12
}

set bw 1
createPlaceBlockage -name pb1 -box 0 0 $width $bw
createPlaceBlockage -name pb2 -box [expr $width - $bw] 0 $width $height
createPlaceBlockage -name pb3 -box 0 [expr $height - $bw] $width $height
createPlaceBlockage -name pb4 -box 0 0 $bw $height
set bw 1
createRouteBlk -name rb1 -layer all -box 0 0 $width $bw
createRouteBlk -name rb2 -layer all -box [expr $width - $bw] 0 $width $height
createRouteBlk -name rb3 -layer all -box 0 [expr $height - $bw] $width $height
createRouteBlk -name rb4 -layer all -box 0 0 $bw $height
#create route blockage on other side of tile aligned with tile id pins
createRouteBlk -name tile_id_oppo -layer M4 -box [list [expr $width - 0.1] $tile_id_min_y $width $tile_id_max_y]

# Keep area around tile_id pins clear so we can route them at top level
createRouteBlk -name tile_id_rb -layer M4 -box [list 0 $tile_id_min_y $tile_id_max_x $tile_id_max_y]
createPlaceBlockage -name tile_id_pb -box 0 $tile_id_min_y $tile_id_max_x $tile_id_max_y

### Tool Settings
setDesignMode -process 16

set_interactive_constraint_modes [all_constraint_modes -active]
setDontUse IOA21D0BWP16P90 true
setDontUse IOA21D0BWP16P90LVT true
setDontUse IOA21D0BWP16P90ULVT true

# Read in global signal constraints file
source ../../scripts/global_signal_tile_constraints.tcl
set_global timing_disable_user_data_to_data_checks false 

setPlaceMode -checkImplantWidth true -honorImplantSpacing true -checkImplantMinArea true
setPlaceMode -honorImplantJog true -honor_implant_Jog_exception true

setDelayCalMode  -SIAware false

setNanoRouteMode -drouteOnGridOnly {wire 4:7 via 3:6}
setNanoRouteMode -routeWithViaInPin {1:1}
setNanoRouteMode -routeTopRoutingLayer $max_route_layer($design)
setNanoRouteMode -routeBottomRoutingLayer 2
setNanoRouteMode -droutePostRouteSpreadWire false
setNanoRouteMode -dbViaWeight {*_P* -1}
setNanoRouteMode -routeExpAdvancedPinAccess true
setNanoRouteMode -routeExpAdvancedTechnology true
setNanoRouteMode -routeReserveSpaceForMultiCut false
setNanoRouteMode -routeWithSiDriven false
setNanoRouteMode -routeWithTimingDriven false
setNanoRouteMode -routeAutoPinAccessForBlockPin true
setNanoRouteMode -routeConcurrentMinimizeViaCountEffort high
setNanoRouteMode -droutePostRouteSwapVia false
setNanoRouteMode -routeExpUseAutoVia true
setNanoRouteMode -drouteExpAdvancedMarFix true

setMultiCpuUsage -localCpu 8

### Place Design
set_interactive_constraint_mode [all_constraint_modes]
#set_clock_uncertainty -hold 0.1 -from clk -to clk
#set_clock_uncertainty -setup 0.2 -from clk -to clk
set_timing_derate -clock -early 0.97 -delay_corner ss_0p72_m40c_dc
set_timing_derate -clock -late 1.03  -delay_corner ss_0p72_m40c_dc
set_timing_derate -data -late 1.05  -delay_corner ss_0p72_m40c_dc
set_timing_derate -clock -early 0.97  -delay_corner ss_0p72_125c_dc
set_timing_derate -clock -late 1.03  -delay_corner ss_0p72_125c_dc
set_timing_derate -data -late 1.05  -delay_corner ss_0p72_125c_dc
set_timing_derate -clock -early 0.97  -delay_corner ff_0p88_0c_dc
set_timing_derate -clock -late 1.03  -delay_corner ff_0p88_0c_dc
set_timing_derate -data -late 1.05   -delay_corner ff_0p88_0c_dc
set_interactive_constraint_mode {}
place_opt_design -place

saveDesign place.enc -def -tcon -verilog

setTieHiLoMode -maxDistance 20 -maxFanout 16
addTieHiLo -cell "TIEHBWP16P90 TIELBWP16P90"

set_global timing_disable_user_data_to_data_checks false 

place_opt_design -opt

saveDesign place_opt.enc -def -tcon -verilog

### CTS
set_global timing_disable_user_data_to_data_checks false 
create_ccopt_clock_tree_spec

ccopt_design -cts

saveDesign cts.enc -def -tcon -verilog

optDesign -postCTS -hold

saveDesign postcts.enc -def -tcon -verilog

#### Route Design
# Route secondary power pins for AON Buf/Invs
routePGPinUseSignalRoute -all

set_global timing_disable_user_data_to_data_checks false 

routeDesign

saveDesign route.enc -def -tcon -verilog
set_global timing_disable_user_data_to_data_checks false 

optDesign -postRoute
set_global timing_disable_user_data_to_data_checks false 
optDesign -postRoute -hold

saveDesign postRoute.enc -def -tcon -verilog

#### Finish
deletePlaceBlockage pb1
deletePlaceBlockage pb2
deletePlaceBlockage pb3
deletePlaceBlockage pb4

deleteRouteBlk -name rb1
deleteRouteBlk -name rb2
deleteRouteBlk -name rb3
deleteRouteBlk -name rb4


editDeleteViolations
ecoRoute
routePGPinUseSignalRoute -all

# Delete tile_id blockages
deletePlaceBlockage tile_id_pb

addFiller -fitGap -cell "DCAP8BWP64P90 DCAP32BWP32P90 DCAP16BWP32P90 DCAP8BWP16P90 DCAP4BWP16P90 FILL64BWP16P90 FILL32BWP16P90 FILL16BWP16P90 FILL8BWP16P90 FILL4BWP16P90 FILL3BWP16P90 FILL2BWP16P90 FILL1BWP16P90"

deletePlaceBlockage toppb
deletePlaceBlockage botpb
deletePlaceBlockage rightpb 

verify_drc 
fixVia -minStep
fixVia -minCut
ecoRoute

deleteRouteBlk -name tile_id_rb
deleteRouteBlk -name tile_id_oppo

saveDesign final.enc -def -tcon -verilog
saveNetlist pnr.v

if $::env(PWR_AWARE) {
    saveNetlist -excludeTopCellPGPort {VDD_SW} -excludeLeafCell -excludeCellInst {BOUNDARY_PCORNERBWP16P90 BOUNDARY_NCORNERBWP16P90 BOUNDARY_RIGHTBWP16P90 BOUNDARY_LEFTBWP16P90 BOUNDARY_PTAPBWP16P90_VPP_VSS BOUNDARY_NTAPBWP16P90_VPP_VSS BOUNDARY_PTAPBWP16P90 BOUNDARY_NTAPBWP16P90 TAPCELLBWP16P90 TAPCELLBWP16P90_VPP_VSS   BOUNDARY_PROW3BWP16P90 BOUNDARY_PROW2BWP16P90 BOUNDARY_NROW3BWP16P90 BOUNDARY_NROW2BWP16P90 FILL64BWP16P90 FILL32BWP16P90 FILL16BWP16P90 FILL8BWP16P90 FILL4BWP16P90 FILL3BWP16P90 FILL2BWP16P90 FILL1BWP16P90} -phys pnr.lvs.v
   saveNetlist -excludeTopCellPGPort {VDD_SW} -includePowerGround pnr.pg.v
} else {
    saveNetlist -excludeLeafCell -excludeCellInst {BOUNDARY_PCORNERBWP16P90 BOUNDARY_NCORNERBWP16P90 BOUNDARY_RIGHTBWP16P90 BOUNDARY_LEFTBWP16P90 BOUNDARY_PTAPBWP16P90 BOUNDARY_NTAPBWP16P90 BOUNDARY_PROW3BWP16P90 BOUNDARY_PROW2BWP16P90 BOUNDARY_NROW3BWP16P90 BOUNDARY_NROW2BWP16P90 TAPCELLBWP16P90 FILL64BWP16P90 FILL32BWP16P90 FILL16BWP16P90 FILL8BWP16P90 FILL4BWP16P90 FILL3BWP16P90 FILL2BWP16P90 FILL1BWP16P90} -phys pnr.lvs.v
}

extractRC
rcOut -setload pnr.setload

lefOut pnr.lef -5.7 -specifyTopLayer 7 

set gds_files [list \
/tsmc16/TSMCHOME/digital/Back_End/gds/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90.gds \
/tsmc16/TSMCHOME/digital/Back_End/gds/tcbn16ffcllbwp16p90pm_100a/tcbn16ffcllbwp16p90pm.gds \
/sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/GDSII/ts1n16ffcllsblvtc512x16m8s_130a_m4xdh.gds \
]

streamOut pnr.gds -uniquifyCellNames -mode ALL -merge ${gds_files} -mapFile /tsmc16/pdk/latest/pnr/innovus/PR_tech/Cadence/GdsOutMap/gdsout_2Xa1Xd_h_3Xe_vhv_2Z_1.2a.map -units 1000

redirect pnr.area {report_area}
redirect pnr.setup.timing {report_timing -max_paths 1000 -nworst 20}
setAnalysisMode -checkType hold
redirect pnr.hold.timing {report_timing -max_paths 1000 -nworst 20}

# Check fanout from SB ports 
set fp [open "check_cells.txt" w+]
foreach_in_collection cell [all_fanout -from SB_* -levels 1 -only_cells ] {
  set name [get_attribute $cell ref_name]
  set cell [get_attribute $cell name]
  puts $fp "cell: $cell"
  if {[regexp {AO} $name] || [regexp {AN2D} $name]  } {
     puts $fp "correct cell $name $cell"
  } else {
    puts $fp "incorrect cell $name $cell"
  }
}
close $fp

# Do this to speed up model generation and top-level P&R
set_interactive_constraint_modes [all_constraint_modes -active]
set_case_analysis 0 [get_ports *SB*]

set_analysis_view -setup [list ss_0p72_m40c] -hold [list ss_0p72_m40c]
do_extract_model pnr.lib -cell_name [get_property [current_design] full_name] -lib_name cgra -format dotlib -view ss_0p72_m40c

