#=========================================================================
# stream-out.tcl
#=========================================================================
# Script used to customize the OASIS stream out step


if { [info exists ADK_DBU_PRECISION] } { 
    set stream_out_units $ADK_DBU_PRECISION
} else {
    set stream_out_units 1000
}

set merge_files_oas \
    [concat \
        [lsort [glob -nocomplain inputs/adk/*.oas*]] \
        [lsort [glob -nocomplain inputs/*.oas*]] \
    ]

streamOut ./design-merged.oas \
    -units ${stream_out_units} \
    -dieAreaAsBoundary \
    -format oasis \
    -mapFile $vars(gds_layer_map) \
    -uniquifyCellNames \
    -merge $merge_files_oas
