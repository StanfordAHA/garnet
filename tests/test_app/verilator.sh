#!/bin/bash

warn='
  -Wno-fatal
  -Wno-PINMISSING
  -Wno-PROTECTED
  -Wno-TIMESCALEMOD
  -Wno-IMPLICITSTATIC
  -Wno-WIDTHEXPAND
  -Wno-WIDTHTRUNC
  -Wno-CMPCONST
  -Wno-CASEINCOMPLETE
  -Wno-UNOPTFLAT
'

# gb_param.svh is used by top.sv so must go first(?)
VFILES=`echo vfiles/*.{v,sv,svh}`
VFILES=`echo $VFILES | tr ' ' '\n' | grep -v global_buffer_param.svh`

CW1=/cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/
CW2=/cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CWTECH/

# TODO should probably delete/move existing obj_files/ dir if exists

echo ''
echo VFILES= $VFILES | tr ' ' '\n'
echo ''

# Takes about a minute as of 10/2024
set -x
verilator $warn --timing --cc --exe vfiles/CGRA.cpp \
  --top-module top \
  vfiles/global_buffer_param.svh \
  $VFILES \
  -F tb/tb_cgra.f \
  -y $CW1 -y $CW2 \
  vfiles/libcgra.so
