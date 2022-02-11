# What a hack!
# 
# Existing fix-shorts script has at least two problems:
# - does not run until after post-route
# - only looks for shorts on layers M4-M9
# 
# This script addresses M2/M3 errors that recently cropped up after "route" step :(

echo "@file_info: Checking for short circuits(!)..."

# First delete ALL markers
deselectAll; select_obj [ dbGet top.markers ]; deleteSelectedFromFPlan



########################################################################
# Fix shorts 1: Fetch a fresh set of violation markers
# Only interested in metal shorts; ignore all others as much as possible
set_verify_drc_mode -ignore_cell_blockage true
set_verify_drc_mode -check_only regular
set_verify_drc_mode -disable_rules "\
  jog2jog_spacing \
  eol_spacing \
  cut_spacing \
  min_cut \
  enclosure \
  color \
  min_step \
  protrusion \
  min_area \
  out_of_die \
"
clearDrc; verify_drc 
echo "DRC violations found:"
foreach m [dbGet top.markers] { echo "  [dbGet $m.subType]" }; echo ""

# Uncomment below to see markers so far
# get_db markers .*
# llength [get_db markers]


########################################################################
# Fix shorts 2: Identify the shorts
set shorts [dbGet top.markers { .subType eq "Metal Short" }]
if { $shorts == "0x0" } {
    echo "@file_info: No shorts found"
} else {
   # Fix shorts 3: Show how many shorts were found
    set nshorts [llength $shorts]
    echo "@file_info: Found $nshorts short circuit(s):"
    foreach m [dbGet top.markers { .subType eq "Metal Short" }] {
        echo "  [dbGet $m.message]"
    }
    echo ""

    # Fix shorts 4: See if we can fix the shorts with ecoRoute
    #
    # Note: "ecoRoute -drc" seems to do much better than
    # globalDetailRoute with "setNanoRouteMode -routeWithEco true"
    #
    # Only interested in metal shorts; so delete all non-short markers
    # (notably "Parallel Run Length Spacing") before starting work
    deselectAll
    select_obj [ dbGet top.markers {.subtype ne "Metal Short"} ]
    deleteSelectedFromFPlan
    ecoRoute -fix_drc

    # Fix shorts 5: Check your work
    clearDrc; verify_drc
    echo "DRC violations found:"
    foreach m [dbGet top.markers] { echo "  [dbGet $m.subType]" }; echo ""

    set shorts [dbGet top.markers { .subType eq "Metal Short" }]
    if { $shorts == "0x0" } {
        echo "@file_info: All shorts fixed"
    } else {

        # Try again on failure why not
        echo "@file_info: Oops looks like I failed; lemme try again"

        # Fix shorts 3a: Show how many shorts were found
        set nshorts [llength $shorts]
        echo "@file_info: Found $nshorts short circuit(s):"
        foreach m [dbGet top.markers { .subType eq "Metal Short" }] {
            echo "  [dbGet $m.message]"
        }
        echo ""

        # Fix shorts 4a: See if we can fix the shorts with eco routing (again)
        echo "@file_info: - Fixing short circuits (again)"
        deselectAll
        select_obj [ dbGet top.markers {.subtype ne "Metal Short"} ]
        deleteSelectedFromFPlan
        ecoRoute -fix_drc

        # Fix shorts 5a: Check your work
        clearDrc; verify_drc
        echo "DRC violations found:"
        foreach m [dbGet top.markers] { echo "  [dbGet $m.subType]" }; echo ""

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
