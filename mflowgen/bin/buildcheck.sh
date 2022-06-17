#!/bin/bash

# Example: buildcheck.sh gold.194

# CHANGE LOG
# sep 2021 added "-e" flag for quick "show_all_errors"
# sep 2021 better detection/reporting of metal short errors
# sep 2021 expanded definition of valid error-log filenames

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
ALL="sLrleRq"
show_all_errs=false

while [ $# -gt 0 ] ; do
    test $DBG && echo "Processing arg '$1'"
    case "$1" in
        --help)  show_help; exit  ;;

        --show*) show_all_errs=true; ;;
        --size*) opstring="${opstring}s" ;;
        --lvs)   opstring="${opstring}L" ;;
        --run*)  opstring="${opstring}r" ;;
        --log*)  opstring="${opstring}l" ;;
        --err*)  opstring="${opstring}e" ;;
        --retr*) opstring="${opstring}R" ;; # retry or retries e.g.
        --qrc*)  opstring="${opstring}q" ;; # qrc check
        --QRC*)  opstring="${opstring}q" ;; # qrc check

        --all)   opstring="${opstring}${ALL}";  ;;
         -a)     opstring="${opstring}${ALL}";  ;;

        --*) show_help; exit ;;         # Unknwon '--' arg
         -*) opstring="$opstring$1" ;;  # Add to opstring

          *) build_dirs+=($1)       ;;  # Target directory(s)
    esac
    if [ "$1" == "-e" ]; then show_all_errs=true; fi
    shift
done
test $DBG && (echo "DONE processing args"; echo '---')

# Default: "do all checks" in "current directory"
[ "$opstring"       == "" ] && opstring="$ALL"
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
echo "--- $0"
echo "Found test dir `pwd`"

if [ "$do_sizes" ]; then
    ####################################################################
    # Size matters
    # 
    # First area indication comes from synthesis report,
    # as much as two hours earlier vs. signoff report, as in the example below:
    # 
    # May  4 08:07 14-cadence-genus-synthesis/results_syn/final_area.rpt
    # May  4 10:16 24-cadence-innovus-signoff/results/Tile_PE.lef
    # 
    # ------------------------------------------------------------------------
    # % cat 14-cadence-genus-synthesis/results_syn/final_area.rpt
    #     Instance Module  Cell Count  Cell Area  Net Area   Total Area 
    #     -------------------------------------------------------------
    #     Tile_PE            10176      4774.620  2214.236     6988.855 


    ####################################################################
    # Latest actual/"correct" sizes as of Jun 2022
    #  16-glb_top/8-glb_tile            231449
    #  16-glb_top                      5139979
    #  17-global_controller               4044
    #  19-tile_array/16-Tile_MemCore     17567
    #  19-tile_array/17-Tile_PE           8131
    #  19-tile_array                     30277
    #  full_chip                      14334645

    echo ''; echo '+++ SIZE CHECK (synthesis report)'

    # Expected / prev values
    declare -A size
    size[glb_tile]=231449
    size[glb_top]=5139979
    size[global_controller]=4044
    size[Tile_MemCore]=17567
    size[Tile_PE]=8131
    size[tile_array]=30277
    size[full_chip]=1433645

    for f in `find * -path '*results_syn/final_area.rpt'`; do
      msg=''
      # e.g. "17-Tile_PE/24-cadence-innovus-signoff/outputs/design.lef" => "17-Tile_PE"
      # e.g. "17-Tile_PE/14-cadence-genus-synthesis/results_syn/final_area.rpt" => "17-Tile_PE"
      f1=`echo $f | sed 's/\/[0-9]*-cadence-genus.*//'`
      # full_chip area has no substep so just use e.g. "full_chip"
      expr $f1 : '.*rpt' > /dev/null && f1=$(basename `pwd`)
      area=`cat $f | awk '/^---/ {next}; FOUND {print $NF;exit}; /^ *Instance/{FOUND=1}'`
      # echo $area $f1
      for key in "${!size[@]}"; do
          expr $f1 : ".*${key}$" > /dev/null \
          && msg=$(printf " (prev was ? %8.0f ?)" ${size[$key]})
      done
      printf "%-30s %8.0f$msg\n" $f1 $area
    done

    ########################################################################
    # More accurate area numbers are available in lef file after signoff...
    # 
    # 14-glb_top/9-glb_tile          SIZE  154 BY 1900 ;
    # 17-tile_array/16-Tile_MemCore  SIZE  279 BY   88 ;
    # 17-tile_array/17-Tile_PE       SIZE  102 BY   88 ;
    # 17-tile_array                  SIZE 4749 BY 1632 ;

    found_lefs=
    echo ''; echo '+++ SIZE CHECK (signoff)'
    for f in `find * -name 'design.lef'`; do

      # E.g. if f="17-Tile_PE/24-cadence-innovus-signoff/outputs/design.lef"
      # then   f1="17-Tile_PE"
      f1=`echo $f | sed 's/\/[0-9]*-cadence-innovus.*//'`

      # E.g. if f="24-cadence-innovus-signoff/outputs/design.lef"
      # get f1 from curdir name 'pwd'; e.g. if pwd="19-tile_array" and
      # f="24-cadence-innovus-signoff/outputs/design.lef" then
      # f1="tile_array"
      expr $f1 : '.*lef' > /dev/null && f1=$(basename `pwd`)

      # E.g. `grep SIZE 28-cadence-innovus-signoff/outputs/design.lef`
      # => "SIZE 4504.140000 BY 1632.384000 ;"
      lef_size=`grep SIZE $f`

      found_lefs=True

      # Find and report signoff actual area
      # E.g. if f="17-Tile_PE/24-cadence-innovus-signoff/outputs/design.lef"
      # then area_rpt="17-Tile_PE/24-cadence-innovus-signoff/reports/signoff.area.rpt"
      area_rpt=`echo $f | sed 's|outputs/design.lef|reports/signoff.area.rpt|'`

      # E.g. `cat $area_rpt`=
      #      Hinst Name   Module Name  Inst Count       Total Area   ...
      #      ------------------------------------------------------- ...
      #      Interconnect                   17177      6226111.682   ...

      # echo "area_rpt=$area_rpt"
      signoff_area=`cat $area_rpt | awk 'NR==3{print $3}'`

      # E.g. "16-Tile_MemCore   SIZE  243 BY   88 ; AREA     15645"
      printf "%-30s %s %4.0f %s %4.0f %s AREA %9.0f\n" $f1 $lef_size $signoff_area

    done
    if [ "$found_lefs" != "True" ]; then echo "  No lefs found"; fi
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
    # +++ RUNTIMES
    # --------------------------------------------------------------------------------
    # 9-rtl                               --         26 min  6 sec 
    # 14-glb_top                          --    1 hr 18 min 35 sec  <-- in progress
    # 17-tile_array                       --   13 hr 24 min 37 sec 
    # --------------------------------------------------------------------------------
    # 
    # Will try to find runtimes even if/when Makefile is absent/corrupted
    echo ''
    if grep ^runtimes Makefile >& /dev/null; then
        get_runtimes="make runtimes"
    else
        get_runtimes="/sim/buildkite-agent/mflowgen.master/mflowgen/scripts/mflowgen-runtimes"
    fi
    $get_runtimes |& egrep -v '^(Total|echo|runtimes)' \
        | grep -vi warning | sed '1d; s/Runtimes/+++ RUNTIMES/'
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
    logfiles=$(find * -name make-\*.log)
    found_retry=false
    grep -H QCHECK /dev/null $logfiles \
        | sed 's/:/: /' \
        | grep ': QCHECK' \
        && found_retry=true

    [ $found_retry == false ] && echo 'No qcheck info found.'
    echo ''
fi

########################################################################
# Error check
if [ "$do_err" ]; then
    echo ''; echo '+++ ERROR CHECK'

    if [ "$show_all_errs" == "true" ]; then 
        echo "ALL ERRORS:"; filter=cat
    else 
        echo "ERROR SUMMARY:"; filter=head
    fi

    errfiles=`find * -name \*.log \
     -exec bash -c \
       "cat {} | grep -v 'Error Limit' | egrep '(^Error|^\*\*ERROR)' > /dev/null" \
     \; \
     -print`
    # echo $errfiles

    function chop { cut -b 1-$1; }
    for f in $errfiles; do (

        # Want only the lowest-level log file
        # e.g. "17-tile_array/17-Tile_PE/24-cadence-genus-genlib/logs/genus.log"
        #  or  "12-gen_sram_macro/lib2db/build/build.log"
        # but not "make-GLC.log" or "17-tile_array/mflowgen-run.log"
        echo $f | egrep 'mflowgen|make' > /dev/null && continue

        # Hack for metal shorts ugh
        shorts=`grep "Metal shorts exist" $f | grep -v echo`
        if [ "$shorts" ]; then
            echo $f
            echo $shorts | egrep '(^Error|^\*\*ERROR)' \
                | grep -v 'Error Limit' \
                | chop 80 | sort | uniq -c | sort -rn | head
            echo ""
        fi

        cat $f | egrep '(^Error|^\*\*ERROR)' \
            | grep -v 'Error Limit' \
            | chop 80 | sort | uniq -c | sort -rn | head
        echo ""
    ) done | $filter

    # find * -name \*.log -exec egrep '(^Error|^\*\*ERROR)' {} \; \
    #   | grep -v 'Error Limit' \
    #   | chop 80 | sort | uniq -c | sort -rn | head

    cat <<EOF

SEE ALL ERRORS (cut-n-paste):

    logs=\`find $bd -name \*.log\`
    pat='(^Error ^(or Limit)|^\*\*ERROR)'
    for L in \$logs; do
      egrep -l "\$pat" \$L && egrep "\$pat" \$L && echo ''; done | less -S

EOF
fi
