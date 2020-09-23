#!/bin/bash

default_space='100G'
function help {
    echo ""
    echo "$0 <dir> <space>"
    echo "    Verify that dir <dir> has at least <space> gigabytes available (default $default_space)"
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

if [ "$dir"   == "" ]; then 
    echo "**ERROR: No dir specified on command line"
    help; exit 13; 
fi
if [ "$space" == "" ]; then 
    echo "WARNING: No space requirement specified on command line"
    echo "WARNING: Will use default requirement '$default_space'"
    space=$default_space
fi

if ! test -d $dir; then
    echo "***ERROR: Cannot find target dir '$dir'"
    exit 13;
fi

# Strip out "G", "g", "gb" etc.
space_wanted=`echo $space | sed 's/[^0-9]//g'`

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
    && echo "Checking that dir '$dir' has at least ${space_wanted}G available space..."

# Trial and error shows that this is what df -H thinks is a gig
G=$(( 1000 * 1000 * 1000))

# Nothing's ever easy. This comes out closest to what df -H reports
space_avail=`df    $dir --output=avail | tail -1`
space_avail_bytes=$(( $space_avail * 1024 ))
space_avail_G=$(( $space_avail_bytes / $G ))

if [[ $space_avail_G -lt $space_wanted ]]; then
    if [ "$VERBOSE" == "true" ]; then
        if [ "$space_avail_G" == "0" ]; then
            avail="less than 1G";
        else
            avail="only ${space_avail_G}G";
        fi
        echo "***ERROR: Looks like dir '$dir' has $avail available space"
        echo "***ERROR: Dir '$dir' needs at least ${space_wanted}G to continue"
        echo ""
    fi
    exit 13
fi

