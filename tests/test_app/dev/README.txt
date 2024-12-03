As of December 2024, we can now use verilator to simulate aha/garnet
verilog. For the backstory, see
garnet issue 1087 <https://github.com/StanfordAHA/garnet/issues/1087>
and garnet pull request 1091 <https://github.com/StanfordAHA/garnet/pull/1091>

We used Verilator version 5.028 for initial development.

This directory has cached versions of garnet verilog and `pointwise`
collateral, so you can quickly run verilator testbench experiments
locally on any machine, no docker containers or garnet-docker-builds
required...


==============================================================================
NOTES

- verilator code was developed using verilator version 5.028
    % verilator --version
    Verilator 5.028 2024-08-21 rev v5.028-44-g1d79f5c59

- "vfiles" subdirectory contains a cache of elaborated garnet verilog
  files; you may or may not want to replace them with the latest
  version of whatever you're testing

- also cached in vfiles: the `libcgra.so` library required to support the testbench

- also cached in vfiles: collateral necessary to run 'pointwise' benchmark

- garnet.v has been compressed to save space on github

- note that the cached garnet.v has been slightly modified to show some
  memory locations as non-arrayed signals for waveform debugging; e.g. search
  for e.g. the signal 'data_array_0' and/or the keyword 'FOO'

- also: `garnet_stub.v` can be used for quicker verilator debugging of testbench


==============================================================================
HOW TO DEBUG LOCALLY (e.g. on kiwi)

Use "VCS Full Run Sequence" to make a pointwise-based vcs log file
and/or waveforms for comparison with verilator output.

Use "Verilator Full Run Sequence" to run verilator with outputs that
can be compared to Vcs results. A full run takes awhile; for faster
turnaround, use the stub run sequence.

Use "Verilator Stub Run Sequence" to run verilator quickly and see if
basic signals seem to be working.

------------------------------------------------------------------------
# VCS FULL GARNET RUN SEQUENCE (e.g. pointwise should finish within 8000ns)
# Output to logs vcs.log<i>, simv.log<i>

APP=+APP0=vfiles/pointwise; i=0
ivcs=$i; (vcs.sh |& tee vcs.log$ivcs; echo -n run | simv -lca -l simv.log$ivcs +vcs+initmem+0 +vcs+initreg+0 -sv_lib libcgra -exitstatus -ucli $APP) |& less

# simv.log* should end with "PASS PASS PASS"
# Check output file hw_output.txt vs. gold copy

pw=pointwise/bin
diff -B <(od -An -x --endian=big $pw/hw_output.raw | sed 's/^ //') hw_output.txt | head
(diff -B <(od -An -x --endian=big $pw/hw_output.raw | sed 's/^ //') hw_output.txt || echo FAIL) | head

# TRACE/WAVEFORMS
simv -lca -l simv.log$ivcs +vcs+initmem+0 +vcs+initreg+0 -sv_lib libcgra -exitstatus -ucli $APP
   dump -file simv3.vpd
   dump -add top -fid VPD0 -depth 6
   run 8000ns
   exit

vpd2vcd -q simv3.vpd > simv3.vcd
gtkwave simv3.vcd

------------------------------------------------------------------------
# VERILATOR FULL GARNET RUN SEQUENCE (e.g. pointwise should finish within 8000ns)

alias rmo='/bin/rm -rf obj_dir'
APP=+APP0=vfiles/pointwise; i=0
iver=$i; rmo; verilator.sh |& tee ver.log$iver
make -C obj_dir/ -f Vtop.mk >& make-vtop.log$iver &
tail -f make-vtop.log$iver | awk '{printf("%3d  %s %s\n", NR, $1, $NF)}' # Counts to 245 ish?
alias vtop='(echo Vtop 8000 "$APP"; obj_dir/Vtop 8000 "$APP")'
vtop |& tee vtop.log$iver | less
# vtop.log* should end with "PASS PASS PASS"

# TRACE/WAVEFORMS
iver=$i; rmo; verilator.sh --trace |& tee ver.log$iver
make -C obj_dir/ -f Vtop.mk >& make-vtop.log$iver &
tail -f make-vtop.log$iver | awk '{printf("%3d  %s %s\n", NR, $1, $NF)}' # Counts to >> 245 ish?
alias vtop='(echo Vtop 8000 +trace "$APP"; obj_dir/Vtop 8000 +trace "$APP")'
vtop |& tee vtop.log$iver | less
gtkwave obj_dir/logs/vlt_dump.vcd

------------------------------------------------------------------------
# VERILATOR STUB RUN SEQUENCE
# same as non-stub above except do this first:
cp vfiles/garnet.v vfiles/garnet.v.orig
cp vfiles/garnet_stub.v vfiles/garnet.v
