# mflowgen will do this part if we set it up properly...
# echo source $env(GARNET_HOME)/mflowgen/common/scripts/stylus-compatibility-procs.tcl

proc snap_to_grid {input granularity {edge_offset 0}} {
   set new_value [expr (ceil(($input - $edge_offset)/$granularity) * $granularity) + $edge_offset]
   return $new_value
}

##############################################################################
# proc add_core_fiducials DONE
proc add_core_fiducials {} {
  # delete_inst -inst ifid*cc*
  deleteInst ifid*cc*

  # I'll probably regret this...
  set_proc_verbose gen_fiducial_set

  ########################################################################
  # Notes from summer 2019:
  #   
  # 6/2019 ORIG SPACING and layout 21x2 (21 rows x 2 columns)
  # LL corner of array is at x,y = 2346.39,2700
  # gen_fiducial_set [snap_to_grid 2346.30 0.09 99.99] 2700.00 cc true 0
  # 
  # 6/2019 To try and reduce congestion of wires trying to traverse ICOVL strip:
  # 1. Increased y-spacing 1.5x from 'dy=41.472' to 'dy=63.000'
  # 2. Doubled x-spacing from '[expr 2*8+2*12.6]' to '[expr 2*(2*8+2*12.6)]'
  # 2. Changed grid LL corner from (2346,2700) to (2274,2200)
  # gen_fiducial_set [snap_to_grid 2274.00 0.09 99.99] 2200.00 cc true 0
  # x,y = 2274,2200


  ########################################################################
  # Notes from spring 2020:
  # 
  # BASELINE LAYOUT: 21x2 grid of cells arranged in a vertical strip in
  # center of chip, LL corner of grid is ~ (2274,2700) (chip is 4900x4900)
  # gen_fiducial_set [snap_to_grid 2274.00 0.09 99.99] 2700.00 cc true 0
  #   ICOVL   0 errors in  0 different categories
  #   DTCD  156 errors in  6 different categories
  #     RULECHECK DTCD.DN.4 ..................... TOTAL Result Count = 26   (26)
  #     RULECHECK DTCD.DN.5:TCDDMY_V2 ........... TOTAL Result Count = 26   (26)
  #     RULECHECK DTCD.DN.5:TCDDMY_V3 ........... TOTAL Result Count = 26   (26)
  #     RULECHECK DTCD.DN.5:TCDDMY_V4 ........... TOTAL Result Count = 26   (26)
  #     RULECHECK DTCD.DN.5:TCDDMY_V5 ........... TOTAL Result Count = 26   (26)
  #     RULECHECK DTCD.DN.5:TCDDMY_V6 ........... TOTAL Result Count = 26   (26)
  # 
  # 
  # HORIZONTAL STRIP EXPERIMENTS intro
  # Above code produces vertical stripe. Can we do horizontal instead?
  # Above code builds vertical strip, 21 rows and two columns beginning at LL {2274,2700}
  # Let's see if we can build a horzontal strip instead, say 21 cols and 2 rows at LL {1500,2600}
  # 
  # HORIZONTAL STRIPE EXPERIMENT 1 (icovl3): 2x21, two rows of 21 cells each
  # FIXME note if you want 21 cols you have to ask for 19
  # FIXME similarly note above where if you ask for 0 cols you get two :(
  # gen_fiducial_set [snap_to_grid 1500.00 0.09 99.99] 2700.00 cc true 19
  # RESULT: actually yields *fewer* DTCD errors than previously...?
  # In fact it appears to be perfect?? FIXME/TODO need to rerun/verify this result!
  #   ICOVL   0 errors in  0 different categories
  #   DTCD    0 errors in  0 different categories
  # 
  # HORIZONTAL STRIPE EXPERIMENT 2 (icovl4): 1x42, one row of 42 cells
  # gen_fiducial_set [snap_to_grid  700.00 0.09 99.99] 2700.00 cc true 40
  #   ICOVL   0 errors in  0 different categories
  #   DTCD  164 errors in 14 different categories
  #     RULECHECK DTCD.DN.4 ..................................... TOTAL Result Count = 26   (26)
  #     RULECHECK DTCD.DN.5:TCDDMY_V2 ........................... TOTAL Result Count = 26   (26)
  #     RULECHECK DTCD.DN.5:TCDDMY_V3 ........................... TOTAL Result Count = 26   (26)
  #     RULECHECK DTCD.DN.5:TCDDMY_V4 ........................... TOTAL Result Count = 26   (26)
  #     RULECHECK DTCD.DN.5:TCDDMY_V5 ........................... TOTAL Result Count = 26   (26)
  #     RULECHECK DTCD.DN.5:TCDDMY_V6 ........................... TOTAL Result Count = 26   (26)
  #     RULECHECK DTCD.R.10.1 ................................... TOTAL Result Count = 1    (1)
  #     RULECHECK DTCD.R.10.2 ................................... TOTAL Result Count = 1    (1)
  #     RULECHECK DTCD.R.10.3:TCDDMY_M2 ......................... TOTAL Result Count = 1    (1)
  #     RULECHECK DTCD.R.10.3:TCDDMY_M3 ......................... TOTAL Result Count = 1    (1)
  #     RULECHECK DTCD.R.10.3:TCDDMY_M4 ......................... TOTAL Result Count = 1    (1)
  #     RULECHECK DTCD.R.10.3:TCDDMY_M5 ......................... TOTAL Result Count = 1    (1)
  #     RULECHECK DTCD.R.10.3:TCDDMY_M6 ......................... TOTAL Result Count = 1    (1)
  #     RULECHECK DTCD.R.10.3:TCDDMY_M7 ......................... TOTAL Result Count = 1    (1)
  # 
  # HORIZONTAL STRIPE EXPERIMENT 3 (icovl5): 2x21@2, two rows of 21 cells each, *widely spaced* (2x)
  # gen_fiducial_set [snap_to_grid  750.00 0.09 99.99] 2700.00 cc true 20 2.0
  #   ICOVL   0 errors in  0 different categories
  #   DTCD  164 errors in 14 different categories
  #     <same as icovl4 above>
  # 
  # HORIZONTAL STRIPE EXPERIMENT 4 (icovl6.3x7): three rows of 14 cells each, evenly spaced across the center
  # gen_fiducial_set [snap_to_grid  750.00 0.09 99.99] 2700.00 cc true 13 3.0
  # oops looks like we got a new icovl error :(
  #   ICOVL   3 errors in  1 different categories
  #     RULECHECK ICOVL.R.50.3 .................................. TOTAL Result Count = 3    (3)
  #   DTCD  164 errors in 14 different categories
  #     <same as icovl4 above>
  # 
  # Exp 4 notes:
  #   - ICOVL.R.50.3, p. 654
  #   - At least 1 {ICOVL_V0_H2 AND ICOVL_M1_L2} must be placed inside
  #   - {{ICOVL_V0_H2 AND ICOVL_M1_L1} SIZING 800μm }
  # 
  # HORIZONTAL STRIPE EXPERIMENT 5 (icovl8.6x7-1500)
  # - six rows of 7 cells each, tighter pattern maybe
  # - result: one icovl error and **NO*** DTCD errors (!)
  # gen_fiducial_set [snap_to_grid 1500.00 0.09 99.99] 2700.00 cc true 5 3.0
  #   DTCD    0 errors in  0 different categories
  #   ICOVL   3 errors in  1 different categories
  #     RULECHECK ICOVL.R.50.3 .................................. TOTAL Result Count = 3    (3)
  # 
  # HORIZONTAL STRIPE EXPERIMENT 6 (icovl9.6x7-1650)
  # - same as above but try for better centering
  # - result: Interesting. when more centered, get two (different) icovl errors
  # gen_fiducial_set [snap_to_grid 1650.00 0.09 99.99] 2700.00 cc true 5 3.0
  #   DTCD    0 errors in  0 different categories
  #   ICOVL   6 errors in  2 different categories
  #     RULECHECK ICOVL.R.50.4:VIA1 ............................. TOTAL Result Count = 3    (3)
  #     RULECHECK ICOVL.R.50.4:VIA4 ............................. TOTAL Result Count = 3    (3)
  # 
  # *************************************************
  # HORIZONTAL STRIPE EXPERIMENT 7 (icovla.6x7-3200y)
  # Same thing but higher (y=3200)
  gen_fiducial_set [snap_to_grid 1800.00 0.09 99.99] 3200.00 cc true 5 3.0
  #   DTCD    0 errors in  0 different categories
  #   ICOVL   0 errors in  0 different categories
  # Whoa! Looks like zero DTCD and ICOVL errors !!??
  # FIXME need to double check this good result
  # *************************************************
  # 
  # HORIZONTAL STRIPE EXPERIMENT 8 (icovlb.6x7-3600y)
  # Same thing but higher still (y=3600)
  # - no icovl errors but got some dtcd errors back.
  # gen_fiducial_set [snap_to_grid 1800.00 0.09 99.99] 3600.00 cc true 5 3.0
  #   ICOVL   0 errors in  0 different categories
  #   DTCD  156 errors in  6 different categories
  #     RULECHECK DTCD.DN.4 ..................................... TOTAL Result Count = 26   (26)
  #     RULECHECK DTCD.DN.5:TCDDMY_V2 ........................... TOTAL Result Count = 26   (26)
  #     RULECHECK DTCD.DN.5:TCDDMY_V3 ........................... TOTAL Result Count = 26   (26)
  #     RULECHECK DTCD.DN.5:TCDDMY_V4 ........................... TOTAL Result Count = 26   (26)
  #     RULECHECK DTCD.DN.5:TCDDMY_V5 ........................... TOTAL Result Count = 26   (26)
  #     RULECHECK DTCD.DN.5:TCDDMY_V6 ........................... TOTAL Result Count = 26   (26)


  ########################################################################
  # placement works more or less like this:
  # 
  # proc gen_fiducial_set {pos_x pos_y {id ul} grid {cols 8}}
  #     set ix $pos_x
  #     set iy $pos_y
  #     set width 12.6
  #     foreach cell $ICOVL_cells {
  #       create_inst -location "$ix $iy" ...
  #       place_inst $fid_name $ix $iy R0 -fixed ; # [stevo]: need this!
  #       set x_start $ix
  #       set x_end [expr $ix+$width]
  #              set ix [expr $x_bound_end + 5]; # (???)
  #       place_inst $fid_name $ix $iy r0; # (place a second instance w/same name?)
  #       # <route blockages etc>
  #         if {($ix-$pos_x)/$dx > $cols} { ; # Note makes two columns when $cols==0 (?)
  #           set ix $pos_x
  #           set iy [expr $iy + $dy]
  #         } else {
  #           set ix [expr $ix + $dx]
  #         }
  #       incr i
  #     }
  ########################################################################
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

# FIXME should this be part of adk/constraints?
proc get_alignment_cells { ICOVL_cells DTCD_cells_feol } {

    # Pass by ref sorta
    upvar $ICOVL_cells      icells
    upvar $DTCD_cells_feol dfcells

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
    set dfcells N16_DTCD_FEOL_20140707   
}

proc get_DTCD_cell_feol {} {
    set dfcell N16_DTCD_FEOL_20140707   
    return $dfcell
}

proc get_DTCD_cells_beol {} {
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

# Original comment: "[stevo]: don't put below/above IO cells"
# My comment:
# [stevr]: looks like it returns a list of (left_edge,right_edge) pairs
# for each iopad in the same top/bottom chip half as proposed alignment cell (pos_y)
# Note/FIXME what happens if $pos_y == $chip_center?
proc get_x_bounds { pos_y core_fp_height } {
    set x_bounds ""
    set chip_center [expr $core_fp_height/2]
    foreach loc [get_db [get_db insts *IOPAD_VDD_**] .bbox] {

        set iopad_left_edge  [lindex $loc 0]
        set iopad_btm        [lindex $loc 1]
        set iopad_right_edge [lindex $loc 2]

        # # y = LL corner of VDD cell?
        # set y [lindex $loc 1]

        # if icov grid in top half of chip, and IO pad in top half, set x bounds = IO cell
        if {$pos_y > $chip_center && $iopad_btm > $chip_center} {
            lappend x_bounds [list $iopad_left_edge $iopad_right_edge]
        }
        # if icov grid in bot half of chip, and IO pad in bot half, set x bounds = IO cell
        if {$pos_y < $chip_center && $iopad_btm < $chip_center} {
            lappend x_bounds [list $iopad_left_edge $iopad_right_edge]
        }
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


proc create_grid_route_blockages { fid_name halo_margin } {

    create_route_blockage -name $fid_name -inst $fid_name -cover \
        -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9} -spacing $halo_margin
    
    # sr 1912 FIXME: why via spacing 2u bigger than metal spacing?
    # sr 1912 FIXME: why halo instead of blockage?
    # sr 1912 FIXME: why it gotta be so big anyways?
    # 
    # sr 2001 got some partial answers maybe
    # - M1 stripes go up to edge of halo and stop
    # - endcap for stripes will not place next to blockage
    # - thus need a bit of halo or no endcaps
    # - trial and error shows that .05u halo might be enough to get endcaps
    # - later maybe I'll find out why original blockage has bigger halos
    #
    # create_route_blockage -name $fid_name -inst $fid_name -cover \
        #      -layers {VIA1 VIA2 VIA3 VIA4 VIA5 VIA6 VIA7 VIA8} -spacing [expr $halo_margin + 2]
    create_route_blockage -name $fid_name -inst $fid_name -cover \
        -layers {VIA1 VIA2 VIA3 VIA4 VIA5 VIA6 VIA7 VIA8} -spacing $halo_margin
    
    # steveri 1912 - HALO NOT GOOD ENOUGH! Router happily installs wires inside the halo :(
    # Then we get hella DRC errors around the icovl cells.
    # Solution: need blockages instead and/or as well, nanoroute seems to understand those...
    # Also need a bit of halo, see comment above about endcaps
    set inst [get_db insts $fid_name]
    set name [get_db $inst .name]_bigblockgf
    set rect [get_db $inst .place_halo_bbox]
    
    # Instead of (actually in addition to, for now, but overrides prev)
    # small blockage with big halo (above), build big blockage w/ tiny halo
    # Actually new blockage goes ON TOP OF (and overrides) prev for now,
    # although probably shouldnt :(
    set halo_metal $halo_margin
    set new_halo 0.20
    set llx_metal [expr [get_db $inst .bbox.ll.x] - $halo_metal + $new_halo ]
    set lly_metal [expr [get_db $inst .bbox.ll.y] - $halo_metal + $new_halo ]
    set urx_metal [expr [get_db $inst .bbox.ur.x] + $halo_metal - $new_halo ]
    set ury_metal [expr [get_db $inst .bbox.ur.y] + $halo_metal - $new_halo ]
    set rect "$llx_metal $lly_metal $urx_metal $ury_metal"
    create_route_blockage -name $name -rects $rect \
        -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9} -spacing $new_halo
    
    # Originally via halo was bigger than metal halo. but why tho?
    # set halo_via [expr $halo_margin + 2]
    set halo_via $halo_margin
    set llx_via [expr [get_db $inst .bbox.ll.x] - $halo_via + $new_halo ]
    set lly_via [expr [get_db $inst .bbox.ll.y] - $halo_via + $new_halo ]
    set urx_via [expr [get_db $inst .bbox.ur.x] + $halo_via - $new_halo ]
    set ury_via [expr [get_db $inst .bbox.ur.y] + $halo_via - $new_halo ]
    set rect "$llx_via $lly_via $urx_via $ury_via"
    create_route_blockage -name $name -rects $rect \
        -layers {VIA1 VIA2 VIA3 VIA4 VIA5 VIA6 VIA7 VIA8} -spacing $new_halo
}

# proc place_icovls { pos_x pos_x core_fp_height ICOVL_cells id grid } {
# }

proc gen_fiducial_set {pos_x pos_y {id ul} grid {cols 8} {xsepfactor 1.0}} {
    # delete_inst -inst ifid_*

    # Build lists of alignment cell names
    get_alignment_cells ICOVL_cells DTCD_cells_feol

    # Set x, y spacing (dx,dy) for alignment cell grid
    # [stevo]: DRC rule sets dx/dy cannot be smaller
    # [stevr]: yeh but imma make it bigger for cc (09/2019)
    # Keep original dx,dy except for cc cells
    if {$id == "cc"} {
        # Okay let's try 1.5 dy spacing ish (dy 41=>63)
        puts "@fileinfo id=$id"
        puts "@fileinfo y-space 1.5x BUT ONLY for center core (cc) cells"
        # New xsep arg e.g. 2.0 => twice as far as default
        set dx [snap_to_grid [expr 2*(2*8+2*12.6)*$xsepfactor] 0.09 0]
        set dy 63.000; # FIXME Why not snap to grid??
    } else {
        set dx [snap_to_grid [expr 2*8+2*12.6] 0.09 0]
        set dy 41.472
    }

    # set ixiy [ place_icovls $pos_x $pos_x $core_fp_height $ICOVL_cells $id $grid ]
    # set ix [lindex $ixiy 0]; set iy [lindex $ixiy 1]
    # LL coordinates for alignment cell grid
    set ix $pos_x; set iy $pos_y

    # set fid_name "init"; # NEVER USED...riiiiiight?
    # set cols 8

    # [stevo]: avoid db access by hard-coding width
    set width 12.6
    set fid_name_id "ifid_icovl_${id}"
# ------------------------------------------------------------------------
# place_ICOVL_cells $ix $iy "ifid_icovl_${id}" $width $grid
# proc place_ICOVL_cells { ix iy fid_name_id width grid }

    set i 1; # Count how many cells get placed

    # FIXME this should come from somewhere else!!!
    set core_fp_width 4900
    set core_fp_height 4900

    # [stevo]: don't put below/above IO cells
    set x_bounds ""
    if {$grid != "true"} {
        # Get a list of left/right edges of iopads in the vicinity (?)
        # Seems more important when/if you have area pads instead of a ring...
        set x_bounds [ get_x_bounds $pos_y $core_fp_height ]
    }
    foreach cell $ICOVL_cells {
        # set fid_name "ifid_icovl_${id}_${i}"
      set fid_name "${fid_name_id}_${i}"
      create_inst -cell $cell -inst $fid_name \
        -location "$ix $iy" -orient R0 -physical -status fixed

      # LEGACY/STYLUS: proc place_inst { args } { eval placeInstance $args }
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
          create_route_blockage -name $fid_name -inst $fid_name -cover -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9} -spacing 2.5
      }

      # increment dx and dy
      if {$grid == "true"} {
        # FIXME this code is wack; if want c cols, must set $cols to (c-2)
        # I.e. cols==0 builds two coloumns etc. BUT WHYYYYYY
        # echo "FOO ix=$ix pos_x=$pos_x dx=$dx cols=$cols"
        # puts "FOO (ix-pos_x)/dx= [ expr ($ix-$pos_x)/$dx ]"
        if {($ix-$pos_x)/$dx > $cols} {
          # echo "FOO --- exceeded max ncols; resetting x, incrementing y ---"
          set ix $pos_x
          set iy [expr $iy + $dy]
        } else {
          set ix [expr $ix + $dx]
        }
      } else {
        set ix [expr $ix + $dx]
      }
      incr i
    }; # foreach cell $ICOVL_cells
    # return $i
# ------------------------------------------------------------------------
    # Check overlap again I guess
    if {$grid != "true"} { 
        set ix [ check_pad_overlap $ix $width $x_bounds ]
    }

    # There's one feol cell and many beol cells, all stacked in one (ix,iy) place (!!?)
    set i [ place_DTCD_cell_feol  $i $ix $iy "ifid_dtcd_feol_${id}" $grid ]
    set i [ place_DTCD_cells_beol $i $ix $iy "ifid_dtcd_beol_${id}"       ]

}

proc place_DTCD_cell_feol { i ix iy fid_name_id grid } {
    set cell [ get_DTCD_cell_feol ] ; # There's only one
    set fid_name "${fid_name_id}_${i}"

    echo "**ERROR sr"     create_inst -cell $cell -inst $fid_name \
        -location "$ix $iy" -orient R0 -physical -status fixed


    create_inst -cell $cell -inst $fid_name \
        -location "$ix $iy" -orient R0 -physical -status fixed

    place_inst $fid_name $ix $iy R0 -fixed
    if {$grid == "true"} {
        set tb_halo_margin 27.76
        set lr_halo_margin 22.534
    } else {
        set tb_halo_margin 8
        set lr_halo_margin 8
    }
    create_place_halo -insts $fid_name \
        -halo_deltas $lr_halo_margin $tb_halo_margin $lr_halo_margin $tb_halo_margin -snap_to_site
    create_route_blockage -name $fid_name -inst $fid_name -cover -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9} -spacing $lr_halo_margin
    create_route_blockage -name $fid_name -inst $fid_name -cover -layers {VIA1 VIA2 VIA3 VIA4 VIA5 VIA6 VIA7 VIA8} -spacing [expr $lr_halo_margin + 2]
    #create_place_halo -insts $fid_name \
    #  -halo_deltas {8 8 8 8} -snap_to_site
    return $i
}
proc place_DTCD_cells_beol { i ix iy fid_name_id } {
    incr i
    # The DTCD cells (feol + all beol) overlap same ix,iy location (??)
    # foreach cell $DTCD_cells_beol {}
    foreach cell [ get_DTCD_cells_beol ] {
        # set fid_name "ifid_dtcd_beol_${id}_${i}"
        set fid_name "${fid_name_id}_${i}"

        echo "**ERROR sr" create_inst -cell $cell -inst \
            -location "$ix $iy" -orient R0 -physical -status fixed

        create_inst -cell $cell -inst \
            -location "$ix $iy" -orient R0 -physical -status fixed
        place_inst $fid_name $ix $iy R0 -fixed
        incr i
    }
}




# I think all the necessary translations for this
# proc are already in stylus compat procs
proc add_boundary_fiducials {} {
  delete_inst -inst ifid*ul*
  # "gen_fiducial_set" is defined above...
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
  # sr 2001 - scooch them over another 400u ish so IOPAD can strap across
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

