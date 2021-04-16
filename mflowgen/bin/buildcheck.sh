#!/bin/bash

# Usage: buildcheck.sh gold.194

function show_help {
cat <<EOF

Usage: $0 [ -slrtgeah ] <build_dir>
  -h,--help     help
  -a,--all     do all checks
  -s,--size    do_sizes
  -L,--lvs     do_lvs
  -r,--run     do_runtimes
  -l,--do_logs (log update times)
  -e,--err     do_err
  -R, --retry  do_qcheck
  -q, --qrc    do_qcheck


EOF
    exit
}

# Debugging?
# DBG=1
DBG=

########################################################################
# Process command-line args
build_dirs=()
opstring=''

while [ $# -gt 0 ] ; do
    test $DBG && echo "Processing arg '$1'"
    case "$1" in
        --help)  show_help; exit  ;;

        --size*) opstring="${opstring}s" ;;
        --lvs)   opstring="${opstring}L" ;;
        --run*)  opstring="${opstring}r" ;;
        --log*)  opstring="${opstring}l" ;;
        --err*)  opstring="${opstring}e" ;;
        --retr*) opstring="${opstring}R" ;; # retry or retries e.g.
        --qrc*)  opstring="${opstring}q" ;; # qrc check
        --QRC*)  opstring="${opstring}q" ;; # qrc check

        --all)   opstring="${opstring}sLrleR";  break  ;;
         -a)     opstring="${opstring}sLrleR";  break  ;;

        --*) show_help; exit ;;         # Unknwon '--' arg
         -*) opstring="$opstring$1" ;;  # Add to opstring

          *) build_dirs+=($1)       ;;  # Target directory(s)
    esac
    shift
done
test $DBG && (echo "DONE processing args"; echo '---')

# Default: "do all checks" in "current directory"
[ "$opstring"       == "" ] && opstring="sLrle"
[ ${#build_dirs[@]} == 0  ] && build_dirs=(.)


[ $DBG ] && echo Build dirs: ${build_dirs[@]}
if [ ${#build_dirs[@]} -ne 1 ]; then
    for bd in ${build_dirs[@]}; do
        $0 -$opstring $bd
    done
    exit
fi
bd=${build_dirs[0]}
[ $DBG ] && echo FOUND BUILD DIR $bd

##############################################################################
# Initialize "options" dictionary
# 
# Example: opstring="slrtge"
#   keys=(e g l r s t) = ${!options[*]}
#   vals=(e g l r s t) =  ${options[*]}

unset options; declare -A options
for (( i=0; i<${#opstring}; i++ )); do
    o="${opstring:$i:1}"
    options[$o]=$o
done

# echo "keys: " ${!options[*]} # keys
# echo "vals: "  ${options[*]} # values

##############################################################################
# Use options array "optons"

[ "${options[h]}" ] && show_help
[ "${options[s]}" ] && do_sizes=true
[ "${options[L]}" ] && do_lvs=true
[ "${options[r]}" ] && do_runtimes=true
[ "${options[l]}" ] && do_logs=true
[ "${options[e]}" ] && do_err=true
[ "${options[R]}" ] && do_qcheck=true
[ "${options[q]}" ] && do_qcheck=true

if [ "$DBG" ]; then
    test "$do_sizes"    == true && echo DO_SIZES
    test "$do_lvs"      == true && echo DO_LVS
    test "$do_runtimes" == true && echo DO_RUNTIMES
    test "$do_logs"     == true && echo DO_LOGS
    test "$do_err"      == true && echo DO_ERR
    test "$do_qcheck"   == true && echo DO_QCHECK
    # exit
fi



########################################################################
# Find target build directory
for backup in /build/gold.$bd /build/$bd; do
    if test -d $bd; then break; fi
    echo "Cannot find dir $bd; trying dir $backup..."
    bd=$backup
done

# User can optionally leave final "/full_chip" off of the dir pathname
cd $bd
test -d full_chip && cd full_chip
echo "Found test dir `pwd`"

if [ "$do_sizes" ]; then
    ####################################################################
    # Size matters
    # 
    # 14-glb_top/9-glb_tile          SIZE  154 BY 1900 ;
    # 17-tile_array/16-Tile_MemCore  SIZE  279 BY   88 ;
    # 17-tile_array/17-Tile_PE       SIZE  102 BY   88 ;
    # 17-tile_array                  SIZE 4749 BY 1632 ;
    echo ''; echo '+++ SIZE CHECK'
    for f in `find * -name 'design.lef'`; do
      # e.g. "17-Tile_PE/24-cadence-innovus-signoff/outputs/design.lef" => "17-Tile_PE"
      f1=`echo $f | sed 's/\/[0-9]*-cadence-innovus.*//'`
      # in case e.g. pwd="17-tile-array" and f="28-cadence-innovus-signoff/outputs/design.lef"
      expr $f1 : '.*lef' > /dev/null && f1=$(basename `pwd`)
      printf "%-30s %s %4.0f %s %4.0f %s\n" $f1 `grep SIZE $f`
    done
fi

if [ "$do_lvs" ]; then
    ####################################################################
    # LVS check e.g.
    #  glb_tile           CORRECT (14-glb_top/9-glb_tile/22-mentor-calibre-lvs/lvs.report)
    #  global_buffer      CORRECT (14-glb_top/24-mentor-calibre-lvs/lvs.report)
    #  global_controller  CORRECT (15-global_controller/19-mentor-calibre-lvs/lvs.report)
    echo ''; echo '+++ LVS CHECK'
    reports=`find . -name lvs.report`
    if [ ! "$reports" ]; then 
        echo 'No LVS report (yet)'
    else
        reports=`find * -name lvs.report -type f`
        for r in $reports; do
            head -10000 $r | grep -v \# | awk '
            /CORR/ { printf("  %-17s %9s ('$r')\n", $2, $1)}
            '
        done
    fi
fi

if [ "$do_runtimes" ]; then
    ########################################################################
    # Status check e.g.
    # 
    # +++ CURRENT STATUS (runtimes)
    # --------------------------------------------------------------------------------
    # 9-rtl                               --         26 min  6 sec 
    # 14-glb_top                          --    1 hr 18 min 35 sec  <-- in progress
    # 17-tile_array                       --   13 hr 24 min 37 sec 
    # --------------------------------------------------------------------------------
    # 
    echo ''
    make runtimes |& egrep -v '^(Total|echo|runtimes)' \
        | grep -vi warning | sed '1d; s/Runtimes/+++ CURRENT STATUS (runtimes)/'
fi

########################################################################
# log check (check latest log update time to see if we might be stuck)
if [ "$do_logs" ]; then
    echo ''; echo "+++ LOG CHECK"
    log=`ls -t */mflowgen-run.log | head -1`
    echo -n "LOG: "; date -d@`stat $log -c %Y`
    echo -n "NOW: "; date

    ########################################################################
    # latest activity
    echo ''; echo '--- LATEST ACTIVITY cut-n-paste'
    echo "tail `pwd`/$log"
    echo ''

    # echo '--------------------------------------------------------------------------------'
    # tail $log | cut -b 1-80
    # echo '--------------------------------------------------------------------------------'
fi

########################################################################
# Check to see if we had to restart/retry anywhere b/c of QRC failures
if [ "$do_qcheck" ]; then

    echo ''; echo '+++ RETRIES REQUIRED?'
    logfiles=$(find * -name \*.log)
    found_retry=false

    grep -H QCHECK $logfiles \
        | sed 's,/make-prh.log.,: ,' \
        | grep ': QCHECK' \
        && found_retry=true

    [ $found_retry == false ] && echo 'No qcheck info found.'
    echo ''
fi


########################################################################
# Error check
if [ "$do_err" ]; then
    echo ''; echo '--- ERROR CHECK'
    echo "ERROR SUMMARY:"

    errfiles=`find * -name \*.log \
     -exec bash -c \
       "cat {} | grep -v 'Error Limit' | egrep '(^Error|^\*\*ERROR)' > /dev/null" \
     \; \
     -print`
    # echo $errfiles

    for f in $errfiles; do

        # egrep filters below should find only the lowest-level log file
        # e.g. "17-tile_array/17-Tile_PE/24-cadence-genus-genlib/logs/genus.log"
        # but not "make-GLC.log" or "17-tile_array/mflowgen-run.log"

        # Filename must include a toolname
        echo $f | egrep 'cadence|innovus|mentor' > /dev/null || continue

        # Filename should be e.g. "genus.log" not "mflowgen-run.log"
        echo $f | egrep 'mflowgen'        > /dev/null && continue

        echo $f
        cat $f | egrep '(^Error|^\*\*ERROR)' \
            | grep -v 'Error Limit' \
            | chop 80 | sort | uniq -c | sort -rn | head
        echo ""
    done | head

    # find * -name \*.log -exec egrep '(^Error|^\*\*ERROR)' {} \; \
    #   | grep -v 'Error Limit' \
    #   | chop 80 | sort | uniq -c | sort -rn | head

    cat <<EOF

SEE ALL ERRORS (cut-n-paste):
egrep '(^Error|^\*\*ERROR)' \`find . -name \*.log\` | less

EOF
fi


exit

# experiments

egrep '(^Error|^\*\*ERROR)' `find * -name \*.log` \
  | grep -v 'Error Limit' \
  | chop 80 | sort | uniq -c | sort -rn | head

find * -name \*.log -exec egrep '(^Error|^\*\*ERROR)' {} \; \
  -exec printf "9999999 %s\n" {} \; \
  | grep -v 'Error Limit' \
  | chop 80 | sort | uniq -c | sort -rn | head


function has_errors {
   egrep '(^Error|^\*\*ERROR)' $1 > /dev/null && return 0 || return 13
}
has_errors make-tile_array.log && echo YES || echo NO

errfiles=`find * -name \*.log \
     -exec bash -c \
       "cat {} | grep -v 'Error Limit' | egrep '(^Error|^\*\*ERROR)' > /dev/null" \
     \; \
     -print`
echo $errfiles

for f in $errfiles; do

    # egrep filters below should find only the lowest-level log file
    # e.g. "17-tile_array/17-Tile_PE/24-cadence-genus-genlib/logs/genus.log"
    # but not "make-GLC.log" or "17-tile_array/mflowgen-run.log"

    # Filename must include a toolname
    echo $f | egrep 'cadence|innovus' > /dev/null || continue

    # Filename should be e.g. "genus.log" not "mflowgen-run.log"
    echo $f | egrep 'mflowgen'        > /dev/null && continue

    echo $f
    cat $f | egrep '(^Error|^\*\*ERROR)' \
        | grep -v 'Error Limit' \
        | chop 80 | sort | uniq -c | sort -rn | head
    echo ""
done | less

# f=14-glb_top/mflowgen-run.log
# 
# f=22-cadence-genus-genlib/.execstamp
# echo $f | egrep 'cadence|innovus' > /dev/null && echo yes || echo no

# egrep 'cadence|innovus' 14-glb_top/mflowgen-run.log && echo yes || echo no




# find * -name \*.log -exec egrep '(^Error|^\*\*ERROR)' {} \; \
#   -exec printf "9999999 %s\n" {} \; \
#   | grep -v 'Error Limit' \
#   | chop 80 | sort | uniq -c | sort -rn | head


##############################################################################
##############################################################################
##############################################################################
# OLD:

# # Remove extraneous dashes from opstring
# [ $DBG ] && echo "opstring BEFORE = '$opstring'"
# opstring=$(echo $opstring | tr -d '-')
# [ $DBG ] && echo "opstring AFTER  = '$opstring'"

    # 'grep -H' => print filename along w/ match e.g.
    #      make-qrc.log:+++ QCHECK QRC CHECK
    #      make-qrc.log:+++ QCHECK: INITIATING RETRY

#     # OLD/DEPRECATED
#     # grep -H QCHECK $logfiles | egrep 'QCHECK QRC CHECK' && found_retry=true
# 
#     # NEW
#     grep -H QCHECK $logfiles | egrep 'PROBLEM|RETRY' && found_retry=true
