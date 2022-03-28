# mflowgen will do this part if we set it up properly...
# echo source $env(GARNET_HOME)/mflowgen/common/scripts/stylus-compatibility-procs.tcl

# Helper function
proc snap_to_grid {input granularity {edge_offset 0}} {
   set new_value [expr (ceil(($input - $edge_offset)/$granularity) * $granularity) + $edge_offset]
   return $new_value
}

proc add_core_fiducials {} {
  # [Blank comment to establish indentation pattern for emacs?]
  puts "+++ @file_info begin ICOVL"
  
  deleteInst ifid*cc*; # stylus: delete_inst -inst ifid*cc*
  set_proc_verbose gen_fiducial_set

  # For alignment cell layout history and experiment details,
  # see "alignment-cell-notes.txt" in this directory

  # 6/2019 ORIG SPACING and layout 21x2 (21 rows x 2 columns)
  # gen_fiducial_set [snap_to_grid 2346.30 0.09 99.99] 2700.00 cc true 0

  # New default placement:
  # 1x42 @ y=4008, custom DTCD placement; no DRC errors
  # puts "@file_info 1x42 ICOVL array @ y=4008"
  # Standard x-offset to center a 1x42 array
  set x [snap_to_grid  700.00 0.09 99.99]
  # Put icovl array between bump rows near top of die
  set y 4008
  set cols [expr 42 - 2]; # 42 columns, this is how we do it :(

  # Previously had DTCD on right side of GLB at (3840,3840). But all
  # the congestion appears to be on the left side of the GLB. The DTCD
  # cell was preventing us from moving the GLB rightward to alleviate
  # the congestion. So now we hvae put DTCD symmetrically across on the
  # LEFT side so GLB can move to the right whenever and however much we like.
  #
  # FIXME the below numbers should probably be a function of die size etc.
  set ::env(DTCD_X) 1055; set ::env(DTCD_Y) 3840

  # Place!
  gen_fiducial_set $x $y cc true $cols

  puts "--- @file_info end ICOVL"
  return

  # Other valid options; also see "alignment-cell-notes.txt".
  # 
  #   # 2x21 @ y=3800, auto DTCD placement; no DRC errors
  #   puts "@file_info 2x21 ICOVL array"
  #   set ::env(DTCD_X) "auto"; set ::env(DTCD_Y) "auto"
  #   set x [snap_to_grid 1500.00 0.09 99.99]; set y 3800; set cols [expr 21 - 2]
  #   gen_fiducial_set $x $y cc true $cols
  # 
  # 
  #   # 6x7 @ y=3800, auto DTCD placement; no DRC errors
  #   set ::env(DTCD_X) "auto"; set ::env(DTCD_Y) "auto"
  #   puts "@file_info 6x7 array, DTCD auto-placed in array"
  #   #   gen_fiducial_set [snap_to_grid 1800.00 0.09 99.99] 3200.00 cc true 5 3.0
  #   set x [snap_to_grid 1800.00 0.09 99.99]; set y 3200; set cols [expr 7 - 2]
  #   set x_spacing_factor 3.0
  #   gen_fiducial_set $x $y cc true $cols $x_spacing_factor
}

##############################################################################
proc gen_fiducial_set {pos_x pos_y {id ul} grid {cols 8} {xsepfactor 1.0}} {

    # delete_inst -inst ifid_*
    # set fid_name "init"; # NEVER USED...riiiiiight?
    # set cols 8

    # ICOVL cells
    set width 12.6; # [stevo]: avoid db access by hard-coding width
    set i_ix_iy [ place_ICOVL_cells $pos_x $pos_y $xsepfactor $id $width $grid $cols ]

    # Unpack return values
    set i  [ lindex $i_ix_iy 0]
    set ix [ lindex $i_ix_iy 1]
    set iy [ lindex $i_ix_iy 2]

    if {$id == "cc"} {
        puts "@file_info CC ICOVL array bbox LL=($pos_x, $pos_y)"
        puts "@file_info CC ICOVL array bbox UR=($ix, $iy)"
        
        # Use env vars to choose auto or manual DTCD placement for cc area
        if {$::env(DTCD_X) == "auto"} {
            puts "@file_info CC DTCD  cells going in at x,y=$ix,$iy"
        } else {
            # Directed manual DTCD placement, overrides ix, iy
            # E.g. (3036.15,3878.0) seems to work always
            set ix $::env(DTCD_X); set iy $::env(DTCD_Y)
            puts "@file_info CC DTCD cells going in at x,y=$ix,$iy (forced)"
        }
    }
    # DTCD cells: there's one feol cell and many beol cells,
    # all stacked in one (ix,iy) place (!!?)
    set i [ place_DTCD_cell_feol  $i $ix $iy "ifid_dtcd_feol_${id}" $grid ]
    set i [ place_DTCD_cells_beol $i $ix $iy "ifid_dtcd_beol_${id}"       ]
}

proc place_ICOVL_cells { pos_x pos_y xsepfactor id width grid cols } {
    set i 1;                         # Count how many cells get placed
    set_dx_dy $id $xsepfactor dx dy; # Set grid x,y spacing
    set ix $pos_x; set iy $pos_y;    # (pos_x,pos_y) = desired LL corner of grid

    # [stevo]: don't put below/above IO cells
    set x_bounds [ get_x_bounds $pos_y $grid ]

    foreach cell [ get_ICOVL_cells ] {
        set fid_name "ifid_icovl_${id}_${i}"
        create_inst -cell $cell -inst $fid_name \
            -location "$ix $iy" -orient R0 -physical -status fixed
        
        # STYLUS place_inst == LEGACY placeInstance
        place_inst $fid_name $ix $iy R0 -fixed ; # [stevo]: need this!
        set ix [ check_pad_overlap $ix $width $x_bounds $grid]
        # FIXME why do this twice? [stever] I guess in case check_pad_overlap changed $ix??
        place_inst $fid_name $ix $iy r0; # Overrides/replaces previous placement
        
        # Halos and blockages for alignment cells
        if {$grid == "true"} {
            set halo_margin_target 15
        } else {
            set halo_margin_target 8
        }
        set halo_margin [snap_to_grid $halo_margin_target 0.09 0]
        
        create_place_halo -insts $fid_name \
            -halo_deltas $halo_margin $halo_margin $halo_margin $halo_margin -snap_to_site
        
        if {$grid == "true"} {
            create_grid_route_blockages $fid_name $halo_margin
        } else {
            create_grid_route_blockages $fid_name 4
        }
        # increment ix and iy (and i)
        incr_ix_iy ix iy $dx $dy $pos_x $cols $grid
        incr i
    }; # foreach cell $ICOVL_cells
    
    # Check overlap again I guess
    set ix [ check_pad_overlap $ix $width $x_bounds $grid ]
    
    # return updated i, ix, iy
    return "$i $ix $iy"
}
proc set_dx_dy { id xsepfactor dx dy } {
    upvar $dx ddx; upvar $dy ddy; # pass-by-ref dx,dy

    # Set x, y spacing (dx,dy) for alignment cell grid
    # [stevo]: DRC rule sets dx/dy cannot be smaller
    # [stevr]: yeh but imma make it bigger for cc (09/2019)
    # Keep original dx,dy except for cc cells
    if {$id == "cc"} {
        # Okay let's try 1.5 dy spacing ish (dy 41=>63)
        puts "@fileinfo id=$id"
        puts "@fileinfo y-space 1.5x BUT ONLY for center core (cc) cells"
        # New xsep arg e.g. 2.0 => twice as far as default
        set ddx [snap_to_grid [expr 2*(2*8+2*12.6)*$xsepfactor] 0.09 0]
        set ddy 63.000; # FIXME Why not snap to grid??
    } else {
        # Note I think "dy" is only used for "grid"
        set ddx [snap_to_grid [expr 2*8+2*12.6] 0.09 0]
        set ddy 41.472
    }
}
proc incr_ix_iy { ix iy dx dy pos_x cols grid } {
    upvar $ix iix; upvar $iy iiy; # pass-by-ref ix,iy

    # increment dx and dy
    if {$grid != "true"} { set cols 999999 }
    if { ($iix - $pos_x)/$dx > $cols } {
        # FIXME this code is wack; if want c cols, must set $cols to (c-2)
        # I.e. cols==0 builds two coloumns etc. BUT WHYYYYYY
        # echo "FOO --- exceeded max ncols; resetting x, incrementing y ---"
        set iix $pos_x
        set iiy [expr $iiy + $dy]
    } else {
        set iix [expr $iix + $dx]
        set iiy [expr $iiy +  0 ]; # unchanged
    }
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

proc get_x_bounds { pos_y grid } {
    # Get a list of left/right edges of iopads in the vicinity (?)
    # Seems more important when/if you have area pads instead of a ring...

    # Original comment: "[stevo]: don't put below/above IO cells"
    # My comment:
    # [stevr]: looks like it returns a list of (left_edge,right_edge) pairs, one
    # for each iopad in the same top/bottom chip half as proposed alignment cell (pos_y)

    if { $grid == "true" } { return "" }

    # FIXME core_fp_{width,height} should come from somewhere else!!!
    set core_fp_width 4900
    set core_fp_height 4900

    set x_bounds ""
    set chip_center [expr $core_fp_height/2]
    foreach loc [get_db [get_db insts *IOPAD_VDD_**] .bbox] {

        set iopad_left_edge  [lindex $loc 0]
        set iopad_btm        [lindex $loc 1]
        set iopad_right_edge [lindex $loc 2]

        # if icov grid in top half of chip, and IO pad in top half, set x bounds = IO cell
        if {$pos_y > $chip_center && $iopad_btm > $chip_center} {
            lappend x_bounds [list $iopad_left_edge $iopad_right_edge]
        }
        # if icov grid in bot half of chip, and IO pad in bot half, set x bounds = IO cell
        if {$pos_y < $chip_center && $iopad_btm < $chip_center} {
            lappend x_bounds [list $iopad_left_edge $iopad_right_edge]
        }
        # Note/FIXME what happens if $pos_y == $chip_center? It could happen!!!
    }
    return x_bounds
}
proc check_pad_overlap { ix width x_bounds grid } {
    # If it looks like icovl will overlap IO cell, scooch it over 5u
    # FIXME but why only if no grid???
    if {$grid == "true"} { return $ix }

    set x_start $ix
    set x_end [expr $ix+$width]
    foreach x_bound $x_bounds {
        set x_bound_start [lindex $x_bound 0]
        set x_bound_end   [lindex $x_bound 1]
        if { ($x_start >= $x_bound_start && $x_start <= $x_bound_end) || \
                 ($x_end   >= $x_bound_start && $x_end   <= $x_bound_end)} {
            set ix [expr $x_bound_end + 5]
        }
    }
    return $ix
}

proc place_DTCD_cell_feol { i ix iy fid_name_id grid } {
    set cell [ get_DTCD_cell_feol ] ; # There's only one
    set fid_name "${fid_name_id}_${i}"

    create_inst -cell $cell -inst $fid_name \
        -location "$ix $iy" -orient R0 -physical -status fixed

    place_inst $fid_name $ix $iy R0 -fixed
    if {$grid == "true"} {
        set tb_halo_margin 16
        set lr_halo_margin 16
    } else {
        set tb_halo_margin 8
        set lr_halo_margin 8
    }
    create_place_halo -insts $fid_name \
        -halo_deltas $lr_halo_margin $tb_halo_margin $lr_halo_margin $tb_halo_margin -snap_to_site
    create_grid_route_blockages $fid_name $lr_halo_margin
    return $i
}
proc place_DTCD_cells_beol { i ix iy fid_name_id } {
    incr i
    # The DTCD cells (feol + all beol) overlap same ix,iy location (??)
    # foreach cell $DTCD_cells_beol {}
    foreach cell [ get_DTCD_cells_beol ] {
        # set fid_name "ifid_dtcd_beol_${id}_${i}"
        set fid_name "${fid_name_id}_${i}"
        create_inst -cell $cell -inst $fid_name \
            -location "$ix $iy" -orient R0 -physical -status fixed
        place_inst $fid_name $ix $iy R0 -fixed
        create_grid_route_blockages $fid_name 4
        incr i
    }
}
proc get_ICOVL_cells {} {
    # FIXME should this be part of adk/constraints?
    set icells {
      ICOVL_CODH_OD_20140702
      ICOVL_CODV_OD_20140702
      ICOVL_IMP1_OD_20140702
      ICOVL_IMP2_OD_20140702
      ICOVL_IMP3_OD_20140702
      ICOVL_PMET_OD_20140702
      ICOVL_VT2_OD_20140702
      ICOVL_PO_OD_20140702
      ICOVL_CPO_OD_20140702
      ICOVL_CMD_OD_20140702
      ICOVL_M0OD_OD_20140702
      ICOVL_M0OD_PO_20140702
      ICOVL_M0PO_CMD_20140702
      ICOVL_M0PO_M0OD_20140702
      ICOVL_M0PO_PO_20140702
      ICOVL_M1L1_M0OD_20140702
      ICOVL_M1L2_M1L1_20140702
      ICOVL_M2L1_M1L1_20140702
      ICOVL_M2L2_M2L1_20140702
      ICOVL_M3L1_M2L1_20140702
      ICOVL_M3L2_M3L1_20140702
      ICOVL_M4L1_M3L1_20140702
      ICOVL_M5L1_M4L1_20140702
      ICOVL_M6L1_M5L1_20140702
      ICOVL_M7L1_M6L1_20140702
      ICOVL_V0H1_M0OD_20140702
      ICOVL_V0H1_M1L1_20140702
      ICOVL_V0H2_M1L1_20140702
      ICOVL_V0H2_M1L2_20140702
      ICOVL_V1H1_M1L1_20140702
      ICOVL_V1H1_M2L1_20140702
      ICOVL_V2H1_M2L1_20140702
      ICOVL_V2H1_M3L1_20140702
      ICOVL_V3H1_M3L1_20140702
      ICOVL_V3H1_M3L2_20140702
      ICOVL_V4H1_M4L1_20140702
      ICOVL_V4H1_M5L1_20140702
      ICOVL_V5H1_M5L1_20140702
      ICOVL_V5H1_M6L1_20140702
      ICOVL_V6H1_M6L1_20140702
      ICOVL_V6H1_M7L1_20140702
    }
    return $icells
}
proc get_DTCD_cell_feol {} {
    # FIXME should this be part of adk/constraints?
    set dfcell N16_DTCD_FEOL_20140707   
    return $dfcell
}
proc get_DTCD_cells_beol {} {
    # FIXME should this be part of adk/constraints?
    set dbcells {
      N16_DTCD_BEOL_M1_20140707
      N16_DTCD_BEOL_M2_20140707
      N16_DTCD_BEOL_M3_20140707
      N16_DTCD_BEOL_M4_20140707
      N16_DTCD_BEOL_M5_20140707
      N16_DTCD_BEOL_M6_20140707
      N16_DTCD_BEOL_M7_20140707
      N16_DTCD_BEOL_V1_20140707
      N16_DTCD_BEOL_V2_20140707
      N16_DTCD_BEOL_V3_20140707
      N16_DTCD_BEOL_V4_20140707
      N16_DTCD_BEOL_V5_20140707
      N16_DTCD_BEOL_V6_20140707
    }
    return $dbcells
}

proc test_vars {} {
    # Test vars for gen_fiducial_set
    # set pos_x 2274.03
    set pos_x [snap_to_grid 2274.00 0.09 99.99]
    set pos_y 2700.00
    set id cc
    set grid true
    set cols 0
}


proc add_boundary_fiducials {} {
  delete_inst -inst ifid*ul*

  set ::env(DTCD_X) "auto"; set ::env(DTCD_Y) "auto"

  gen_fiducial_set 100 4824.0 ul false
  select_obj [get_db insts ifid*ul*]
  snap_floorplan -selected
  deselect_obj -all

  delete_inst -inst ifid*ur*
  gen_fiducial_set 2500.0 4824.00 ur false
  select_obj [get_db insts ifid*ur*]
  snap_floorplan -selected
  deselect_obj -all

  delete_inst -inst ifid*ll*
  ################################################################
  # sr 2001 - scooch fiducials over another 300u ish so IOPAD can strap across
  # see github issue ???
# gen_fiducial_set 100.0 58.70 ll false
# gen_fiducial_set 400.0 58.70 ll false
  gen_fiducial_set 440.0 58.70 ll false
  ################################################################
  select_obj [get_db insts ifid*ll*]
  snap_floorplan -selected
  deselect_obj -all

  delete_inst -inst ifid*lr*
  gen_fiducial_set 2500.0 58.70 lr false
  select_obj [get_db insts ifid*lr*]
  snap_floorplan -selected
  deselect_obj -all
}

set_proc_verbose add_core_fiducials; add_core_fiducials
add_boundary_fiducials

