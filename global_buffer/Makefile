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


.PHONY: rdl_param rdl_final rdl_pre clean compile html param_files

param_files: global_buffer_main.py
	cd .. && \
	python -m global_buffer.global_buffer_main -p

rdl_param: param_files systemRDL/rdl_models/glb.rdl systemRDL/rdl_models/glb.rdl.param
	cat systemRDL/rdl_models/glb.rdl.param systemRDL/rdl_models/glb.rdl > systemRDL/rdl_models/glb.rdl.pre

rdl_pre: rdl_param
	../systemRDL/perlpp.pl systemRDL/rdl_models/glb.rdl.pre -o systemRDL/rdl_models/glb.rdl.final

rdl_final: rdl_pre
	java -jar ../systemRDL/Ordt.jar -parms systemRDL/ordt_params/glb.parms -systemverilog systemRDL/output/ systemRDL/rdl_models/glb.rdl.final

html: rdl_final
	python ../systemRDL/gen_html.py systemRDL/rdl_models/glb.rdl.final

compile: rdl_final
	$(NCSIM) 

run: compile
	$(SIMV)

clean:
	rm -rf coverage.vdb csrc DVEfiles inter.vpd simv simv.daidir ucli.key vc_hdrs.h vcs.log INCA_libs irun.history irun.log
