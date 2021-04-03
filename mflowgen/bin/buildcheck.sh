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

EOF
    exit
}

########################################################################
# Process command-line args
bd=.        ; # default = current directory
opstring=''

# DBG=1
DBG=
while [ $# -gt 0 ] ; do
    test $DBG && echo "Processing arg '$1'"
    case "$1" in
        --help)  show_help; exit  ;;
        --size*) opstring="${opstring}s" ;;
        --lvs)   opstring="${opstring}L" ;;
        --run*)  opstring="${opstring}r" ;;
        --log*)  opstring="${opstring}l" ;;
        --err*)  opstring="${opstring}e" ;;

        --all)   opstring="-a";  break  ;;
        -a)      opstring="-a";  break  ;;

#         --size*) do_sizes=true    ;;
#         --lvs)   do_lvs=true      ;;
#         --run*)  do_runtimes=true ;;
#         --log*)  do_logs=true     ;;
#         --err*)  do_err=true      ;;
#         --all)   opstring="-a"; break  ;;

        --*) show_help; exit ;;         # Unknwon '--' arg
         -*) opstring="$opstring$1" ;;  # Add to opstring
          *) bd=$1        ;;            # Target directory
    esac
    shift
done
test $DBG && (echo "DONE processing args"; echo '---')

# DEFAULT = do all checks
if [ "$opstring" == ""   ]; then opstring="-a"    ; fi
if [ "$opstring" == "-a" ]; then opstring="-sLrle"; fi


##############################################################################
# Initialize options array "optons"
# 
# Example: opstring="-slrtge"
#   keys=(e g l - r s t) = ${!options[*]}
#   vals=(e g l - r s t) =  ${options[*]}

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

if [ "$DBG" ]; then
    test "$do_sizes"    == true && echo DO_SIZES
    test "$do_lvs"      == true && echo DO_LVS
    test "$do_runtimes" == true && echo DO_RUNTIMES
    test "$do_logs"     == true && echo DO_LOGS
    test "$do_err"      == true && echo DO_ERR
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

if [ "$do_logs" ]; then
    ########################################################################
    # log check (check latest log update time to see if we might be stuck)
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

if [ "$do_err" ]; then
    ########################################################################
    # Check to see if we had to restart/retry anywhere
    echo ''; echo '+++ RETRIES REQUIRED?'
    logfiles=$(find * -name \*.log)

    # OLD/DEPRECATED
    grep -H QCHECK $logfiles | egrep 'QCHECK QRC CHECK'; # '-H' ==> print filename

    # NEW
    grep -H QCHECK $logfiles | egrep 'PROBLEM|RETRY'; # '-H' ==> print filename

    ########################################################################
    # Error check
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

# # Optional error check
# if [ '' ]; then
# echo ''; echo ''
# grep -i error `find . -name \*.log` \
#     | egrep -v ': *#' \
#     | grep -v ' 0 error' \
#     | grep -v 'Error=0' \
#     | uniq \
#     | cat
# fi

# grep -i error \`find . -name \*.log\` \\
#   | egrep -v ': *#' | grep -v ' 0 error' \\
#   | grep -v 'Error=0' | uniq
# 
# egrep '(^Error|^\*\*ERROR)' \`find . -name \*.log\` | chop 80 | wc -l
# egrep '(^Error|^\*\*ERROR)' \`find . -name \*.log\` | chop 80 | less
# egrep '(^Error|^\*\*ERROR)' \`find . -name \*.log\` | sort | uniq -c
# 
# find . -name \*.log -exec egrep '(^Error|^\*\*ERROR)' {} \; \
# | chop 80 | sort | uniq -c | sort -rn
#   14280 Error   : Could not interpret SDC command. [SDC-202] [read_sdc]
#      85 **ERROR: (IMPSP-2021):  Could not legalize <2> instances in the design. Check war
#      80 **ERROR: (IMPSP-9022):  Command 'refinePlace' completed with some error(s).
#      60 **ERROR: (IMPSP-2021):  Could not legalize <7> instances in the design. Check war
#      20 **ERROR: (IMPSP-2021):  Could not legalize <1> instances in the design. Check war
#      20 **ERROR: (IMPSP-2021):  Could not legalize <11> instances in the design. Check wa
#      15 **ERROR: (IMPSP-2021):  Could not legalize <8> instances in the design. Check war
#      14 Error Limit = 1000; Warning Limit = 50
#      10 Error   : Invalid SDC command option combination. [SDC-204] [set_driving_cell]
#      10 **ERROR: (IMPSP-2021):  Could not legalize <6> instances in the design. Check war
#       5 **ERROR: (IMPSP-2021):  Could not legalize <9> instances in the design. Check war




