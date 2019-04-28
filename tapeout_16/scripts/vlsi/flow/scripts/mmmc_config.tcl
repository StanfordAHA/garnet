##############################################################################
## LIBRARY SETS
##############################################################################

set setup_corners "0p72v125c"
set hold_corners  "0p88v0c"

# [stevo]: tph* are the IO cells
# [stevo]: ts* are the memories

# TODO: program this better
foreach setupc $setup_corners {
  puts "Defining timing files for library set ${setupc}.SS"
  create_library_set \
    -name ${setupc}.SS \
    -timing [subst {
      [get_db tech]/lib/tcbn16ffcllbwp16p90ssgnp0p72v125c_ecsm.lib
      [get_db tech]/lib/tcbn16ffcllbwp16p90lvtssgnp0p72v125c_ecsm.lib
      [get_db tech]/lib/tcbn16ffcllbwp16p90ulvtssgnp0p72v125c_ecsm.lib
      [get_db tech]/lib/tphn16ffcllgv18essgnp0p72v1p62v125c.lib
      [get_db tech]/lib/CLK_RX_amp_buf_tt0p8v25c.lib
      [get_db tech]/lib/RX_ADC_TOP_ssgnp0p72v125c.lib
      [glob -nocomplain [get_db tech]/lib/ts*ss*${setupc}*.lib]
      [get_db tech]/lib/TISARADC_SFFT_ttgnp0p8v25c.lib
      [get_db tech]/lib/serdes_afe_ssgnp0p72v125c.lib
    }]
}

foreach holdc $hold_corners {
  puts "Defining timing files for library set ${holdc}.FF"
  create_library_set \
    -name ${holdc}.FF \
    -timing [subst {
      [get_db tech]/lib/tcbn16ffcllbwp16p90ffgnp0p88v0c_ecsm.lib
      [get_db tech]/lib/tcbn16ffcllbwp16p90lvtffgnp0p88v0c_ecsm.lib
      [get_db tech]/lib/tcbn16ffcllbwp16p90ulvtffgnp0p88v0c_ecsm.lib
      [get_db tech]/lib/tphn16ffcllgv18effgnp0p88v1p98v0c.lib
      [get_db tech]/lib/CLK_RX_amp_buf_tt0p8v25c.lib
      [get_db tech]/lib/RX_ADC_TOP_ffgnp0p88v0c.lib
      [glob -nocomplain [get_db tech]/lib/ts*ff*${holdc}*.lib]
      [get_db tech]/lib/TISARADC_SFFT_ttgnp0p8v25c.lib
      [get_db tech]/lib/serdes_afe_ffgnp0p88v0c.lib
    }]
}

##############################################################################
## ADD OCV SETS
##############################################################################

#foreach librarySet $library_sets {
# puts "Defining timing files for library set $librarySet."
#update_library_set -name $librarySet  \
#-aocv [ glob [get_db lib_dir]/Front_End/timing_power_noise/ECSM/*/*$librarySet*]
#}
##############################################################################
## OPERATING CONDITIONS
##############################################################################
#regexp -all {^((.*)p(.*)v)(.*)c}  $setupc tot vtot vreal vdec temp

foreach setupc $setup_corners {
  puts "Creating operating condition for corner $setupc"
  regexp -all {^((.*)p([0-9]+)[a-z]+)([0-9]+)c}  $setupc tot vtot vreal vdec  temp
  #puts "$vreal.$vdec"
  #puts "$temp"
  create_opcond \
    -name               $setupc.max \
    -process            1 \
    -voltage            $vreal.$vdec \
    -temperature        $temp
}

foreach holdc $hold_corners {
  puts "Creating operating condition for corner $holdc"
  regexp -all {^((.*)p([0-9]+)[a-z]+)([0-9]+)c}  $holdc tot vtot vreal vdec  temp
  #puts "$vreal.$vdec"
  #puts "$temp"
  create_opcond \
    -name               $holdc.min \
    -process            1 \
    -voltage            $vreal.$vdec \
    -temperature        $temp
}

#
##############################################################################
## TIMING CONDITIONS
##############################################################################
foreach setupc $setup_corners {
  puts "Creating timing condition for corner $setupc"
  create_timing_condition \
    -name               $setupc.setup \
    -library_sets       [list ${setupc}.SS  ] \
    -opcond             $setupc.max 
}

foreach holdc $hold_corners {
  puts "Creating timing condition for corner $holdc"
  create_timing_condition \
    -name               $holdc.hold \
    -library_sets       [list ${holdc}.FF  ] \
    -opcond             $holdc.min 
}


##############################################################################
## RC CORNERS
##############################################################################
create_rc_corner \
    -name               cworst_CCworst \
    -temperature        125 \
    -qrc_tech           /tools/tstech16/CLN16FFC/packages/T-N16-CL-BL-097-V1/cworst/Tech/cworst_CCworst/qrcTechFile

create_rc_corner \
    -name               rcworst_CCworst \
    -temperature        125 \
    -qrc_tech           /tools/tstech16/CLN16FFC/packages/T-N16-CL-BL-097-V1/rcworst/Tech/rcworst_CCworst/qrcTechFile

create_rc_corner \
    -name               cbest_CCbest \
    -temperature        0 \
    -qrc_tech           /tools/tstech16/CLN16FFC/packages/T-N16-CL-BL-097-V1/cbest/Tech/cbest_CCbest/qrcTechFile

create_rc_corner \
    -name               rcbest_CCbest \
    -temperature        0 \
    -qrc_tech           /tools/tstech16/CLN16FFC/packages/T-N16-CL-BL-097-V1/rcbest/Tech/rcbest_CCbest/qrcTechFile
    
##############################################################################
## DELAY CORNERS
##############################################################################
foreach setupc $setup_corners {
  puts "Defining delay corners for $setupc."
  create_delay_corner \
    -name               ${setupc}.setup_rcworst_CCworst \
    -timing_condition   ${setupc}.setup \
    -rc_corner          rcworst_CCworst
}

foreach setupc $setup_corners {
  puts "Defining delay corners for $setupc."
  create_delay_corner \
    -name               ${setupc}.setup_cworst_CCworst \
    -timing_condition   ${setupc}.setup \
    -rc_corner          cworst_CCworst
}

foreach holdc $hold_corners {
  puts "Defining delay corners for $holdc."
  create_delay_corner \
    -name               ${holdc}.hold_rcbest_CCbest \
    -timing_condition   ${holdc}.hold \
    -rc_corner          rcbest_CCbest
}

foreach holdc $hold_corners {
  puts "Defining delay corners for $holdc."
  create_delay_corner \
    -name               ${holdc}.hold_cbest_CCbest \
    -timing_condition   ${holdc}.hold \
    -rc_corner          cbest_CCbest
}

foreach holdc $hold_corners {
  puts "Defining delay corners for $holdc."
  create_delay_corner \
    -name               ${holdc}.hold_cworst_CCworst \
    -timing_condition   ${holdc}.hold \
    -rc_corner          cworst_CCworst
}

foreach holdc $hold_corners {
  puts "Defining delay corners for $holdc."
  create_delay_corner \
    -name               ${holdc}.hold_rcworst_CCworst \
    -timing_condition   ${holdc}.hold \
    -rc_corner          rcworst_CCworst
}
##############################################################################
##############################################################################
## CONSTRAINT MODES
##############################################################################
create_constraint_mode \
    -name               func \
    -sdc_files          [get_db constraints_files]
##############################################################################
## ANALYSIS VIEWS
##############################################################################
foreach setupc $setup_corners {
  puts "Defining analysis views for $setupc."
  create_analysis_view \
    -name               func-${setupc}.setup_cworst_CCworst \
    -constraint_mode    func \
    -delay_corner       ${setupc}.setup_cworst_CCworst \
    -power_mode         aon
}

foreach setupc $setup_corners {
  puts "Defining analysis views for $setupc."
  create_analysis_view \
    -name               func-${setupc}.setup_rcworst_CCworst \
    -constraint_mode    func \
    -delay_corner       ${setupc}.setup_rcworst_CCworst \
    -power_mode         aon
}

foreach holdc $hold_corners {
  puts "Defining analysis views for $holdc."
  create_analysis_view \
    -name               func-${holdc}.hold_cbest_CCbest \
    -constraint_mode    func \
    -delay_corner       ${holdc}.hold_cbest_CCbest \
    -power_mode         aon
}
 
foreach holdc $hold_corners {
  puts "Defining analysis views for $holdc."
  create_analysis_view \
    -name               func-${holdc}.hold_rcbest_CCbest \
    -constraint_mode    func \
    -delay_corner       ${holdc}.hold_rcbest_CCbest \
    -power_mode         aon
}
 
foreach holdc $hold_corners {
  puts "Defining analysis views for $holdc."
  create_analysis_view \
    -name               func-${holdc}.hold_cworst_CCworst \
    -constraint_mode    func \
    -delay_corner       ${holdc}.hold_cworst_CCworst \
    -power_mode         aon
}

foreach holdc $hold_corners {
  puts "Defining analysis views for $holdc."
  create_analysis_view \
    -name               func-${holdc}.hold_rcworst_CCworst \
    -constraint_mode    func \
    -delay_corner       ${holdc}.hold_rcworst_CCworst \
    -power_mode         aon
}
##############################################################################
## LIBRARY SETS
##############################################################################
set_analysis_view \
    -setup  [list func-0p72v125c.setup_cworst_CCworst ] \
    -hold   [list func-0p88v0c.hold_cbest_CCbest ] 
