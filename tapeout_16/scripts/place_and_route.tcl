### Tool Settings
setDesignMode -process 16

set_interactive_constraint_modes [all_constraint_modes -active]
setDontUse IOA21D0BWP16P90 true
setDontUse IOA21D0BWP16P90LVT true
setDontUse IOA21D0BWP16P90ULVT true

setPlaceMode -checkImplantWidth true -honorImplantSpacing true -checkImplantMinArea true
setPlaceMode -honorImplantJog true -honor_implant_Jog_exception true

setNanoRouteMode -drouteOnGridOnly {wire 4:7 via 3:6}
setNanoRouteMode -routeWithViaInPin {1:1}
setNanoRouteMode -routeTopRoutingLayer 9
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


### Place Design
##set_multi_cpu_usage -local_cpu 8
set_interactive_constraint_modes [all_constraint_modes]
set_multicycle_path -thr */C -setup 3
set_multicycle_path -thr */C -hold 2
set_false_path -thr global_controller/*
set_multicycle_path -thr */PAD -setup 2
set_multicycle_path -thr */PAD -hold 1
set_dont_touch true [get_nets -of */PAD]
set_multicycle_path -to [get_pins -hier *gin*] -setup 10
set_multicycle_path -to [get_pins -hier *gin*] -hold 9
set_multicycle_path -from [get_pins *_io_bit_reg/CP] -through [get_pins */C] -setup 10
set_multicycle_path -from [get_pins *_io_bit_reg/CP] -through [get_pins */C] -hold 9
set_multicycle_path -from [get_pins */clk_in] -setup 2
set_multicycle_path -from [get_pins */clk_in] -hold 1
set_multicycle_path -from [get_pins */clk_in] -to [get_pins -hier *gin*] -setup 10
set_multicycle_path -from [get_pins */clk_in] -to [get_pins -hier *gin*] -hold 9
set_interactive_constraint_modes {}

eval_novus {create_fence -area {400 4585 450 4720} -name global_controller}
##place_connected -attractor [get_property [get_cells -filter "ref_name=~pe*||ref_name=~mem*"] full_name] -level 1
##
set_interactive_constraint_mode [all_constraint_modes]
set_clock_uncertainty -hold 0.1 -from clk -to clk
set_clock_uncertainty -setup 0.2 -from clk -to clk
set_timing_derate -clock -early 0.97 -delay_corner _default_delay_corner_ 
set_timing_derate -clock -late 1.03  -delay_corner _default_delay_corner_
set_timing_derate -data -late 1.05  -delay_corner _default_delay_corner_
set_interactive_constraint_mode {}

eval_novus {set_db [get_nets rte] .skip_routing true}
place_opt_design -place

eval_novus {write_db place.db -def -sdc -verilog}

place_opt_design -opt

eval_novus {write_db place_opt.db -def -sdc -verilog}
setTieHiLoMode -maxDistance 20 -maxFanout 16
addTieHiLo -cell "TIEHBWP16P90 TIELBWP16P90"
  
### Clock Tree 


create_ccopt_clock_tree_spec

ccopt_design -cts
optDesign -postCTS -hold
eval_novus {write_db cts.db -def -sdc -verilog}


#### Route Design
routeDesign
eval_novus {write_db routed.db -def -sdc -verilog}


## Chip Finishing
eval_legacy {
addFiller -fitGap -cell "DCAP8BWP64P90 DCAP32BWP32P90 DCAP16BWP32P90 DCAP8BWP16P90 DCAP4BWP16P90 FILL64BWP16P90 FILL32BWP16P90 FILL16BWP16P90 FILL8BWP16P90 FILL4BWP16P90 FILL3BWP16P90 FILL2BWP16P90 FILL1BWP16P90"

create_net -name RTE_ANA 
create_net -name POC_ANA -ground -physical
create_net -name ESD_ANA -ground -physical

foreach x [get_property [get_cells -filter "full_name=~*pad_ana* || full_name=~*ANA*"] full_name] {                                                                                  
connect_pin -net RTE_ANA   -pin RTE -inst $x
connect_global_net ESD_ANA -netlist_override -pin ESD -inst $x
connect_global_net POC_ANA -pin POCCTRL -inst $x
}

create_net -name RTE_DIG 
create_net -name ESD_DIG -ground -physical
create_net -name POC_DIG -ground -physical
foreach x [get_property [add_to_collection [get_cell -of [get_nets -of [get_ports {*S3* pad_t* pad_clk_in* pad_reset_in*}]]] [get_cells {IOPAD_S3_*VDD_* IOPAD_S3_*VDDPST_* *POC_DIG *RTE_DIG}]] full_name] {
connect_pin -net RTE_DIG  -pin RTE -inst $x
connect_global_net ESD_DIG  -netlist_override -pin ESD -inst $x
connect_global_net POC_DIG -pin POCCTRL -inst $x
}

create_net -name RTE_DIG2
create_net -name ESD_DIG2 -ground -physical
create_net -name POC_DIG2 -ground -physical
foreach x [get_property [add_to_collection [get_cell -of [get_nets -of [get_ports {*S0*}]]] [get_cells {IOPAD_S0_*VDD_* IOPAD_S0_*VDDPST_* *POC_DIG2 *RTE_DIG2}]] full_name] {
connect_pin -net RTE_DIG2  -pin RTE -inst $x
connect_global_net ESD_DIG2 -netlist_overrid -pin ESD -inst $x
connect_global_net POC_DIG2 -pin POCCTRL -inst $x
}

foreach x [get_property [add_to_collection [get_cell -of [get_nets -of [get_ports {*S1*}]]] [get_cells {IOPAD_S1_*VDD_* IOPAD_S1_*VDDPST_*}]] full_name] {
connect_pin -net RTE_DIG2  -pin RTE -inst $x
connect_global_net ESD_DIG2 -netlist_overrid -pin ESD -inst $x
connect_global_net POC_DIG2 -pin POCCTRL -inst $x
}

foreach x [get_property [add_to_collection [get_cell -of [get_nets -of [get_ports {*S2*}]]] [get_cells {IOPAD_S2_*VDD_* IOPAD_S2_*VDDPST_*}]] full_name] {
connect_pin -net RTE_DIG2  -pin RTE -inst $x
connect_global_net ESD_DIG2 -netlist_override -pin ESD -inst $x
connect_global_net POC_DIG2 -pin POCCTRL -inst $x
} 

eval_novus {write_db final.enc -def -sdc -verilog}

addInst -cell N16_SR_B_1KX1K_DPO_DOD_FFC_5x5 -inst sealring -physical -loc {-50 -50}

set gds_files [list \
/tsmc16/TSMCHOME/digital/Back_End/gds/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90.gds \
/tsmc16/TSMCHOME/digital/Back_End/gds/tpbn16v_090a/fc/fc_lf_bu/APRDL/tpbn16v.gds \
/tsmc16/TSMCHOME/digital/Back_End/gds/tphn16ffcllgv18e_110e/mt_1/9m/9M_2XA1XD_H_3XE_VHV_2Z/tphn16ffcllgv18e.gds \
/tsmc16/pdk/2016.09.15_MOSIS/FFC/T-N16-CL-DR-032/N16_DTCD_library_kit_20160111/N16_DTCD_library_kit_20160111/gds/N16FF_Phantom_v1d0_1a_20140707.gds \
/sim/nikhil3/mem_compile/130a/TSMCHOME/sram/Compiler/tsn16ffcllhdspsbsram_20131200_130a/ts1n16ffcllsblvtc512x16m8s_130a/GDSII/ts1n16ffcllsblvtc512x16m8s_130a_m4xdh.gds \
/tsmc16/download/TECH16FFC/ICOVL/43_ICOVL_cells_FFC.gds \
/home/nikhil3/run1/layout/N16_SR_B_1KX1K_DPO_DOD_FFC_5x5.gds \
../memory_tile_unq1/pnr.gds \
../pe_tile_new_unq1/pnr.gds \
/sim/bclim/mdll_top/mdll_top.gds
]


streamOut final.gds -uniquifyCellNames -offset {47.576 47.576} -mode ALL -merge ${gds_files} -mapFile /tsmc16/pdk/latest/pnr/innovus/PR_tech/Cadence/GdsOutMap/gdsout_2Xa1Xd_h_3Xe_vhv_2Z_1.2a.map -outputMacros -units 1000

saveNetlist pnr.lvs.v -includePowerGround -excludeLeafCell -includeBumpCell -phys
}
