#!/bin/bash
DESIGN = ./design
TB = ./testbench
GENESIS_DIR = $(DESIGN)/genesis
TB_GENESIS_DIR = $(TB)/genesis
RTL_DIR = $(DESIGN)/genesis_verif
TB_RTL_DIR = $(TB)/genesis_verif
GENESIS_FILES := $(wildcard $(GENESIS_DIR)/*.svp)
TB_GENESIS_FILES := $(wildcard $(TB_GENESIS_DIR)/*.svp)
TOP_MODULE = global_controller

TB_NCSIM = irun \
		-timescale 1ns/1ps \
		-l irun.log \
		-sv \
		-sysv \
		-64bit \
		-notimingchecks \
		-vcdextend \
		-input "$(TB)/run.tcl" \
		-top top \
		-F tb_$(TOP_MODULE).filelist 
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

TB_FILELIST = find $(TB_RTL_DIR) -type f -name '*.sv' > tb_$(TOP_MODULE).filelist


.PHONY: rdl clean compile html genesis tb_genesis rtl tb_rtl tb_compile

genesis: $(GENESIS_FILES)
	Genesis2.pl -parse -generate -top ${TOP_MODULE} -inputlist $(GENESIS_DIR)/$(TOP_MODULE).filelist && \
	rm -rf $(RTL_DIR) && \
	mv genesis_verif $(RTL_DIR)

tb_genesis: $(TB_GENESIS_FILES)
	Genesis2.pl -parse -generate -top top -inputlist $(TB_GENESIS_DIR)/tb_$(TOP_MODULE).filelist $(GENESIS_DIR)/$(TOP_MODULE).filelist && \
	rm -rf $(TB_RTL_DIR) && \
	mv genesis_verif $(TB_RTL_DIR)

rdl: systemRDL/rdl_models/glc.rdl systemRDL/ordt_params/glc.parms
	../systemRDL/perlpp.pl systemRDL/rdl_models/glc.rdl -o systemRDL/rdl_models/glc.rdl.final
	java -jar ../systemRDL/Ordt.jar -parms systemRDL/ordt_params/glc.parms -systemverilog systemRDL/output/ systemRDL/rdl_models/glc.rdl.final

html: rdl
	python ../systemRDL/gen_html.py systemRDL/rdl_models/glc.rdl.final

rtl: rdl genesis
	$(FILELIST)

compile: rtl
	$(FILELIST)
	$(NCSIM) 

tb_rtl: rtl tb_genesis
	$(TB_FILELIST)

tb_compile: tb_rtl
	$(TB_NCSIM)

run: compile
	$(SIMV)

clean:
	rm -rf coverage.vdb csrc DVEfiles inter.vpd simv simv.daidir ucli.key vc_hdrs.h vcs.log INCA_libs irun.history irun.log $(TOP_MODULE).filelist
	cd $(DESIGN); ./genesis_clean.cmd
