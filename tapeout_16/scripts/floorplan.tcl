#######################################################################
##
## CGRA layout flow. Created with lots of help from Brian Richards
## and Stevo Bailey.
##
###################################################################

delete_global_net_connections
connect_global_net VDDPST -type pgpin -pin VDDPST -inst *
connect_global_net VSS -type pgpin -pin VSSPST -inst * 
connect_global_net VDD -type pgpin -pin VDD -inst *
connect_global_net VDD -type tiehi
connect_global_net VSS -type pgpin -pin VSS -inst *
connect_global_net VSS -type tielo
connect_global_net VDD -type pgpin -pin VPP -inst *
connect_global_net VSS -type pgpin -pin VBB -inst *

########################################################################
# ??? sr 1912 iphy pins are tied low by the above command
#   "connect_global_net VSS -type tielo"
# b/c they have this property .constant==0 for some reason
# Keeping them tied low is causing problems later so I'm disconnecting them:
set iphy_tielo_pins [ \
  get_db pins -if { .constant != no_constant && .name == *iphy* }
]
puts "@file_info # "
puts "@file_info # Disconnect iphy pins from tielo"
puts "@file_info: BEFORE (should say net=VSS)"
foreach p $iphy_tielo_pins {
    # pin_name "iphy/foo" => "foo"
    set pin_name [ get_db $p .name ]
    set pin_name [ string range $pin_name 5 end ]
    puts "@file_info:     net=[ get_db $p .net ] $p"
    disconnect_pin -inst iphy -pin $pin_name -net VSS
}
puts "@file_info: AFTER (should say net={} )"
foreach p $iphy_tielo_pins {
    puts "@file_info:     net=[ get_db $p .net ] $p"
}

###Initialize the floorplan
create_floorplan -core_margins_by die -die_size_by_io_height max -site core -die_size 4900.0 4900.0 100 100 100 100

# If everything is set up all canonical and correct, io_file
# will be in enclosing gitlab repo e.g. we should be here:
#   aha-arm-soc-june-2019/components/cgra/garnet/tapeout_16/synth/GarnetSOC_pad_frame
# ...and io_file should be here:
#   aha-arm-soc-june-2019/components/pad_frame/io_file
set if1 ../../../../../pad_frame/io_file
# Note ../../../../.. will not exist in buildkite; want to instead look for...?
# set if2 /sim/ajcars/aha-arm-soc-june-2019/components/pad_frame/io_file
# This one is better :)
set if2 /sim/steveri/soc/components/pad_frame/io_file
########################################################################
puts "@file_info # "
puts "@file_info # ALERT FIXME TERRIBLE HACK AHEAD"
puts "@file_info # sr 1912 existing io_file places two pads on top of each other (!!!)."
puts "@file_info # See github issue tht I plan to file shortly."
puts "@file_info # In the meantime, this new io_file manually moves to rte pad off to"
puts "@file_info # the right a bit so that it does not sit under a VDD pad :("
puts "@file_info # "
# set if1 ../../examples/io_file_hacked
########################################################################
if { [file exists $if1] } {
  puts "Found io_file $if1"
  read_io_file $if1 -no_die_size_adjust 
    # FIXME
    # **WARN: (IMPFP-53):     Failed to find instance 'IOPAD_left_POC_DIG'.
    # **WARN: (IMPFP-53):     Failed to find instance 'IOPAD_right_POC_DIG'.
} elseif { [file exists $if2] } {
  puts "@file_info: WARNING Could not find io_file '$if1'"
  puts "@file_info: WARNING Using pre-built io_file '$if2'"
  read_io_file $if2 -no_die_size_adjust 
} else {
  puts stderr "ERROR: Cannot find $if1"
  puts stderr "ERROR: And also cannot find $if2"
  exit 13
}
set_multi_cpu_usage -local_cpu 8
snap_floorplan_io
# "check_floorplan" at this point should give 0 warnings, 0 errors


# Add iphy (butterphy) instance, pwr/gnd stripes, and blockages
source ../../scripts/phy_placement.tcl

# snap separations to grid
# Note "tile_separation_x" is defined in "init_design_multi_vt.tcl"
# which is sourced in "top_garnet_staged.tcl"
set tile_separation_x [snap_to_grid $tile_separation_x $tile_x_grid 0]
set tile_separation_y [snap_to_grid $tile_separation_y $tile_y_grid 0]


# actual core to edge
set core_to_edge 99.99

set tile_info [calculate_tile_info $Tile_PE_util $Tile_MemCore_util $min_tile_height $min_tile_width $tile_x_grid $tile_y_grid $tile_stripes_array]

# snap x and y start to grid
set start_x [expr [snap_to_grid $start_x $tile_x_grid $core_to_edge]]
set start_y [expr [snap_to_grid $start_y $tile_y_grid $core_to_edge]]

# We will find the grid width/height from tiles
set max_row 0
set max_col 0

set min_row 99999
set min_col 99999

# put all of the tiles into a 2D array so we know their relative locations in grid
# NOTE if cannot find Tile_PE instances you probably read a bad results_syn directory
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
    create_route_blockage -name $tiles($row,$col,name) -inst $tiles($row,$col,name) -cover -layers {M2 M3 M4 M5 M6 M7 M8 M9} -spacing 0
    #Update x location for next tile using rightmost boundary of this tile
    set x_loc [get_property [get_cells $tiles($row,$col,name)] x_coordinate_max]
    # Add spacing between tiles if desired
    set x_loc [expr $x_loc + $tile_separation_x]
    set x_loc [snap_to_grid $x_loc $m9_s2s $core_to_edge]
  }
  # Update y location for next row using topmost boundary of this row
  set y_loc [get_property [get_cells $tiles($row,0,name)] y_coordinate_max]
  # Add spacing between rows if desired
  set y_loc [expr $y_loc + $tile_separation_y]
  set y_loc [snap_to_grid $y_loc $m8_s2s $core_to_edge]
}
# check_floorplan => 0 warn 0 err

#Get bbox of tile grid
set grid_llx $start_x
set grid_lly $start_y
set grid_urx [get_property [get_cells $tiles($min_row,$max_col,name)] x_coordinate_max]
set grid_ury [get_property [get_cells $tiles($min_row,$max_col,name)] y_coordinate_max]

# Create M1 PG net blockage above tile grid
create_route_blockage -area $grid_llx $grid_ury $grid_urx [expr $grid_ury + 2] -layers M1 -pg_nets

# Create M1 PG net blockage below tile grid
create_route_blockage -area $grid_llx $grid_lly $grid_urx [expr $grid_lly - 2] -layers M1 -pg_nets

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
      set id_net_name [get_property $id_net hierarchical_name]
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


# Get Collection of all Global buffer SRAMs
set bank_height 8
set glbuf_srams [get_cells *cgra*/*GlobalBuffer*/* -filter "ref_name=~TS1N*"]
set sram_width 60.755
set sram_height 226.32

### SRAM HALO CALCULATION ###
set sram_halo_margin_b $target_sram_margin
set sram_halo_margin_l [snap_to_grid $target_sram_margin 0.09 0]
set sram_halo_margin_t $target_sram_margin
set snapped_width [snap_to_grid [expr 2 * $sram_width] 0.09 0]
set width_diff [expr $snapped_width - [expr 2 * $sram_width]]
set sram_halo_margin_r [snap_to_grid $target_sram_margin 0.09 $width_diff]
### END SRAM HALO CALCULATION ###

set glbuf_sram_start_x [snap_to_grid [expr $grid_llx - 100] [dict get $tile_info M9,s2s] $core_to_edge] 
set glbuf_sram_start_y [expr $grid_ury + 500]
set sram_spacing_x_even 0
#set sram_spacing_x_odd [expr [dict get $tile_info M9,s2s] + 4]
set sram_spacing_x_odd [expr 2 * [dict get $tile_info M9,s2s] + 4]

# Ensure that every SRAM has the same relative distance to set of power straps to avoid DRCs
set unit_width [expr (2 * $sram_width) + $sram_spacing_x_even + $sram_spacing_x_odd]
set snapped_width [snap_to_grid $unit_width [dict get $tile_info M9,s2s] 0]
set sram_spacing_x_odd [expr $sram_spacing_x_odd + ($snapped_width - $unit_width)]
set sram_spacing_y 0
# Don't place SRAMS over ICOVL cells in center of chip
set x_block_left [expr 2340 - $sram_width - $sram_spacing_x_odd - 3]
set x_block_right [snap_to_grid 2457 [dict get $tile_info M9,s2s] $core_to_edge]

glbuf_sram_place $glbuf_srams $glbuf_sram_start_x $glbuf_sram_start_y $sram_spacing_x_even $sram_spacing_x_odd $sram_spacing_y $bank_height $sram_height $sram_width $x_block_left $x_block_right 0 1 $target_sram_margin

# Get Collection of all Processor SRAMs
set ps_sram_start_x [snap_to_grid [expr $grid_urx + 700] [dict get $tile_info M9,s2s] $core_to_edge]
set bank_height 3
set sram_width 60.755
set sram_height 226.32
#set sram_start_y [expr ($grid_lly) + (($grid_ury - $grid_lly - ($bank_height * $sram_height)) / 2)]
#set ps_sram_start_y [expr ($grid_ury) - (($grid_ury - $grid_lly - ($bank_height * $sram_height)) / 3)]
set ps_sram_start_y [expr $grid_ury - 600]
set ps_srams [get_cells *proc_tlx*/* -filter "ref_name=~TS1N*"]
set sram_spacing_x_even 0
set sram_spacing_x_odd [expr 2 * [dict get $tile_info M9,s2s] + 4]
set sram_spacing_y 0
# Ensure that every SRAM has the same relative distance to set of power straps to avoid DRCs
set unit_width [expr (2 * $sram_width) + $sram_spacing_x_even + $sram_spacing_x_odd]
set snapped_width [snap_to_grid $unit_width [dict get $tile_info M9,s2s] 0]
set sram_spacing_x_odd [expr $sram_spacing_x_odd + ($snapped_width - $unit_width)]


glbuf_sram_place $ps_srams $ps_sram_start_x $ps_sram_start_y $sram_spacing_x_even $sram_spacing_x_odd $sram_spacing_y $bank_height $sram_height $sram_width 0 0 0 1 $target_sram_margin
# Create halos around all of the SRAMs we just placed
#create_place_halo -cell TS1N16FFCLLSBLVTC2048X64M8SW -halo_deltas $sram_halo_margin_l $sram_halo_margin_b $sram_halo_margin_r $sram_halo_margin_t
create_place_halo -cell TS1N16FFCLLSBLVTC2048X64M8SW -halo_deltas 3 3 3 3
# Create halos around all of the CGRA Tiles we just placed
set tile_halo_margin [snap_to_grid $target_tile_margin 0.09 0]
set tile_halo_margin [snap_to_grid $target_tile_margin 0.09 0]
#create_place_halo -cell Tile_PE -halo_deltas $tile_halo_margin $tile_halo_margin $tile_halo_margin $tile_halo_margin
#create_place_halo -cell Tile_MemCore -halo_deltas $tile_halo_margin $tile_halo_margin $tile_halo_margin $tile_halo_margin
create_place_halo -cell Tile_PE -halo_deltas 3 3 3 3
create_place_halo -cell Tile_MemCore -halo_deltas 3 3 3 3

# Need to snap all corners when placing guides, else
# check_floorplan will give ERROR(s) later
set saved_SnapAllCorners_preference [ get_preference SnapAllCorners ]
puts "@file_info SnapAllCorners hack"
puts "saved_SnapAllCorners_preference=$saved_SnapAllCorners_preference"
set_preference SnapAllCorners 1

#Create guide for all cgra related cells around tile grid
# set cgra_subsys [get_cells -hier cgra_subsystem] # oopsie no
  set cgra_subsys [get_cells -hier core_cgra_subsystem]
set name [get_property $cgra_subsys hierarchical_name]
set margin 200
puts "create_guide -area [expr $grid_llx - $margin] $core_to_edge [expr $grid_urx + $margin] [expr $grid_ury + $margin] -name $name"
# create_guide -area 403.99 99.99 3545.562 1883.887 -name core_cgra_subsystem
create_guide -area [expr $grid_llx - $margin] $core_to_edge [expr $grid_urx + $margin] [expr $grid_ury + $margin] -name $name
# Without snap_all_corners, get this warning here and ERRORs later
# **WARN: (IMPFP-7400): Module core_cgra_subsystems vertexes
#   (404.0100000000 , 1883.8810000000) (3545.5820000000 ,
#   1883.8810000000) (3545.5820000000 , 99.9840000000) are NOT on
#   FinFet/InstanceGrid. Please use command floorplan_get_snap_rule to
#   check current Grid settings. And use command floorplan_Set_snap_rule
#   to change which grid to snap to. Use command set_preference
#   SnapAllCorners 1(0) control if all vertexes need snap to grid.
# create_guide -area 403.99 99.99 3545.562 1883.887 -name core_cgra_subsystem
# create_guide -area 400 100 3545 1883 -name core_cgra_subsystem

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
puts "create_guide -area $gc_llx $grid_ury $gc_urx $gc_ury -name $gc_name"
create_guide -area $gc_llx $grid_ury $gc_urx $gc_ury -name $gc_name

#Create region for global buffer
set glbuf [get_cells -hier *GlobalBuffer*]
set glbuf_area [get_property $glbuf area]
set glbuf_name [get_property $glbuf hierarchical_name]
set glbuf_llx 100
set glbuf_urx 4900
create_guide -area $glbuf_llx $grid_ury $glbuf_urx $glbuf_sram_start_y -name $glbuf_name

#Create guide for processor subsystem
set ps [get_cells -hier *proc_tlx*]
set ps_name [get_property $ps hierarchical_name]
create_guide -area [expr $grid_urx - 100] [expr $ps_sram_start_y - 100] 4900 [expr $ps_sram_start_y * 3 + 100] -name $ps_name

# Without SnapAllCorners, check_floorplan below will give ERROR
puts "restoring SnapAllCorners_preference=$saved_SnapAllCorners_preference"
set_preference SnapAllCorners $saved_SnapAllCorners_preference
check_floorplan

source ../../scripts/vlsi/flow/scripts/gen_floorplan.tcl
set_multi_cpu_usage -local_cpu 8

# FIXME I do a thing once...why do it again? (steveri 1912)
set_multi_cpu_usage -local_cpu 8

eval_legacy {editPowerVia -area {1090 1090 3840 3840} -delete_vias true}

foreach x \
    [get_property \
         [get_cells -filter "ref_name=~*PDD* || ref_name=~*PRW* || ref_name=~*FILL*" ]\
         full_name \
        ] \
    {
        disconnect_pin -inst $x -pin RTE
    }

set_db route_design_antenna_diode_insertion true 
set_db route_design_antenna_cell_name ANTENNABWP16P90 
set_db route_design_fix_top_layer_antenna true 

# Add ICOVL alignment cells to center/core of chip
set_proc_verbose add_core_fiducials; add_core_fiducials

write_db placed_macros.db

gen_power

########################################################################
# sr 2001 I think this is preventing endcap generation, so I'm moving it
# from before to after gen_power...
# FIXME/TODO Also I think this is (at least partially) redundant with
# code in gen_floorplan.tcl, search for "bigblock"
# ----
# sr 1912 Add new bigblocks
# icovl halos apparently not sufficient to keep routes out of
# blank space surrounding icovl center array cells. So we add (yet
# another) set of route blockages.
# 
# Add new bigblocks
# Big route blockage around each central icovl cell
# Otherwise weird spacing problems when routing later
# But not too big else adjacency shorts :(
# foreach inst [get_db insts ifid_icovl_cc_33] {
foreach inst [get_db insts ifid_icovl_cc_*] {
    set name [get_db $inst .name]_bigblockfp
    set rect [get_db $inst .place_halo_bbox]
    # puts [get_db $inst .bbox]
    set llx [expr [get_db $inst .bbox.ll.x] - 14 ]
    set lly [expr [get_db $inst .bbox.ll.y] - 14 ]
    set urx [expr [get_db $inst .bbox.ur.x] + 14 ]
    set ury [expr [get_db $inst .bbox.ur.y] + 14 ]
    set rect "$llx $lly $urx $ury"
    # echo $llx $lly $urx $ury; echo $rect; 
    # echo create_route_blockage -name $name -rect $rect -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9}
    create_route_blockage -name $name -rects $rect -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9}
}
########################################################################



# M7-M9 power straps. vertical. very fast (< 10m)
# 0715-
foreach layer {M7 M8 M9} {
    add_stripes \
        -nets {VDD VSS} \
        -layer $layer \
        -direction [dict get $tile_info $layer,direction] \
        -start [expr $core_to_edge + [dict get $tile_info $layer,start]] \
        -width [dict get $tile_info $layer,width] \
        -spacing [dict get $tile_info $layer,spacing] \
        -set_to_set_distance [dict get $tile_info $layer,s2s]
    eval_legacy {editPowerVia -delete_vias true}
}

# This seems to take some time, particularly between layers 7 and ?1?...maybe 15m in all
eval_legacy {editPowerVia -delete_vias true}
eval_legacy {editPowerVia -add_vias true -orthogonal_only true -top_layer 9 -bottom_layer 8}
eval_legacy {editPowerVia -add_vias true -orthogonal_only true -top_layer 8 -bottom_layer 7}
eval_legacy {editPowerVia -add_vias true -orthogonal_only true -top_layer 7 -bottom_layer 1}

write_db gen_power.db

# Note: proc gen_bumps is defined in gen_floorplan.tcl
gen_bumps
snap_floorplan -all

# gen_route_bumps
# FIXED bump routing sr 12/2019
# Old proc "gen_route_bumps" warned "too many bumps are selected"
# and it took a long time and a lot of bumps didn't get routed.
# New routine getn_route_bumps_sr below uses area restrictions
# etc. to only do a few bumps at a time.
# 
# New route_bumps routine "gen_route_bumps_sr" has
# - incremental bump routing instead of all at once
# - better check for routed vs. unrouted bumps
source ../../scripts/gen_route_bumps_sr.tcl
set_proc_verbose gen_route_bumps_sr; # For debugging
gen_route_bumps_sr

# Skip retry because
# 1 should happen in gen_route_bumps
# 2 gen_route_bumps_sr gets all routable bumps
# 
# Try again to get any missed bumps/pads
# route_flip_chip -eco -target connect_bump_to_pad

# Everything should be connected now (note this only checks signal pads)
check_connectivity -nets pad*



# after routing bumps, insert io fillers
# "done_fp" is defined in vlsi/flow/scripts/gen_floorplan.tcl
set_proc_verbose done_fp; done_fp

# Drop RV power vias last
eval_legacy {
  editPowerVia -add_vias true -orthogonal_only true -top_layer AP -bottom_layer 9
}

check_io_to_bump_connectivity
check_connectivity -nets pad*

write_db powerplanned.db
