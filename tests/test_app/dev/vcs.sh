#!/bin/bash
############################################################################
############################################################################
############################################################################
# 
# TODO Ignore this file for now, it will be cleaned up in the next release.
# 
############################################################################
############################################################################
############################################################################


which vcs
if ! which vcs; then
  source /cad/modules/tcl/init/sh
  module load base/1.0
  module load vcs/Q-2020.03-SP2
fi
which vcs

# vcs -sverilog -timescale=1ps/1ps -full64 -ldflags "-Wl,--no-as-needed" \
# -CFLAGS "-m64" -top top +vcs+lic+wait +vcs+initreg+random +overlap \
# +v2k -l vcs.log +define+CLK_PERIOD=1ns +nospecify \
# /aha/garnet/tests/test_app//../../global_buffer/header/global_buffer_param.svh \
# /aha/garnet/tests/test_app//../../global_buffer/header/glb.svh \
# /aha/garnet/tests/test_app//../../global_controller/header/glc.svh \
# /aha/garnet/tests/test_app//../../garnet.v \
# /aha/garnet/tests/test_app//../../global_buffer/systemRDL/output/glb_pio.sv \
# /aha/garnet/tests/test_app//../../global_buffer/systemRDL/output/glb_jrdl_decode.sv \
# /aha/garnet/tests/test_app//../../global_buffer/systemRDL/output/glb_jrdl_logic.sv \
# /aha/garnet/tests/test_app//../../global_controller/systemRDL/output/glc_pio.sv \
# /aha/garnet/tests/test_app//../../global_controller/systemRDL/output/glc_jrdl_decode.sv \
# /aha/garnet/tests/test_app//../../global_controller/systemRDL/output/glc_jrdl_logic.sv \
#     /aha/garnet/tests/test_app//../../genesis_verif/*.sv \
#     -F tb/tb_cgra.f \
# -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/ \
# -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CWTECH/ \
# +libext+.v+.sv

CW1=/cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/
CW2=/cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CWTECH/

ls -l vcs.log*

# For not tracing?
WAVEFORM_ARGS=""

# For tracing
WAVEFORM_ARGS="-debug_access+all -kdb +vpi +memcbk +vcsd"
WAVEFORM_ARGS="-debug_access+all +vpi +memcbk +vcsd"


/bin/rm -rf deleteme/{simv,csrc,simv.daidir}
mv simv csrc/ simv.daidir/ deleteme

# //  $WAVEFORM_ARGS

#   -debug_access+all -kdb +vpi +memcbk +vcsd \
#   -debug_access+all -kdb +vpi +memcbk\

if test -f hw_output.txt; then
    echo WARNING found existing hw_output.txt
    echo Sending it to savedir and DELETING IT
    test -d savedir || mkdir savedir
    ~steveri/bin/save hw_output.txt
    rm hw_output.txt
fi

test -e vfiles/garnet.v || (cd vfiles; gunzip -c garnet.v.gz > garnet.v)
test -d tb || ln -s ../tb
test -e libcgra.so || ln -s vfiles/libcgra.so

/bin/bash \
vcs -sverilog -timescale=1ps/1ps -full64 -ldflags "-Wl,--no-as-needed" \
  -CFLAGS "-m64" -top top +vcs+lic+wait +vcs+initreg+random +overlap \
  +v2k -l vcs.log \
  $WAVEFORM_ARGS \
  +define+CLK_PERIOD=1ns +nospecify \
  vfiles/global_buffer_param.svh vfiles/glb.svh vfiles/glc.svh \
  vfiles/garnet.v vfiles/*.sv \
  -F tb/tb_cgra.f \
  -y $CW1 -y $CW2 \
  +libext+.v+.sv

# ../simv up to date
# CPU time: 4.037 seconds to compile + .783 seconds to elab + .235 seconds to link

# % ls /aha/garnet/tests/test_app/csrc
# ls: cannot access '/aha/garnet/tests/test_app/csrc': No such file or directory

# if [ -x ../simv ]; then chmod a-x ../simv; fi


exit

#   -sv_lib libcgra \

export WAVEFORM=0
export WAVEFORM_GLB_ONLY=0
export SAIF=0

# # +APP0=/aha/Halide-to-Hardware/apps/hardware_benchmarks/apps/pointwise

# APP=+APP0=/nobackup/steveri/github/garnet/tests/test_app/test_data/pointwise
APP=+APP0=pointwise

export WAVEFORM=1

# +UVM_TIMEOUT=1000

simv -lca -l simv$ivcs.log +vcs+initmem+0 +vcs+initreg+0 -sv_lib libcgra -exitstatus -ucli $APP
# ucli%
  dump -file simv4.vpd
  dump -add top -fid VPD0 -depth 0
  dump -add top -fid VPD0 -depth 6
  run 5000ns

# CHECK THE RESULT!!!
gold=pointwise/bin/hw_output.raw
diff -B <(od -An -x --endian=big $gold | sed 's/^ //') hw_output.txt | head

ls -l simv$ivcs.vpd
vpd2vcd -q simv$ivcs.vpd > simv$ivcs.vcd
gtkwave -F simv$ivcs.vcd vcs-classful.gtkw
0x38.gtkw 

simv -lca -l run.log +vcs+initmem+0 +vcs+initreg+0 -sv_lib libcgra \
  -exitstatus -ucli -i dump_fsdb.tcl  $APP |& tee simv.log$i


#NO
#NO simv -lca -sv_lib vfiles/libcgra $APP -ucli
#NO dump -file simv0.vpd
#NO # dump -add top -fid VPD0 -depth 0
#NO # dump -add top -fid VPD0 -depth 1
#NO dump -add top -fid VPD0 -depth 6
#NO run
#NO 
#NO vpd2vcd -q simv7.vpd > simv7.vcd
#NO ls -lh simv7*

 


 1   2   3     4           5       6
top.dut.GLC.axi_addrmap.glc_pio.pio_decode

./simv -lca -l run.log +vcs+initmem+0 +vcs+initreg+0 \
  +vcs+stop+4000ns \
  -sv_lib vfiles/libcgra \
  +vcs+dumpon+0 \
  +vcs+dumpoff+1000 \
  +vcs+dumpfile+foo.vcd \
  +vcs+flush+dump \
  +vcs+flush+all \
  +vcs+vcdpluson \
  +vcs+dumpvars \
  $APP

+vcs+dumpfile+fozzy
+vcs+flush+dump
+vcs+flush+all

dump -file foo5.vpd
# dump -add top -fid VPD0 -depth 0
dump -add top -fid VPD0 -depth 1
run
ls -lh foo5.vpd



+vcs+vpdfile+fooz

  -exitstatus -ucli -i dump_fsdb.tcl \
  |& tee simv.log1 | less




# simv error FIXED
# "tb/kernel.sv", 547: $unit::\Kernel::assert_ .unnamed$$_0: started at 100ps failed at 100ps
# Offending 'cond'
# Unable to find /aha/Halide-to-Hardware/apps/hardware_benchmarks/apps/pointwise/bin/design_meta.json

# simv error FIXED
# file dump_fsdb.tcl, line 1: can't read "::env(WAVEFORM)": no such variable
# 
# 
# ucli% if { $::env(WAVEFORM) != "0" } {
#   dump -file cgra.fsdb -type FSDB
#   dump -add top -fsdb_opt +mda+packedmda+struct
# } elseif { $::env(WAVEFORM_GLB_ONLY) != "0" } {
#   dump -file global_buffer.fsdb -type FSDB
#   dump -add "top.dut.global_buffer*" -fsdb_opt +mda+packedmda+struct
# }
# ucli% if { $::env(SAIF) == "0" } {
# 
# 
# export WAVEFORM ?= 0
# export WAVEFORM_GLB_ONLY ?= 0
# export SAIF ?= 0
# 
# FALSE:
# # ifeq ($(WAVEFORM), 1)
# # WAVEFORM_ARGS = -debug_access+all -kdb +vpi +memcbk +vcsd
# # endif


# ifeq ($(WHICH_SOC), amber)
# TIMESCALE = -timescale=100ps/1ps
# else
# TIMESCALE = -timescale=1ps/1ps
# endif






#   vfiles/glb_pio.sv \
#   vfiles/glb_jrdl_decode.sv \
#   vfiles/glb_jrdl_logic.sv \
#   vfiles/glc_pio.sv \
#   vfiles/glc_jrdl_decode.sv \
#   vfiles/glc_jrdl_logic.sv \
#   
# 



# /cad/synopsys/vcs/T-2022.06-SP2/bin/vcs: eval: line 2954: syntax error near unexpected token `('
# /cad/synopsys/vcs/T-2022.06-SP2/bin/vcs: eval: line 2954:
# 
# `/cad/synopsys/vcs/T-2022.06-SP2/bin/vcsMsgReport "LNX_OS_VERUN"
# "NAME="Ubuntu" VERSION="20.04.6 LTS (Focal Fossa)" ID=ubuntu
# ID_LIKE=debian PRETTY_NAME="Ubuntu 20.04.6 LTS" VERSION_ID="20.04"
# HOME_URL="https://www.ubuntu.com/"
# SUPPORT_URL="https://help.ubuntu.com/"
# BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
# PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
# VERSION_CODENAME=focal UBUNTU_CODENAME=focal" "x86_64"'
# 
# 
# make[1]: Entering directory '/aha/garnet/tests/test_app/csrc'
# rm -f _cuarc*.so _csrc*.so pre_vcsobj_*.so share_vcsobj_*.so
# 
# if [ -x ../simv ]; then chmod a-x ../simv; fi
# 
# g++ -o ../simv -no-pie -Wl,--no-as-needed -rdynamic
# -Wl,-rpath='$ORIGIN'/simv.daidir -Wl,-rpath=./simv.daidir
# -Wl,-rpath=/cad/synopsys/vcs/T-2022.06-SP2/linux64/lib
# -L/cad/synopsys/vcs/T-2022.06-SP2/linux64/lib -Wl,-rpath-link=./
# -Wl,--no-as-needed objs/amcQw_d.o _102544_archive_1.so
# _prev_archive_1.so SIM_l.o rmapats_mop.o rmapats.o rmar.o rmar_nd.o
# rmar_llvm_0_1.o rmar_llvm_0_0.o -lvirsim -lerrorinf -lsnpsmalloc -lvfs
# -lvcsnew -lsimprofile -luclinative
# /cad/synopsys/vcs/T-2022.06-SP2/linux64/lib/vcs_tls.o
# -Wl,-whole-archive -lvcsucli -Wl,-no-whole-archive
# ./../simv.daidir/vc_hdrs.o
# /cad/synopsys/vcs/T-2022.06-SP2/linux64/lib/vcs_save_restore_new.o
# -ldl -lc -lm -lpthread -ldl
# 
# ./simv -lca -l run.log +vcs+initmem+0 +vcs+initreg+0 -sv_lib libcgra -exitstatus -ucli -i dump_fsdb.tcl  +APP0=/aha/Halide-to-Hardware/apps/hardware_benchmarks/apps/pointwise
# 
# 
# cat << EOF------------------------------------------------------------------------EOF
# Monitor initialization success
# [APP0-pointwise]Initilizing the APP Done
# Input 0: /aha/Halide-to-Hardware/apps/hardware_benchmarks/apps/pointwise/bin/hw_input_stencil.raw - 8192 Byte.
# Output 0: /aha/Halide-to-Hardware/apps/hardware_benchmarks/apps/pointwise/bin/hw_output.raw - 8192 Byte.
# [APP0-pointwise] Parsing the metadata done
# [APP0-pointwise] num_inputs: 1
# [APP0-pointwise] num_outputs: 1
# [APP0-pointwise] num_groups: 2
# Reading input data /aha/Halide-to-Hardware/apps/hardware_benchmarks/apps/pointwise/bin/hw_input_stencil.raw
# Parse input_0 data Done
# input_0 has 1 input blocks
# 
# Start mapping kernel 0
# number of groups: 2
# number of inputs: 1
# number of outputs: 1
# monitor.num_groups: 2
# Mapping input_0_block_0 to global buffer
# Input block mapped to tile: 0
# Input block start addr: 0x0
# Input block cycle start addr: 0
# Input block dimensionality: 1
# =====Before Optimization=====
# [ITER CTRL - loop 0] extent: 4096, cycle stride: 1, data stride: 1
# =====After Optimization=====
# [ITER CTRL - loop 0] extent: 4094, cycle stride: 1, data stride: 2
# Mapping output_0_block_0 to global buffer
# Output block mapped to tile: 0
# Output block start addr: 0x10000
# Output block cycle start addr: 4
# Output block dimensionality: 1
# =====Before Optimization=====
# [ITER CTRL - loop 0] extent: 4096, cycle stride: 1, data stride: 1
# =====After Optimization=====
# [ITER CTRL - loop 0] extent: 4094, cycle stride: 1, data stride: 2
# Configuration of flush signal crossbar is updated to 0x0
# [APP0-pointwise] group_start: 0
# [APP0-pointwise] glb mapping success
# Mapping kernel 0 Succeed
# Turn on interrupt enable registers
# [APP0-pointwise] write bitstream to glb start at 61.50 ns
# [APP0-pointwise] write bitstream to glb end at 138.50 ns
# [APP0-pointwise] It takes 77.00 ns time to write the bitstream to glb.
# [APP0-pointwise] glb configuration start at 138.50 ns
# [APP0-pointwise] glb configuration end at 652.50 ns
# Stall CGRA with stall mask 000000ff
# [APP0-pointwise] fast configuration start at 670.50 ns
# PCFG interrupt from tile 0
# PCFG interrupt clear
# [APP0-pointwise] fast configuration end at 777.50 ns
# [APP0-pointwise] It takes 107.00 ns time to do parallel configuration.
# [APP0-pointwise] write input_0_block_0 to glb start at 787.50 ns
# [APP0-pointwise] write input_0_block_0 to glb end at 1821.50 ns
# [APP0-pointwise] It takes 1034.00 ns time to write 8192 Byte data to glb.
# Unstall CGRA with stall mask 00ff
# [APP0-pointwise] kernel start at 1839.50 ns
# STRM_G2F interrupt from tile 0
# STRM_G2F interrupt clear
# [APP0-pointwise] GLB-to-CGRA streaming done at 5971.50 ns
# STRM_F2G interrupt from tile 0
# [APP0-pointwise] kernel end at 5981.50 ns
# [APP0-pointwise] It takes 4142.00 ns total time to run kernel.
# [APP0-pointwise] The size of output is 8192 Byte.
# [APP0-pointwise] The initial latency is 10.00 ns.
# [APP0-pointwise] The throughput is 0.002 (GB/s).
# STRM_F2G interrupt clear
# [APP0-pointwise] read output_0_block_0 from glb start
# [APP0-pointwise] read output_0_block_0 from glb end
# $finish at simulation time           7052.50 ns
#            V C S   S i m u l a t i o n   R e p o r t 
# Time: 7052500 ps
# CPU Time:      0.900 seconds;       Data structure size:  40.7Mb
# Mon Oct 14 15:15:48 2024
# EOF------------------------------------------------------------------------EOF
