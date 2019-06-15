#!/bin/bash
if [[ $# < 2 ]]
then
    echo "Usage: lvs <verilog> <top cell> "
    exit 1
fi

verilog_orig="$1"
verilog=$(readlink -e "$verilog_orig")
toplevel="$2"

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

lvs_file_dir="/home/kongty/runsets"

mkdir -p $rundir
cd $rundir

declare lvs_file
lvs_file_dir="/home/kongty/runsets"
lvs_file="${lvs_file_dir}/calibre.lvs"

echo "running v2lvs"
v2lvs \
    -s /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90_100a.spi \
    -s /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90pm_100a/tcbn16ffcllbwp16p90pm_100a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/SPICE/ts1n16ffcllsblvtc512x16m8s_130a.spi \
    -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90_100a.spi \
    -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90pm_100a/tcbn16ffcllbwp16p90pm_100a.spi \
    -lsr /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/SPICE/ts1n16ffcllsblvtc512x16m8s_130a.spi \
    -v ${verilog} -o ${toplevel}.sp

calibre -spice /*.sp -turbo -hyper -lvs -hier -nowait /fdfdfcalibre.lvs
cd ..
