# get the ADK environment variables
source ./inputs/adk/adk.tcl

# read the oasis
set L [ layout create ./inputs/design.oas \
               -dt_expand \
               -preservePaths \
               -preserveProperties ]

# rename the top cell
$L cellname [$L topcell] $env(intel_database_name)_v

# create a new top cell
$L create cell $env(intel_database_name)

# instantiate the original poly-vertical cell, and rotate it to poly-horizontal
# Intel requires the database to be rotated 90 degrees clockwise
# Calibredrv ang option is counter-clockwise, so it should be 270
$L create ref $env(intel_database_name) $env(intel_database_name)_v 0 0 0 270 1

# Assert the top cell name is correct
set topcell [$L topcell]
if {$topcell != $env(intel_database_name)} {
    error "Assertion failed: The top cell should be $env(intel_database_name), but it is $topcell"
}

# get the bbox
set bbox [$L bbox $topcell]
set bbox_llx [lindex $bbox 0]
set bbox_lly [lindex $bbox 1]
set bbox_urx [lindex $bbox 2]
set bbox_ury [lindex $bbox 3]

# Stamp the final PR boundary layer on top of the design
set boundary_layer $ADK_PR_BOUNDARY_LAYER
set layer_exist [$L exists layer $boundary_layer]
if { $layer_exist == 0 } {
    puts "Specified layer: $boundary_layer does not exist in the input oasis file."
    $L create layer $boundary_layer
    puts "Successfully created layer: $boundary_layer"
}
puts "Creating cover box on layer: $boundary_layer with bbox: $bbox_llx $bbox_lly $bbox_urx $bbox_ury"
$L create polygon $topcell $boundary_layer $bbox_llx $bbox_lly $bbox_urx $bbox_ury

# move the origin back to (0, 0)
$L modify origin $topcell $bbox_llx $bbox_lly

# write out the new database
set out_file ./outputs/$env(intel_database_name)_h.oas
puts "Writing out the oasis file to: $out_file"
$L oasisout $out_file
