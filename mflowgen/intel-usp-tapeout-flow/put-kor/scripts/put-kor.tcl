
# get the ADK environment variables
source ./inputs/adk/adk.tcl

# read the oasis
set L [ layout create ./inputs/design.oas \
               -dt_expand \
               -preservePaths \
               -preserveProperties ]

# rename the top cell
set topcell [$L topcell]

# Confirm that KOR layer exists
set kor_layer $ADK_GLOBAL_KOR_LAYER
set layer_exist [$L exists layer $kor_layer]
if { $layer_exist == 0 } {
    puts "Specified layer: $kor_layer does not exist in the input oasis file."
    $L create layer $kor_layer
    puts "Successfully created layer: $kor_layer"
}

# Loop through each prefilled cells and put KOR in it
foreach cell $ADK_CELLS_NEED_KOR {
    set bbox [$L bbox $cell]
    set bbox_llx [lindex $bbox 0]
    set bbox_lly [lindex $bbox 1]
    set bbox_urx [lindex $bbox 2]
    set bbox_ury [lindex $bbox 3]
    puts "Creating KOR ($kor_layer) on cell $cell with bbox: $bbox_llx $bbox_lly $bbox_urx $bbox_ury"
    $L create polygon $cell $kor_layer $bbox_llx $bbox_lly $bbox_urx $bbox_ury
}

# write out the new database
set out_file ./outputs/design.oas
puts "Writing out the oasis file to: $out_file"
$L oasisout $out_file
