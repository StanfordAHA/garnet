#!/bin/tcsh
RTL_ROOT = ./rtl
TB_ROOT = ./tb
TOP_MODULE = global_buffer

VCS = vcs \
	  -R \
	  -debug_all \
	  -sverilog \
	  -timescale=1ns/1ps \
      +lint=TFIPC-L \
	  +vcs+dumpvars+global_buffer.vcd \
	  +vcs+lic+wait \
	  +define+VCS_BUILD \
      +v2k \
      -noIncrComp \
      +memcbk \
      +vcs+dumparrays \
      -full64 \
      -ldflags "-Wl,--no-as-needed" \
	  +incdir+$(RTL_ROOT) \
	  +incdir+"$(RTL_ROOT)/interface" \
	  +incdir+$(TB_ROOT) \
	  -top tb_global_buffer \
	  -F $(TB_ROOT)/"tb_$(TOP_MODULE).filelist" 

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

comp:
	$(VCS) 

comp_ncsim:
	$(NCSIM) 

run:
	$(SIMV)

clean:
	rm -rf coverage.vdb csrc DVEfiles inter.vpd simv simv.daidir ucli.key vc_hdrs.h vcs.log INCA_libs irun.history irun.log
