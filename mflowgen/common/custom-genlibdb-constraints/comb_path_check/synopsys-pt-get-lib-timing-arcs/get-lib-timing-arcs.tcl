#=========================================================================
# get-lib-timing-arcs.tcl
#=========================================================================
# Final reports
#
# Author : Alex Carsello
# Date   : March 12, 2024
#
# Generates a reports with all of the timing arcs present in a given
# timing model.

# Please do not modify the sdir variable.
# Doing so may cause script to fail.
set sdir "."

# Read in the library
read_lib inputs/design.lib

# Generating timing arc report
report_lib $::env(design_name) -timing_arcs > lib_timing_arcs


exit

