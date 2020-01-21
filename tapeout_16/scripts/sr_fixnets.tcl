# Try and fix all net-related DRC violations
proc sr_fixnets {} {
    # Assumes that "check_drc" was run and markers exist
    set srf_markers [ get_db markers ]
    set n_markers [ llength $srf_markers ]
    if { $n_markers == 0 } { return }

    # Scan markers for problem nets
    set errnets [ find_nets_in_markers $srf_markers ] 
    puts "Beginning errnet list:"
    foreach n $errnets { puts " $n" }
    check_each_net $errnets; # (optional)

    # Fix GB pinspacing error nets FIRST
    puts "@file_info -----"
    puts "@file_info sr_fixnets(): Found $n_markers DRC errors"
    puts "@file_info sr_fixnets(): First try fixing gb_pinspacing errors"
    # set_proc_verbose fixgb_pinspacing_errors
    # set_proc_verbose retry_nets
    fixgb_pinspacing_errors
        
    # Check problem nets to see which are still problems
    set errnets [ check_all_nets $errnets ]
    puts "New errnet list:"; foreach n $errnets { puts " $n" }

    set max_tries 3; set n_tries 0
    while { $errnets != "" } {
        # Note retry_nets() will automatically skip any fixed wires I think
        incr n_tries; 
        set n_errnets [ llength $errnets ]
        puts "@file_info ----------------------------------------------------------------"
        puts "@file_info sr_fixnets(): Clean up $n_errnets remaining nets, attempt $n_tries of $max_tries"
        foreach n $errnets { retry_nets $n }

        # Check problem nets to see which (if any) are still problems
        set errnets [ check_all_nets $errnets ]
        if { $errnets == "" } {
            puts "@file_info sr_fixnets(): Looks like we got 'em all, hooray!"
            break
        }
        # Don't get stuck in an infinite loop!
        if { $n_tries >= $max_tries } {
            puts "@file_info sr_fixnets(): Exceeded max tries; giving gup"
            break
        }
        puts "New errnet list:"; foreach n $errnets { puts " $n" }
    }
}
proc check_each_net { netlist } {
    # Must(?) save and restore existing markers
    write_drc_markers tmp.srf.drc_markers
    foreach n $netlist {
        #         puts "@file_info Retry problem net $n"
        #         retry_nets $n
        puts "Checking net $n"
        deselect_obj -all; select_obj $n; delete_markers
        check_drc -check_only selected_net -limit 10 > tmp
        set n_errors [ llength [ get_db markers ] ]
        puts "Found $n_errors errors for net $n"
    }
    read_drc_markers tmp.srf.drc_markers
}
proc check_all_nets { netlist } {
    # Check all nets at once
    # Destroys existing markers, builds new ones
    # Returns new errnet list based on markers
    delete_markers
    deselect_obj -all
    puts "Selecting nets..."
    foreach n $netlist {
        puts " $n"
        select_obj $n; 
    }
    puts "Checking selecting nets..."
    check_drc -check_only selected_net -limit 10 > tmp
    set n_errors [ llength [ get_db markers ] ]
    puts "Found $n_errors"
    set errnets [ find_nets_in_markers [ get_db markers ] ]
    puts "Found errnets"
    foreach n $errnets { puts " $n" }
    return $errnets
}

proc find_nets_in_markers { markers } {
    # e.g. set errnets2 [ find_nets_in_markers [ get_db markers ] ]
    set errnets ""
    foreach m $markers {
        # eg "Regular Wire of Net core_u_proc_tlx/proc_subsys_dma1_pc[23] & Regular Wire of Net core_u_proc_tlx/n_438377"
        set msg [ get_db $m .message ]

        # Find net(s) mentioned in errmsg; add to list if new/unique
        set i 0
        regexp {(Regular Wire of Net )(.*)} $msg m_all m1 m2
        while { [ regexp {(Regular Wire of Net )(.*)} $msg m_all m1 m2 ] } {
            set n [ lindex $m2 0 ]
            
            # Add to list if unique/new
            if { [ lsearch -exact $errnets $n] == -1} {
                puts "found new/unique net $n"
                lappend errnets $n
            } else {
                puts "net $n in list already"
            }
            set msg $m2
            puts "now msg = $msg "
            incr i; puts $i
            if { $i > 10 } {
                puts "oof too many nets something's wrong"
                break
            }
        }
        foreach n $errnets { puts $n }
    }
    return $errnets
}    

# Fix all nets mentioned in DRC error messages
# It's okay if some nets have already been fixed;
# retry_nets will verify error before fixing
proc fix_all_nets { markers } {
    # Scrub through markers and list all nets mentioned therein
    # read_drc_markers ~/viols.drc
    set errnets find_nets_in_markers $markers
    foreach n $errnets {
        puts "@file_info Retry problem net $n"
        retry_nets $n
        puts $n
    }
}
proc fixgb_pinspacing_errors {} {
    # Global buffer has a tendency to produce idiomatic errors where a pin
    # gets jailed in by vertical m3 wires and there's insufficient space
    # to connect to the pin. This produces an m2 spacing error that this
    # procedure is designed to fix.

    # Find m2-metal-spacing violations. Looking for messages like
    #   Regular Wire of Net core_cgra_subsystem/GlobalBuffer_inst0/FE_OFN1616124_FE_OFN37588_global_buffer_inst0_global_buffer_int_memory_bank_24_glbuf_memory_core_sram_to_mem_data_17
    #   & Pin of Cell core_cgra_subsystem/GlobalBuffer_inst0/FE_OFC91028_FE_OFN37588_global_buffer_inst0_global_buffer_int_memory_bank_24_glbuf_memory_core_sram_to_mem_data_17
    set markers [
                 get_db markers -if { 
                     .layer == "layer:M2" && 
                     .subtype == "Metal*SameMask*Spacing" &&
                     .message == Regular*Wire*of*Net*
                 }
                ]
    puts "@file_info Found [ llength $markers ] GB pin-spacing errors"
    # set_proc_verbose fixgb_pinspacing_error
    foreach m $markers { fixgb_pinspacing_error $m }
}
proc fixgb_pinspacing_error { mar } {
    # "mar" is error marker for m2 spacing violation in global buffer
    # Idiomatically, this can be solved using below algorithm.

    # Err-marker net e.g. "core_cgra_subsystem/GlobalBuffer_inst0/FE_OFN51225_global_buffer_inst0_global_buffer_int_memory_bank_6_glbuf_memory_core_memory_n_40"
    set m [ get_db $mar .message ]
    set n [ lindex $m 4 ]
    set problem_net "net:$n"
    puts "@file_info ----------------------------------------------------------------"
    puts "@file_info Found gb(?) problem net [ rightmost $problem_net 45 ]"

    # Err-marker bounding box
    set llx [get_db $mar .bbox.ll.x]; set lly [get_db $mar .bbox.ll.y]
    set urx [get_db $mar .bbox.ur.x]; set ury [get_db $mar .bbox.ur.y]
    puts "@file_info Found gb-error bounding box $llx $lly $urx $ury"

    # Huh has to be zoomed in I guess
    # (does any of this work no_gui???)
    gui_zoom -rect \
        [ expr $llx - 0.5 ] \
        [ expr $lly - 0.5 ] \
        [ expr $urx + 0.5 ] \
        [ expr $ury + 0.5 ]

    # Theory: nearby m3 wires prevent 2/3 via on m2 pin
    # Find, record and delete all m3 wires near violation
    set nearby_nets [ get_nearby_nets $llx $lly $problem_net ]
    foreach n $nearby_nets { puts "found nearby net $n" }

    # Can do this to see the nets in the gui
    # deselect_obj -all; select_obj $problem_net
    # deselect_obj -all; foreach n $nearby_nets { select_obj $n }

    # To step through nets
#     foreach n $nearby_nets {
#         echo $n
#         deselect_obj -all; select_obj $n; gui_redraw; sleep 1
#         puts -nonewline "<enter> to continue"; gets stdin your_answer
#     }

    # Delete the blocking nets maybe
    # Note: delete_routes fials silently if netname not found :(
    foreach n $nearby_nets {
        puts "@file_info - delete blocking net [ rightmost $n 45 ]"
        delete_routes -net $n
    }
    # Now, with blocking wires, out of the way, retry orig problem net.
    # set_proc_verbose retry_nets
    retry_nets $problem_net

    # Reconnect deleted blocking nets
    puts "@file_info Reconnect deleted blocking nets"

#     deselect_obj -all
#     foreach n $nearby_nets { select_net $n }   
#     get_db selected
#     puts "@file_info Reconnect deleted blocking nets"


#     retry_nets $nearby_nets

    puts "Reconnect should take about...? I dunno...?"
    deselect_obj -all
    foreach n $nearby_nets { select_obj $n }

    set_multi_cpu_usage -local_cpu 8
    set_db route_design_selected_net_only true
    set_db route_design_detail_end_iteration 10

    route_design -no_placement_check
    deselect_obj -all
    puts "Reconnect done!"
}
proc get_nearby_nets { llx lly problem_net } {
    # Given lower-left x,y coords of a bounding box,
    # Find all (vertical) m3 wires within +/- 0.15u
    # Sweep .15u left and right from llx, find all m3 nets
    # (Ignore problem net itself)
    # NOTE m3 wires are like .04u wide
    set xstart [ expr $llx - 0.15 ]
    set xfin   [ expr $llx + 0.15 ]
    set n 0
    set nearby_nets ""
    set_layer_preference node_layer -is_visible 0
    set_layer_preference M3 -is_visible 1
    for {set x $xstart} {$x <= $xfin} { set x [ expr $x + 0.03 ] } {
        deselect_obj -all
        # echo gui_select -point $x $lly
        gui_select -point $x $lly
        # puts [ get_db selected .obj_type ]
        set w [ get_db selected -if { .obj_type == "wire" } ]
        if { $w != "" } { 
            # echo foo $w
            set n [ get_db $w .net ]
            # echo bar $n
            echo "---"
            echo $problem_net
            echo $n
            echo "---"
            if { $n == $problem_net } { continue }
            if { [ lsearch -exact $nearby_nets $n] != -1} { continue }
            puts "found nearby net $n"
            lappend nearby_nets $n
        }
    }
    foreach n $nearby_nets { puts "found nearby net $n" }
    return $nearby_nets
}
proc rightmost { s n } {
    # Return rightmost n chars of string s
    set l [ string length $s ]
    set i [ expr $l - $n ]
    return [ string range $s $i 999 ]
}
proc retry_nets { nlist } {
    # Verify that net has error
    delete_markers
    deselect_obj -all
    foreach n $nlist { 
        puts "@file_info Retry problem net(s) [ rightmost $n 45 ]"
        select_obj $n
    }
    check_drc -check_only selected_net -limit 10 > tmp
    tail tmp
    set n_errors [ llength [ get_db markers ] ]
    if { $n_errors == 0 } {
        puts "@file_info - huh looks like net(s) is/are okay after all"
        return
    }
    # Tell nanorouter to operate only on selected nets
    # Max 10 iterations, although I'm pretty sure one is enough (it's fast).
    set_multi_cpu_usage -local_cpu 8
    set_db route_design_selected_net_only true
    set_db route_design_detail_end_iteration 10

    #     deselect_obj -all; select_obj $n
    #     delete_routes -net $n

    # Expect this to take like 15 minutes
    puts "Retry should take about fifteen minutes"
    deselect_obj -all
    foreach n $nlist { select_obj $n; delete_routes -net $n }
    route_design -no_placement_check
    deselect_obj -all
    puts "Retry done!"
}
