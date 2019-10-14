#!/bin/bash

# 10/2019 SR added (for top)
#     -s   /sim/steveri/garnet/tapeout_16/lvs/local_repo/butterphy_top.spi \
#     -s ../pe/Tile_PE/Tile_PE.sp \
#     -s ../mem/Tile_MemCore/Tile_MemCore.sp \
#     -s   /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90lvt_100a/tcbn16ffcllbwp16p90lvt_100a.spi \
#     -s   /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90ulvt_100a/tcbn16ffcllbwp16p90ulvt_100a.spi \
#     -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90lvt_100a/tcbn16ffcllbwp16p90lvt_100a.spi \
#     -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90ulvt_100a/tcbn16ffcllbwp16p90ulvt_100a.spi \
#     -l /sim/steveri/garnet/tapeout_16/synth/Tile_PE/pnr.lvs.v \
#     -l /sim/steveri/garnet/tapeout_16/synth/Tile_MemCore/pnr.lvs.v \
#     -l /sim/ajcars/aha-arm-soc-june-2019/components/butterphy/butterphy_top.mapped.v \
# 
if [[ $# < 3 ]]
then
    echo "Usage: lvs <gds> <verilog> <top cell> "
    exit 1
fi
set -x

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

# lvs_file="/home/kongty/runsets/calibre.lvs.kongty"
lvs_file="/home/steveri/runsets/calibre.lvs.kongty"

echo "running v2lvs"
# -s <filename>    : .INCLUDE "filename" is added to the generated spice file (-o).                                       
# -l <filename>    : Verilog library file, parsed for interface pin configurations(see -s). 
# -lsp <filename>  : Spice library file name, pin mode. The Spice file is parsed for        
#
if  [ $toplevel == "Tile_PE" ] || [ $toplevel == "Tile_MemCore" ]
then
v2lvs \
    -s /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90_100a.spi \
    -s /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90pm_100a/tcbn16ffcllbwp16p90pm_100a.spi \
    \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/SPICE/ts1n16ffcllsblvtc512x16m8s_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8sw_130a/SPICE/ts1n16ffcllsblvtc512x16m8sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m4sw_130a/SPICE/ts1n16ffcllsblvtc512x16m4sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc256x32m4sw_130a/SPICE/ts1n16ffcllsblvtc256x32m4sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc256x32m8sw_130a/SPICE/ts1n16ffcllsblvtc256x32m8sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc2048x32m8sw_130a/SPICE/ts1n16ffcllsblvtc2048x32m8sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/SPICE/ts1n16ffcllsblvtc2048x64m8sw_130a.spi \
    \
    -s /tsmc16/TSMCHOME/digital/Back_End/spice/tphn16ffcllgv18e_090a/tphn16ffcllgv18e.spi \
    \
    -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90_100a.spi \
    -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90pm_100a/tcbn16ffcllbwp16p90pm_100a.spi \
    -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tphn16ffcllgv18e_090a/tphn16ffcllgv18e.spi \
    \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/VERILOG/ts1n16ffcllsblvtc512x16m8s_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8sw_130a/VERILOG/ts1n16ffcllsblvtc512x16m8sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m4sw_130a/VERILOG/ts1n16ffcllsblvtc512x16m4sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc256x32m4sw_130a/VERILOG/ts1n16ffcllsblvtc256x32m4sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc256x32m8sw_130a/VERILOG/ts1n16ffcllsblvtc256x32m8sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc2048x32m8sw_130a/VERILOG/ts1n16ffcllsblvtc2048x32m8sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/VERILOG/ts1n16ffcllsblvtc2048x64m8sw_130a_pwr.v \
    -v ${verilog} -o ${toplevel}.sp
else
pwd; ls -l ../pe/Tile_PE/Tile_PE.sp ../mem/Tile_MemCore/Tile_MemCore.sp
v2lvs \
    -s   /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90_100a.spi \
    -s   /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90pm_100a/tcbn16ffcllbwp16p90pm_100a.spi \
    \
    -s   /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90lvt_100a/tcbn16ffcllbwp16p90lvt_100a.spi \
    -s   /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90ulvt_100a/tcbn16ffcllbwp16p90ulvt_100a.spi \
    -s   /tsmc16/TSMCHOME/digital/Back_End/spice/tphn16ffcllgv18e_090a/tphn16ffcllgv18e.spi \
    -s   /sim/steveri/garnet/tapeout_16/lvs/local_repo/butterphy_top.spi \
    \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/SPICE/ts1n16ffcllsblvtc512x16m8s_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8sw_130a/SPICE/ts1n16ffcllsblvtc512x16m8sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m4sw_130a/SPICE/ts1n16ffcllsblvtc512x16m4sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc256x32m4sw_130a/SPICE/ts1n16ffcllsblvtc256x32m4sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc256x32m8sw_130a/SPICE/ts1n16ffcllsblvtc256x32m8sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc2048x32m8sw_130a/SPICE/ts1n16ffcllsblvtc2048x32m8sw_130a.spi \
    -s /sim/ajcars/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/SPICE/ts1n16ffcllsblvtc2048x64m8sw_130a.spi \
    \
    -s ../pe/Tile_PE/Tile_PE.sp \
    -s ../mem/Tile_MemCore/Tile_MemCore.sp \
    \
    -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90_100a.spi \
    -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90pm_100a/tcbn16ffcllbwp16p90pm_100a.spi \
    -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90lvt_100a/tcbn16ffcllbwp16p90lvt_100a.spi \
    -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90ulvt_100a/tcbn16ffcllbwp16p90ulvt_100a.spi \
    -lsp /tsmc16/TSMCHOME/digital/Back_End/spice/tphn16ffcllgv18e_090a/tphn16ffcllgv18e.spi \
    \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/VERILOG/ts1n16ffcllsblvtc512x16m8s_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8sw_130a/VERILOG/ts1n16ffcllsblvtc512x16m8sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m4sw_130a/VERILOG/ts1n16ffcllsblvtc512x16m4sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc256x32m4sw_130a/VERILOG/ts1n16ffcllsblvtc256x32m4sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc256x32m8sw_130a/VERILOG/ts1n16ffcllsblvtc256x32m8sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc2048x32m8sw_130a/VERILOG/ts1n16ffcllsblvtc2048x32m8sw_130a_pwr.v \
    -l /sim/ajcars/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/VERILOG/ts1n16ffcllsblvtc2048x64m8sw_130a_pwr.v \
    \
    -l /sim/steveri/garnet/tapeout_16/synth/Tile_PE/pnr.lvs.v \
    -l /sim/steveri/garnet/tapeout_16/synth/Tile_MemCore/pnr.lvs.v \
    -l /sim/ajcars/aha-arm-soc-june-2019/components/butterphy/butterphy_top.mapped.v \
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

# NOTES - debugging 10/2019
#     -s /sim/kongty/garnet/tapeout_16_final/lvs/Tile_PE/Tile_PE.sp \
#     -s /sim/kongty/garnet/tapeout_16_final/lvs/Tile_MemCore/Tile_MemCore.sp \
#     -l /sim/kongty/garnet/tapeout_16_final/synth/Tile_PE/pnr.lvs.append.v \
#     -l /sim/kongty/garnet/tapeout_16_final/synth/Tile_MemCore/pnr.lvs.append.v \

# list from init_design_multi*.tcl:
#   /tsmc16/download/TECH16FFC/N16FF_PRTF_Cad_1.2a/PR_tech/Cadence/LefHeader/Standard/VHV/N16_Encounter_9M_2Xa1Xd3Xe2Z_UTRDL_9T_PODE_1.2a.tlef \
#   ../Tile_PE/pnr.lef \
#   ../Tile_MemCore/pnr.lef \
#   /tsmc16/TSMCHOME/digital/Back_End/lef/tcbn16ffcllbwp16p90_100a/lef/tcbn16ffcllbwp16p90.lef \
#   /tsmc16/TSMCHOME/digital/Back_End/lef/tcbn16ffcllbwp16p90lvt_100a/lef/tcbn16ffcllbwp16p90lvt.lef \
#   /tsmc16/TSMCHOME/digital/Back_End/lef/tcbn16ffcllbwp16p90ulvt_100a/lef/tcbn16ffcllbwp16p90ulvt.lef \
#   /tsmc16/TSMCHOME/digital/Back_End/lef/tpbn16v_090a/fc/fc_lf_bu/APRDL/lef/tpbn16v.lef \
#   /tsmc16/TSMCHOME/digital/Back_End/lef/tphn16ffcllgv18e_110e/mt/9m/9M_2XA1XD_H_3XE_VHV_2Z/lef/tphn16ffcllgv18e_9lm.lef \
#   /tsmc16/pdk/2016.09.15_MOSIS/FFC/T-N16-CL-DR-032/N16_DTCD_library_kit_20160111/N16_DTCD_library_kit_20160111/lef/topMxyMxe_M9/N16_DTCD_v1d0a.lef \
#   /tsmc16/pdk/2016.09.15_MOSIS/FFC/T-N16-CL-DR-032/N16_ICOVL_library_kit_FF+_20150528/N16_ICOVL_library_kit_FF+_20150528/lef/topMxMxaMxc_M9/N16_ICOVL_v1d0a.lef \
#   /sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/LEF/ts1n16ffcllsblvtc512x16m8s_130a_m4xdh.lef \
#   /sim/ajcars/mc/ts1n16ffcllsblvtc256x32m4sw_130a/LEF/ts1n16ffcllsblvtc256x32m4sw_130a_m4xdh.lef \
#   /sim/ajcars/mc/ts1n16ffcllsblvtc256x32m8sw_130a/LEF/ts1n16ffcllsblvtc256x32m8sw_130a_m4xdh.lef \
#   /sim/ajcars/mc/ts1n16ffcllsblvtc2048x32m8sw_130a/LEF/ts1n16ffcllsblvtc2048x32m8sw_130a_m4xdh.lef \
#   /sim/ajcars/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/LEF/ts1n16ffcllsblvtc2048x64m8sw_130a_m4xdh.lef \
#   /home/ajcars/N16_SR_B_1KX1K_DPO_DOD_FFC_5x5.lef \
#   /sim/ajcars/aha-arm-soc-june-2019/components/butterphy/butterphy_top.lef \

# srtop:
#         echo "Running top v2lvs"
#         ./lvs.sh ../synth/gpf8_handbuilt_gds/final_final.gds
#                  ../synth/gpf8_handbuilt_gds/pnr.final.lvs.v
#                  GarnetSOC_pad_frame

##############################################################################
# Warning: No module declaration for module CKBD10BWP16P90ULVT first encountered in module GlobalBuffer
# Warning: No module declaration for module CKBD18BWP16P90ULVT first encountered in module GlobalBuffer
# 
# innovus.log3:WARNING: A structure name CKBD10BWP16P90ULVT already exists in one of the merging GDSII files.
# innovus.log3:Rename it in file /sim/ajcars/aha-arm-soc-june-2019/components/butterphy/butterphy_top.gds to CKBD10BWP16P90ULVT_butterphy_top_gds.
# 
# grep CKBD10BWP16P90ULVT /tsmc16/TSMCHOME/digital/Back_End/spice/*/*
# 
# /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90ulvt_100a/tcbn16ffcllbwp16p90ulvt_100a.spi:
# .subckt CKBD10BWP16P90ULVT I Z VDD VSS VPP VBB
# 
# /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90ulvt_100a/tcbn16ffcllbwp16p90ulvt_100a.spi:
# .subckt DCCKBD10BWP16P90ULVT I Z VDD VSS VPP VBB

# Warning: No module declaration for module BUFFD0BWP16P90LVT first encountered in module GlobalBuffer
# grep BUFFD0BWP16P90LVT /tsmc16/TSMCHOME/digital/Back_End/spice/*/*
# /tsmc16/TSMCHOME/digital/Back_End/spice/tcbn16ffcllbwp16p90lvt_100a/tcbn16ffcllbwp16p90lvt_100a.spi:
# .subckt BUFFD0BWP16P90LVT I Z VDD VSS VPP VBB


##############################################################################
# LVS completed. NOT COMPARED. See report file: GarnetSOC_pad_frame.lvs.report
# ERROR: Source could not be read.
# results summary in 
# less ./GarnetSOC_pad_frame/GarnetSOC_pad_frame.lvs.report
# View results  : calibre -rve -lvs ./GarnetSOC_pad_frame/svdb
# 
# Error: Can't access file "mem/Tile_MemCore/Tile_MemCore.sp" (No such
# file or directory) referred to on line 15 in file
# "GarnetSOC_pad_frame.sp"
# 
# ---
# Error: Can't access file "pe/Tile_PE/Tile_PE.sp" (No such file or
# directory) referred to on line 16 in file "GarnetSOC_pad_frame.sp"
# 
# Error: No matching ".SUBCKT" statement for "Tile_PE" at 
# line 955053 in file "GarnetSOC_pad_frame.sp"
# 
# 955053  XInterconnect_inst0_Tile_X00_Y01 Tile_PE $PINS 
# 
# pe/Tile_PE/Tile_PE.sp:
# .SUBCKT Tile_PE SB_T0_EAST_SB_IN_B16_0[15] SB_T0_EAST_SB_IN_B16_0[14] 
# 
# ---
# Error: No matching ".SUBCKT" statement for "butterphy_top" at line
# 2376648 in file "GarnetSOC_pad_frame.sp"
# 
# Error: No matching ".SUBCKT" statement for "butterphy_top" at line 2376648 in file "GarnetSOC_pad_frame.sp"
# line 2376648 in file "GarnetSOC_pad_frame.sp"
# 
# 2376648 Xiphy butterphy_top $PINS ext_Vcm=ext_Vcm ext_clk_async_p=ext_clk_async_p 
# 
# grep SUBCKT /sim/ajcars/aha-arm-soc-june-2019/components/butterphy/butterphy_top.spi | grep butter
# .SUBCKT butterphy_top ext_rx_inp ext_rx_inn ext_Vcm ext_Vcal ext_rx_inp_test 

##############################################################################
# Error: No matching ".SUBCKT" statement for "rhim_m" at line 4963 in
# file
# "/tsmc16/TSMCHOME/digital/Back_End/spice/tphn16ffcllgv18e_090a/tphn16ffcllgv18e.spi"
# grep -R 'SUBCKT rhim_m' /tsmc16/TSMCHOME/

##############################################################################
# Spice library interface parser failed for file 
# /sim/ajcars/aha-arm-soc-june-2019/components/butterphy/butterphy_top.spi
#     -lsp /sim/ajcars/aha-arm-soc-june-2019/components/butterphy/butterphy_top.spi \
# 
#     -s   /sim/ajcars/aha-arm-soc-june-2019/components/butterphy/butterphy_top.spi \
