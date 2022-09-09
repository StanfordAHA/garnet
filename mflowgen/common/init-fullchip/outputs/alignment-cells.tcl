# mflowgen will do this part if we set it up properly...
# echo source $env(GARNET_HOME)/mflowgen/common/scripts/stylus-compatibility-procs.tcl

# Helper function
proc snap_to_grid {input granularity {edge_offset 0}} {
   set new_value [expr (ceil(($input - $edge_offset)/$granularity) * $granularity) + $edge_offset]
   return $new_value
}

proc create_grid_route_blockages { fid_name halo_margin } {
    # steveri 1912 - HALO NOT GOOD ENOUGH! Router happily installs wires inside the halo :(
    # Then we get hella DRC errors around the icovl cells.
    # Solution: need blockages instead and/or as well, nanoroute seems to understand those...
    # Also need a bit of halo, see comment above about endcaps
    set inst [get_db insts $fid_name]
    set name [get_db $inst .name]_bigblockgf
    set rect [get_db $inst .place_halo_bbox]
    set new_halo 2   
    # small blockage with big halo (above), build big blockage w/ tiny halo
    set halo_metal $halo_margin
    set llx_metal [expr [get_db $inst .bbox.ll.x] - $halo_metal + $new_halo ]
    set lly_metal [expr [get_db $inst .bbox.ll.y] - $halo_metal + $new_halo ]
    set urx_metal [expr [get_db $inst .bbox.ur.x] + $halo_metal - $new_halo ]
    set ury_metal [expr [get_db $inst .bbox.ur.y] + $halo_metal - $new_halo ]
    set rect "$llx_metal $lly_metal $urx_metal $ury_metal"
    create_route_blockage -name $name -rects $rect \
        -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9} -spacing $new_halo
    
    # Originally via halo was bigger than metal halo. but why tho?
    set halo_via [expr $halo_margin + 3.5]
    set llx_via [expr [get_db $inst .bbox.ll.x] - $halo_via + $new_halo ]
    set lly_via [expr [get_db $inst .bbox.ll.y] - $halo_via + $new_halo ]
    set urx_via [expr [get_db $inst .bbox.ur.x] + $halo_via - $new_halo ]
    set ury_via [expr [get_db $inst .bbox.ur.y] + $halo_via - $new_halo ]
    set rect "$llx_via $lly_via $urx_via $ury_via"
    create_route_blockage -name $name -rects $rect -pg_nets \
        -layers {VIA1 VIA2 VIA3 VIA4 VIA5 VIA6 VIA7 VIA8} -spacing $new_halo
}

# Begin NEW GF Procs
proc create_and_place_cell {pos_x pos_y cellname instname} {
  create_inst -cell $cellname -inst $instname \
      -location "$pos_x $pos_y" -orient R0 -physical -status fixed
  # Arbitrary halo margin
  set halo_margin 5
  create_place_halo -insts $instname \
    -halo_deltas $halo_margin $halo_margin $halo_margin $halo_margin -snap_to_site
}

proc create_cell_grid {ori_x ori_y x_sep y_sep numrows numcols cellname instname_base} {
  for {set row 0} {$row < $numrows} {incr row} {
    set y [expr $ori_y + ($row * $y_sep)]
    for {set col 0} {$col < $numcols} {incr col} {
      set x [expr $ori_x + ($col * $x_sep)]
      set instname "${instname_base}_r${row}_c${col}"
      create_and_place_cell $x $y $cellname $instname
    }
  }
}

# Create grid of alignment cells over center of chip
set alignment_cellname "CDMMTYPE2_32422"
set alignment_instname_base "core_alignment_grid"
#create_cell_grid 300 300 1500 1500 3 3 $alignment_cellname $alignment_instname_base

# Place alignment cells
create_and_place_cell 900 4000 $alignment_cellname "cdmm1"
create_and_place_cell 2400 3600 $alignment_cellname "cdmm2"
create_and_place_cell 4400 3530 $alignment_cellname "cdmm3"
create_and_place_cell 250 2000 $alignment_cellname "cdmm4"
create_and_place_cell 4655 2000 $alignment_cellname "cdmm5"
create_and_place_cell 2250 250 $alignment_cellname "cdmm6"
create_and_place_cell 4250 250 $alignment_cellname "cdmm7"

