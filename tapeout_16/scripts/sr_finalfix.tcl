# DELETE SEALRING!!!
set had_sealring 0
if { [get_db insts sealring] ne "" } {
    set had_sealring 1
    set sr [get_db insts sealring]
    set sr_cell [get_db [get_db $sr .base_cell] .name]; puts $sr_cell
    set sr_locx [get_db $sr .location.x]; puts $sr_locx
    set sr_locy [get_db $sr .location.y]; puts $sr_loc#
    puts "@file_info WARNING Found existing sealring $sr_cell at loc $sr_locx $sr_locy"
    puts "@file_info WARNING Deleteing sealring, will restore later"
    puts "#file_info delete_inst -inst sealring"
    delete_inst -inst sealring; # gui_redraw
}

# If all went well up to this point, there should be only 37 DRC
# errors left. This script is supposed to eliminate nine of them.
# The remaining 28 errors all stem from the bottom IOPAD placement
# problem, for which I haven't decided on a good solution yet...

# 2001 update: all went *very* well up to this point, there is now
# just one error. Unfortunately it's one I thought we fixed earlier

# AUGH it keeps coming back!
# I guess it keeps getting deleted and re-created to prevent
# "missing corner_ur" error in database read
# FIXME/TODO solve this problem earlier/better.

# Hm think maybe I fixed this, back in top_garnet_staged.tcl...
# but will leave this here for now jut in case...
if { [ get_db insts corner_ur] != "" } { 
    set ur [get_db inst:corner_ur .bbox]
    set ll [get_db inst:corner_ll .bbox]
    if [ expr $ur == $ll ] {
    puts "@file_info ----------------------------------------------------------------"
    puts "@file_info looks like corner_ur is on top of corner_ll (again)"
    puts "@file_info Deleting corner_ur (again): 'delete_inst -inst corner_ur'"
    delete_inst -inst corner_ur*
    puts "@file_info ----------------------------------------------------------------"
    }
}



########################################################################
# Tell nanorouter to operate only on selected nets
# Max 10 iterations, although I'm pretty sure one is enough (it's fast).
set_multi_cpu_usage -local_cpu 8
set_db route_design_selected_net_only true
set_db route_design_detail_end_iteration 10

# Haha looks like we fixed them all!!!
# FIXME/TODO: build an algorithm to do this automatically
if { 0 } {

    ########################################################################
    # 1568581 M2 (first of three nanoroute violations)
    puts "@file_info Fixing net 1568581, should take about 30 minutes"

    # 1. Delete problem net
    set n net:core_cgra_subsystem/GlobalBuffer_inst0/FE_OFN1613594_n_1568581
    set found_net [get_db nets $n]
    if { "$found_net" eq "" } { echo no net found }
    deselect_obj -all; select_obj $n
    # check_drc -check_only selected_net
    delete_routes -net $n

    # 2. Delete nearby nets that block M3 attachment:
    set n1 net:GarnetSOC_pad_frame/core_cgra_subsystem/GlobalBuffer_inst0/FE_OFN1614041_global_buffer_inst0_global_buffer_int_memory_bank_27_glbuf_memory_core_sram_to_mem_data_32
    set n2 {net:GarnetSOC_pad_frame/core_cgra_subsystem/GlobalBuffer_inst0/global_buffer_inst0_global_buffer_int_memory_bank_27_glbuf_memory_core_memory_sram_gen_genblk1\[5\].Q_temp[38]}
    delete_routes -net [list $n $n1 $n2]

    # Redo problem net: expect this to take 15 min
    deselect_obj -all; select_obj $n
    route_design -no_placement_check
    # Expect this to take about 15m

    # Reattach (deleted) blocking nets: expect this to take 15 min
    deselect_obj -all; select_obj [list $n1 $n2]
    route_design -no_placement_check
    deselect_obj -all

    ########################################################################
    # 391528 M2 (remaining two nanoroute violations)
    puts "@file_info Fixing net 391528, should take about 30 minutes"

    # One problem net and two blocking nets
    set n net:GarnetSOC_pad_frame/core_u_proc_tlx/n_391528
    set n1 net:GarnetSOC_pad_frame/core_u_proc_tlx/CTS_660
    set n2 {net:GarnetSOC_pad_frame/core_u_proc_tlx/proc_subsys_dma0_upl330_engine_upl330_icache_upl330_icache_array_w2_icache_array\[11\][11]}

    # Delete them all
    select_obj [list $n $n1 $n2]
    delete_routes -net [list $n $n1 $n2]

    # Redo problem net: expect this to take 15 min
    deselect_obj -all; select_obj $n
    route_design -no_placement_check

    # Reattach (deleted) blocking nets: expect this to take 15 min
    deselect_obj -all; select_obj [list $n1 $n2]
    route_design -no_placement_check
    deselect_obj -all

    ########################################################################
    # bad patch wire M4
    puts "@file_info Fixing M4 patch wire, should take about 15 minutes"

    set n {net:GarnetSOC_pad_frame/core_u_proc_tlx/proc_subsys_dma0_upl330_engine_upl330_lsq_upl330_write_lsq_upl330_write_lsq_array_data_array\[15\][50]}

    deselect_obj -all; select_obj $n
    delete_routes -net $n

    # Expect this to take like 15 minutes
    deselect_obj -all; select_obj $n
    route_design -no_placement_check
    deselect_obj -all
}

########################################################################
# RESTORE SEALRING why not
if { $had_sealring } {
    # addInst -cell N16_SR_B_1KX1K_DPO_DOD_FFC_5x5 -inst sealring
    # -physical -loc {-52.344 -53.7}
    puts "@file_info WARNING restoring sealring"
    puts "@file_info addInst -cell $sr_cell -inst sealring -physical -loc {$sr_locx $sr_locy}"
    # haha $sr_cell cannot survive the eval_legacy wrapper haha :( :(
    set ::env(TMP1) $sr_cell
    set ::env(TMP2) $sr_locx
    set ::env(TMP3) $sr_locy
    eval_legacy {
        set sr_cell $::env(TMP1)
        set sr_locx $::env(TMP2)
        set sr_locy $::env(TMP3)
        puts "addInst -cell $sr_cell -inst sealring -physical -loc {$sr_locx $sr_locy}"
        # addInst -cell $sr_cell -inst sealring -physical -loc {$sr_locx $sr_locy} NOPE!
        addInst -cell $sr_cell -inst sealring -physical -loc [list $sr_locx $sr_locy]
    }
}
