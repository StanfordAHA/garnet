#!/bin/bash

if [[ $# < 2 ]]
then
    echo "Usage: drc <gds> <top cell> [-noip] [-nofullchip] [-noantenna]"
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
has_arg -noip "$@" || checks+=(ip)
has_arg -nofullchip "$@" || checks+=(fullchip)
has_arg -noantenna "$@" || checks+=(antenna)
#has_arg -nobackup "$@" || checks+=(backup)

d="$(readlink -e "${BASH_SOURCE[0]}")"
d="$(dirname "$d")"/../drc

rundir=$toplevel

mkdir -p $rundir
cd $rundir

declare -A files
drc_file_dir="/home/kongty/runsets"
files[ip]="${drc_file_dir}/calibre_ip.drc.noDensity"
files[fullchip]="${drc_file_dir}/calibre_fullchip.drc.noDensity"
#files[fullchip]="${drc_file_dir}/calibre_pad_no_sealring.drc.noDensity"
files[antenna]="${drc_file_dir}/calibre_antenna.drc"
#files[backup]="${drc_file_dir}/BACKUP_DRC/CLN16FFC_9M_2Xa1Xd2Xe2Y1Z_032.15a.encrypt"

rm -f drc.log

for check in "${checks[@]}"; do
    cat <<EOF > calibre.drc
LAYOUT PATH "$gds"
LAYOUT PRIMARY "$toplevel"
DRC RESULTS DATABASE "../${check}_results_${toplevel}.txt"
DRC SUMMARY REPORT "../${check}_summary_${toplevel}.txt"

INCLUDE "${files[$check]}"
EOF

    echo "running $check check"
    calibre -drc -hier -turbo -hyper -64 calibre.drc | tee -a drc.log | grep -P '^ERROR|^DRC RuleCheck' | sed -e 's/Number of Results = [1-9].*/\x1b[31m&\x1b[39m/I'
done

cd ..

grep "Result Count = [1-9]" ${checks[@]/%/_summary_${toplevel}.txt} > failing_summary_${toplevel}.txt
chmod -x ${checks[@]/%/_results_${toplevel}.txt}

echo -e "\nCalibre log in $rundir/drc.log"


for check in "${checks[@]}"; do
    cat <<EOF

$check results summary in ${check}_summary_${toplevel}.txt
View results  : calibre -rve -drc ${check}_results_${toplevel}.txt
View with gds : calibredrv $gdsorig -rve -drc ${check}_results_${toplevel}.txt
Import to icc : read_drc_error_file $(readlink -e ${check}_results_${toplevel}.txt)
EOF
done

echo -e "\nFailing checks : failing_summary_${toplevel}.txt"
