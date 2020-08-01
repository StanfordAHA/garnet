#=========================================================================
# floorplan.tcl
#=========================================================================
# This script is called from the Innovus init flow step.

# Should this be in power step??
delete_global_net_connections
connect_global_net VDDPST -type pgpin -pin VDDPST -inst *
connect_global_net VSS -type pgpin -pin VSSPST -inst * 
connect_global_net VDD -type pgpin -pin VDD -inst *
connect_global_net VDD -type tiehi
connect_global_net VSS -type pgpin -pin VSS -inst *
connect_global_net VSS -type tielo
connect_global_net VDD -type pgpin -pin VPP -inst *
connect_global_net VSS -type pgpin -pin VBB -inst *



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

# Adding PCORNER cells here, io_file will take
# care of orientation and location
create_inst -inst corner_lr -cell PCORNER
create_inst -inst corner_ll -cell PCORNER
create_inst -inst corner_ul -cell PCORNER

# read_io_file inputs/io_file -no_die_size_adjust 
loadIoFile inputs/io_file -noAdjustDieSize

# Disconnect IO-pad RTE pins
foreach x \
    [get_property \
         [get_cells -filter "ref_name=~*PDD* || ref_name=~*PRW* || ref_name=~*FILL* || ref_name=~*PVDD1* || ref_name=~*PVDD2* || ref_name=~*PDB2* || ref_name=~PCORNER" ]\
         full_name \
        ] \
    {
        # disconnect_pin -inst $x -pin RTE
        detachTerm $x RTE
    }

# snap_floorplan_io - Snaps I/O cells to a user-defined grid

snapFPlanIO


# insert io fillers. previously, this was done *after* routing bumps
# copied from "proc done_fp" in "gen_floorplan.tcl"




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
