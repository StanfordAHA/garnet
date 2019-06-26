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
declare lvs
lvs = 1
shift; shift; shift
has_arg -nolvs "$@" || lvs = 0

dir="$(readlink -e "${BASH_SOURCE[0]}")"
rundir="$(dirname "$d")"/$toplevel

mkdir -p $rundir
cd $rundir

lvs_file="/home/kongty/runsets/calibre.lvs.kongty"

echo "running v2lvs"
if  [ $toplevel == "Tile_PE" ] || [ $toplevel == "Tile_MemCore" ]
then
v2lvs \
    -s /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90_100a.spi \
    -s /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90pm_100a/tcbn16ffcllbwp16p90pm_100a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/SPICE/ts1n16ffcllsblvtc512x16m8s_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8sw_130a/SPICE/ts1n16ffcllsblvtc512x16m8sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m4sw_130a/SPICE/ts1n16ffcllsblvtc512x16m4sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc256x32m4sw_130a/SPICE/ts1n16ffcllsblvtc256x32m4sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc256x32m8sw_130a/SPICE/ts1n16ffcllsblvtc256x32m8sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc2048x32m8sw_130a/SPICE/ts1n16ffcllsblvtc2048x32m8sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/SPICE/ts1n16ffcllsblvtc2048x64m8sw_130a.spi \
    -s /tsmc16/TSMCHOME/digital/Back_End/spice/tphn16ffcllgv18e_090a/tphn16ffcllgv18e.spi \
    -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90_100a.spi \
    -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90pm_100a/tcbn16ffcllbwp16p90pm_100a.spi \
    -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tphn16ffcllgv18e_090a/tphn16ffcllgv18e.spi \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/VERILOG/ts1n16ffcllsblvtc512x16m8s_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8sw_130a/VERILOG/ts1n16ffcllsblvtc512x16m8sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m4sw_130a/VERILOG/ts1n16ffcllsblvtc512x16m4sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc256x32m4sw_130a/VERILOG/ts1n16ffcllsblvtc256x32m4sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc256x32m8sw_130a/VERILOG/ts1n16ffcllsblvtc256x32m8sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc2048x32m8sw_130a/VERILOG/ts1n16ffcllsblvtc2048x32m8sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/VERILOG/ts1n16ffcllsblvtc2048x64m8sw_130a_pwr.v \
    -v ${verilog} -o ${toplevel}.sp
else
v2lvs \
    -s /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90_100a.spi \
    -s /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90pm_100a/tcbn16ffcllbwp16p90pm_100a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/SPICE/ts1n16ffcllsblvtc512x16m8s_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8sw_130a/SPICE/ts1n16ffcllsblvtc512x16m8sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m4sw_130a/SPICE/ts1n16ffcllsblvtc512x16m4sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc256x32m4sw_130a/SPICE/ts1n16ffcllsblvtc256x32m4sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc256x32m8sw_130a/SPICE/ts1n16ffcllsblvtc256x32m8sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc2048x32m8sw_130a/SPICE/ts1n16ffcllsblvtc2048x32m8sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/SPICE/ts1n16ffcllsblvtc2048x64m8sw_130a.spi \
    -s /tsmc16/TSMCHOME/digital/Back_End/spice/tphn16ffcllgv18e_090a/tphn16ffcllgv18e.spi \
    -s /sim/kongty/garnet/tapeout_16_final/lvs/Tile_PE/Tile_PE.sp \
    -s /sim/kongty/garnet/tapeout_16_final/lvs/Tile_MemCore/Tile_MemCore.sp \
    -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90_100a.spi \
    -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90pm_100a/tcbn16ffcllbwp16p90pm_100a.spi \
    -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tphn16ffcllgv18e_090a/tphn16ffcllgv18e.spi \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/VERILOG/ts1n16ffcllsblvtc512x16m8s_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8sw_130a/VERILOG/ts1n16ffcllsblvtc512x16m8sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m4sw_130a/VERILOG/ts1n16ffcllsblvtc512x16m4sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc256x32m4sw_130a/VERILOG/ts1n16ffcllsblvtc256x32m4sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc256x32m8sw_130a/VERILOG/ts1n16ffcllsblvtc256x32m8sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc2048x32m8sw_130a/VERILOG/ts1n16ffcllsblvtc2048x32m8sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/VERILOG/ts1n16ffcllsblvtc2048x64m8sw_130a_pwr.v \
    -l /sim/kongty/garnet/tapeout_16_final/synth/Tile_PE/pnr.lvs.append.v \
    -l /sim/kongty/garnet/tapeout_16_final/synth/Tile_MemCore/pnr.lvs.append.v \
    -v ${verilog} -o ${toplevel}.sp
fi

cat <<EOF > _calibre.lvs
LAYOUT PATH "$gds"
LAYOUT PRIMARY "$toplevel"

SOURCE PATH "${toplevel}.sp"
SOURCE PRIMARY "$toplevel"

LVS REPORT "${toplevel}.lvs.report"

LVS FILTER UNUSED OPTION AI SOURCE
LVS FILTER UNUSED OPTION AI LAYOUT
INCLUDE "${lvs_file}"
EOF

echo "running lvs check"
calibre -turbo -hyper -lvs -hier -nowait _calibre.lvs
cd ..


cat <<EOF
results summary in ${rundir}/${toplevel}.lvs.report
View results  : calibre -rve -lvs ${rundir}/svdb
EOF
