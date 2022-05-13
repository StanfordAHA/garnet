#=========================================================================
# floorplan.tcl
#=========================================================================
# This script is called from the Innovus init flow step.

# Run this in floorplanning step to make io filler addition step happy
# (see add-io-fillers.tcl). Will be re-run in power step
delete_global_net_connections
connect_global_net VDDPST -type pgpin -pin VDDIO -inst *
connect_global_net VSS -type pgpin -pin VSSIO -inst * 
connect_global_net VDD -type pgpin -pin VDDC -inst *
connect_global_net VDD -type tiehi
connect_global_net VSS -type pgpin -pin VSSC -inst *
connect_global_net VSS -type pgpin -pin VSS_CM -inst *
connect_global_net VSS -type tielo
connect_global_net VSS -type pgpin -pin VPW -inst *
connect_global_net VDD -type pgpin -pin VNW -inst *



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
    -adjustToSite \
    -d 4900.0 4900.0 200 200 200 200

# read_io_file inputs/io_file -no_die_size_adjust 
loadIoFile inputs/io_file -noAdjustDieSize

# Use IO_PAD tech site to create grid for pad placement
# This ensures that all gaps between pads will be fillable
# by io filler cells. 
set io_site [dbGet -p head.sites.name IO_PAD]
set_preference ConstraintUserXGrid [dbGet ${io_site}.size_x]
set_preference ConstraintUserYGrid [dbGet ${io_site}.size_y]

# snap_floorplan_io - Snaps I/O cells to user-defined grid

snapFPlanIO -userGrid

# Do we need/want this?? It's from tile_array or something
# # setFlipping - Specifies the orientation of the bottom row in the core area
# # * s: Specifies that the second row flips from the bottom up.
# setFlipping s

# Checks the quality of the floorplan to detect potential
# problems before the design is passed on to other tools.

# check_floorplan
checkFPlan



# DONE




# TODO (in stylus!!)
# source ../../scripts/vlsi/flow/scripts/gen_floorplan.tcl
# set_multi_cpu_usage -local_cpu 8


# # Add ICOVL alignment cells to center/core of chip
# set_proc_verbose add_core_fiducials; add_core_fiducials



# # This is probably for the RDL bump routing I guess?
# # See "man setNanoRouteMode" for legacy equivalents
# set_db route_design_antenna_diode_insertion true 
# set_db route_design_antenna_cell_name ANTENNABWP16P90 
# set_db route_design_fix_top_layer_antenna true 





# POWER commands from original/prev floorplan.tcl
# eval_legacy {editPowerVia -area {1090 1090 3840 3840} -delete_vias true}
