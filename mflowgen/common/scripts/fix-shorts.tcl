########################################################################
# Save route blockage info in name() box() and layer() arrays
set i 0
foreach ptr [get_db route_blockages] {
    select_obj $ptr

    set blockage_names($i)  [get_db $ptr .name]
    set blockage_boxes($i)  [get_db $ptr .rects]
    set blockage_layers($i) [get_db $ptr .layer.name]

    # echo $i $ptr $name($i)
    # printf "%2d %s %s\n" $i $ptr $name($i)
    incr i
}
set nblockages $i

########################################################################
# Display list of blockages found e.g.
#    0 RouteBlk -layer M3 -box {15.93 1670.88 77.225 1898.352} -name def
#    1 RouteBlk -layer AP -box {0.0 0.0 0.3 1900.416} -name left
#    2 RouteBlk -layer M9 -box {0.0 0.0 0.3 1900.416} -name left
#   ...
#   52 RouteBlk -layer M3 -box {15.93 765.504 77.225 992.976} -name def
#   53 RouteBlk -layer M3 -box {15.93 539.136 77.225 766.608} -name def
#   54 RouteBlk -layer M3 -box {15.93 312.816 77.225 540.288} -name def
#   55 RouteBlk -layer M3 -box {15.93 86.448 77.225 313.92} -name def
echo "@file_info: Found and saved info for $nblockages route blockages"
for { set i 0 } { $i < $nblockages } { incr i } {
    printf "#   %2d " $i
    echo RouteBlk \
        -layer $blockage_layers($i) \
        -box $blockage_boxes($i)    \
        -name $blockage_names($i)   \
        ;
}

########################################################################
# Delete route blockages (will restore them again later)
echo "@file_info: Deleting route blockages"
deleteRouteBlk -all
redraw; sleep 1

########################################################################
# Fix shorts 1: Fetch a fresh set of violation markers
# Note Tile_PE has VDD shorts on lower layers that we choose to ignore...
# FIXME what's up with the VDD shorts!!??
clearDrc
verify_drc -layer_range { M4 M9 }



########################################################################
# Fix shorts 2: Identify the shorts
set shorts [dbGet top.markers { .subType eq "Metal Short" }]
if { $shorts == "0x0" } {
    echo "@file_info: No shorts found"
} else {
   # Fix shorts 3: Show how many shorts were found
    set nshorts [llength $shorts]
    echo "@file_info: Found $nshorts short circuit(s):"
    echo [ dbGet [dbGet top.markers { .subType eq "Metal Short" }].message ]

    # Fix shorts 4: See if globalDetailRoute can fix the shorts with eco
    #   08/2021 changed num iterations from 2 to 10,
    #   see garnet issue https://github.com/StanfordAHA/garnet/issues/803
    echo "@file_info: Fixing short circuits"
    setNanoRouteMode -routeWithEco true
    setNanoRouteMode -drouteEndIteration 10
    globalDetailRoute

    # Fix shorts 5: Check your work
    clearDrc
    verify_drc -layer_range { M4 M9 }

    set shorts [dbGet top.markers { .subType eq "Metal Short" }]
    if { $shorts == "0x0" } {
        echo "@file_info: All shorts fixed"
    } else {

        # PE requires two tries maybe
        echo "@file_info: Oops looks like I failed; lemme try again"

        # Fix shorts 3a: Show how many shorts were found
        set nshorts [llength $shorts]
        echo "@file_info: - Found $nshorts short circuit(s):"
        echo [ dbGet [dbGet top.markers { .subType eq "Metal Short" }].message ]

        # Fix shorts 4a: See if globalDetailRoute can fix the shorts with eco
        echo "@file_info: - Fixing short circuits"
        setNanoRouteMode -routeWithEco true
        setNanoRouteMode -drouteEndIteration 2
        globalDetailRoute

        # Fix shorts 5a: Check your work
        clearDrc
        verify_drc -layer_range { M4 M9 }

        set shorts [dbGet top.markers { .subType eq "Metal Short" }]
        if { $shorts == "0x0" } {
            echo "@file_info: All shorts fixed"

            # FIXME doesn't the wrapper script save the design?
            # FIXME in which case we don't need this line here?
            # Save changes *only* if shorts fixed
            saveDesign checkpoints/design.checkpoint/save.enc -user_path

        } else {
            echo "@file_info: - Oops looks like I failed again oh no"
            echo ""
            echo "**ERROR: Metal shorts exist, see stdout for details"
            echo "@file_info: -- Found $nshorts short circuit(s):"
            echo "@file_info: -- Giving up now"
            exit 13
        }
    }
}

########################################################################
# Restore route blockages
redraw; sleep 1
echo "@file_info: Restoring $nblockages route blockages"
for { set i 0 } { $i < $nblockages } { incr i } {
    printf "%2d " $i
    echo createRouteBlk \
        -layer $blockage_layers($i) \
        -box $blockage_boxes($i)    \
        -name $blockage_names($i)   \
        ;
    createRouteBlk \
        -layer $blockage_layers($i) \
        -box $blockage_boxes($i)    \
        -name $blockage_names($i)   \
        ;
}
redraw; sleep 1
