proc place_ios {width height ns_offset ew_offset} {
  source ../../scripts/helper_funcs.tcl
  source ../../scripts/params.tcl

  # snap offsets to pin grid (variable set in common.tcl)
  set ns_offset [snap_to_grid $ns_offset $pin_x_grid 0]
  set ew_offset [snap_to_grid $ew_offset $pin_y_grid 0]
  
  puts "Info: IO placement called with width $width and height $height"
  redirect io_file {puts "##"}
  redirect -append io_file {puts "(globals\n    version = 3\n    io_order = default\n)"}
  redirect -append io_file {puts "(iopin"}
  for {set i 0} {$i < 4} {incr i} {
    if {$i==0} {set tag right}
    if {$i==1} {set tag bottom}
    if {$i==2} {set tag left}
    if {$i==3} {set tag top}
    redirect -append io_file {puts "  ($tag"}
    set pports ""
    set qports ""
    set rports ""
    set sports ""
    set xports ""
    if {$i==0} {
      set pports [get_ports SB_*_EAST_SB_IN_B1_0*]
      set qports [get_ports SB_*_EAST_SB_OUT_B1[*]]
      set rports [get_ports SB_*_EAST_SB_IN_B16_0*]
      set sports [get_ports SB_*_EAST_SB_OUT_B16*]
      set xports ""
      set pin_grid $pin_y_grid
    }
    if {$i==1} {
      set pports [get_ports SB_*_SOUTH_SB_IN_B1_0*]
      set qports [get_ports SB_*_SOUTH_SB_OUT_B1[*]]
      set rports [get_ports SB_*_SOUTH_SB_IN_B16_0*]
      set sports [get_ports SB_*_SOUTH_SB_OUT_B16*]
      set xports [get_ports {clk_out reset_out stall_out*  config_out_config_* config_out_read* config_out_write* read_config_data}]
      set pin_grid $pin_x_grid
    }
    if {$i==2} {
      set pports [get_ports SB_*_WEST_SB_OUT_B1[*]]
      set qports [get_ports SB_*_WEST_SB_IN_B1_0*]
      set rports [get_ports SB_*_WEST_SB_OUT_B16*]
      set sports [get_ports SB_*_WEST_SB_IN_B16_0*]
      set xports [get_ports {tile_id* hi* lo*}]
      set pin_grid $pin_y_grid
    }
    if {$i==3} {
      set pports [get_ports SB_*_NORTH_SB_OUT_B1[*]]
      set qports [get_ports SB_*_NORTH_SB_IN_B1_0*]
      set rports [get_ports SB_*_NORTH_SB_OUT_B16*]
      set sports [get_ports SB_*_NORTH_SB_IN_B16_0*]
      set xports  [get_ports {clk reset stall* config_config_* config_read* config_write* read_config_data_in[*]}]
      set pin_grid $pin_x_grid
    }
    if {$i==0 || $i==2} {
      set layer [list 4 6]
      # Grid granularity integer multiple of layer pitch
      set grid [list 0.24 0.24]
      set grid_width [list 0.04 0.04]
      set max $height
      set offset $ew_offset
    } else {
      set layer [list 3 5]
      # Grid granularity integer multiple of layer pitch
      set grid [list 0.21 0.24]
      set grid_width [list 0.038 0.04]
      set max $width
      set offset $ns_offset
    }
    set off_incr $pin_grid
    set layer_index 0
    set ports ""
    set pports [sort_collection $pports full_name]
    set qports [sort_collection $qports full_name]
    set rports [sort_collection $rports full_name]
    set sports [sort_collection $sports full_name]
    # HACK: don't sort tile_id xports (side 2)
    if {([sizeof_collection $xports]>1) && ($i != 2)} {set xports [sort_collection $xports full_name]}
    set pin_count [list 0 0]
    #foreach ports {pports qports rports sports xports} {
    #}
    foreach_in_collection p $pports {
      set pn [get_property $p full_name]
      set xlayer [lindex $layer $layer_index]
      set xwidth [lindex $grid_width $layer_index] 
      set xgrid  [lindex $grid $layer_index]
      set pcount  [lindex $pin_count $layer_index]
      set gridded_offset [expr $offset + ($pcount*$xgrid)]
      incr pcount 
      lset pin_count $layer_index $pcount
      redirect -append io_file {puts "    (pin name=\"$pn\" offset=$gridded_offset layer=$xlayer depth=0.1 width=$xwidth place_status=fixed)"}
      incr layer_index
      if {$layer_index > [expr [llength $layer] - 1]} {
        set layer_index 0
        if {([expr (int($gridded_offset-0.8)%10)]==1) && ($i==1||$i==3)} {
          set offset [expr $offset + 3]
          #snap to grid again
          set offset [snap_to_grid $offset $pin_grid 0]
        }
      }
      if {$gridded_offset > $max} {
        puts "ERROR: Core side $tag less than needed"
      }
    }
    set offset [expr $offset + $off_incr]
    
    foreach_in_collection p $qports {
      set pn [get_property $p full_name]
      set xlayer [lindex $layer $layer_index]
      set xwidth [lindex $grid_width $layer_index] 
      set xgrid  [lindex $grid $layer_index]
      set pcount  [lindex $pin_count $layer_index]
      set gridded_offset [expr $offset + ($pcount*$xgrid)]
      incr pcount 
      lset pin_count $layer_index $pcount
      redirect -append io_file {puts "    (pin name=\"$pn\" offset=$gridded_offset layer=$xlayer depth=0.1 width=$xwidth place_status=fixed)"}
      incr layer_index
      if {$layer_index > [expr [llength $layer] - 1]} {
        set layer_index 0
        if {([expr (int($gridded_offset-0.8)%10)]==1) && ($i==1||$i==3)} {
          set offset [expr $offset + 3]
          #snap to grid again
          set offset [snap_to_grid $offset $pin_grid 0]
        }
      }
      if {$gridded_offset > $max} {
        puts "ERROR: Core side $tag less than needed"
      }
    }
    set offset [expr $offset + $off_incr]
    
    foreach_in_collection p $rports {
      set pn [get_property $p full_name]
      set xlayer [lindex $layer $layer_index]
      set xwidth [lindex $grid_width $layer_index] 
      set xgrid  [lindex $grid $layer_index]
      set pcount  [lindex $pin_count $layer_index]
      set gridded_offset [expr $offset + ($pcount*$xgrid)]
      incr pcount 
      lset pin_count $layer_index $pcount
      redirect -append io_file {puts "    (pin name=\"$pn\" offset=$gridded_offset layer=$xlayer depth=0.1 width=$xwidth place_status=fixed)"}
      incr layer_index
      if {$layer_index > [expr [llength $layer] - 1]} {
        set layer_index 0
        if {([expr (int($gridded_offset-0.8)%10)]==1) && ($i==1||$i==3)} {
          set offset [expr $offset + 3]
          #snap to grid again
          set offset [snap_to_grid $offset $pin_grid 0]
        }
      }
      if {$gridded_offset > $max} {
        puts "ERROR: Core side $tag less than needed"
      }
    }
    set offset [expr $offset + $off_incr]
  
    foreach_in_collection p $sports {
      set pn [get_property $p full_name]
      set xlayer [lindex $layer $layer_index]
      set xwidth [lindex $grid_width $layer_index] 
      set xgrid  [lindex $grid $layer_index]
      set pcount  [lindex $pin_count $layer_index]
      set gridded_offset [expr $offset + ($pcount*$xgrid)]
      incr pcount 
      lset pin_count $layer_index $pcount
      redirect -append io_file {puts "    (pin name=\"$pn\" offset=$gridded_offset layer=$xlayer depth=0.1 width=$xwidth place_status=fixed)"}
      incr layer_index
      if {$layer_index > [expr [llength $layer] - 1]} {
        set layer_index 0
        if {([expr (int($gridded_offset-0.8)%10)]==1) && ($i==1||$i==3)} {
          set offset [expr $offset + 3]
          #snap to grid again
          set offset [snap_to_grid $offset $pin_grid 0]
        }
      }
      if {$gridded_offset > $max} {
        puts "ERROR: Core side $tag less than needed"
      }
    }
    set offset [expr $offset + $off_incr]
    #HACK: Create more space for tile_id pins, which are side 2 xports
    if {$i == 2} { 
      set offset [expr $offset + 20 * $off_incr]
      #TODO: Re-sort the xports to be like | hi | id | lo | id | hi | id | etc...
      set hi_ports [remove_from_collection $xports [get_ports {tile_id* lo*}]]
      set lo_ports [remove_from_collection $xports [get_ports {tile_id* hi*}]]
      set tile_id_ports [remove_from_collection $xports [get_ports {lo* hi*}]]
      echo "hi : [sizeof_collection $hi_ports] pins"
      echo "lo : [sizeof_collection $lo_ports] pins"
      echo "id: [sizeof_collection $tile_id_ports] pins"
      set size 0
      set xports [remove_from_collection $xports [get_ports *]]
      set tile_id_index 0
      set hi_index 0
      set lo_index 0
      while {$size < 32} {
        append_to_collection xports [index_collection $hi_ports $hi_index]
        incr hi_index
        incr size
        append_to_collection xports [index_collection $tile_id_ports $tile_id_index]
        incr tile_id_index
        incr size
        append_to_collection xports [index_collection $lo_ports $lo_index]
        incr lo_index
        incr size
        append_to_collection xports [index_collection $tile_id_ports $tile_id_index]
        incr tile_id_index
        incr size
      }
      append_to_collection xports [index_collection $hi_ports $hi_index]

    }

    foreach_in_collection p $xports {
      set pn [get_property $p full_name]
      set xwidth [lindex $grid_width $layer_index] 
      set xgrid  [lindex $grid $layer_index]
      set pcount  [lindex $pin_count $layer_index]
      set gridded_offset [expr $offset + ($pcount*$xgrid)]
      set xlayer [lindex $layer $layer_index]
      incr pcount 
      lset pin_count $layer_index $pcount
      redirect -append io_file {puts "    (pin name=\"$pn\" offset=$gridded_offset layer=$xlayer depth=0.1 width=$xwidth place_status=fixed)"}
      if {$i != 2} {
        incr layer_index
      }
      if {$layer_index > [expr [llength $layer] - 1]} {
        set layer_index 0
        if {([expr (int($gridded_offset-0.8)%10)]==1) && ($i==1||$i==3)} {
          set offset [expr $offset + 3]
          #snap to grid again
          set offset [snap_to_grid $offset $pin_grid 0]
        }
      }
      if {$gridded_offset > $max} {
        puts "ERROR: Core side $tag less than needed"
      }
    }

    redirect -append io_file {puts "  )"}   
  }
  redirect -append io_file {puts ")"}
  loadIoFile io_file 
}
