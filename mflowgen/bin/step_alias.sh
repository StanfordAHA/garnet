#!/bin/bash
# Function to expand step aliases
# Uses output of "make list" from a valid mflowgen step, e.g.
#   % cd /build/gold.93/full_chip
#   % make list | step_alias.sh syn
#       synopsys-dc-synthesis

if [[ -t 0 ]]; then
    echo "Oops you forgot to give me 'make list' info"
    echo "Examples:"
    echo "    make list | $0 syn"
    echo "    make list > tmp.txt; $0 syn < tmp.txt"
    echo ""
    exit 13
fi

# Siphon stdin off to temp file for safekeeping
makelist=/tmp/deleteme.step_alias.$$
cat > $makelist

# SILENTLY delete trash files older than one hour"
# (Result of 'step_alias' must be only the single-word alias!!)
nmin=60
find /tmp \
     -mmin +$nmin \
     -name deleteme.step_alias.\* \
     -exec ls -l {} \; \
     -exec /bin/rm {} \; \
     |& grep -v 'Permission denied'

# E.g. 'step_alias.sh syn' returns 'synopsys-dc-synthesis' or
# 'cadence-genus-synthesis' as appropriate

if [ "$1" == "" ]; then
    echo "***ERROR: no step arg provided to '$0'"
    echo "Usage: make list | $0 <step>"
    exit 13
fi

case "$1" in
    # This is probably dangerous; init is heavily overloaded
    init)      s=cadence-innovus-init      ;;

    # "synthesis" will expand to dc or genus according to what's
    # in "make list" (see below). Same for gdsmerge etc.
    syn)       s=synthesis ;;

    phy)       s=dragonphy ;;
    dragon)    s=dragonphy ;;

    gds)       s=gdsmerge-dragonphy-rdl ;;
    tape)      s=gdsmerge-dragonphy-rdl ;;
    merge)     s=gdsmerge-dragonphy-rdl ;;
    gdsmerge)  s=gdsmerge-dragonphy-rdl ;;
    *)         s="$1" ;;
esac

# 1. First, look for exact match
ntries=1
s1=`cat $makelist |& egrep -- " $s"'$' | awk '{ print $NF; exit }'`

# Then look for alias that expands to synopsys/cadence/mentor tool
# Uses *first* pattern match found in "make list" to expand e.g.
# "synthesis" => "synopsys-dc-synthesis" or "cadence-genus-synthesis"
if ! [ "$s1" ]; then
    ntries=2
    p=' synopsys| cadence| mentor'
    s1=`cat $makelist |& egrep "$p" | egrep -- "$s"'$' | awk '{ print $NF; exit }'`
fi

# Then look for alias that expands to anything that kinda matches
if ! [ "$s1" ]; then
    ntries=3
    s1=`cat $makelist |& egrep -- "$s"'$' | awk '{ print $NF; exit }'`
fi

if ! [ "$s1" ]; then
    echo "**ERROR: Could not find a valid alias for '$1'"
    exit 13
fi

DBG=""; if [ "$DBG" ] ; then
    echo '---'
    echo "FINAL '$s' -> '$s1' (after $ntries tries)"
fi

# Note: returns null ("") if no alias found
echo $s1; # return value = $s1

# Clean up and exit
test -f $makelist && /bin/rm $makelist
exit




##############################################################################
##############################################################################
##############################################################################
# UNIT TESTS for step_alias, cut'n'paste

# See below for deleteme.makelist defs

# Tile array steps
listfile=deleteme.makelist.tile-array.$$
test_steps="constraints MemCore PE rtl synthesis custom-dc-postcompile tsmc16 synthesis foooo"

# Full-chip steps
listfile=deleteme.makelist.fullchip.$$
test_steps="dragon syn init cts place route postroute gds tape merge gdsmerge lvs drc"

for s in $test_steps; do
    a=$(cat $listfile | step_alias.sh $s )
    printf "%-30s ==> %s\n" "$s" "$a"
done

########################################################################
cat << EOF > deleteme.makelist.fullchip.$$
***WARNING OVERRIDING MAKE, USING 'ECHO|MAKE' INSTEAD
echo '' | /usr/bin/make list
Makefile:2010: warning: overriding recipe for target '24-cadence-innovus-init/inputs/.stamp.add-endcaps-welltaps.tcl'
Makefile:2005: warning: ignoring old recipe for target '24-cadence-innovus-init/inputs/.stamp.add-endcaps-welltaps.tcl'

Generic Targets:

 - list      -- List all steps
 - status    -- Print build status for each step
 - runtimes  -- Print runtimes for each step
 - graph     -- Generate a PDF of the step dependency graph
 - clean-all -- Remove all build directories
 - clean-N   -- Clean target N
 - info-N    -- Print configured info for step N
 - diff-N    -- Diff target N

Targets:

 -   0 : cgra_sim_build
 -   1 : constraints
 -   2 : custom-init
 -   3 : custom-lvs-rules
 -   4 : custom-power-chip
 -   5 : custom-read-design
 -   6 : dragonphy
 -   7 : info
 -   8 : netlist-fixing
 -   9 : pre-route
 -  10 : rtl
 -  11 : sealring
 -  12 : soc-rtl
 -  13 : tsmc16
 -  14 : cgra_rtl_sim_compile
 -  15 : gen_sram_macro
 -  16 : glb_top
 -  17 : global_controller
 -  18 : io_file
 -  19 : tile_array
 -  20 : cadence-genus-synthesis
 -  21 : cgra_rtl_sim_run
 -  22 : init-fullchip
 -  23 : cadence-innovus-flowsetup
 -  24 : cadence-innovus-init
 -  25 : cadence-innovus-power
 -  26 : cadence-innovus-place
 -  27 : power-drc
 -  28 : cadence-innovus-cts
 -  29 : cadence-innovus-postcts_hold
 -  30 : cadence-innovus-route
 -  31 : cadence-innovus-postroute
 -  32 : cadence-innovus-postroute_hold
 -  33 : cadence-innovus-signoff
 -  34 : gdsmerge-dragonphy-rdl
 -  35 : synopsys-pt-timing-signoff
 -  36 : mentor-calibre-fill
 -  37 : mentor-calibre-lvs
 -  38 : gdsmerge-fill
 -  39 : antenna-drc
 -  40 : mentor-calibre-drc
 -  41 : cadence-innovus-debug-calibre

Debug Targets:

 - debug-20 : debug-cadence-genus-synthesis
 - debug-24 : debug-cadence-innovus-init
 - debug-25 : debug-cadence-innovus-power
 - debug-26 : debug-cadence-innovus-place
 - debug-27 : debug-power-drc
 - debug-28 : debug-cadence-innovus-cts
 - debug-29 : debug-cadence-innovus-postcts_hold
 - debug-30 : debug-cadence-innovus-route
 - debug-31 : debug-cadence-innovus-postroute
 - debug-32 : debug-cadence-innovus-postroute_hold
 - debug-33 : debug-cadence-innovus-signoff
 - debug-34 : debug-gdsmerge-dragonphy-rdl
 - debug-36 : debug-mentor-calibre-fill
 - debug-37 : debug-mentor-calibre-lvs
 - debug-38 : debug-gdsmerge-fill
 - debug-39 : debug-antenna-drc
 - debug-40 : debug-mentor-calibre-drc
 
EOF
    


########################################################################
cat << EOF > deleteme.makelist.tile-array.$$
***WARNING OVERRIDING MAKE, USING 'ECHO|MAKE' INSTEAD
echo '' | /usr/bin/make list
Makefile:1367: warning: overriding recipe for target '18-cadence-genus-synthesis/inputs/.stamp.design.v'
Makefile:1362: warning: ignoring old recipe for target '18-cadence-genus-synthesis/inputs/.stamp.design.v'

Generic Targets:

 - list      -- List all steps
 - status    -- Print build status for each step
 - runtimes  -- Print runtimes for each step
 - graph     -- Generate a PDF of the step dependency graph
 - clean-all -- Remove all build directories
 - clean-N   -- Clean target N
 - info-N    -- Print configured info for step N
 - diff-N    -- Diff target N
Targets:

 -   0 : constraints
 -   1 : custom-cts-overrides
 -   2 : custom-dc-postcompile
 -   3 : custom-init
 -   4 : custom-lvs-rules
 -   5 : custom-power-hierarchical
 -   6 : e2e_testbench_cascade
 -   7 : e2e_testbench_conv_3_3
 -   8 : e2e_testbench_harris_auto
 -   9 : e2e_testbench_resnet_i1_o1_mem
 -  10 : e2e_testbench_resnet_i1_o1_pond
 -  11 : gls-args
 -  12 : info
 -  13 : rtl
 -  14 : testbench
 -  15 : tsmc16
 -  16 : Tile_MemCore
 -  17 : Tile_PE
 -  18 : cadence-genus-synthesis
 -  19 : cadence-innovus-flowsetup
 -  20 : cadence-innovus-init
 -  21 : cadence-innovus-power
 -  22 : cadence-innovus-place
 -  23 : cadence-innovus-cts
 -  24 : cadence-innovus-postcts_hold
 -  25 : cadence-innovus-route
 -  26 : cadence-innovus-postroute
 -  27 : cadence-innovus-postroute_hold
 -  28 : cadence-innovus-signoff
 -  29 : cadence-genus-genlib
 -  30 : e2e_xcelium_sim_cascade
 -  31 : e2e_xcelium_sim_conv_3_3
 -  32 : e2e_xcelium_sim_harris_auto
 -  33 : e2e_xcelium_sim_resnet_i1_o1_mem
 -  34 : e2e_xcelium_sim_resnet_i1_o1_pond
 -  35 : mentor-calibre-drc
 -  36 : mentor-calibre-lvs
 -  37 : synopsys-vcs-sim
 -  38 : cadence-innovus-debug-calibre
 -  39 : e2e_ptpx_gl_cascade
 -  40 : e2e_ptpx_gl_conv_3_3
 -  41 : e2e_ptpx_gl_harris_auto
 -  42 : e2e_ptpx_gl_resnet_i1_o1_mem
 -  43 : e2e_ptpx_gl_resnet_i1_o1_pond

Debug Targets:

 - debug-18 : debug-cadence-genus-synthesis
 - debug-20 : debug-cadence-innovus-init
 - debug-21 : debug-cadence-innovus-power
 - debug-22 : debug-cadence-innovus-place
 - debug-23 : debug-cadence-innovus-cts
 - debug-24 : debug-cadence-innovus-postcts_hold
 - debug-25 : debug-cadence-innovus-route
 - debug-26 : debug-cadence-innovus-postroute
 - debug-27 : debug-cadence-innovus-postroute_hold
 - debug-28 : debug-cadence-innovus-signoff
 - debug-35 : debug-mentor-calibre-drc
 - debug-36 : debug-mentor-calibre-lvs

EOF
