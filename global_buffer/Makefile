#!/bin/bash
RTL_ROOT = ./rtl
TB_ROOT = ./sim
TOP_MODULE = global_buffer
TILE_MODULE = glb_tile

SIM_XRUN = xrun \
		   -64bit \
		   -sv \
		   -sysv \
		   -l xrun.log \
		   -notimingchecks \
	   	   -access +r \
	   	   -covoverwrite \
	   	   -timescale 1ns/1ps \
		   -top top \
		   +loadpli1=debpli:deb_PLIPtr \
		   -initmem0 \
		   -initreg0 \
		   -run \
		   -F $(RTL_ROOT)/"$(TOP_MODULE).filelist" \
		   -F $(TB_ROOT)/"tb_$(TOP_MODULE).filelist" \
		   +dump="$(TOP_MODULE).fsdb"

VCS = vcs \
	  -debug_acc+all \
	  -sverilog \
	  -timescale=1ns/1ps \
	  -v2k_generate \
	  -full64 \
	  -ldflags "-Wl,--no-as-needed" \
	  -CFLAGS "-m64" \
	  -top top \
	  -R \
	  +lint=TFIPC-L \
	  +vcs+lic+wait \
	  +vcs+initreg+random \
	  +overlap \
	  +v2k \
	  +memcbk \
	  $(VCSARGS) \
	  $(DESIGNARGS) \

.PHONY: param rdl_pre rdl rtl html sim pwr clean

param: global_buffer_main.py
	cd .. && python -m global_buffer.global_buffer_main -p

rdl_pre: param systemRDL/rdl_models/glb.rdl systemRDL/rdl_models/glb.rdl.param
	cat systemRDL/rdl_models/glb.rdl.param systemRDL/rdl_models/glb.rdl > systemRDL/rdl_models/glb.rdl.pre

rdl: rdl_pre
	../systemRDL/perlpp.pl systemRDL/rdl_models/glb.rdl.pre -o systemRDL/rdl_models/glb.rdl.final

rtl: rdl
	java -jar ../systemRDL/Ordt.jar -parms systemRDL/ordt_params/glb.parms -systemverilog systemRDL/output/ systemRDL/rdl_models/glb.rdl.final

html: rdl
	python ../systemRDL/gen_html.py systemRDL/rdl_models/glb.rdl.final

sim: VCSARGS+=+notimingcheck
sim: DESIGNARGS += -F $(RTL_ROOT)/$(TOP_MODULE).filelist -F $(TB_ROOT)/tb_$(TOP_MODULE).filelist
sim: rtl 
	$(VCS)

sim-syn: rtl
	$(VCS)

sim-pnr: VCSARGS += +sdfverbose +multisource_int_delays +neg_tchk -negdelay +define+PNR -P sdf.tab
sim-pnr: DESIGNARGS += \
	$(RTL_ROOT)/global_buffer_param.svh \
	$(RTL_ROOT)/global_buffer_pkg.svh \
	-F $(TB_ROOT)/tb_$(TOP_MODULE).filelist \
	`find /tsmc16/TSMCHOME/digital/Front_End/verilog/ -name '*.v' | grep -v "pwr" | sed -e 's/^/-v /' | xargs` \
	`find /sim/ajcars/mc -name '*.v' | grep -v pwr | sed -e 's/^/-v /' | xargs` \
	/sim/kongty/pnr_annotate/global_buffer.v \
	/sim/kongty/pnr_annotate/glb_tile.v
sim-pnr: rtl
	$(VCS)

clean:
	rm -rf coverage.vdb csrc DVEfiles inter.vpd simv simv.daidir ucli.key vc_hdrs.h vcs.log INCA_libs irun.history irun.log
