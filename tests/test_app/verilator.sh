#!/bin/bash

if test -e obj_dir; then
    echo "Oops looks like obj_dir already exists"
    read -p "Continue [yn]? " REPLY
    [[ $REPLY =~ ^[Yy] ]] && echo yes || exit 13
    read -p "Are you sure [yn]? " REPLY
    [[ $REPLY =~ ^[Yy] ]] && echo yes || exit 13
fi

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
# Took 4min today (also 10/2024) 
echo "This took four minutes last time I ran it..."
set -x

# Note: libcgra.so must be relative to ./obj_dir :(
# TODO: find a better way to do this :(
verilator $warn --timing --cc --exe vfiles/CGRA.cpp \
  --top-module top \
  vfiles/global_buffer_param.svh \
  $VFILES \
  -F tb/tb_cgra.f \
  -y $CW1 -y $CW2 \
  ../vfiles/libcgra.so

o=obj_dir
f=Vtop__Syms.cpp
tail $o/$f
set +x

exit


ls -l obj_dir/Vtop.mk
# i=3
ls -l make-vtop.log*; printf "NEXT:%62s\n" "make-vtop.log$i (i=$i)"
msg_bad="oops no log file exists already\n\n"
test -f make-vtop.log$i && printf "\nERROR $msg_bad" || printf "\nOKAY\n\n"
make -C obj_dir/ -f Vtop.mk |& tee make-vtop.log$i; ((i++))

exit

# NEXT: lookup g++ error msg: error: lvalue required as unary ‘&’ operand
# g++ error lvalue required as unary ‘&’ operand
# 
# # Vtop___024unit__03a__03aKernel__Vclpkg__DepSet_h31ff4afb__0.cpp:38:54:
# # error: lvalue required as unary ‘&’ operand
# #    38 |  &((IData)(
# #       |   ~^~~~~~~~
# #    39 |            (unnamedblk9__DOT__entry
# #       |            ~~~~~~~~~~~~~~~~~~~~~~~~
# #    40 |             >> 0x20U))),
# #       |             ~~~~~~~~~~~
# # 
# # Vtop___024unit__03a__03aKernel__Vclpkg__DepSet_h31ff4afb__0.cpp:42:54:
# # error: lvalue required as unary ‘&’ operand
# #    42 |  &((IData)(unnamedblk9__DOT__entry))) ;
# #       |   ~^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 
# o=obj_dir
# less -N $o/Vtop___024unit__03a__03aKernel__Vclpkg__DepSet_h31ff4afb__0.cpp
#
# FIXED!
