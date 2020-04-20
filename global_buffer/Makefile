#!/bin/bash
RTL_ROOT = ./rtl
TB_ROOT = ./testbench
TOP_MODULE = global_buffer

VCS = vcs \
	  -debug_all \
	  -sverilog \
	  -v2k_generate \
	  -timescale=1ns/1ps \
      +lint=TFIPC-L \
	  +vcs+lic+wait \
	  +vcs+initreg+random \
      +vcs+dumparrays+4096 \
	  +vcs+finish+10000000 \
	  +define+VCS_BUILD \
      +v2k \
	  +memcbk \
      -full64 \
      -ldflags "-Wl,--no-as-needed" \
	  -CFLAGS "-m64" \
	  -top top \
	  -F $(RTL_ROOT)/"$(TOP_MODULE).filelist" \
	  -F $(TB_ROOT)/"tb_$(TOP_MODULE).filelist"

SIMV = ./simv -ucli -do dump.tcl +vcs+initreg+0

TB_NCSIM = irun \
		-timescale 1ns/1ps \
		-l irun.log \
		-sv \
		-sysv \
		-access +rwc \
		-64bit \
		-vcdextend \
		-top "tb_$(TOP_MODULE)" \
		-input "$(TB_ROOT)/cmd.tcl" \
		-F $(RTL_ROOT)/"$(TOP_MODULE).filelist" \
		-F $(TB_ROOT)/"tb_test.filelist" 
		# -coverage all \

NCSIM = irun \
		-timescale 1ns/1ps \
		-l irun.log \
		-sv \
		-sysv \
		-64bit \
		-notimingchecks \
		-vcdextend \
		-top $(TOP_MODULE) \
		-F $(RTL_ROOT)/"$(TOP_MODULE).filelist" 
		# -coverage all \

.PHONY: rdl_param rdl_final rdl_pre clean compile html param_files tb_compile run

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

tb_compile: rdl_final
	$(VCS) 

run: tb_compile
	$(SIMV)

clean:
	rm -rf coverage.vdb csrc DVEfiles inter.vpd simv simv.daidir ucli.key vc_hdrs.h vcs.log INCA_libs irun.history irun.log

