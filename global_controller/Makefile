#!/bin/bash
DESIGN = ./design
GENESIS_DIR = $(DESIGN)/genesis
RTL_DIR = $(DESIGN)/genesis_verif
GENESIS_FILES := $(wildcard $(GENESIS_DIR)/*.svp)
TOP_MODULE = global_controller

NCSIM = irun \
		-timescale 1ns/1ps \
		-l irun.log \
		-sv \
		-sysv \
		-64bit \
		-notimingchecks \
		-vcdextend \
		-top $(TOP_MODULE) \
		-F $(TOP_MODULE).filelist 
		# -coverage all \

SIMV = ./simv \
	   +vcs+lic+wait \
	   +vcs+flush+log \
	   -assert nopostproc \
	   -l vcs.log

FILELIST = find $(RTL_DIR) -type f -name '*.sv' > $(TOP_MODULE).filelist; \
		   find ./systemRDL/output -type f -name '*.sv' >> $(TOP_MODULE).filelist; \
		   echo "/cad/synopsys/syn/P-2019.03/dw/sim_ver/DW_tap.v" >> $(TOP_MODULE).filelist

.PHONY: rdl clean compile html genesis

genesis: $(GENESIS_FILES)
	cd $(DESIGN) && \
	Genesis2.pl -parse -generate -top ${TOP_MODULE} -inputlist genesis/$(TOP_MODULE).filelist

rdl: systemRDL/rdl_models/glc.rdl systemRDL/ordt_params/glc.parms
	../systemRDL/perlpp.pl systemRDL/rdl_models/glc.rdl -o systemRDL/rdl_models/glc.rdl.final
	java -jar ../systemRDL/Ordt.jar -parms systemRDL/ordt_params/glc.parms -systemverilog systemRDL/output/ systemRDL/rdl_models/glc.rdl.final

html: rdl
	python ../systemRDL/gen_html.py systemRDL/rdl_models/glc.rdl.final

compile: rdl genesis
	$(FILELIST)
	$(NCSIM) 

run: compile
	$(SIMV)

clean:
	rm -rf coverage.vdb csrc DVEfiles inter.vpd simv simv.daidir ucli.key vc_hdrs.h vcs.log INCA_libs irun.history irun.log $(TOP_MODULE).filelist
	cd $(DESIGN); ./genesis_clean.cmd
