#!/bin/bash

if [ $# != 2 ]
then
    echo "Usage: ./dummy_util.sh <gds> <top cell>"
    exit 1
fi

gds=$(readlink -e "$1")
toplevel="$2"

d="/home/ajcars/new_runsets/dummies"

mkdir -p dummy_util
cd dummy_util

cat <<EOF > dummy_util.drc
LAYOUT PATH "$gds"
LAYOUT PRIMARY "$toplevel"
DRC RESULTS DATABASE "${toplevel}_dummy_util.gds" GDSII _dummy_only
DRC SUMMARY REPORT "${toplevel}_dummy_util_summary.txt"


INCLUDE "$d/Dummy_FEOL_CalibreYE_16nmFFP.14c.ip"
INCLUDE "$d/Dummy_BEOL_CalibreYE_16nmFFP.14c.ip"
EOF

echo "running Calibre dummy utility"
calibre -drc -hier -turbo -hyper -64 dummy_util.drc | tee ${toplevel}_dummy_util.log | grep -P '^ERROR|^DRC RuleCheck'

echo "Merging dummy metal gds with original gds"
mgds=${toplevel}_$(basename $1 .gds)_with_dummy.gds
calibredrv -a layout filemerge -in "$gds" -in ${toplevel}_dummy_util.gds -out "../$mgds" -map_cell "${toplevel}_dummy_only" "$toplevel" -topcell "$toplevel"
cd ..
echo -e "\nFinal gds is $mgds"
