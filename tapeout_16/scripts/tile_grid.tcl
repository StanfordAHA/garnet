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
set start_x 0
set start_y 0

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

read_netlist results_syn/syn_out.v -top GarnetSOC

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
set tile_info [calculate_tile_info $Tile_PE_util $Tile_MemCore_util $min_tile_height $min_tile_width $tile_x_grid $tile_y_grid $tile_stripes_array]
set tile_grid_width 32
set tile_grid_height 16
set fp_width [expr ($tile_grid_width * 0.75 * [dict get $tile_info Tile_PE,width]) + ($tile_grid_width * 0.25 * [dict get $tile_info Tile_MemCore,width])]
set fp_height [expr $tile_grid_height * [dict get $tile_info Tile_PE,height]]
create_floorplan -site core -die_size $fp_width $fp_height 0 0 0 0
set_multi_cpu_usage -local_cpu 8
snap_floorplan_io


# snap separations to grid
set tile_separation_x [snap_to_grid $tile_separation_x $tile_x_grid 0]
set tile_separation_y [snap_to_grid $tile_separation_y $tile_y_grid 0]


# snap x and y start to grid
set start_x [expr [snap_to_grid $start_x $tile_x_grid 0]]
set start_y [expr [snap_to_grid $start_y $tile_y_grid 0]]

# We will find the grid width/height from tiles
set max_row 0
set max_col 0

set min_row 99999
set min_col 99999

# put all of the tiles into a 2D array so we know their relative locations in grid
foreach_in_collection tile [get_cells -hier -filter "ref_name=~Tile_PE* || ref_name=~Tile_MemCore*"] {
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

set max_row [expr $tile_grid_height + $min_row - 1]
set max_col [expr $tile_grid_width + $min_col - 1]
# Get grid height/width from max_row/col
set grid_height [expr $max_row - $min_row + 1]
set grid_width [expr $max_col - $min_col + 1]

set m8_s2s [dict get $tile_info M8,s2s]
set m9_s2s [dict get $tile_info M9,s2s]

#Actually place the tiles
set y_loc $start_y
for {set row $max_row} {$row >= $min_row} {incr row -1} {
  set x_loc $start_x
  for {set col $min_col} {$col <= $max_col} {incr col} {
    set tiles($row,$col,x_loc) $x_loc
    set tiles($row,$col,y_loc) $y_loc
    place_inst $tiles($row,$col,name) $x_loc $y_loc -fixed
    create_route_blockage -name $tiles($row,$col,name) -inst $tiles($row,$col,name) -cover -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9} -spacing 0
    #Update x location for next tile using rightmost boundary of this tile
    set x_loc [get_property [get_cells $tiles($row,$col,name)] x_coordinate_max]
    # Add spacing between tiles if desired
    set x_loc [expr $x_loc + $tile_separation_x]
    set x_loc [snap_to_grid $x_loc $m9_s2s 0]
  }
  # Update y location for next row using topmost boundary of this row
  set y_loc [get_property [get_cells $tiles($row,0,name)] y_coordinate_max]
  # Add spacing between rows if desired
  set y_loc [expr $y_loc + $tile_separation_y]
  set y_loc [snap_to_grid $y_loc $m8_s2s 0]
}

#Get bbox of tile grid
set grid_llx $start_x
set grid_lly $start_y
set grid_urx [get_property [get_cells $tiles($min_row,$max_col,name)] x_coordinate_max]
set grid_ury [get_property [get_cells $tiles($min_row,$max_col,name)] y_coordinate_max]

# Manually connect all of the tile_id pins
set connection_width 0.08
set pin_depth [expr 0.376 / 2]
set connection_layer M4
for {set row $min_row} {$row <= $max_row} {incr row} {
  for {set col $min_col} {$col <= $max_col} {incr col} {
    set tile_id_pins [get_pins $tiles($row,$col,name)/tile_id*]
    set num_id_pins [sizeof_collection $tile_id_pins]
    for {set index 0} {$index < $num_id_pins} {incr index} {
      set id_pin [index_collection $tile_id_pins [expr $num_id_pins - $index - 1]]
      set id_pin_x [get_property $id_pin x_coordinate]
      set id_pin_y [get_property $id_pin y_coordinate]
      set id_net [get_net -of_objects $id_pin]
      set id_net_name [get_property $id_net name]
      set tie_pin [get_pins -of_objects $id_net -filter "hierarchical_name!~*id*"] 
      set tie_pin_y [get_property $tie_pin y_coordinate]
      set llx [expr $id_pin_x - $pin_depth]
      set urx [expr $llx + $connection_width]
      set lly [expr min($tie_pin_y, $id_pin_y)]
      set ury [expr max($tie_pin_y, $id_pin_y)]
      create_shape -net $id_net_name -layer $connection_layer -rect $llx $lly $urx $ury
    }
  }
}

write_db tile_grid.db

eval_legacy {
  source ../../scripts/stream_func.tcl
  gen_gds tile_grid.gds
}
