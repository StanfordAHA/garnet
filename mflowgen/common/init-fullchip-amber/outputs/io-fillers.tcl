# mflowgen will do this part if we set it up properly...
# source $env(GARNET_HOME)/mflowgen/common/scripts/stylus_compatibility_procs.tcl

########################################
## Drawn heavily from gen_floorplan.tcl,
## a collection of floorplan procedures
## mostly written by Brian Richards
## modified heavily by Stevo Bailey
########################################

# Previously this was "proc done_fp {}" in "gen_floorplan.tcl"
# proc io_fillers {} {

    set ioFillerCells "PFILLER10080 PFILLER00048 PFILLER01008 PFILLER00001"

    # Snap the right and left IO drivers to the 0.048um fin grid
    # snap_floorplan -io_pad 
    snapFPlan -ioPad
    
    # [stevo]: delete upper right corner cell, because LOGO can't be close to metal
    # delete_inst -inst corner_ur*
    deleteInst corner_ur*

    # FIXME should we run globalNetCommand before add_io_fillers?
    #
    # From Innovus Text Command Reference manual, for "addIoFiller":
    # Note: Before using addIoFiller, run the globalNetCommand to provide
    # global-net-connection rules for supply pins of the added
    # fillers. Without these rules, the built-in design-rule checks of
    # addIoFiller will not be accurate.
    #
    # (The globalNetCommand note does not appear in the stylus version of the 
    # man page (add_io_fillers)

    # [stevo]: add -logic so fillers get RTE signal connection
    #   [steveri 11/2019]: Dunno where "-derive_connectivity" came from, but it
    #   throws errs when used in conjunction w/Soong-jin's ANAIOPAD shenanigans
    # add_io_fillers -cells "$ioFillerCells" -logic -derive_connectivity
    # add_io_fillers -cells "$ioFillerCells" -logic
    addIoFiller -cell "$ioFillerCells" -logic

    set_db [get_db nets esd] .skip_routing true
    set_db [get_db nets esd] .dont_touch true
    
    set_db [get_db nets rte*] .skip_routing true
    set_db [get_db nets rte*] .dont_touch true

    # end of "rte_madness.tcl"
    ########################################################################


    # Done!
    # snap_floorplan -all; check_floorplan
    snapFPlan -all
    checkFPlan

# Trying the thing
# # Uh, now stream it out i guess
# # FIXME should this be a separate "streamout.tcl" script maybe?
#   # -units "specifies the resolution for values in the GDSII file"
#   # streamOut $vars(results_dir)/$vars(design).gds.gz -units 1000 -mapFile $vars(gds_layer_map)
#   streamOut outputs/design.gds.gz -units 1000 -mapFile $vars(gds_layer_map)
