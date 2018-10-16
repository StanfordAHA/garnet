#######################################################################
##
## CGRA layout flow. Created with lots of help from Brian Richards
## and Stevo Bailey.
##
###################################################################

###Initialize the design
set_db init_power_nets {VDD VDDPST}

set_db init_ground_nets {VSS VSSPST}

read_mmmc ../../scripts/mmode.tcl

read_physical -lef [list \
/tsmc16/download/TECH16FFC/N16FF_PRTF_Cad_1.2a/PR_tech/Cadence/LefHeader/Standard/VHV/N16_Encounter_9M_2Xa1Xd3Xe2Z_UTRDL_9T_PODE_1.2a.tlef \
../pe_tile_new_unq1/pnr.lef \
../memory_tile_unq1/pnr.lef \
/sim/bclim/TO_mdll/mdll_top_Model/library/mdll_top.lef \
/tsmc16/TSMCHOME/digital/Back_End/lef/tcbn16ffcllbwp16p90_100a/lef/tcbn16ffcllbwp16p90.lef \
/tsmc16/TSMCHOME/digital/Back_End/lef/tpbn16v_090a/fc/fc_lf_bu/APRDL/lef/tpbn16v.lef \
/tsmc16/TSMCHOME/digital/Back_End/lef/tphn16ffcllgv18e_110e/mt/9m/9M_2XA1XD_H_3XE_VHV_2Z/lef/tphn16ffcllgv18e_9lm.lef \
/tsmc16/pdk/2016.09.15_MOSIS/FFC/T-N16-CL-DR-032/N16_DTCD_library_kit_20160111/N16_DTCD_library_kit_20160111/lef/topMxyMxe_M9/N16_DTCD_v1d0a.lef \
/tsmc16/pdk/2016.09.15_MOSIS/FFC/T-N16-CL-DR-032/N16_ICOVL_library_kit_FF+_20150528/N16_ICOVL_library_kit_FF+_20150528/lef/topMxMxaMxc_M9/N16_ICOVL_v1d0a.lef \
/home/nikhil3/run1/layout/N16_SR_B_1KX1K_DPO_DOD_FFC_5x5.lef \
]

read_netlist {results_syn/syn_out.v} -top top 

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
read_io_file io_file -no_die_size_adjust 
set_multi_cpu_usage -local_cpu 8
## NB: Place MDLL correctly here
place_inst mdll_top 200 4600 -fixed 
create_place_blockage -area {150 4550 450 4850} 
create_route_blockage -area {150 4550 450 4850}  -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9}
snap_floorplan_io

set grid_height 16
set grid_width 16
set grid_x [expr 78.03 + 150 + 0.45]
set grid_y [expr 85.248 + (0.576*200)]
set start_x [expr 600 + 0.07]
set start_y [expr int(400/0.576)*0.576 - 0.237]+[expr $grid_height * $grid_y]
set slice_width [expr (78.03*3) + (129.86*1) +  (150*4) - 0.75]

foreach_in_collection x [get_cells -hier -filter "ref_name=~pe_tile* || ref_name=~memory_tile*"] {
  set xn [get_property $x full_name]
  regexp {0x(\S*)} $xn -> num
  set loc [exec grep "tile_addr='0x${num}'" cgra_info.txt]
  regexp {row='(\S*)' col='(\S*)'} $loc -> row col
  set row [expr $row - 2]
  set col [expr $col - 2]
  set col_slice [expr $col/4]
  set x_loc [expr $start_x + ($col_slice * $slice_width) + (($col % 4) * $grid_x)]
  set y_loc [expr $start_y - ($row * $grid_y)]
  place_inst $xn $x_loc $y_loc -fixed
}

source ../../scripts/vlsi/flow/scripts/gen_floorplan.tcl
set_multi_cpu_usage -local_cpu 8
done_fp
add_core_fiducials

#set_multi_cpu_usage -local_cpu 8
#####gen_bumps
snap_floorplan -all
gen_route_bumps
check_io_to_bump_connectivity
eval_legacy {editPowerVia -area {1090 1090 3840 3840} -delete_vias true}
foreach x [get_property [get_cells -filter "ref_name=~*PDD* || ref_name=~*PRW* || ref_name=~*FILL*" ] full_name] {disconnect_pin -inst $x -pin RTE}
create_place_halo -all_macros -halo_deltas 2 2 2 2  
create_route_halo -all_blocks -bottom_layer M1 -top_layer M9 -space 2  
set_db route_design_antenna_diode_insertion true 
set_db route_design_antenna_cell_name ANTENNABWP16P90 
set_db route_design_fix_top_layer_antenna true 

foreach x [get_db insts *icovl*] {regexp {inst:top/(\S*)} $x dummy y; create_route_halo -inst $y -bottom_layer M1 -top_layer M9 -space 15} 
foreach x [get_db insts *dtdc*] {regexp {inst:top/(\S*)} $x dummy y; create_route_halo -inst $y -bottom_layer M1 -top_layer M9 -space 15} 

write_db init1.db

gen_power

#
set grid_height 16
set grid_width 16
set grid_x [expr 78.03 + 150 + 0.45]
set grid_y [expr 85.248 + (0.576*200)]
set start_x [expr 600 + 0.07]
set start_y [expr int(400/0.576)*0.576 - 0.237]+[expr $grid_height * $grid_y]
set slice_width [expr (78.03*3) + (129.86*1) +  (150*4) - 0.75]
foreach_in_collection x [get_cells -hier -filter "ref_name=~pe_tile* || ref_name=~memory_tile*"] {
  set xn [get_property $x full_name]
  regexp {0x(\S*)} $xn -> num
  set loc [exec grep "tile_addr='0x${num}'" cgra_info.txt]
  regexp {row='(\S*)' col='(\S*)'} $loc -> row col
  set row [expr $row - 2]
  set col [expr $col - 2]
  set col_slice [expr $col/4]
  set x_loc [expr $start_x + ($col_slice * $slice_width) + (($col % 4) * $grid_x)]
  set y_loc [expr $start_y - ($row * $grid_y)]
  #place_inst $xn $x_loc $y_loc -fixed
  if {$row==0} {
    if {[regexp {pe_tile} [get_property $x ref_name]]} {
      for {set z 0} {$z < 22} {incr z} {
       #add_stripes -start [expr $x_loc + ($z*14) + 2] -direction vertical -layer M7 -number_of_sets 1 -nets {VDD VSS} -width 1 -spacing 0.5
       if {$z > 10} {incr z}
       set a  [expr $x_loc + ($z*10) + 2 + 0]
       set a1 [expr $x_loc + ($z*10) + 2 + 1]
       set a2 [expr $x_loc + ($z*10) + 2 + 1 + 0.5 + 0]
       set a3 [expr $x_loc + ($z*10) + 2 + 1 + 0.5 + 1]
       create_shape -net VDD -layer M7 -rect [list $a  90 $a1 4808] -shape stripe -status fixed
       create_shape -net VSS -layer M7 -rect [list $a2 90 $a3 4808] -shape stripe -status fixed
      }
      for {set z 0} {$z < 12} {incr z} {
       #add_stripes -start [expr $x_loc + ($z*6) + 4] -direction vertical -layer M9 -number_of_sets 1 -nets {VDD VSS} -width 4 -spacing 2
       set a [expr $x_loc  + ($z*16) + 4 + 0]
       set a1 [expr $x_loc + ($z*16) + 4 + 4]
       set a2 [expr $x_loc + ($z*16) + 4 + 4 + 2 + 0]
       set a3 [expr $x_loc + ($z*16) + 4 + 4 + 2 + 4]
       create_shape -net VDD -layer M9 -rect [list $a  90 $a1 4808] -shape stripe -status fixed
       create_shape -net VSS -layer M9 -rect [list $a2 90 $a3 4808] -shape stripe -status fixed
      }
    } else {
      for {set z 0} {$z < 27} {incr z} {
       #add_stripes -start [expr $x_loc + ($z*18) + 2] -direction vertical -layer M7 -number_of_sets 1 -nets {VDD VSS} -width 1 -spacing 0.5
       if {$z > 15} {incr z}
       set a  [expr $x_loc + ($z*10) + 2 + 0]
       set a1 [expr $x_loc + ($z*10) + 2 + 1]
       set a2 [expr $x_loc + ($z*10) + 2 + 1 + 0.5 + 0]
       set a3 [expr $x_loc + ($z*10) + 2 + 1 + 0.5 + 1]
       create_shape -net VDD -layer M7 -rect [list $a  90 $a1 4808] -shape stripe -status fixed
       create_shape -net VSS -layer M7 -rect [list $a2 90 $a3 4808] -shape stripe -status fixed
      }
      for {set z 0} {$z < 16} {incr z} {
       #add_stripes -start [expr $x_loc + ($z*16) + 4]  -direction vertical -layer M9 -number_of_sets 1 -nets {VDD VSS} -width 4 -spacing 2
       set a [expr $x_loc  + ($z*16) + 4 + 0]
       set a1 [expr $x_loc + ($z*16) + 4 + 4]
       set a2 [expr $x_loc + ($z*16) + 4 + 4 + 2 + 0]
       set a3 [expr $x_loc + ($z*16) + 4 + 4 + 2 + 4]
       create_shape -net VDD -layer M9 -rect [list $a  90 $a1 4808] -shape stripe -status fixed
       create_shape -net VSS -layer M9 -rect [list $a2 90 $a3 4808] -shape stripe -status fixed
      }
    }
  }
  if {$col==0} {
    if {[regexp {pe_tile} [get_property $x ref_name]]} {
      for {set z 0} {$z < 16} {incr z} {
       set a  [expr $y_loc + ($z*12) + 4 + 0]
       set a1 [expr $y_loc + ($z*12) + 4 + 3]
       set a2 [expr $y_loc + ($z*12) + 4 + 3 + 2 + 0]
       set a3 [expr $y_loc + ($z*12) + 4 + 3 + 2 + 3]
       create_shape -net VDD -layer M8 -rect [list 90 $a  4808 $a1] -shape stripe -status fixed
       create_shape -net VSS -layer M8 -rect [list 90 $a2 4808 $a3] -shape stripe -status fixed
      }
    } else {
      for {set z 0} {$z < 16} {incr z} {
       set a  [expr $y_loc + ($z*12) + 4 + 0]
       set a1 [expr $y_loc + ($z*12) + 4 + 3]
       set a2 [expr $y_loc + ($z*12) + 4 + 3 + 2 + 0]
       set a3 [expr $y_loc + ($z*12) + 4 + 3 + 2 + 3]
       create_shape -net VDD -layer M8 -rect [list 90 $a  4808 $a1] -shape stripe -status fixed
       create_shape -net VSS -layer M8 -rect [list 90 $a2 4808 $a3] -shape stripe -status fixed
      }
    }
  }
}


######NB: Make only M7,8,9 visible before executing the foll
eval_legacy {
foreach_in_collection x [get_cells -hier -filter "ref_name=~pe_tile* || ref_name=~memory_tile*"] {
  set xn [get_property $x full_name]
  set bbox [dbGet [dbGetInstByName $xn].box]
  set bbox1 [lindex $bbox 0]
  set l0 [expr [lindex $bbox1 0] - 1.5] 
  set l1 [expr [lindex $bbox1 1] - 1.5] 
  set l2 [expr [lindex $bbox1 2] + 1.5] 
  set l3 [expr [lindex $bbox1 3] + 1.5] 
  editCutWire -box [list $l0 $l1 $l2 $l3] -only_visible_wires
  gui_select -rect [list $l0 $l1 $l2 $l3]
  deleteSelectedFromFPlan
}
}

eval_legacy {
foreach_in_collection x [get_cells -hier -filter "ref_name=~pe_tile* || ref_name=~memory_tile*"] {
  set xn [get_property $x full_name]
  set bbox [dbGet [dbGetInstByName $xn].box]
  set bbox1 [lindex $bbox 0]
  set l0 [expr [lindex $bbox1 0] + 0.0] 
  set l1 [expr [lindex $bbox1 1] + 0.0] 
  set l2 [expr [lindex $bbox1 2] - 0.0] 
  set l3 [expr [lindex $bbox1 3] - 0.0] 
  createRouteBlk -box [list $l0 $l1 $l2 $l3] -layer {M1 M2 M3 M4 M5 M6 M7}
}
}

for {set y_loc 110} {$y_loc < 580} {incr y_loc 20} {
  create_shape -net VDD -layer M8 -rect [list 90 $y_loc 4808 [expr $y_loc + 3]] -shape stripe -status fixed
  create_shape -net VSS -layer M8 -rect [list 90 [expr $y_loc + 4] 4808 [expr $y_loc + 7]] -shape stripe -status fixed
}
for {set y_loc 3810} {$y_loc < 4780} {incr y_loc 20} {
  create_shape -net VDD -layer M8 -rect [list 90 $y_loc 4808 [expr $y_loc + 3]] -shape stripe -status fixed
  create_shape -net VSS -layer M8 -rect [list 90 [expr $y_loc + 4] 4808 [expr $y_loc + 7]] -shape stripe -status fixed
}

for {set x_loc 110} {$x_loc < 580} {incr x_loc 20} {
  create_shape -net VDD -layer M7 -rect [list $x_loc 100 [expr $x_loc + 1] 4808] -shape stripe -status fixed
  create_shape -net VSS -layer M7 -rect [list [expr $x_loc + 1.5] 100 [expr $x_loc + 2.5] 4808] -shape stripe -status fixed
}
for {set x_loc 4480} {$x_loc < 4780} {incr x_loc 20} {
  create_shape -net VDD -layer M7 -rect [list $x_loc 100 [expr $x_loc + 1] 4808] -shape stripe -status fixed
  create_shape -net VSS -layer M7 -rect [list [expr $x_loc + 1.5] 100 [expr $x_loc + 2.5] 4808] -shape stripe -status fixed
}
write_db init2.db

eval_legacy {editPowerVia -add_vias true -orthogonal_only true -top_layer AP -bottom_layer 9}
eval_legacy {editPowerVia -add_vias true -orthogonal_only true -top_layer 9 -bottom_layer 8}
eval_legacy {editPowerVia -add_vias true -orthogonal_only true -top_layer 8 -bottom_layer 7}
eval_legacy {editPowerVia -add_vias true -orthogonal_only true -top_layer 7 -bottom_layer 1}

write_db init4.db

foreach x [get_db insts *icovl*] {
  set bbox [get_db $x .bbox]
  set bbox1 [lindex $bbox 0]
  set l0 [expr [lindex $bbox1 0] - 13] 
  set l1 [expr [lindex $bbox1 1] - 13] 
  set l2 [expr [lindex $bbox1 2] + 13] 
  set l3 [expr [lindex $bbox1 3] + 13] 
  if {$l0 < 10} continue;
  edit_cut_route -box [list $l0 $l1 $l2 $l3] -only_visible_wires
  gui_select -rect [list $l0 $l1 $l2 $l3]
  puts "Deleting $l0 $l1 $l2 $l3"
  delete_selected_from_floorplan
}


foreach x [get_db insts *icovl*] {
  set bbox [get_db $x .bbox]
  set bbox1 [lindex $bbox 0]
  set l0 [expr [lindex $bbox1 0] - 2.2] 
  set l1 [expr [lindex $bbox1 1] - 2.2] 
  set l2 [expr [lindex $bbox1 2] + 2.2] 
  set l3 [expr [lindex $bbox1 3] + 2.2] 
  if {$l0 < 10} continue;
  create_route_blockage -area [list $l0 $l1 $l2 $l3]  -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9}
  
}

foreach x [get_db insts *dtdc*] {
  set bbox [get_db $x .bbox]
  set bbox1 [lindex $bbox 0]
  set l0 [expr [lindex $bbox1 0] - 13] 
  set l1 [expr [lindex $bbox1 1] - 13] 
  set l2 [expr [lindex $bbox1 2] + 13] 
  set l3 [expr [lindex $bbox1 3] + 13] 
  if {$l0 < 10} continue;
  edit_cut_route -box [list $l0 $l1 $l2 $l3] -only_visible_wires
  gui_select -rect [list $l0 $l1 $l2 $l3]
  puts "Deleting $l0 $l1 $l2 $l3"
  delete_selected_from_floorplan
}


#######eval_legacy {
#######foreach_in_collection x [get_cells -hier -filter "ref_name=~pe_tile* || ref_name=~memory_tile*"] {
#######  set xn [get_property $x full_name]
#######  set bbox [dbGet [dbGetInstByName $xn].box]
#######  set bbox1 [lindex $bbox 0]
#######  set l0 [lindex $bbox1 0] 
#######  set l1 [lindex $bbox1 1] 
#######  set l2 [lindex $bbox1 2] 
#######  set l3 [lindex $bbox1 3] 
#######  editPowerVia -area [list $l0 $l1 $l2 $l3] -delete_vias true
#######  eval_novus {edit_cut_route -box [list $l0 $l1 $l2 $l3] -only_visible_wires}
#######  eval_novus {gui_select -rect [list $l0 $l1 $l2 $l3]}
#######  eval_novus {delete_selected_from_floorplan}
#######}
#######}
####
write_db fp.db
