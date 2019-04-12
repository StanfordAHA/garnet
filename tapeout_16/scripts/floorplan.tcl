#######################################################################
##
## CGRA layout flow. Created with lots of help from Brian Richards
## and Stevo Bailey.
##
###################################################################
source ../../scripts/common.tcl
###Initialize the design
set_db init_power_nets {VDD VDDPST}

set_db init_ground_nets {VSS VSSPST}

read_mmmc ../../scripts/mmode.tcl

read_physical -lef [list \
/tsmc16/download/TECH16FFC/N16FF_PRTF_Cad_1.2a/PR_tech/Cadence/LefHeader/Standard/VHV/N16_Encounter_9M_2Xa1Xd3Xe2Z_UTRDL_9T_PODE_1.2a.tlef \
../Tile_PECore/pnr.lef \
../Tile_MemCore/pnr.lef \
/tsmc16/TSMCHOME/digital/Back_End/lef/tcbn16ffcllbwp16p90_100a/lef/tcbn16ffcllbwp16p90.lef \
/tsmc16/TSMCHOME/digital/Back_End/lef/tpbn16v_090a/fc/fc_lf_bu/APRDL/lef/tpbn16v.lef \
/tsmc16/TSMCHOME/digital/Back_End/lef/tphn16ffcllgv18e_110e/mt/9m/9M_2XA1XD_H_3XE_VHV_2Z/lef/tphn16ffcllgv18e_9lm.lef \
/tsmc16/pdk/2016.09.15_MOSIS/FFC/T-N16-CL-DR-032/N16_DTCD_library_kit_20160111/N16_DTCD_library_kit_20160111/lef/topMxyMxe_M9/N16_DTCD_v1d0a.lef \
/tsmc16/pdk/2016.09.15_MOSIS/FFC/T-N16-CL-DR-032/N16_ICOVL_library_kit_FF+_20150528/N16_ICOVL_library_kit_FF+_20150528/lef/topMxMxaMxc_M9/N16_ICOVL_v1d0a.lef \
/home/nikhil3/run1/layout/N16_SR_B_1KX1K_DPO_DOD_FFC_5x5.lef \
]

read_netlist {results_syn/syn_out.v} -top CGRA

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
#read_io_file io_file -no_die_size_adjust 
set_multi_cpu_usage -local_cpu 8
snap_floorplan_io

set grid_height 2
set grid_width 2
set tile_separation_x 0.56
set tile_separation_y 0

# snap separations to grid
set tile_separation_x [snap_to_grid $tile_separation_x $tile_x_grid 0]
set tile_separation_y [snap_to_grid $tile_separation_y $tile_y_grid 0]

# lower left coordinate of tile grid
set start_x 600
set start_y 400

# actual core to edge
set core_to_edge_tb 99.99
set core_to_edge_lr 99.99

# snap x and y start to grid
set start_x [expr [snap_to_grid $start_x $tile_x_grid $core_to_edge_lr]]
set start_y [expr [snap_to_grid $start_y $tile_y_grid $core_to_edge_tb]]

# put all of the tiles into a 2D array so we know their relative locations in grid
foreach_in_collection tile [get_cells -hier -filter "ref_name=~Tile_PECore* || ref_name=~Tile_MemCore*"] {
  set tile_name [get_property $tile full_name]
  regexp {X(\S*)_} $tile_name -> col
  regexp {Y(\S*)} $tile_name -> row

  # remove leading zeros
  set row [expr $row + 0]
  set col [expr $col + 0]

  set tiles($row,$col,name) $tile_name
}

#Actually place the tiles
set y_loc $start_y
for {set row [expr $grid_height - 1]} {$row >= 0} {incr row -1} {
  set x_loc $start_x
  for {set col 0} {$col < $grid_width} {incr col} {
    set tiles($row,$col,x_loc) $x_loc
    set tiles($row,$col,y_loc) $y_loc
    place_inst $tiles($row,$col,name) $x_loc $y_loc -fixed
    #Update x location for next tile using rightmost boundary of this tile
    set x_loc [get_property [get_cells $tiles($row,$col,name)] x_coordinate_max]
    # Add spacing between tiles if desired
    set x_loc [expr $x_loc + $tile_separation_x]
    set x_loc [snap_to_grid $x_loc $tile_x_grid $core_to_edge_lr]
  }
  # Update y location for next row using topmost boundary of this row
  set y_loc [get_property [get_cells $tiles($row,0,name)] y_coordinate_max]
  # Add spacing between rows if desired
  set y_loc [expr $y_loc + $tile_separation_y]
  set y_loc [snap_to_grid $y_loc $tile_y_grid $core_to_edge_tb]
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

set y_loc $start_y
for {set row [expr $grid_height - 1]} {$row >= 0} {incr row -1} {
  set x_loc $start_x
  for {set col 0} {$col < $grid_width} {incr col} {
    set tile [get_cell $tiles($row,$col,name)]
    if {$row==0} {
      if {[regexp {Tile_PECore} [get_property $tile ref_name]]} {
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
      if {[regexp {Tile_PECore} [get_property $tile ref_name]]} {
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
    #Update x location for next tile using rightmost boundary of this tile
    set x_loc [get_property [get_cells $tiles($row,$col,name)] x_coordinate_max]
    # Add spacing between tiles if desired
    set x_loc [expr $x_loc + $tile_separation_x]
  }
  # Update y location for next row using topmost boundary of this row
  set y_loc [get_property [get_cells $tiles($row,0,name)] y_coordinate_max]
  # Add spacing between rows if desired
  set y_loc [expr $y_loc + $tile_separation_y]
}


######NB: Make only M7,8,9 visible before executing the foll
# tiles already have stripes, so we won't add extras on top of them
eval_legacy {
foreach_in_collection x [get_cells -hier -filter "ref_name=~Tile_PECore* || ref_name=~Tile_MemCore*"] {
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
foreach_in_collection x [get_cells -hier -filter "ref_name=~Tile_PECore* || ref_name=~Tile_MemCore*"] {
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

# power for rest of CGRA (outside of tile grid)
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

# DFM HOLE
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
