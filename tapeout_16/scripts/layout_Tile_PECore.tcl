set lef_file [list /tsmc16/download/TECH16FFC/N16FF_PRTF_Cad_1.2a/PR_tech/Cadence/LefHeader/Standard/VHV/N16_Encounter_9M_2Xa1Xd3Xe2Z_UTRDL_9T_PODE_1.2a.tlef \
/tsmc16/TSMCHOME/digital/Back_End/lef/tcbn16ffcllbwp16p90pm_100a/lef/tcbn16ffcllbwp16p90pm.lef \
/tsmc16/TSMCHOME/digital/Back_End/lef/tcbn16ffcllbwp16p90_100a/lef/tcbn16ffcllbwp16p90.lef]
 

###################################################################################

source ../../scripts/common.tcl
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
set delaycal_input_transition_delay {100ps}

setLibraryUnit -time 1ns

init_design

if $::env(PWR_AWARE) {
   read_power_intent -1801 ../../scripts/upf.port.fix.tcl
   commit_power_intent
   write_power_intent  -1801 upf.out.tcl
}

if $::env(PWR_AWARE) {
   #TODO: Confirm this for SD domain
   globalNetConnect VDD -type tiehi
   globalNetConnect VSS -type tielo
   #TODO: Confirm this for SD domain
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

setNanoRouteMode -routeTopRoutingLayer 7
setTrialRouteMode -maxRouteLayer 7
setPinAssignMode -maxLayer 7
setDesignMode -process 16

set tcells [get_cells -hier * -filter "is_hierarchical==false"]
set tarea 0.0
foreach_in_collection tc $tcells {
  set ca [get_property $tc area]
  set tarea [expr $tarea + $ca]
}
#0.576 = row height
set height 85 
# set min width to fit all  of the IOs
set min_width 65 
set target_utilization 0.6
set width [format "%0.1f" [expr (($tarea/$target_utilization)/$height)]]

# if width < min_width, we'll choose the min_width
set width [expr max($width, $min_width)]

#snap height width to grid granularity to enable abutted floorplan
set height [snap_to_grid $height $tile_y_grid 0]
set width [snap_to_grid $width $tile_x_grid 0]

floorPlan -site core -s $width $height 0 0 0 0

createRouteBlk -name cut01 -cutLayer all -box [list 0 [expr $height - 0.5] $width [expr $height + 1]]
createRouteBlk -name cut02 -cutLayer all -box [list 0 -1 $width 0.5]

if $::env(PWR_AWARE) {
   #modifyPowerDomainAttr AON -box 27 1.152 41.94 9.792 -minGaps 0.576 0.576 0.18 0.18 
   modifyPowerDomainAttr AON -box 27 [expr $height - 9.792]  41.94 [expr $height - 1.152]  -minGaps 0.576 0.576 0.18 0.18
}


if $::env(PWR_AWARE) {
   addStripe -direction vertical   -start 4 -create_pins 1 -layer M9 -nets {VDD VSS VDD_SW} -width 4 -spacing 2 -set_to_set_distance 20
   selectObject Group AON
   addStripe -direction vertical   -start 4 -create_pins 1 -layer M9 -nets {VDD  VSS} -width 4 -spacing 2 -set_to_set_distance 20 -over_power_domain 1
   editPowerVia -delete_vias true
   
   addStripe -direction horizontal -start 4 -create_pins 1 -layer M8 -nets {VDD VSS VDD_SW} -width 3 -spacing 2 -set_to_set_distance 15
   selectObject Group AON
   addStripe -direction horizontal -start 4 -create_pins 1 -layer M8 -nets {VDD  VSS} -width 3 -spacing 2 -set_to_set_distance 15 -over_power_domain 1
   editPowerVia -delete_vias true
   
   addStripe -direction vertical   -start 2 -create_pins 1 -layer M7 -nets {VDD VSS VDD_SW} -width 1 -spacing 0.5 -set_to_set_distance 10
   selectObject Group AON
   addStripe -direction vertical   -start 2 -create_pins 1 -layer M7 -nets {VDD  VSS} -width 1 -spacing 0.5 -set_to_set_distance 10 -over_power_domain 1
} else {
   addStripe -direction vertical   -start 4 -create_pins 1 -layer M9 -nets {VDD VSS} -width 4 -spacing 2 -set_to_set_distance 16
   editPowerVia -delete_vias true
   addStripe -direction horizontal -start 4 -create_pins 1 -layer M8 -nets {VDD VSS} -width 3 -spacing 2 -set_to_set_distance 12 
   editPowerVia -delete_vias true
   addStripe -direction vertical   -start 2 -create_pins 1 -layer M7 -nets {VDD VSS} -width 1 -spacing 0.5 -set_to_set_distance 10 
}

sroute -allowJogging 0 -allowLayerChange 0 -floatingStripeTarget stripe

editPowerVia -delete_vias true

editPowerVia -add_vias true -orthogonal_only true -top_layer 9 -bottom_layer 8
editPowerVia -add_vias true -orthogonal_only true -top_layer 8 -bottom_layer 7
editPowerVia -add_vias true -orthogonal_only true -top_layer 7 -bottom_layer 1

deleteRouteBlk -name cut01
deleteRouteBlk -name cut02

source ../../scripts/tile_io_place.tcl
set ns_io_offset 7
set ew_io_offset 30
place_ios $width $height $ns_io_offset $ew_io_offset

set_well_tap_mode \
 -rule 6 \
 -bottom_tap_cell BOUNDARY_NTAPBWP16P90 \
 -top_tap_cell BOUNDARY_PTAPBWP16P90 \
 -cell TAPCELLBWP16P90

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
addEndCap

addWellTap -cellInterval 12

if $::env(PWR_AWARE) {
    addPowerSwitch -column \-powerDomain TOP  \-leftOffset 5  -bottomOffset 1 \-horizontalPitch 24 \-checkerBoard \-loopBackAtEnd -topOffset 1 -enableNetOut PSenableNetOut -noFixedStdCellOverlap
}
   

set bw 1.5
createPlaceBlockage -name pb1 -box 0 0 $width $bw
createPlaceBlockage -name pb2 -box [expr $width - $bw] 0 $width $height
createPlaceBlockage -name pb3 -box 0 [expr $height - $bw] $width $height
createPlaceBlockage -name pb4 -box 0 0 $bw $height
set bw 1.2
createRouteBlk -name rb1 -layer all -box 0 0 $width $bw
createRouteBlk -name rb2 -layer all -box [expr $width - $bw] 0 $width $height
createRouteBlk -name rb3 -layer all -box 0 [expr $height - $bw] $width $height
createRouteBlk -name rb4 -layer all -box 0 0 $bw $height
set bw 0.2
createRouteBlk -name xrb1 -layer all -box 0 0 $width $bw
createRouteBlk -name xrb2 -layer all -box [expr $width - $bw] 0 $width $height
createRouteBlk -name xrb3 -layer all -box 0 [expr $height - $bw] $width $height
createRouteBlk -name xrb4 -layer all -box 0 0 $bw $height


## Tool Settings
setDesignMode -process 16

set_interactive_constraint_modes [all_constraint_modes -active]
setDontUse IOA21D0BWP16P90 true
setDontUse IOA21D0BWP16P90LVT true
setDontUse IOA21D0BWP16P90ULVT true

setPlaceMode -checkImplantWidth true -honorImplantSpacing true -checkImplantMinArea true
setPlaceMode -honorImplantJog true -honor_implant_Jog_exception true

setDelayCalMode  -SIAware false

setNanoRouteMode -drouteOnGridOnly {wire 4:7 via 3:6}
setNanoRouteMode -routeWithViaInPin {1:1}
setNanoRouteMode -routeTopRoutingLayer 7 
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
set_clock_uncertainty -hold 0.1 -from clk -to clk
set_clock_uncertainty -setup 0.2 -from clk -to clk
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

remove_assigns -net * -report

place_opt_design -place

saveDesign place.enc -def -tcon -verilog

setTieHiLoMode -maxDistance 20 -maxFanout 16
addTieHiLo -cell "TIEHBWP16P90 TIELBWP16P90"

place_opt_design -opt

saveDesign place_opt.enc -def -tcon -verilog

### CTS
create_ccopt_clock_tree_spec

ccopt_design -cts

saveDesign cts.enc -def -tcon -verilog

optDesign -postCTS -hold

saveDesign postcts.enc -def -tcon -verilog

#### Route Design

routeDesign

saveDesign route.enc -def -tcon -verilog

optDesign -postRoute

optDesign -postRoute -hold

setAnalysisMode -cppr both

saveDesign postRoute.enc -def -tcon -verilog

### Finish
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

addFiller -fitGap -cell "DCAP8BWP64P90 DCAP32BWP32P90 DCAP16BWP32P90 DCAP8BWP16P90 DCAP4BWP16P90 FILL64BWP16P90 FILL32BWP16P90 FILL16BWP16P90 FILL8BWP16P90 FILL4BWP16P90 FILL3BWP16P90 FILL2BWP16P90 FILL1BWP16P90"

editDeleteViolations
ecoRoute

deleteRouteBlk -name xrb1
deleteRouteBlk -name xrb2
deleteRouteBlk -name xrb3
deleteRouteBlk -name xrb4

editDeleteViolations
ecoRoute

saveDesign final.enc -def -tcon -verilog

checkDesign -all > pnr.check_design
saveNetlist pnr.v

if $::env(PWR_AWARE) {
   saveNetlist -includePowerGround pnr.pg.v
}

extractRC
rcOut -setload pnr.setload

lefOut pnr.lef -5.7 -specifyTopLayer 7 

set gds_files [list \
/tsmc16/TSMCHOME/digital/Back_End/gds/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90.gds \
]

streamOut pnr.gds -uniquifyCellNames -mode ALL -merge ${gds_files} -mapFile /tsmc16/pdk/latest/pnr/innovus/PR_tech/Cadence/GdsOutMap/gdsout_2Xa1Xd_h_3Xe_vhv_2Z_1.2a.map -outputMacros -units 1000

redirect pnr.area {report_area}
redirect pnr.setup.timing {report_timing -max_paths 1000 -nworst 20}
setAnalysisMode -checkType hold
redirect pnr.hold.timing {report_timing -max_paths 1000 -nworst 20}


set_analysis_view -setup [list ss_0p72_m40c] -hold [list ss_0p72_m40c]
do_extract_model pnr.lib -cell_name [get_property [current_design] full_name] -lib_name cgra -format dotlib -view ss_0p72_m40c

