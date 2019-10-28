#!/bin/bash
function usage {
cat <<EOF

Uses buildkite scripts to run synthesis and layout locally

Usage:
    # Use -v for verbose, -q for quiet execution
    $0 [ -v | -q ] <options>

Examples:
    # Run generator, PE and mem tile synthesis and layout, and top-level layout
    $0

    # Run top-level layout only EXCLUDING final optDesign stage
    $0 --top_only

    # Run ONLY the final optDesign stage (prior design db must exist in local or gold dir)
    $0 --opt_only

    # Quietly run all seven stages of top-level synthesis EXCEPT final optDesign
    $0 -q --top_only
    $0 -q --top_only --vto_stages="floorplan place cts fillers route eco"

    # Quietly run all seven stages of top-level synthesis including final optDesign
    $0 -q --top_only --vto_stages="all"
    $0 -q --top_only --vto_stages="floorplan place cts fillers route opt eco"

EOF
}

##############################################################################
# Defaults

# VERBOSE currently unused I think
VERBOSE=false
TOP_ONLY=false
TILES_ONLY=false

##############################################################################
# args
while [ $# -gt 0 ] ; do

    case "$1" in
        -h)     usage; exit ;;
        --help) usage; exit ;;

        -q) VERBOSE=false; shift ;;
        -v) VERBOSE=true;  shift ;;

        --top_only)
            TOP_ONLY=true; shift ;;

        --tiles_only)
            TILES_ONLY=true; shift ;;

        --opt_only)
            TOP_ONLY=true;  
            # Need BOTH of these to run optdesign
            export VTO_STAGES=opt
            export VTO_OPTDESIGN=1
            shift ;;

        # E.g. --vto_stages="a b c"
        --vto_stages=*)
            s=`expr "$1" : '.*=\(.*\)'`
            export VTO_STAGES="$s"
            shift ;;

        *)
            printf "ERROR: did not recognize option '%s', please try --help\\n" "$1"
            exit 1
            ;;
    esac
done
echo VERBOSE=$VERBOSE
echo "VTO_STAGES = '$VTO_STAGES'"
for s in $VTO_STAGES; do echo "  $s"; done
##############################################################################



# Little hack, builds minimal CGRA grid, doesn't seem to help anything much
# LITTLE=''
# if [ "$1" == "--LITTLE" ] ; then LITTLE="$1"; shift; fi

# Check to see if we're in the right place e.g. "tapeout_16" directory
# expr `pwd` : '.*/garnet/tapeout_16$' && rightplace=true || rightplace=false
expr `pwd` : '.*/tapeout_16$' > /dev/null && rightplace=true || rightplace=false
if [ $rightplace != true ] ; then
  echo ""
  echo "ERROR looks like you're in the wrong place"
  echo "- you are here:   `pwd`"
  echo "- should be here: .../tapeout_16"
  exit 13
fi

# Designate a cache directory CACHEDIR for staging different phases:
# 
# GEN.sh puts generated verilog in CACHEDIR/genesis_verif
# GEN.sh puts generated mem_cfg.txt, mem_synth.txt in CACHEDIR
# 
# SYN.sh fetches genesis_verif, mem_cfg.txt, mem_synth.txt from CACHEDIR
# SYN.sh copies synth/{append.csh,PE/,run_all.csh,Tile_MemCore/,Tile_PE/} to CACHEDIR
#
# TOP.sh on local machine fetches synth info from CACHEDIR
# TOP.sh on buildkite does not use CACHEDIR

# Use e.g. /tmp/cache-steveri as the cache directory CACHEDIR
set -x
export CACHEDIR=/tmp/cache-$USER

# TOP.sh will do this (maybe)
# # Copy contents of synth directory to local runspace
# ls $CACHEDIR/synth synth/
# cp -rp $CACHEDIR/synth/* synth/
# ls synth

# Hm okay let's hold off on this for now.
# [ -e $CACHEDIR ] && /bin/rm -rf $CACHEDIR
# mkdir -p $CACHEDIR

# Start at top level dir, just like buildkite would do
cd ..


if [ "$TOP_ONLY" == "false" ] ; then
    .buildkite/GEN.sh -v $LITTLE

    .buildkite/SYN.sh -q PE
    .buildkite/SYN.sh -q MemCore

    .buildkite/PNR.sh -q PE
    .buildkite/PNR.sh -q MemCore
fi

if [ "$TILES_ONLY" == "false" ] ; then
    .buildkite/TOP.sh -q
fi


# Later we can try this
# $nobuf .buildkite/SYN.sh -q PE | $nobuf awk '{print "PE: " $0}' &
# .buildkite/SYN.sh -q MemCore | $nobuf awk '{print "    Mem: " $0}' &


# Cleaning gup
/bin/rm -rf ./cache

# OLD
# # VERBOSE currently unused I think
# VERBOSE=false
# if   [ "$1" == "-v" ] ; then VERBOSE=true;  shift;
# elif [ "$1" == "-q" ] ; then VERBOSE=false; shift;
# fi
# 
# TOP_ONLY=false
# if [ "$1" == "--top_only" ] ; then TOP_ONLY=true;  shift; fi
# 
# # Run only optdesign stage
# if [ "$1" == "--opt_only" ] ; then
#     TOP_ONLY=true;  
#     # Need BOTH of these to run optdesign
#     export VTO_STAGES=opt
#     export VTO_OPTDESIGN=1
#     shift
# fi

