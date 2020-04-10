#!/bin/bash
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
      +vcs+dumparrays \
	  +define+VCS_BUILD \
      +v2k \
	  +memcbk \
      -full64 \
      -ldflags "-Wl,--no-as-needed" \
	  -CFLAGS "-m64" \
	  +incdir+$(RTL_ROOT) \
	  +incdir+"$(RTL_ROOT)/interface" \
	  +incdir+$(TB_ROOT) \
	  -top tb_global_buffer \
	  -F $(TB_ROOT)/"tb_$(TOP_MODULE).filelist" 

NCSIM_TB = irun \
		-timescale 1ns/1ps \
		-l irun.log \
		-sv \
		-sysv \
		-64bit \
		-notimingchecks \
		-vcdextend \
		-top "tb_global_buffer" \
	    +incdir+"$(RTL_ROOT)/interface" \
		-input run.tcl \
		-F $(TB_ROOT)/"tb_$(TOP_MODULE).filelist" 
		# -coverage all \

NCSIM = irun \
		-timescale 1ns/1ps \
		-l irun.log \
		-sv \
		-sysv \
		-64bit \
		-notimingchecks \
		-vcdextend \
		-top "global_buffer" \
		-F $(RTL_ROOT)/"$(TOP_MODULE).filelist" 
		# -coverage all \

SIMV = ./simv \
	   +vcs+lic+wait \
	   +vcs+flush+log \
	   -assert nopostproc \
	   -l vcs.log


.PHONY: rdl clean compile html

rdl: systemRDL/rdl_models/glb.rdl systemRDL/ordt_params/glb.parms
	../systemRDL/perlpp.pl systemRDL/rdl_models/glb.rdl -o systemRDL/rdl_models/glb.rdl.final
	java -jar ../systemRDL/Ordt.jar -parms systemRDL/ordt_params/glb.parms -systemverilog systemRDL/output/ systemRDL/rdl_models/glb.rdl.final

html: rdl
	python ../systemRDL/gen_html.py systemRDL/rdl_models/glb.rdl.final

compile: rdl
	$(NCSIM) 

run: compile
	$(SIMV)

clean:
	rm -rf coverage.vdb csrc DVEfiles inter.vpd simv simv.daidir ucli.key vc_hdrs.h vcs.log INCA_libs irun.history irun.log
