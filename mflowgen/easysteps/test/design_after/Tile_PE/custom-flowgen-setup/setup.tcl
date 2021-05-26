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

set setup_a_views {}
set hold_a_views {}
foreach s ${active_scenarios} {
    lappend setup_a_views analysis_setup_${s}
    lappend hold_a_views analysis_hold_${s}
}

set vars(analysis_views)                         [concat ${setup_a_views} ${hold_a_views}]

foreach s ${active_scenarios} {
    set vars(analysis_setup_${s},delay_corner)          delay_default
    set vars(analysis_setup_${s},constraint_mode)       constraints_${s}
    if {[lsearch -exact $vars(delay_corners) "delay_best"] != -1} {
      set vars(analysis_hold_${s},delay_corner)          delay_best
    } else {
      set vars(analysis_hold_${s},delay_corner)          delay_default
    }
    set vars(analysis_hold_${s},constraint_mode)       constraints_${s}
}

set vars(default_setup_view)                   "analysis_setup_default_c"
set vars(setup_analysis_views)                 "[join ${setup_a_views}]"
set vars(active_setup_views)                   "[join ${setup_a_views}]"

set vars(default_hold_view)                    "analysis_hold_default_c"
set vars(hold_analysis_views)                  "[join ${hold_a_views}]"
set vars(active_hold_views)                    "[join ${hold_a_views}]"

set vars(power_analysis_view)                  analysis_setup_default_c
