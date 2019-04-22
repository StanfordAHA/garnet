#######################################################################
##
## CGRA layout flow. Created with lots of help from Brian Richards
## and Stevo Bailey.
##
###################################################################
source ../../scripts/common.tcl

############### PARAMETERS ##################
set grid_height 16
set grid_width 32
set tile_separation_x 0
set tile_separation_y 0
# lower left coordinate of tile grid
set start_x 600
set start_y 400

############## END PARAMETERS ###############

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

read_netlist {results_syn/syn_out.v} -top Chip

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


# snap separations to grid
set tile_separation_x [snap_to_grid $tile_separation_x $tile_x_grid 0]
set tile_separation_y [snap_to_grid $tile_separation_y $tile_y_grid 0]


# actual core to edge
set core_to_edge 99.99

# snap x and y start to grid
set start_x [expr [snap_to_grid $start_x $tile_x_grid $core_to_edge]]
set start_y [expr [snap_to_grid $start_y $tile_y_grid $core_to_edge]]

# put all of the tiles into a 2D array so we know their relative locations in grid
foreach_in_collection tile [get_cells -hier -filter "ref_name=~Tile_PECore* || ref_name=~Tile_MemCore*"] {
  set tile_name [get_property $tile full_name]
  regexp {X(\S*)_} $tile_name -> col
  regexp {Y(\S*)} $tile_name -> row

  # remove leading zeros
  set row [expr 0x$row]
  set col [expr 0x$col]

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
    set x_loc [snap_to_grid $x_loc $tile_x_grid $core_to_edge]
  }
  # Update y location for next row using topmost boundary of this row
  set y_loc [get_property [get_cells $tiles($row,0,name)] y_coordinate_max]
  # Add spacing between rows if desired
  set y_loc [expr $y_loc + $tile_separation_y]
  set y_loc [snap_to_grid $y_loc $tile_y_grid $core_to_edge]
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

foreach x [get_db insts *icovl*] {
    regexp {inst:Chip/(\S*)} $x dummy y;
    create_route_halo -inst $y -bottom_layer M1 -top_layer M9 -space 15
} 
foreach x [get_db insts *dtdc*] {
    regexp {inst:Chip/(\S*)} $x dummy y; 
    create_route_halo -inst $y -bottom_layer M1 -top_layer M9 -space 15
} 

write_db init1.db

gen_power

# min and max x or y coords for stripes
set min 90
set max 4808

#Get bbox of tile grid
set grid_llx $start_x
set grid_lly $start_y
set grid_urx [get_property [get_cells $tiles(0,[expr $grid_width - 1],name)] x_coordinate_max]
set grid_ury [get_property [get_cells $tiles(0,0,name)] y_coordinate_max]

# Create placement region for global controller and TODO: global buffer
create_region -area $grid_llx $grid_ury $grid_urx [expr $grid_ury + 180] -name [get_property [get_cells -hier *GlobalController*] hierarchical_name]


#Horizontal stripes M8
for {set row [expr $grid_height - 1]} {$row >= 0} {incr row -1} {
    set tile $tiles($row,0,name)
    set offset [expr $tiles($row,0,y_loc) + $tile_stripes(M8,start)]
    # How much space is actually required to start another set of stripes
    set stop_margin [expr 2*$tile_stripes(M8,width) + $tile_stripes(M8,spacing)]
    # Stop making new stripes when the offset is > end of tile - margin
    set stop_location [get_property [get_cells $tile] y_coordinate_max]
    set stop_location [expr $stop_location - $stop_margin]

    while {$offset < $stop_location} {
        set stripe_top [expr $tile_stripes(M8,width) + $offset]
        create_shape -net VDD -layer M8 -rect [list $min $offset $grid_llx $stripe_top] -shape stripe -status fixed
        create_shape -net VDD -layer M8 -rect [list $grid_urx $offset $max $stripe_top] -shape stripe -status fixed
        
        #now set up VSS location
        set vss_offset [expr $stripe_top + $tile_stripes(M8,spacing)]
        set stripe_top [expr $tile_stripes(M8,width) + $vss_offset]
        create_shape -net VSS -layer M8 -rect [list $min $vss_offset $grid_llx $stripe_top] -shape stripe -status fixed
        create_shape -net VSS -layer M8 -rect [list $grid_urx $vss_offset $max $stripe_top] -shape stripe -status fixed

        #Set up offset for next set of stripes
        set offset [expr $tile_stripes(M8,s2s) + $offset]
    }
}

#Vertical stripes M7, M9
foreach layer {M7 M9} {
    for {set col 0} {$col < $grid_width} {incr col 1} {
        set tile $tiles(0,$col,name)
        set offset [expr $tiles(0,$col,x_loc) + $tile_stripes($layer,start)]
        # How much space is actually required to start another set of stripes
        set stop_margin [expr 2*$tile_stripes($layer,width) + $tile_stripes($layer,spacing)]
        # Stop making new stripes when the offset is > end of tile - margin
        set stop_location [get_property [get_cells $tile] x_coordinate_max]
        set stop_location [expr $stop_location - $stop_margin]
    
        while {$offset < $stop_location} {
            set stripe_top [expr $tile_stripes($layer,width) + $offset]
            create_shape -net VDD -layer $layer -rect [list $offset $min $stripe_top $grid_lly] -shape stripe -status fixed
            create_shape -net VDD -layer $layer -rect [list $offset $grid_ury $stripe_top $max] -shape stripe -status fixed
            
            #now set up VSS location
            set vss_offset [expr $stripe_top + $tile_stripes($layer,spacing)]
            set stripe_top [expr $tile_stripes($layer,width) + $vss_offset]
            create_shape -net VSS -layer $layer -rect [list $vss_offset $min $stripe_top $grid_lly] -shape stripe -status fixed
            create_shape -net VSS -layer $layer -rect [list $vss_offset $grid_ury $stripe_top $max] -shape stripe -status fixed
    
            #Set up offset for next set of stripes
            set offset [expr $tile_stripes($layer,s2s) + $offset]
        }
    }
}


# power for rest of chip (outside of tile grid)
# vertical
foreach layer {M7 M9} {
    add_stripes \
        -nets {VDD VSS} \
        -layer $layer \
        -direction vertical \
        -start [expr $core_to_edge + 10] \
        -stop $grid_llx \
        -width $tile_stripes($layer,width) \
        -spacing $tile_stripes($layer,spacing) \
        -set_to_set_distance $tile_stripes($layer,s2s)
    add_stripes \
        -nets {VDD VSS} \
        -layer $layer \
        -direction vertical \
        -start $grid_urx \
        -width $tile_stripes($layer,width) \
        -spacing $tile_stripes($layer,spacing) \
        -set_to_set_distance $tile_stripes($layer,s2s)
}

#horizontal
foreach layer {M8} {
    add_stripes \
        -nets {VDD VSS} \
        -layer $layer \
        -direction horizontal \
        -start [expr $core_to_edge + 10] \
        -stop $grid_lly \
        -width $tile_stripes($layer,width) \
        -spacing $tile_stripes($layer,spacing) \
        -set_to_set_distance $tile_stripes($layer,s2s)
    add_stripes \
        -nets {VDD VSS} \
        -layer $layer \
        -direction horizontal \
        -start $grid_ury \
        -width $tile_stripes($layer,width) \
        -spacing $tile_stripes($layer,spacing) \
        -set_to_set_distance $tile_stripes($layer,s2s)
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


write_db fp.db
