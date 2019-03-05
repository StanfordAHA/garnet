proc place_ios {width height} {
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
      set pports [get_ports *EAST_SB_IN_B1*]
      set qports [get_ports *EAST_SB_OUT_B1*]
      set rports [get_ports *EAST_SB_IN_B16*]
      set sports [get_ports *EAST_SB_OUT_B16*]
    }
    if {$i==1} {
      set pports [get_ports *SOUTH_SB_IN_B1*]
      set qports [get_ports *SOUTH_SB_OUT_B1*]
      set rports [get_ports *SOUTH_SB_IN_B16*]
      set sports [get_ports *SOUTH_SB_OUT_B16*]
      set xports [get_ports {config_out* clk_out reset_out stall_out read_config_data}]
    }
    if {$i==3} {
      set pports [get_ports *NORTH_SB_OUT_B1*]
      set qports [get_ports *NORTH_SB_IN_B1*]
      set rports [get_ports *NORTH_SB_OUT_B16*]
      set sports [get_ports *NORTH_SB_IN_B16*]
      set xports [get_ports {config_config* config_read config_write clk reset stall read_config_data_in}]
    }
    set remaining_ports [remove_from_collection [get_ports *] [get_ports {*_SB_* *config* clk* reset* stall*}]]
    if {$i==2} {
      set pports [get_ports *WEST_SB_OUT_B1*]
      set qports [get_ports *WEST_SB_IN_B1*]
      set rports [get_ports *WEST_SB_OUT_B16*]
      set sports [get_ports *WEST_SB_IN_B16*]
      set xports $remaining_ports
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
      set offset 10
    }
    set off_incr  [lindex $grid 1]   
    set layer_index 0

    foreach ports [list $pports $qports $rports $sports $xports] {
      if {$ports != ""} {
        set $ports [sort_collection $ports full_name]
      }
    }


    foreach_in_collection p $pports {
      set pn [get_property $p full_name]
      set xlayer [lindex $layer $layer_index]
      set xwidth [lindex $grid_width $layer_index] 
      set xgrid  [lindex $grid $layer_index] 
      set gridded_offset [expr ceil($offset/$xgrid)*$xgrid]
      redirect -append io_file {puts "    (pin name=\"$pn\" offset=$gridded_offset layer=$xlayer depth=0.1 width=$xwidth place_status=fixed)"}
      incr layer_index
      if {$layer_index > [expr [llength $layer] - 1]} {set layer_index 0; set offset [expr $offset + $off_incr]; if {([expr (int($offset-0.8)%10)]==1) && ($i==1||$i==3)} {set offset [expr $offset + 3]}}
      if {$offset > $max} {
        puts "ERROR: Core side $tag less than needed"
      }
    }
    set offset [expr $offset + $off_incr]
    foreach_in_collection p $qports {
      set pn [get_property $p full_name]
      set xlayer [lindex $layer $layer_index]
      set xwidth [lindex $grid_width $layer_index] 
      set xgrid  [lindex $grid $layer_index] 
      set gridded_offset [expr double(ceil($offset/$xgrid)*$xgrid)]
      redirect -append io_file {puts "    (pin name=\"$pn\" offset=$gridded_offset layer=$xlayer depth=0.1 width=$xwidth place_status=fixed)"}
      incr layer_index
      if {$layer_index > [expr [llength $layer] - 1]} {set layer_index 0; set offset [expr $offset + $off_incr]; if {([expr (int($offset-0.8)%10)]==1) && ($i==1||$i==3)} {set offset [expr $offset + 3]}}
      if {$offset > $max} {
        puts "ERROR: Core side $tag less than needed"
      }
    } 
    set offset [expr $offset + $off_incr]
    foreach_in_collection p $rports {
      set pn [get_property $p full_name]
      set xlayer [lindex $layer $layer_index]
      set xwidth [lindex $grid_width $layer_index] 
      set xgrid  [lindex $grid $layer_index] 
      set gridded_offset [expr ceil($offset/$xgrid)*$xgrid]
      redirect -append io_file {puts "    (pin name=\"$pn\" offset=$gridded_offset layer=$xlayer depth=0.1 width=$xwidth place_status=fixed)"}
      incr layer_index
      if {$layer_index > [expr [llength $layer] - 1]} {set layer_index 0; set offset [expr $offset + $off_incr]; if {([expr (int($offset-0.8)%10)]==1) && ($i==1||$i==3)} {set offset [expr $offset + 3]}}
      if {$offset > $max} {
        puts "ERROR: Core side $tag less than needed"
      }
    }
    set offset [expr $offset + $off_incr]
    foreach_in_collection p $sports {
      set pn [get_property $p full_name]
      set xlayer [lindex $layer $layer_index]
      set xwidth [lindex $grid_width $layer_index] 
      set xgrid  [lindex $grid $layer_index] 
      set gridded_offset [expr double(ceil($offset/$xgrid)*$xgrid)]
      redirect -append io_file {puts "    (pin name=\"$pn\" offset=$gridded_offset layer=$xlayer depth=0.1 width=$xwidth place_status=fixed)"}
      incr layer_index
      if {$layer_index > [expr [llength $layer] - 1]} {set layer_index 0; set offset [expr $offset + $off_incr]; if {([expr (int($offset-0.8)%10)]==1) && ($i==1||$i==3)} {set offset [expr $offset + 3]}}
      if {$offset > $max} {
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
      set gridded_offset [expr ceil($offset/$xgrid)*$xgrid]
      redirect -append io_file {puts "    (pin name=\"$pn\" offset=$gridded_offset layer=$xlayer depth=0.1 width=$xwidth place_status=fixed)"}
      incr layer_index
      if {$layer_index > [expr [llength $layer] - 1]} {set layer_index 0; set offset [expr $offset + $off_incr]; if {([expr (int($offset-0.8)%10)]==1) && ($i==1||$i==3)} {set offset [expr $offset + 3]}}
      if {$offset > $max} {
        puts "ERROR: Core side $tag less than needed"
      }
    } 
    redirect -append io_file {puts "  )"}   
  }
  redirect -append io_file {puts ")"}
  loadIoFile io_file 
}
