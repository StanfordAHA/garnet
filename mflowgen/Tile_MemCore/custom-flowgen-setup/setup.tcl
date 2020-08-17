set active_scenarios [list UNIFIED_BUFFER FIFO SRAM]

set c_modes {}
foreach s ${active_scenarios} {
    lappend c_modes constraints_${s}
}

set vars(constraint_modes)                    [list ${c_modes}]

foreach s ${active_scenarios} {
    set vars(constraints_${s},pre_cts_sdc)    inputs/sdc/${s}.sdc
    set vars(constraints_${s},post_cts_sdc)   inputs/sdc/${s}.sdc
}

set a_views {}
foreach s ${active_scenarios} {
    lappend a_views analysis_${s}
}

set vars(analysis_views)                         [join ${a_views}]

foreach s ${active_scenarios} {
    set vars(analysis_${s},delay_corner)          delay_default
    set vars(analysis_${s},constraint_mode)       constraints_${s}
}

set vars(default_setup_view)                   "analysis_UNIFIED_BUFFER"
set vars(setup_analysis_views)                 "[join ${a_views}]"
set vars(active_setup_views)                   "[join ${a_views}]"

set vars(default_hold_view)                    "analysis_UNIFIED_BUFFER"
set vars(hold_analysis_views)                  "[join ${a_views}]"
set vars(active_hold_views)                    "[join ${a_views}]"

set vars(power_analysis_view)                  analysis_UNIFIED_BUFFER
