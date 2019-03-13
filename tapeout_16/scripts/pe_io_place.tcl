proc place_ios {width height} {
#set width 83.0
#set height 50.112
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
    }
    if {$i==1} {
      set pports [get_ports SB_*_SOUTH_SB_IN_B1_0*]
      set qports [get_ports SB_*_SOUTH_SB_OUT_B1[*]]
      set rports [get_ports SB_*_SOUTH_SB_IN_B16_0*]
      set sports [get_ports SB_*_SOUTH_SB_OUT_B16*]
      set xports [get_ports {clk_out reset_out stall_out*  config_out_config_* config_read* config_write* read_config_data_in}]
    }
    if {$i==2} {
      set pports [get_ports SB_*_WEST_SB_OUT_B1[*]]
      set qports [get_ports SB_*_WEST_SB_IN_B1_0*]
      set rports [get_ports SB_*_WEST_SB_OUT_B16*]
      set sports [get_ports SB_*_WEST_SB_IN_B16_0*]
      set xports [get_ports {tile_id*}]
    }
    if {$i==3} {
      set pports [get_ports SB_*_NORTH_SB_OUT_B1[*]]
      set qports [get_ports SB_*_NORTH_SB_IN_B1_0*]
      set rports [get_ports SB_*_NORTH_SB_OUT_B16*]
      set sports [get_ports SB_*_NORTH_SB_IN_B16_0*]
      set xports  [get_ports {clk reset stall* config_config_* config_out_read* config_out_write* read_config_data[*]}]
    }
    set offset 0.4
    set off_incr 0.3
    if {$i==0 || $i==2} {
      set layer [list 4 6]
      set grid [list 0.24 0.24]
      set grid_width [list 0.04 0.04]
      set max $height
      set offset 10
    } else {
      set layer [list 3 5]
      set grid [list 0.21 0.24]
      set grid_width [list 0.038 0.04]
      set max $width
      set offset 15
    }
    set off_incr  [lindex $grid 1]   
    set layer_index 0
    set pports [sort_collection $pports full_name]
    set qports [sort_collection $qports full_name]
    set rports [sort_collection $rports full_name]
    set sports [sort_collection $sports full_name]
    if {[sizeof_collection $xports]>1} {set xports [sort_collection $xports full_name]}
    set pin_count [list 0 0]
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
      if {$layer_index > [expr [llength $layer] - 1]} {set layer_index 0; if {([expr (int($gridded_offset-0.8)%10)]==1) && ($i==1||$i==3)} {set offset [expr $offset + 3]}}
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
      if {$layer_index > [expr [llength $layer] - 1]} {set layer_index 0; if {([expr (int($gridded_offset-0.8)%10)]==1) && ($i==1||$i==3)} {set offset [expr $offset + 3]}}
      if { $gridded_offset > $max} {
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
      if {$layer_index > [expr [llength $layer] - 1]} {set layer_index 0; if {([expr (int($gridded_offset-0.8)%10)]==1) && ($i==1||$i==3)} {set offset [expr $offset + 3]}}
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
      if {$layer_index > [expr [llength $layer] - 1]} {set layer_index 0; if {([expr (int($gridded_offset-0.8)%10)]==1) && ($i==1||$i==3)} {set offset [expr $offset + 3]}}
      if { $gridded_offset > $max} {
        puts "ERROR: Core side $tag less than needed"
      }
    }
    set offset [expr $offset + $off_incr]
    set offset [expr $offset + 1] 
    foreach_in_collection p $xports {
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
      if {$layer_index > [expr [llength $layer] - 1]} {set layer_index 0; if {([expr (int($gridded_offset-0.8)%10)]==1) && ($i==1||$i==3)} {set offset [expr $offset + 3]}}
      if { $gridded_offset > $max} {
        puts "ERROR: Core side $tag less than needed"
      }
    } 
    redirect -append io_file {puts "  )"}   
  }
  redirect -append io_file {puts ")"}
  loadIoFile io_file 
}
