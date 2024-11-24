========================================================================
========================================================================
========================================================================

TODO Ignore this file for now, it will be cleaned up in the next release.

========================================================================
========================================================================
========================================================================



the "dev" directory has cached versions of garnet-verilog and
pointwise collateral, so you can quickly run verilator testbench
experiments locally on any machine, no docker containers or
garnet-docker-builds required...


dev/README
- how to debug locally (e.g. on kiwi)
- verilator code was developed using verilator version 5.028
    % verilator --version
    Verilator 5.028 2024-08-21 rev v5.028-44-g1d79f5c59
- "vfiles" subdirectory contains a cache of elaborated garnet verilog files; you may or may not want to replace them with the latest version of whatever you're testing
- also cached in vfiles: the `libcgra.so` library required to support the testbench
- also cached in vfiles: collateral necessary to run 'pointwise' benchmark
- garnet.v has been compressed to save space on github
- note that the cached garnet.v has been slightly modified to make certain memory available as non-arrayed signals for waveform debugging; search for e.g. the signal 'data_array_0' and/or the keyword 'FOO'
- there is also a garnet_stub.v that can be used for quicker verilator debugging of testbench

------------------------------------------------------------------------
VCS FULL GARNET RUN SEQUENCE (e.g. pointwise should finish within 8000ns)
# Output to logs vcs.log<i>, simv.log<i>
APP=+APP0=vfiles/pointwise
ivcs=$i; (vcs.sh |& tee vcs.log$ivcs; echo -n run | simv -lca -l simv.log$ivcs +vcs+initmem+0 +vcs+initreg+0 -sv_lib libcgra -exitstatus -ucli $APP) |& less
# simv.log* should end with "PASS PASS PASS"
# Check output file hw_output.txt vs. gold copy
pw=pointwise/bin
diff -B <(od -An -x --endian=big $pw/hw_output.raw | sed 's/^ //') hw_output.txt | head
(diff -B <(od -An -x --endian=big $pw/hw_output.raw | sed 's/^ //') hw_output.txt || echo FAIL) | head

# TRACE
simv -lca -l simv.log$ivcs +vcs+initmem+0 +vcs+initreg+0 -sv_lib libcgra -exitstatus -ucli $APP
   dump -file simv3.vpd
   dump -add top -fid VPD0 -depth 6
   run 8000ns
   exit
vpd2vcd -q simv3.vpd > simv3.vcd
gtkwave simv3.vcd

------------------------------------------------------------------------
VERILATOR FULL GARNET RUN SEQUENCE (e.g. pointwise should finish within 8000ns)
iver=$i; rmo; verilator.sh |& tee ver.log$iver
make -C obj_dir/ -f Vtop.mk >& make-vtop.log$iver &
tail -f make-vtop.log$iver | awk '{printf("%3d  %s %s\n", NR, $1, $NF)}' # Counts to 245 ish?
alias vtop='(echo Vtop 8000 "$APP"; obj_dir/Vtop 8000 "$APP")'
vtop |& tee vtop.log$iver | less
# vtop.log* should end with "PASS PASS PASS"

# TRACE
iver=$i; rmo; verilator.sh --trace |& tee ver.log$iver
make -C obj_dir/ -f Vtop.mk >& make-vtop.log$iver &
tail -f make-vtop.log$iver | awk '{printf("%3d  %s %s\n", NR, $1, $NF)}' # Counts to >> 245 ish?
alias vtop='(echo Vtop 8000 +trace "$APP"; obj_dir/Vtop 8000 +trace "$APP")'
vtop |& tee vtop.log$iver | less
gtkwave obj_dir/logs/vlt_dump.vcd

------------------------------------------------------------------------
VERILATOR STUB RUN SEQUENCE
# same as non-stub above except do this first:
cp vfiles/garnet_stub.v vfiles/garnet.v
