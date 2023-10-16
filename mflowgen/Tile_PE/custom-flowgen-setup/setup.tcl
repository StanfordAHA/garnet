#---------------------------------------------------------------------
# Custom Tie Cell Settings
#---------------------------------------------------------------------
set vars(tie_cells,max_distance) $ADK_TIE_MAX_DISTANCE
set vars(tie_cells,max_fanout)   $ADK_TIE_MAX_FANOUT

#---------------------------------------------------------------------
# MMMC Setup (Library Sets)
#---------------------------------------------------------------------
# library_set: socv (not sure if foundation flow supports it)
set vars(libs_typical,socv) [glob -nocomplain $vars(adk_dir)/*.socv.setup]
set vars(libs_bc,socv)      [glob -nocomplain $vars(adk_dir)/*.socv.hold]
set vars(libs_wc,socv)      [glob -nocomplain $vars(adk_dir)/*.socv.setup]

#---------------------------------------------------------------------
# MMMC Setup (RC Corners)
#---------------------------------------------------------------------
# rc_corner: typical
set vars(typical,qx_tech_file)  $vars(adk_dir)/pdk-typical-qrcTechFile
set vars(typical,T)             25

# rc_corner: bc
set vars(rcbest,qx_tech_file)   $vars(adk_dir)/pdk-rcbest-qrcTechFile
set vars(rcbest,T)              -40

# rc_corner: wc
set vars(rcworst,qx_tech_file)  $vars(adk_dir)/pdk-rcworst-qrcTechFile
set vars(rcworst,T)             125

#---------------------------------------------------------------------
# MMMC Setup (Delay Corners)
#---------------------------------------------------------------------
# define delay corners
set vars(delay_corners) "delay_best delay_worst"

# delay_corner: best
set vars(delay_best,early_library_set)    libs_bc
set vars(delay_best,late_library_set)     libs_bc
set vars(delay_best,rc_corner)            rcbest

# delay_corner: worst
set vars(delay_worst,early_library_set)    libs_wc
set vars(delay_worst,late_library_set)     libs_wc
set vars(delay_worst,rc_corner)            rcworst

#---------------------------------------------------------------------
# MMMC Setup (Constraint Mode)
#---------------------------------------------------------------------
set active_scenarios [list default_c]

set c_modes {}
foreach s ${active_scenarios} {
    lappend c_modes constraints_${s}
}

set vars(constraint_modes)                    [list ${c_modes}]

foreach s ${active_scenarios} {
    set vars(constraints_${s},pre_cts_sdc)    inputs/sdc/${s}.sdc
    set vars(constraints_${s},post_cts_sdc)   inputs/sdc/${s}.sdc
}

#---------------------------------------------------------------------
# MMMC Setup (Analysis Views)
#---------------------------------------------------------------------
set setup_a_views {}
set hold_a_views {}
foreach s ${active_scenarios} {
    lappend setup_a_views analysis_setup_${s}
    lappend hold_a_views analysis_hold_${s}
}

set vars(analysis_views)                         [concat ${setup_a_views} ${hold_a_views}]

foreach s ${active_scenarios} {
    set vars(analysis_setup_${s},delay_corner)         delay_worst
    set vars(analysis_setup_${s},constraint_mode)      constraints_${s}
    set vars(analysis_hold_${s},delay_corner)          delay_best
    set vars(analysis_hold_${s},constraint_mode)       constraints_${s}
}

set vars(default_setup_view)                   "analysis_setup_default_c"
set vars(setup_analysis_views)                 "[join ${setup_a_views}]"
set vars(active_setup_views)                   "[join ${setup_a_views}]"

set vars(default_hold_view)                    "analysis_hold_default_c"
set vars(hold_analysis_views)                  "[join ${hold_a_views}]"
set vars(active_hold_views)                    "[join ${hold_a_views}]"

set vars(power_analysis_view)                  analysis_setup_default_c
