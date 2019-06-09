#######################################################################
##
## CGRA layout flow. Created with lots of help from Brian Richards
## and Stevo Bailey.
##
###################################################################
set ::env(PWR_AWARE) 1
set ::env(DESIGN) GarnetSOC_pad_frame
source ../../scripts/helper_funcs.tcl
source ../../scripts/params.tcl

############### PARAMETERS ##################
set tile_separation_x 0
set tile_separation_y 0
# lower left coordinate of tile grid
set start_x 600
set start_y 300

############## END PARAMETERS ###############

###Initialize the design
set_db init_power_nets {VDD VDDPST}

set_db init_ground_nets {VSS VSSPST}
set_multi_cpu_usage -local_cpu 8

read_mmmc ../../scripts/mmode.tcl

read_physical -lef [list \
/tsmc16/download/TECH16FFC/N16FF_PRTF_Cad_1.2a/PR_tech/Cadence/LefHeader/Standard/VHV/N16_Encounter_9M_2Xa1Xd3Xe2Z_UTRDL_9T_PODE_1.2a.tlef \
../Tile_PE/pnr.lef \
../Tile_MemCore/pnr.lef \
/tsmc16/TSMCHOME/digital/Back_End/lef/tcbn16ffcllbwp16p90_100a/lef/tcbn16ffcllbwp16p90.lef \
/tsmc16/TSMCHOME/digital/Back_End/lef/tpbn16v_090a/fc/fc_lf_bu/APRDL/lef/tpbn16v.lef \
/tsmc16/TSMCHOME/digital/Back_End/lef/tphn16ffcllgv18e_110e/mt/9m/9M_2XA1XD_H_3XE_VHV_2Z/lef/tphn16ffcllgv18e_9lm.lef \
/tsmc16/pdk/2016.09.15_MOSIS/FFC/T-N16-CL-DR-032/N16_DTCD_library_kit_20160111/N16_DTCD_library_kit_20160111/lef/topMxyMxe_M9/N16_DTCD_v1d0a.lef \
/tsmc16/pdk/2016.09.15_MOSIS/FFC/T-N16-CL-DR-032/N16_ICOVL_library_kit_FF+_20150528/N16_ICOVL_library_kit_FF+_20150528/lef/topMxMxaMxc_M9/N16_ICOVL_v1d0a.lef \
/sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/LEF/ts1n16ffcllsblvtc512x16m8s_130a_m4xdh.lef \
/sim/ajcars/mc/ts1n16ffcllsblvtc256x32m4sw_130a/LEF/ts1n16ffcllsblvtc256x32m4sw_130a_m4xdh.lef \
/sim/ajcars/mc/ts1n16ffcllsblvtc256x32m8sw_130a/LEF/ts1n16ffcllsblvtc256x32m8sw_130a_m4xdh.lef \
/sim/ajcars/mc/ts1n16ffcllsblvtc2048x32m8sw_130a/LEF/ts1n16ffcllsblvtc2048x32m8sw_130a_m4xdh.lef \
/sim/ajcars/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/LEF/ts1n16ffcllsblvtc2048x64m8sw_130a_m4xdh.lef \
/home/ajcars/N16_SR_B_1KX1K_DPO_DOD_FFC_5x5.lef \
]

read_netlist results_syn/syn_out.v -top GarnetSOC_pad_frame

init_design

delete_global_net_connections
connect_global_net VDDPST -type pgpin -pin VDDPST -inst *
connect_global_net VSS -type pgpin -pin VSSPST -inst * 
connect_global_net VDD -type pgpin -pin VDD -inst *
connect_global_net VDD -type tiehi
connect_global_net VSS -type pgpin -pin VSS -inst *
connect_global_net VSS -type tielo
connect_global_net VDD -type pgpin -pin VPP -inst *
connect_global_net VSS -type pgpin -pin VBB -inst *

###Initialize the floorplan
create_floorplan -core_margins_by die -die_size_by_io_height max -site core -die_size 4900.0 4900.0 100 100 100 100
#eval_legacy {addInst -cell N16_SR_B_1KX1K_DPO_DOD_FFC_5x5 -inst sealring -physical -loc {-50 -50}}
read_io_file ../../../../../pad_frame/io_file  -no_die_size_adjust 
set_multi_cpu_usage -local_cpu 8
snap_floorplan_io
source ../../scripts/vlsi/flow/scripts/gen_floorplan.tcl
done_fp
eval_legacy {addInst -cell N16_SR_B_1KX1K_DPO_DOD_FFC_5x5 -inst sealring -physical -loc {-50 -50}}
eval_legacy {
  source ../../scripts/stream_func.tcl
  gen_gds pads_placed.gds
}
#set_multi_cpu_usage -local_cpu 8
#gen_bumps
#eval_legacy {
#  source ../../scripts/stream_func.tcl
#  gen_gds gen_bumps.gds
#}
#snap_floorplan -all
#gen_route_bumps
#check_io_to_bump_connectivity
#eval_legacy {
#  source ../../scripts/stream_func.tcl
#  gen_gds bumps_routed.gds
#}
#
#add_core_fiducials
#eval_legacy {
#  source ../../scripts/stream_func.tcl
#  gen_gds icovl_placed.gds
#}
#set blockage_width [snap_to_grid 15 $tile_x_grid 0]
#set fiducial_rbs ""
#set rb_cnt 0
#foreach x [get_db insts *icovl*] {
#  set bbox [get_db $x .bbox]
#  set bbox1 [lindex $bbox 0]
#  set l0 [expr [lindex $bbox1 0] - $blockage_width] 
#  set l1 [expr [lindex $bbox1 1] - $blockage_width] 
#  set l2 [expr [lindex $bbox1 2] + $blockage_width] 
#  set l3 [expr [lindex $bbox1 3] + $blockage_width] 
#  if {$l0 < 10} continue;
#  set name icovl_rb_$rb_cnt
#  lappend fiducial_rbs $name
#  incr rb_cnt
#  create_route_blockage -name $name -area [list $l0 $l1 $l2 $l3]  -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9}
#  create_place_blockage -area [list $l0 $l1 $l2 $l3]
#}
#
#set rb_cnt 0
#foreach x [get_db insts *dtcd*] {
#  set bbox [get_db $x .bbox]
#  set bbox1 [lindex $bbox 0]
#  set l0 [expr [lindex $bbox1 0] - $blockage_width] 
#  set l1 [expr [lindex $bbox1 1] - $blockage_width] 
#  set l2 [expr [lindex $bbox1 2] + $blockage_width] 
#  set l3 [expr [lindex $bbox1 3] + $blockage_width] 
#  if {$l0 < 10} continue;
#  set name dtcd_rb_$rb_cnt
#  lappend fiducial_rbs $name
#  incr rb_cnt
#  create_route_blockage -name $name -area [list $l0 $l1 $l2 $l3]  -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9}
#  create_place_blockage -area [list $l0 $l1 $l2 $l3]
#}

