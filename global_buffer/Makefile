#!/bin/tcsh
RTL_ROOT = ./rtl
TOP_MODULE = global_buffer

VCS = vcs \
	  -sverilog \
	  -timescale=1ns/1ps \
	  +vcs+lic+wait \
	  +define+VCS_BUILD \
      +v2k \
      -noIncrComp \
      -debug \
      +lint=TFIPC-L \
      +memcbk \
      -full64 \
      -ldflags "-Wl,--no-as-needed" \
	  +incdir+"./rtl" \
      -F $(RTL_ROOT)/$(TOP_MODULE).filelist

NCSIM = irun \
		-timescale 1ns/1ps \
		-l irun.log \
		-access \
		+rwc \
		-notimingchecks \
		-F $(RTL_ROOT)/$(TOP_MODULE).filelist


SIMV = ./simv \
	   +vcs+lic+wait \
	   +vcs+flush+log \
	   -assert nopostproc \
	   -l vcs.log

comp_vcs:
	$(VCS) 

comp_ncsim:
	$(NCSIM) 

run:
	$(SIMV)

clean:
	rm -rf coverage.vdb csrc DVEfiles inter.vpd simv simv.daidir ucli.key vc_hdrs.h vcs.log INCA_libs irun.history irun.log
