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


# ?? Is this placement ??
# read_io_file inputs/io_file -no_die_size_adjust 
loadIoFile inputs/io_file -noAdjustDieSize

# ?? Is this placement ??
# snap_floorplan_io
snapFPlanIO




# Do we need/want this?? It's from tile_array or something
# # setFlipping - Specifies the orientation of the bottom row in the core area
# # * s: Specifies that the second row flips from the bottom up.
# setFlipping s
