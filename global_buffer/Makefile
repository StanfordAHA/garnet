#!/bin/bash
RTL_ROOT = ./rtl
TB_ROOT = ./testbench
TOP_MODULE = global_buffer
TILE_MODULE = glb_tile

POWER = vcs \
		-debug \
		-sverilog \
				+vcs+initreg+random \
				+vcs+dumpvars+$(TOP_MODULE)_power.vcd \
				+sdfverbose \
				+overlap \
				+multisource_int_delays \
				-ldflags "-Wl,--no-as-needed" \
				-timescale=1ns/1ps \
				-top top \
				+neg_tchk \
				-negdelay \
				`find /tsmc16/TSMCHOME/digital/Front_End/verilog/ -name '*.v' | grep -v "pwr" | sed -e 's/^/-v /' | xargs` \
				`find /sim/ajcars/mc -name '*.v' | grep -v pwr | sed -e 's/^/-v /' | xargs` \
				$(RTL_ROOT)/global_buffer_param.svh \
				$(RTL_ROOT)/global_buffer_pkg.svh \
				/sim/kongty/pnr_annotate/global_buffer.v \
				/sim/kongty/pnr_annotate/glb_tile.v \
				-F $(TB_ROOT)/"tb_$(TOP_MODULE).filelist"


VCS = vcs \
			-debug_all \
			-sverilog \
			-v2k_generate \
			-timescale=1ns/1ps \
			+lint=TFIPC-L \
			+vcs+lic+wait \
			+vcs+initreg+random \
			+define+VCS_BUILD \
			+v2k \
			+memcbk \
			-full64 \
			-ldflags "-Wl,--no-as-needed" \
			-CFLAGS "-m64" \
			-top top \
			-F $(RTL_ROOT)/"$(TOP_MODULE).filelist" \
			-F $(TB_ROOT)/"tb_$(TOP_MODULE).filelist"
			# +lint=all \
					
SIMV = ./simv -ucli -do dump.tcl +vcs+initreg+0 +vcs+initmem+0

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

.PHONY: rdl_pre rdl rtl clean compile html param tb run

param: global_buffer_main.py
		cd .. && \
		python -m global_buffer.global_buffer_main -p

rdl_pre: param systemRDL/rdl_models/glb.rdl systemRDL/rdl_models/glb.rdl.param
		cat systemRDL/rdl_models/glb.rdl.param systemRDL/rdl_models/glb.rdl > systemRDL/rdl_models/glb.rdl.pre

rdl: rdl_pre
		../systemRDL/perlpp.pl systemRDL/rdl_models/glb.rdl.pre -o systemRDL/rdl_models/glb.rdl.final

rtl: rdl
		java -jar ../systemRDL/Ordt.jar -parms systemRDL/ordt_params/glb.parms -systemverilog systemRDL/output/ systemRDL/rdl_models/glb.rdl.final

html: rdl
		python ../systemRDL/gen_html.py systemRDL/rdl_models/glb.rdl.final

compile: rtl
		$(NCSIM) 

tb: rtl
		$(VCS) 
		$(SIMV)

power: rtl
		$(POWER)
		$(SIMV)

clean:
		rm -rf coverage.vdb csrc DVEfiles inter.vpd simv simv.daidir ucli.key vc_hdrs.h vcs.log INCA_libs irun.history irun.log

