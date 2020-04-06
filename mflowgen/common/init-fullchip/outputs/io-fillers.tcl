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

    ########################################################################
    # Note this section has nothing to do with IO fillers.
    # This could easily be a separate script, call it something like "rte_mmadness.tcl"

    # [stevo]: connect corner cells to RTE
    # delete and recreate cell to set "is_physical" attribute to false (can't connect net to pin of physical-only cell)
    #     
    # FIXME steveri 1912 - "get_db insts pads/corner*" does
    # nothing. Did you mean to say "get_db insts corner*"?
    # NOTE THAT elsewhere (floorplan.tcl maybe) we *disconnected* all the RTE pins
    foreach inst [get_db insts pads/corner*] {
      puts "this line is never reached :("
      set loc [get_db $inst .location]
      set ori [get_db $inst .orient]
      set name [get_db $inst .name]
      delete_inst -inst $name
      create_inst -inst $name -cell PCORNER  -status fixed \
          -location [lindex $loc 0] -orient [string toupper $ori]
      # connect_pin -net pads/rte -pin RTE -inst $name
      # connect_pin -inst $name -pin RTE -net pads/rte
        #attachTerm $name RTE pads/rte
    }
    # At this point there are no rte or esd nets (see above)
    # (e.g. 'get_db nets rte' returns empty set)
    # so this does nothing as well
    set_db [get_db nets rte*] .skip_routing true
    set_db [get_db nets rte*] .dont_touch true
    set_db [get_db nets esd] .skip_routing true
    set_db [get_db nets esd] .dont_touch true

    # end of "rte_madness.tcl"
    ########################################################################


    # [sr 1912] Re-create (but don't place) corner_ur that was deleted just above
    # This prevents missing-cell error when/if read results_syn again, e.g.
    # 
    # **ERROR: (TCLCMD-917): Cannot find 'cells' that match 'corner_ur'
    # (File /sim/steveri/garnet/tapeout_16/synth/GarnetSOC_pad_frame/
    # powerplanned.db/libs/mmmc/syn_out._default_constraint_mode_.sdc,
    # Line 105657): "set_dont_touch [get_cells corner_ur]"
    #create_inst -inst corner_ur -cell PCORNER

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
