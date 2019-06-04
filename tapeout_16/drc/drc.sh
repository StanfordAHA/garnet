#!/bin/bash

if [[ $# < 2 ]]
then
    echo "Usage: drc <gds> <top cell> [-nodrc] [-noantenna] [-nobackup]"
    exit 1
fi

gdsorig="$1"
gds=$(readlink -e "$gdsorig")
toplevel="$2"

function has_arg () {
    s="$1"
    shift
    for i in "$@"; do
        [ $i == $s ] && return 0
    done
    return 1
}

checks=()
# remove first two arguments
shift; shift
has_arg -nodrc "$@" || checks+=(drc)
has_arg -noantenna "$@" || checks+=(antenna)
has_arg -nobackup "$@" || checks+=(backup)

d="$(readlink -e "${BASH_SOURCE[0]}")"
d="$(dirname "$d")"/../drc

rundir=drc

mkdir -p $rundir
cd $rundir

declare -A files
drc_file_dir="/sim/ajcars/aha-arm-soc-june-2019/drc"
files[drc]="${drc_file_dir}/LOGIC_TopMr_DRC/CLN16FFC_9M_2Xa1Xd3Xe2R_032.15a.encrypt"
files[antenna]="${drc_file_dir}/ANTENNA_DRC/CLN16FFC_9M_032_ANT.15a"
files[backup]="${drc_file_dir}/BACKUP_DRC/CLN16FFC_9M_2Xa1Xd2Xe2Y1Z_032.15a.encrypt"

rm -f drc.log

for check in "${checks[@]}"; do
    cat <<EOF > calibre.drc
LAYOUT PATH "$gds"
LAYOUT PRIMARY "$toplevel"
DRC RESULTS DATABASE "../${check}_results.txt"
DRC SUMMARY REPORT "../${check}_summary.txt"

INCLUDE "${files[$check]}"
EOF

    echo "running $check check"
    calibre -drc -hier -turbo -hyper -64 calibre.drc | tee -a drc.log | grep -P '^ERROR|^DRC RuleCheck' | sed -e 's/Number of Results = [1-9].*/\x1b[31m&\x1b[39m/I'
done

cd ..

grep "Result Count = [1-9]" ${checks[@]/%/_summary.txt} > failing_summary.txt
chmod -x ${checks[@]/%/_results.txt}

echo -e "\nCalibre log in $rundir/drc.log"


for check in "${checks[@]}"; do
    cat <<EOF

$check results summary in ${check}_summary.txt
View results  : calibre -rve -drc ${check}_results.txt
View with gds : calibredrv $gdsorig -rve -drc ${check}_results.txt
Import to icc : read_drc_error_file $(readlink -e ${check}_results.txt)
EOF
done

echo -e "\nFailing checks : failing_summary.txt"
