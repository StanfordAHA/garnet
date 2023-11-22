set lib_files {}
set views {}

# decode corner into analysis view name
if { $::env(corner) == "typical" } {
    set view_keyword setup
} elseif { $::env(corner) == "wc" } {
    set view_keyword setup
} elseif { $::env(corner) == "bc" } {
    set view_keyword hold
} else {
    puts "ERROR: Unknown corner $::env(corner)"
    exit 1
}

foreach view [all_analysis_views] {

    # Check if this is the view we want
    # by checking whether the view keyword is in the view name
    if {[string first $view_keyword $view] >= 0} {
        set lib_name "${view}.lib"
        lappend lib_files $lib_name
        lappend views $view
        set_analysis_view -setup $view -hold $view
        do_extract_model $lib_name -view $view
    }

}

# If we have more than one analysis view, merge them into a single design.lib
if {[llength $lib_files] > 1} {
    merge_model_timing -library $lib_files -modes $views -mode_group combined -outfile design.lib
} else {
    mv $lib_files design.lib
}


