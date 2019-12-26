proc sr_funcs_setenv_VTO_GOLD {} {
    # Where to find reference/gold db files
    # set ::VTO_GOLD /sim/steveri/garnet/tapeout_16/synth/ref
    # set ::VTO_GOLD /sim/steveri/garnet/tapeout_16/synth/gpf0_gold
    if { [info exists ::env(VTO_GOLD)] } {
        puts "@file_info: gold ref dir VTO_GOLD=$::env(VTO_GOLD)"
    } else {
        # set ::env(VTO_GOLD) /sim/steveri/garnet/tapeout_16/synth/gpf7_DRC0_no_optdesign
        set ::env(VTO_GOLD) /sim/steveri/garnet/tapeout_16/synth/ref
        puts "@file_info: Env var VTO_GOLD not set"
        puts "@file_info: Using default gold ref dir VTO_GOLD=$::env(VTO_GOLD)"
        # FIXME this puts/ls combo below did not work!?
        # puts -nonewline "@file_info: "
        # ls -l $::env(VTO_GOLD)
        # FIXED?
        if { [catch { exec ls -l $::env(VTO_GOLD) } result] == 0} { 
            puts "@file_info: $result"
        } else { 
            puts "@file_info: oh this looks like trouble :("
        } 
    }
    # # Want a record of where the reference db files are coming from
    # if { ! [file isdirectory $::env(VTO_GOLD)] } {
    #     puts "@file_info: No ref dir (daring aren't we)" 
    # } else {
    #     puts -nonewline "@file_info: "
    #     ls -l $::env(VTO_GOLD)
    # }
}
                     
sr_funcs_set_stages {} {
    ##############################################################################
    # Figure out which stages are wanted
    # 
    # Default: do all stages of the flow
    # 
    # Note: previously had best success with stages "route eco" only
    
    if { ! [info exists env(VTO_STAGES)] } {
        set ::env(VTO_STAGES) "all"
    }
    set vto_stage_list [split $::env(VTO_STAGES) " "]
    puts "@file_info: $vto_stage_list"
    
    # To do all stages, unset env var VTO_STAGES and/or set to "all"
    # To do e.g. just floorplan and eco, do 'export VTO_STAGES="floorplan eco"'
    if {[lsearch -exact $vto_stage_list "all"] >= 0} {
        set ::env(VTO_STAGES) "floorplan place cts fillers route optDesign eco"
        set vto_stage_list [split $::env(VTO_STAGES) " "]
        puts "@file_info: $vto_stage_list"
    }
    
    # Turn stages env variable into a useful list
    puts "@file_info: VTO_STAGES='$::env(VTO_STAGES)'"
    puts "@file_info: vto_stage_list='$vto_stage_list'"
    return vto_stage_list
}
##############################################################################
# Read gold or local snapshots from previous stages of execution...
proc sr_read_db_local { db } {
    if { ! [file isdirectory $db] } {
        puts "@file_info: Could not find local db $db"
        return 0
    } else {
        puts "@file_info: read_db $db"
        read_db $db
        return 1
    }
}
proc sr_read_db_gold { db } {
    set db $::env(VTO_GOLD)/$db
    if { ! [file isdirectory $db] } {
        puts "@file_info: Could not find gold db $db"
        return 0
    } else {
        puts "@file_info: read_db $db"
        read_db $db
        return 1
    }
}
proc sr_find_and_read_db { db } {
    if   { [ sr_read_db_local $db ] } { return 1 } \
    else {   sr_read_db_gold  $db   }
}

# sr_info "Begin stage 'floorplan'"
# => "@file_info 11:45 Begin stage 'floorplan'"
proc sr_info { msg } {
  set time [ clock format [ clock seconds ] -format "%H:%M" ]
  puts "@file_info $time $msg"
} 

proc sr_funcs_find_or_create_results_syn {} {
    ##############################################################################
    # Where is results_syn? Which one should we use?
    # 
    # Apparently everyone needs results_syn/syn_out.v?
    # @file_info 11:53 Begin stage 'floorplan'
    # **ERROR: (IMPIMEX-10):	Specified file cannot be found: results_syn/syn_out.v.
    # 
    # results_syn in VTO_GOLD is maybe unreliable b/c it was often a symlink
    # 
    #     # ERROR: (TCLCMD-989): cannot open SDC file
    #     # 'results_syn/syn_out._default_constraint_mode_.sdc' for mode 'functional'
    #     if { ! [file isdirectory results_syn] } {
    #         # set db $::env(VTO_GOLD)/$db
    #         ln -s $::env(VTO_GOLD)/results_syn
    # 
    if { ! [file isdirectory results_syn] } {
        puts "@file_info WARNING Looks like there is no results_syn directory"
        puts "@file_info WARNING It should have been created by something like"
        puts "@file_info WARNING implementation/synthesis/full_chip_flow.sh"
        puts "@file_info WARNING I will try and find it."

        # If everything were canonical, we should be here right now:
        # aha-arm-soc-june-2019/components/cgra/garnet/tapeout_16/synth/GarnetSOC_pad_frame
        # and results_syn would be here:
        # aha-arm-soc-june-2019/implementation/synthesis/synth/GarnetSOC_pad_frame/results_syn
        set top ../../../../../..
        set synth implementation/synthesis/synth/GarnetSOC_pad_frame
        set local_rsyn $top/$synth/results_syn

        set need_cached 1
        puts "@file_info: Checking for local results_syn dir '$local_rsyn'"
        if { ! [file isdirectory $local_rsyn] } {
            puts "@file_info: WARNING Cannot find local results_syn dir, will use cached version instead"
            set need_cached 1
        } else {
            if { [ catch { grep -q Tile_PE $local_rsyn/syn_out.v } ] } {
                puts "@file_info: Found no local syn_out.v with Tile_PE, will use cached version"
                set need_cached 1
            } else {
                puts "@file_info: Found valid local results_syn dir, will build symlink"
                puts "ln -s $local_rsyn"
                ln -s $local_rsyn
                set need_cached 0
            }
        }
        # puts need_cached=$need_cached
        if { $need_cached } {
            puts "@file_info WARNING using cached version of results_syn"
            set cached_version /sim/ajcars/aha-arm-soc-june-2019
            set cached_version $cached_version/components/cgra/garnet/tapeout_16
            set cached_version $cached_version/final_synth/GarnetSOC_pad_frame
            set cached_rsyn $cached_version/results_syn
            puts "ln -s $cached_rsyn"
            ls $cached_rsyn
            ln -s $cached_rsyn
        }
    }
}    

# NOT USED this was a bad idea
# proc sr_funcs_setenv_VTO_OPTDESIGN {} {
#     # env var VTO_OPTDESIGN lets us optionally skip optDesign stage
#     # FIXME this is a
# 
#     # set ::env(VTO_OPTDESIGN) 0
#     # # delete this after at least one successful run!
#     # if { $::env(VTO_OPTDESIGN) } {
#     #      puts "@file_info: VTO_OPTDESIGN=$::env(VTO_OPTDESIGN)"
#     # }
#     # puts "@file_info: VTO_OPTDESIGN=$::env(VTO_OPTDESIGN)"
#     if { [info exists ::env(VTO_OPTDESIGN)] } {
#         puts "@file_info: VTO_OPTDESIGN=$::env(VTO_OPTDESIGN)"
#     } else {
#         puts "@file_info: No VTO_OPTDESIGN found (yet)"
#         puts "@file_info: Will default to 1 (do optDesign)"
#         set ::env(VTO_OPTDESIGN) 1
#     }
# }
