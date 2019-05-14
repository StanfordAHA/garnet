#######################################################################
##
## CGRA layout flow. Created with lots of help from Brian Richards
## and Stevo Bailey.
##
###################################################################
source ../../scripts/common.tcl

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

#read_mmmc ../../scripts/mmode.tcl

read_physical -lef [list \
/tsmc16/download/TECH16FFC/N16FF_PRTF_Cad_1.2a/PR_tech/Cadence/LefHeader/Standard/VHV/N16_Encounter_9M_2Xa1Xd3Xe2Z_UTRDL_9T_PODE_1.2a.tlef \
../Tile_PECore/pnr.lef \
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

read_netlist {../Garnet/results_syn/syn_out.v /sim/ajcars/garnet/pad_frame/genesis_verif/Garnet_SoC_pad_frame.sv /sim/ajcars/aha-arm-soc-june-2019/implementation/synthesis/synth/processor_subsystem/results_syn/syn_out.v /sim/ajcars/aha-arm-soc-june-2019/integration/garnet_soc.v} -top Garnet_SoC_pad_frame

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
read_io_file ../../scripts/io_file  -no_die_size_adjust 
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

# We will find the grid width/height from tiles
set max_row 0
set max_col 0

set min_row 99999
set min_col 99999

# put all of the tiles into a 2D array so we know their relative locations in grid
foreach_in_collection tile [get_cells -hier -filter "ref_name=~Tile_PECore* || ref_name=~Tile_MemCore*"] {
  set tile_name [get_property $tile full_name]
  regexp {X(\S*)_} $tile_name -> col
  regexp {Y(\S*)} $tile_name -> row

  # Convert hex IDs to decimal
  set row [expr 0x$row + 0]
  set col [expr 0x$col + 0]

  set tiles($row,$col,name) $tile_name

  # grid height = max row value
  if {$row > $max_row} {
    set max_row $row
  }
  if {$row < $min_row} {
    set min_row $row
  }
  if {$col > $max_col} {
    set max_col $col
  }
  if {$col < $min_col} {
    set min_col $col
  }
}
# Get grid height/width from max_row/col
set grid_height [expr $max_row - $min_row + 1]
set grid_width [expr $max_col - $min_col + 1]

#Actually place the tiles
set y_loc $start_y
for {set row $max_row} {$row >= $min_row} {incr row -1} {
  set x_loc $start_x
  for {set col $min_col} {$col <= $max_col} {incr col} {
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

#Get bbox of tile grid
set grid_llx $start_x
set grid_lly $start_y
set grid_urx [get_property [get_cells $tiles($min_row,$max_col,name)] x_coordinate_max]
set grid_ury [get_property [get_cells $tiles($min_row,$max_col,name)] y_coordinate_max]

# Create M1 PG net blockage above tile grid
create_route_blockage -area $grid_llx $grid_ury $grid_urx [expr $grid_ury + 2] -layers M1 -pg_nets

# Create M1 PG net blockage below tile grid
create_route_blockage -area $grid_llx $grid_lly $grid_urx [expr $grid_lly - 2] -layers M1 -pg_nets

# Get Collection of all Global buffer SRAMs
set sram_start_x 180
set sram_start_y [expr $grid_ury + 300]
set bank_height 8
set glbuf_srams [get_cells core/cgra/GlobalBuffer*/*sram_array* -filter "ref_name=~TS1N*"]
set sram_width 60.755
set sram_height 226.32
set sram_spacing_x_even 0
set sram_spacing_x_odd 15
set sram_spacing_y 0

glbuf_sram_place $glbuf_srams $sram_start_x $sram_start_y $sram_spacing_x_even $sram_spacing_x_odd $sram_spacing_y $bank_height $sram_height $sram_width

# Get Collection of all Processor SRAMs
set sram_start_x 3800
set sram_start_y 3800
set bank_height 3
set ps_srams [get_cells core/processor/*/*/*/*/* -filter "ref_name=~TS1N*"]
set sram_width 60.755
set sram_height 226.32
set sram_spacing_x_even 0
set sram_spacing_x_odd 20
set sram_spacing_y 0

glbuf_sram_place $ps_srams $sram_start_x $sram_start_y $sram_spacing_x_even $sram_spacing_x_odd $sram_spacing_y $bank_height $sram_height $sram_width

# Create placement region for global controller
set gc [get_cells -hier *GlobalController*]
set gc_area [get_property $gc area]
set gc_name [get_property $gc hierarchical_name]
set utilization 0.2
set target_area [expr $gc_area / $utilization]
set mid_grid_x [expr (($grid_llx + $grid_urx)/2)]
set gc_llx [expr $mid_grid_x - (sqrt($target_area)/2)]
set gc_urx [expr $mid_grid_x + (sqrt($target_area)/2)]
set gc_ury [expr $grid_ury + sqrt($target_area)]
create_guide -area $gc_llx $grid_ury $gc_urx $gc_ury -name $gc_name
#Create region for global buffer
set glbuf [get_cells -hier *GlobalBuffer*]
set glbuf_area [get_property $glbuf area]
set glbuf_name [get_property $glbuf hierarchical_name]
set utilization 0.2
set target_area [expr $glbuf_area / $utilization]
set glbuf_llx 100
set glbuf_urx 4900
set glbuf_ury [expr $target_area/($glbuf_urx - $glbuf_llx)]
create_guide -area $glbuf_llx 1500 $glbuf_urx 3000 -name $glbuf_name
#Create guide for read_data_or gate at bottom of tile grid
set read_data_or [get_cells -hier *read_config_data_or*]
set area [get_property $read_data_or area]
set name [get_property $read_data_or hierarchical_name]
set utilization 0.1
set target_area [expr $area / $utilization]
create_guide -area $mid_grid_x [expr $grid_lly - sqrt($area)] [expr $mid_grid_x + sqrt($area)] $grid_lly -name $name
#Create guide for processor subsystem
set ps [get_cells -hier *processor*]
set ps_name [get_property $ps hierarchical_name]
create_guide -area 3600 3600 4900 4900 -name $ps_name


source ../../scripts/vlsi/flow/scripts/gen_floorplan.tcl
set_multi_cpu_usage -local_cpu 8
done_fp
add_core_fiducials

#set_multi_cpu_usage -local_cpu 8
gen_bumps
snap_floorplan -all
#gen_route_bumps
check_io_to_bump_connectivity
eval_legacy {editPowerVia -area {1090 1090 3840 3840} -delete_vias true}
foreach x [get_property [get_cells -filter "ref_name=~*PDD* || ref_name=~*PRW* || ref_name=~*FILL*" ] full_name] {disconnect_pin -inst $x -pin RTE}
create_place_halo -all_macros -halo_deltas 2 2 2 2  
create_route_halo -all_blocks -bottom_layer M1 -top_layer M9 -space 2  
set_db route_design_antenna_diode_insertion true 
set_db route_design_antenna_cell_name ANTENNABWP16P90 
set_db route_design_fix_top_layer_antenna true 

# Create M1 routing blockages to keep space between power straps and memories
#foreach_in_collection mem [get_cells -hier * -filter "ref_name=~TS1N*"] {
#  macro_pg_blockage $mem 2
#}

foreach x [get_db insts *icovl*] {
    regexp {inst:Garnet_SoC_pad_frame/(\S*)} $x dummy y;
    create_route_halo -inst $y -bottom_layer M1 -top_layer M9 -space 15
} 
foreach x [get_db insts *dtdc*] {
    regexp {inst:Garnet_SoC_pad_frame/(\S*)} $x dummy y; 
    create_route_halo -inst $y -bottom_layer M1 -top_layer M9 -space 15
} 

write_db init1.db

gen_power

# min and max x or y coords for stripes
set min 90
set max 4808


#Horizontal stripes M8
for {set row [expr $max_row]} {$row >= $min_row} {incr row -1} {
    set tile $tiles($row,$min_col,name)
    set offset [expr $tiles($row,$min_col,y_loc) + $tile_stripes(M8,start)]
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
    for {set col $min_col} {$col <= $max_col} {incr col 1} {
        set tile $tiles($min_row,$col,name)
        set offset [expr $tiles($min_row,$col,x_loc) + $tile_stripes($layer,start)]
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

#foreach x [get_db insts *icovl*] {
#  set bbox [get_db $x .bbox]
#  set bbox1 [lindex $bbox 0]
#  set l0 [expr [lindex $bbox1 0] - 13] 
#  set l1 [expr [lindex $bbox1 1] - 13] 
#  set l2 [expr [lindex $bbox1 2] + 13] 
#  set l3 [expr [lindex $bbox1 3] + 13] 
#  if {$l0 < 10} continue;
#  edit_cut_route -box [list $l0 $l1 $l2 $l3] -only_visible_wires
#  gui_select -rect [list $l0 $l1 $l2 $l3]
#  puts "Deleting $l0 $l1 $l2 $l3"
#  delete_selected_from_floorplan
#}
#
#
#foreach x [get_db insts *icovl*] {
#  set bbox [get_db $x .bbox]
#  set bbox1 [lindex $bbox 0]
#  set l0 [expr [lindex $bbox1 0] - 2.2] 
#  set l1 [expr [lindex $bbox1 1] - 2.2] 
#  set l2 [expr [lindex $bbox1 2] + 2.2] 
#  set l3 [expr [lindex $bbox1 3] + 2.2] 
#  if {$l0 < 10} continue;
#  create_route_blockage -area [list $l0 $l1 $l2 $l3]  -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9}
#  
#}
#
#foreach x [get_db insts *dtdc*] {
#  set bbox [get_db $x .bbox]
#  set bbox1 [lindex $bbox 0]
#  set l0 [expr [lindex $bbox1 0] - 13] 
#  set l1 [expr [lindex $bbox1 1] - 13] 
#  set l2 [expr [lindex $bbox1 2] + 13] 
#  set l3 [expr [lindex $bbox1 3] + 13] 
#  if {$l0 < 10} continue;
#  edit_cut_route -box [list $l0 $l1 $l2 $l3] -only_visible_wires
#  gui_select -rect [list $l0 $l1 $l2 $l3]
#  puts "Deleting $l0 $l1 $l2 $l3"
#  delete_selected_from_floorplan
#}


write_db fp.db
