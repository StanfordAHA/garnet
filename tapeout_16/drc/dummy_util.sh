#!/bin/bash

if [[ $# < 2 ]]
then
    echo "Usage: ./dummy_util.sh <gds> <top cell> [-full]"
    exit 1
fi

gds=$(readlink -e "$1")
toplevel="$2"

function has_arg () {
    s="$1"
    shift
    for i in "$@"; do
        [ $i == $s ] && return 0
    done
    return 1
}

shift; shift
if has_arg -full "$@"
then
    suffix=""
else
    suffix=".ip"
fi

d="/home/ajcars/new_runsets/dummies"

mkdir -p ${toplevel}_dummy_util
cd ${toplevel}_dummy_util

cat <<EOF > dummy_feol.drc
LAYOUT PATH "$gds"
LAYOUT PRIMARY "$toplevel"
DRC RESULTS DATABASE "feol_dummy.gds"
DRC SUMMARY REPORT "feol_dummy_summary.txt"
INCLUDE "$d/Dummy_FEOL_CalibreYE_16nmFFP.14c${suffix}"
EOF
echo "running Calibre feol dummy utility"
calibre -drc -hier -turbo 2 -64 dummy_feol.drc | tee feol_dummy_util.log | grep -P '^ERROR|^DRC RuleCheck'

cat <<EOF > dummy_beol.drc
LAYOUT PATH "$gds"
LAYOUT PRIMARY "$toplevel"
DRC RESULTS DATABASE "beol_dummy.gds"
DRC SUMMARY REPORT "beol_dummy_summary.txt"
INCLUDE "$d/Dummy_BEOL_CalibreYE_16nmFFP.14c${suffix}"
EOF
echo "running Calibre beol dummy utility"
calibre -drc -hier -turbo 2 -64 dummy_beol.drc | tee beol_dummy_util.log | grep -P '^ERROR|^DRC RuleCheck'

echo "Merging dummy metal gds with original gds"
mgds=${toplevel}_$(basename $1 .gds)_with_dummy.gds
calibredrv -a layout filemerge -append -in "$gds" -in FEOL.gds -in BEOL.gds -out "../$mgds" -map_cell "F14c${toplevel}" "$toplevel" -map_cell "B14c${toplevel}" "$toplevel"
cd ..
echo -e "\nFinal gds is $mgds"
