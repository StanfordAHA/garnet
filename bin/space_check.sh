#!/bin/bash

function help {
    echo ""
    echo "$0 <dir> <space>"
    echo "    Verify that dir <dir> has at least <space> gigabytes available"
    echo ""
    echo "Examples:"
    echo "    $0 /sim/tmp 0G"
    echo "    $0 /sim/tmp 100"
    echo "    $0 /sim/tmp 100G"
    echo "    $0 /sim/tmp 100gb"
    echo "    $0 ./build_dir 10G"
    echo ""
}

########################################################################
# Command-line switches / args / argv
VERBOSE=false; dir= ; space=
while [ $# -gt 0 ] ; do
    case "$1" in
        -h|--help)    help; exit;    ;;
        -v|--verbose) VERBOSE=true;  ;;
        -q|--quiet)   VERBOSE=false; ;;
        -d|--debug)   VERBOSE=true;  ;;
        -*)
            echo "***ERROR unrecognized arg '$1'"; help; exit; ;;
         *)
            if   [ "$dir"   == "" ]; then   dir="$1"; 
            elif [ "$space" == "" ]; then space="$1";
            fi ;; 
    esac
    shift
done

if [ "$dir"   == "" ]; then help; exit 13; fi
if [ "$space" == "" ]; then help; exit 13; fi
if ! test -d $dir; then
    echo "***ERROR: Cannot find target dir '$dir'"
    exit 13;
fi

# Strip out "G", "g", "gb" etc.
space=`echo $space | sed 's/[^0-9]//g'`
# echo $space

if [ '' ]; then
    # cut-n-paste tests
    space_check.sh foo 0
    space_check.sh foo 0gb
    space_check.sh foo 100
    space_check.sh foo 100G
    space_check.sh foo 100GB
fi

[ "$VERBOSE" == "true" ] && echo ""
[ "$VERBOSE" == "true" ] \
    && echo "Checking that dir '$dir' has at least ${space}G available space..."

G=$(( 1024 * 1024 )) ; # As reported by df in 1024-byte blocks!
space_wanted=$(( $space * $G ))

space_avail=`df    $dir --output=avail | tail -1`
avail_human=`df -H $dir --output=avail | tail -1`
avail_human=`echo $avail_human` ; # Eliminate whitespace?

if [[ $space_avail -lt $space_wanted ]]; then
    if [ "$VERBOSE" == "true" ]; then
        echo "***ERROR: Looks like $dir has only $avail_human available space"
        echo "***ERROR: $dir needs at least ${space}G to continue"
        echo ""
    fi
    exit 13
fi

if [ "$VERBOSE" == "true" ]; then
    echo "Looks like '$dir' has $avail_human space available. Good enough!"
    echo ""
fi

