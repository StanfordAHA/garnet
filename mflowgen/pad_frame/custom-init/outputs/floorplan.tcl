#=========================================================================
# floorplan.tcl
#=========================================================================
# This script is called from the Innovus init flow step.

# Original `stylus` cmd from 06/2019 tapeout
# create_floorplan \
#     -core_margins_by die \
#     -die_size_by_io_height max \
#     -site core \
#     -die_size 4900.0 4900.0 100 100 100 100

# Translated to legacy cmd
floorPlan \
    -coreMarginsBy die \
    -dieSizeByIoHeight max \
    -site core \
    -d 4900.0 4900.0 100 100 100 100

# Dunno what this is...?
# setFlipping s
