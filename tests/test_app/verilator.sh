#!/bin/bash

if test -e obj_dir; then
    echo "Oops looks like obj_dir already exists"
    read -p "Continue [yn]? " REPLY
    [[ $REPLY =~ ^[Yy] ]] && echo yes || exit 13
    read -p "Are you sure [yn]? " REPLY
    [[ $REPLY =~ ^[Yy] ]] && echo yes || exit 13
fi

TRACE=""
[ "$1" == "--trace" ] && TRACE='--trace'

# Should not be TIMESCALEMOD warnings if '--timescale' properly specified!!!
#  -Wno-TIMESCALEMOD
warn='
  -Wno-fatal
  -Wno-PINMISSING
  -Wno-PROTECTED
  -Wno-IMPLICITSTATIC
  -Wno-CMPCONST
  -Wno-CASEINCOMPLETE
'
warn='
  -Wno-fatal
  -Wno-WIDTHEXPAND
  -Wno-WIDTHTRUNC
  -Wno-UNOPTFLAT
'

# gb_param.svh is used by top.sv so must go first(?)
VFILES=`echo vfiles/*.{v,sv,svh}`
VFILES=`echo $VFILES | tr ' ' '\n' | grep -v global_buffer_param.svh`
VFILES=`echo $VFILES | tr ' ' '\n' | grep -v garnet_stub.v`

CW1=/cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/
CW2=/cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CWTECH/

# TODO should probably delete/move existing obj_files/ dir if exists

echo ''
echo VFILES= $VFILES | tr ' ' '\n'
echo ''

# Takes about a minute without --trace
# Clsoer to 4 min if --trace is active
set -x

# Note: libcgra.so must be relative to ./obj_dir :(
# TODO: find a better way to do this :(

# //  --trace \

d=`pwd`
verilator $warn --timing --cc --exe vfiles/CGRA.cpp \
  --timescale 1ps/1ps \
  --top-module top \
  $TRACE \
  $d/vfiles/global_buffer_param.svh \
  $VFILES \
  -F tb/tb_cgra.f \
  -y $CW1 -y $CW2 \
  $d/vfiles/libcgra.so

# o=obj_dir; f=Vtop__Syms.cpp; tail $o/$f
set +x

exit


ls -l obj_dir/Vtop.mk
# i=3
ls -l make-vtop.log*; printf "NEXT:%62s\n" "make-vtop.log$i (i=$i)"
msg_bad="oops no log file exists already\n\n"
test -f make-vtop.log$i && printf "\nERROR $msg_bad" || printf "\nOKAY\n\n"
make -C obj_dir/ -f Vtop.mk |& tee make-vtop.log$i; ((i++))

exit

i=3
rmo
verilator.sh |& tee vlog$i | less
make -C obj_dir/ -f Vtop.mk |& tee make-vtop.log$i | cat -n | chop | less
Vtop "$APP" |& tee vtop.log$i







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
