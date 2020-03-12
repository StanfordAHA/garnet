# mflowgen will do this part if we set it up properly...
# source $env(GARNET_HOME)/mflowgen/common/scripts/stylus_compatibility_procs.tcl

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

  # ORIG SPACING
  # gen_fiducial_set [snap_to_grid 2346.30 0.09 99.99] 2700.00 cc true 0
  # x,y = 2346.39,2700

  # Want to double the footprint of the alignment cells in both x and y
  # gen_fiducial_set [snap_to_grid 2274.00 0.09 99.99] 2200.00 cc true 0
  # x,y = 2274,2200

  # Congestion happens at the bottom of the column between like 2200-2700
  # So let's move them back up, but keep some spacing b/c that was good I think
  gen_fiducial_set [snap_to_grid 2274.00 0.09 99.99] 2700.00 cc true 0
  # x,y = 2274,2700
}

proc test_vars {} {
    # Test vars for gen_fiducial_set
    set pos_x [snap_to_grid 2274.00 0.09 99.99]
    set pos_y 2700.00
    set id cc
    set grid true
    set cols 0
}

proc tmp_gcs_parms {} {
    set pos_x 2274.03
    set pos_y 2700.00
    set id cc
    set grid true
    set cols 0
}

proc gen_fiducial_set {pos_x pos_y {id ul} grid {cols 8}} {
    # delete_inst -inst ifid_*
    # FEOL
    set core_fp_width 4900
    set core_fp_height 4900

    set ICOVL_cells {
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

    set DTCD_cells_feol N16_DTCD_FEOL_20140707   

    set DTCD_cells_beol {
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

    # [stevo]: DRC rule sets this, cannot be smaller
    # [stevr]: yeh but imma make it bigger (09/2019) (doubling dx, dy)

    # set dx [snap_to_grid [expr 2*(2*8+2*12.6)] 0.09 0]
    # set dy [expr 2*41.472]
    if {$id == "cc"} {

#         puts "@fileinfo id=$id"
#         puts "@fileinfo Double it BUT ONLY for center core (cc) cells"
#         set dx [snap_to_grid [expr 2*(2*8+2*12.6)] 0.09 0]
#         set dy [expr 2*41.472]

        # Okay let's try 1.5 spacing ish
        puts "@fileinfo id=$id"
        puts "@fileinfo y-space 1.5x BUT ONLY for center core (cc) cells"
        set dx [snap_to_grid [expr 2*(2*8+2*12.6)] 0.09 0]
        set dy 63.000


    } else {    
        set dx [snap_to_grid [expr 2*8+2*12.6] 0.09 0]
        set dy 41.472
    }
    set ix $pos_x
    set iy $pos_y
    set i 1
    set fid_name "init"
    # set cols 8


    # [stevo]: don't put below/above IO cells
    if {$grid != "true"} {
      set x_bounds ""
      foreach loc [get_db [get_db insts *IOPAD_VDD_**] .bbox] {
        set y [lindex $loc 1]
        if {$pos_y > [expr $core_fp_height/2] && $y > [expr $core_fp_height/2]} {
          lappend x_bounds [list [lindex $loc 0] [lindex $loc 2]]
        }
        if {$pos_y < [expr $core_fp_height/2] && $y < [expr $core_fp_height/2]} {
          lappend x_bounds [list [lindex $loc 0] [lindex $loc 2]]
        }
      }
    }

    # [stevo]: avoid db access by hard-coding width
    set width 12.6
    
    foreach cell $ICOVL_cells {
      set fid_name "ifid_icovl_${id}_${i}"
      create_inst -cell $cell -inst $fid_name \
        -location "$ix $iy" -orient R0 -physical -status fixed
      place_inst $fid_name $ix $iy R0 -fixed ; # [stevo]: need this!
      set x_start $ix
      set x_end [expr $ix+$width]
      if {$grid != "true"} {
        foreach x_bound $x_bounds {
          set x_bound_start [lindex $x_bound 0]
          set x_bound_end [lindex $x_bound 1]
          if {($x_start >= $x_bound_start && $x_start <= $x_bound_end) || ($x_end >= $x_bound_start && $x_end <= $x_bound_end)} {
            set ix [expr $x_bound_end + 5]
          }
        }
      }
      place_inst $fid_name $ix $iy r0
      if {$grid == "true"} {
          set halo_margin_target 15
      } else {
          set halo_margin_target 8
      }
      set halo_margin [snap_to_grid $halo_margin_target 0.09 0]
      create_place_halo -insts $fid_name \
        -halo_deltas $halo_margin $halo_margin $halo_margin $halo_margin -snap_to_site
      if {$grid == "true"} {
        create_route_blockage -name $fid_name -inst $fid_name -cover -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9} -spacing $halo_margin

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
        # create_route_blockage -name $fid_name -inst $fid_name -cover -layers {VIA1 VIA2 VIA3 VIA4 VIA5 VIA6 VIA7 VIA8} -spacing [expr $halo_margin + 2]
        create_route_blockage -name $fid_name -inst $fid_name -cover -layers {VIA1 VIA2 VIA3 VIA4 VIA5 VIA6 VIA7 VIA8} -spacing $halo_margin

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

      } else {
        create_route_blockage -name $fid_name -inst $fid_name -cover -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9} -spacing 2.5
      }
      if {$grid == "true"} {
        if {($ix-$pos_x)/$dx > $cols} {
          set ix $pos_x
          set iy [expr $iy + $dy]
        } else {
          set ix [expr $ix + $dx]
        }
      } else {
        set ix [expr $ix + $dx]
      }
      incr i
    }

    # once more for the DTCD fiducial
    if {$grid != "true"} { 
      set x_start $ix
      set x_end [expr $ix+$width]
      foreach x_bound $x_bounds {
        set x_bound_start [lindex $x_bound 0]
        set x_bound_end [lindex $x_bound 1]
        if {($x_start >= $x_bound_start && $x_start <= $x_bound_end) || ($x_end >= $x_bound_start && $x_end <= $x_bound_end)} {
          set ix [expr $x_bound_end + 5]
        }
      }
    }

    # The DTCD cells overlap
    set cell $DTCD_cells_feol
    set fid_name "ifid_dtcd_feol_${id}_${i}"
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
    incr i
    foreach cell $DTCD_cells_beol {
      set fid_name "ifid_dtcd_beol_${id}_${i}"
      create_inst -cell $cell -inst $fid_name \
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
