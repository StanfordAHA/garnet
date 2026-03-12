#=========================================================================
# place-tile-array.tcl
#=========================================================================
#
# Author : Po-Han Chen
# Date   : 

proc snap_to_grid {input granularity} {
   set new_value [expr ceil($input / $granularity) * $granularity]
   return $new_value
}

set hori_pitch [dbGet top.fPlan.coreSite.size_x]
set vert_pitch [dbGet top.fPlan.coreSite.size_y]
set tech_pitch_x [expr 5 * $hori_pitch]
set tech_pitch_y [expr 1 * $vert_pitch]

# set rows_per_pipeline_stage $::env(pipeline_config_interval)
set rows_per_pipeline_stage 8
set pipeline_stage_height [expr 20 * $tech_pitch_y]

#-------------------------------------------------------------------------
# Collect Tile Information
#-------------------------------------------------------------------------
set array_width  0
set array_height 0
set min_col 99999
set min_row 99999
set max_row -99999
set max_col -99999
set pe_tiles [get_cells -hier -filter "ref_name=~Tile_PE*"]
set mem_tiles [get_cells -hier -filter "ref_name=~Tile_MemCore*"]

foreach_in_collection tile [concat $pe_tiles $mem_tiles] {
  set tile_name [get_property $tile full_name]
  regexp {X(\S*)_} $tile_name -> col
  regexp {Y(\S*)} $tile_name -> row

  # Convert hex IDs to decimal
  set row [expr 0x$row + 0]
  set col [expr 0x$col + 0]

  set tiles($row,$col,name)   $tile_name
  set tiles($row,$col,width)  [dbGet [dbGet -p top.insts.name $tile_name -i 0].cell.size_x]
  set tiles($row,$col,height) [dbGet [dbGet -p top.insts.name $tile_name -i 0].cell.size_y]

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
puts "Tile Array Size: $min_row to $max_row rows, $min_col to $max_col columns"

#-------------------------------------------------------------------------
# Place Tiles
#-------------------------------------------------------------------------
# set tile_array_llx [snap_to_grid 1360 $tech_pitch_x]
# set tile_array_llx [snap_to_grid 1403.2 $tech_pitch_x]
set tile_array_llx [snap_to_grid 1735.0 $tech_pitch_x]
set tile_array_lly [snap_to_grid  120.0 $tech_pitch_y]

set y_loc $tile_array_lly
for {set row $max_row} {$row >= $min_row} {incr row -1} {
    # reset x_loc
    set x_loc $tile_array_llx
    for {set col $min_col} {$col <= $max_col} {incr col} {
        # place tile
        set tiles($row,$col,x_loc) $x_loc
        set tiles($row,$col,y_loc) $y_loc
        placeInstance $tiles($row,$col,name) $x_loc $y_loc -fixed
        # increment x_loc
        set x_loc [expr $x_loc + $tiles($row,$col,width)]
    }
    # increment y_loc
    set y_loc [expr $y_loc + $tiles($row,$min_col,height)]
    # add extra space if this is a pipeline stage
    if { ($rows_per_pipeline_stage != 0) && ([expr ($row-$min_row) % $rows_per_pipeline_stage] == 0)} {
        set y_loc [expr $y_loc + $pipeline_stage_height]
    }
}

# after placement, we know the tile array size
set tile_array_llx [dbGet [dbGet -p top.insts.name $tiles($max_row,$min_col,name)].box_llx]
set tile_array_lly [dbGet [dbGet -p top.insts.name $tiles($max_row,$min_col,name)].box_lly]
set tile_array_urx [dbGet [dbGet -p top.insts.name $tiles($min_row,$max_col,name)].box_urx]
set tile_array_ury [dbGet [dbGet -p top.insts.name $tiles($min_row,$max_col,name)].box_ury]

#-------------------------------------------------------------------------
# Place Routing Blockages and Halos
#-------------------------------------------------------------------------
set tb_margin [expr $vert_pitch * 1]
set lr_margin [expr $hori_pitch * 3]
for {set row $min_row} {$row <= $max_row} {incr row} {
    for {set col $min_col} {$col <= $max_col} {incr col} {
        # Add Power stripe Routing Blockages over tiles on M3, ADK_POWER_MESH_BOT_LAYER,
        # because the tiles already have these stripes
        set llx [dbGet [dbGet -p top.insts.name $tiles($row,$col,name)].box_llx]
        set lly [dbGet [dbGet -p top.insts.name $tiles($row,$col,name)].box_lly]
        set urx [dbGet [dbGet -p top.insts.name $tiles($row,$col,name)].box_urx]
        set ury [dbGet [dbGet -p top.insts.name $tiles($row,$col,name)].box_ury]
        # createRouteBlk \
        #     -box [expr $llx - $lr_margin] [expr $lly - $tb_margin] [expr $urx + $lr_margin] [expr $ury + $tb_margin] \
        #     -layer [list m1 m2 m3 m4 m5 m6 m7 m8] \
        #     -pgnetonly
        # put route blockage

        set margin 0.32

        createRouteBlk \
            -name cgra_tile_r${row}c${col}_rblk_sig_non_pin_layers \
            -layer { m1 m2       m5 m6 m7 m8 } \
            -inst $tiles($row,$col,name) \
            -spacing $margin \
            -exceptpgnet \
            -cover
        createRouteBlk \
            -name cgra_tile_r${row}c${col}_rblk_sig_pin_layers \
            -layer {       m3 m4             } \
            -inst $tiles($row,$col,name) \
            -exceptpgnet \
            -cover
        createRouteBlk \
            -name cgra_tile_r${row}c${col}_rblk_bot_m4 \
            -layer {          m4             } \
            -box $llx [expr $lly - $margin] $urx $lly \
            -exceptpgnet
        createRouteBlk \
            -name cgra_tile_r${row}c${col}_rblk_top_m4 \
            -layer {          m4             } \
            -box $llx $ury $urx [expr $ury + $margin] \
            -exceptpgnet
        createRouteBlk \
            -name cgra_tile_r${row}c${col}_rblk_left_m3 \
            -layer {       m3                } \
            -box [expr $llx - $margin] $lly $llx $ury \
            -exceptpgnet
        createRouteBlk \
            -name cgra_tile_r${row}c${col}_rblk_right_m3 \
            -layer {       m3                } \
            -box $urx $lly [expr $urx + $margin] $ury \
            -exceptpgnet
        createRouteBlk \
            -name cgra_tile_r${row}c${col}_rblk_pwr \
            -layer { m1 m2 m3 m4 m5 m6 m7 m8 } \
            -inst $tiles($row,$col,name) \
            -pgnetonly \
            -spacing [expr 2*$margin] \
            -cover
        addHaloToBlock \
            [expr $hori_pitch * 3] \
            [expr $vert_pitch * 2] \
            [expr $hori_pitch * 3] \
            [expr $vert_pitch * 2] \
            -snapToSite \
            $tiles($row,$col,name)
    }
}

#-------------------------------------------------------------------------
# Place Via Blockages
#-------------------------------------------------------------------------
# Create a blockage for PG vias around the grid since vias too close to the
# grid edges can block connections from pins on the edges to tie cells.
# --left
createRouteBlk \
    -box \
        [expr $tile_array_llx - $hori_pitch * 7] \
        $tile_array_lly \
        $tile_array_llx \
        $tile_array_ury \
    -pgnetonly \
    -cutLayer all
# --top
createRouteBlk \
    -box \
        $tile_array_llx \
        $tile_array_ury \
        $tile_array_urx \
        [expr $tile_array_ury + $vert_pitch] \
    -pgnetonly \
    -cutLayer all
# --right 
createRouteBlk \
    -box \
        $tile_array_urx \
        $tile_array_lly \
        [expr $tile_array_urx + $hori_pitch * 7] \
        $tile_array_ury \
    -pgnetonly \
    -cutLayer all
# --bottom
createRouteBlk \
    -box \
        $tile_array_llx \
        [expr $tile_array_lly - $vert_pitch] \
        $tile_array_urx \
        $tile_array_lly \
    -pgnetonly \
    -cutLayer all

#-------------------------------------------------------------------------
# Tile ID Connections
#-------------------------------------------------------------------------
# TODO: This code cannot work until the dont_touch constraints worked after synthesis
#       Which I believe I already fixed it.
set connection_layer [dbGet -p head.layers.name M4]
set connection_width [dbGet $connection_layer.wrongwayWidth]
# Iterate over all tiles
for {set row $min_row} {$row <= $max_row} {incr row} {
  for {set col $min_col} {$col <= $max_col} {incr col} {
    # For this tile, get all of the tile id pins
    set tile_id_pins [get_pins $tiles($row,$col,name)/tile_id*]
    set num_id_pins [sizeof_collection $tile_id_pins]
    # The ID pins are on the left side of the tile,
    # all have same x coordinate as the tile itself
    set id_pin_x [dbGet [dbGet top.insts.name -p $tiles($row,$col,name)].box_llx]
    # Iterate over tile id pins for this tile and connect each
    # to the corresponding hi/lo pin
    for {set index 0} {$index < $num_id_pins} {incr index} {
      set id_pin [index_collection $tile_id_pins [expr $num_id_pins - $index - 1]]
      set id_pin_y [get_property $id_pin y_coordinate]
      set id_net [get_net -of_objects $id_pin]
      set id_net_name [get_property $id_net hierarchical_name]
      # Here, we find whcih hi/lo pin is supposed to drive this tile_id input pin
      # We're going to draw a shape to connect these two pins

      # Find the nearest hi/lo pin to which we can connect the id pin
      set tie_pin [get_pins -of_objects $id_net -filter "hierarchical_name!~*id*"] 
          
      # Build the shape that connects id pin to hi/lo pin
      set tie_pin_y [get_property $tie_pin y_coordinate]
      # For X, start our shape at the lefmost edge of the tile
      set llx [expr $id_pin_x]
      # Come into the tile by connection_width
      set urx [expr $llx + $connection_width]
      # For y, start at whichever of the two pins is lower 
      set lly [expr min($tie_pin_y, $id_pin_y)]
      # End at the higher of the two pins
      set ury [expr max($tie_pin_y, $id_pin_y)]
      add_shape -net $id_net_name -layer $connection_layer -rect $llx $lly $urx $ury
    }
  }
}
