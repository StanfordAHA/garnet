#!/bin/bash
if [[ $# < 3 ]]
then
    echo "Usage: lvs <gds> <verilog> <top cell> "
    exit 1
fi


gdsorig="$1"
gds=$(readlink -e "$gdsorig")

verilog_orig="$2"
verilog=$(readlink -e "$verilog_orig")

toplevel="$3"

function has_arg () {
    s="$1"
    shift
    for i in "$@"; do
        [ $i == $s ] && return 0
    done
    return 1
}

dir="$(readlink -e "${BASH_SOURCE[0]}")"
rundir="$(dirname "$d")"/$toplevel

mkdir -p $rundir
cd $rundir

lvs_file="/home/kongty/runsets/calibre.lvs"

echo "running v2lvs"
v2lvs \
    -s /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90_100a.spi \
    -s /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90pm_100a/tcbn16ffcllbwp16p90pm_100a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/SPICE/ts1n16ffcllsblvtc512x16m8s_130a.spi \
    -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90_100a.spi \
    -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90pm_100a/tcbn16ffcllbwp16p90pm_100a.spi \
    -lsr /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/SPICE/ts1n16ffcllsblvtc512x16m8s_130a.spi \
    -v ${verilog} -o ${toplevel}.sp

cat <<EOF > _calibre.lvs
LAYOUT PATH "$gds"
LAYOUT PRIMARY "$toplevel"

SOURCE PATH "${toplevel}.sp"
SOURCE PRIMARY "$toplevel"

LVS REPORT "${toplevel}.lvs.report"

INCLUDE "${lvs_file}"
EOF

    echo "running lvs check"
    calibre -turbo -hyper -lvs -hier -nowait _calibre.lvs
cd ..
