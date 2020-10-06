#!/bin/bash
RTL = ./rtl
TB = ./sim
GENESIS_DIR = $(RTL)/genesis
TB_GENESIS_DIR = $(TB)/genesis
RTL_DIR = $(RTL)/genesis_verif
TB_RTL_DIR = $(TB)/genesis_verif
GENESIS_FILES := $(wildcard $(GENESIS_DIR)/*.svp)
TB_GENESIS_FILES := $(wildcard $(TB_GENESIS_DIR)/*.svp)
TOP_MODULE = global_controller

TB_NCSIM = irun \
		-timescale 1ns/1ps \
		-l irun.log \
		-sv \
		-sysv \
		-access +rwc \
		-64bit \
		-vcdextend \
		-input "$(TB)/cmd.tcl" \
		-top top \
		-F $(TB)/tb_$(TOP_MODULE).filelist 
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
		-F $(TOP_MODULE).filelist \
		-F TB_$(TOP_MODULE).filelist 
		# -coverage all \

SIMV = ./simv \
	   +vcs+lic+wait \
	   +vcs+flush+log \
	   -assert nopostproc \
	   -l vcs.log

GEN_RTL_FILELIST = \
	find $(RTL_DIR) -type f -name '*.sv' > $(TOP_MODULE).filelist; \
	find ./systemRDL/output -type f -name '*.sv' >> $(TOP_MODULE).filelist; \
	echo "/cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/CW_tap.v" >> $(TOP_MODULE).filelist; \


.PHONY: rdl clean compile html genesis sim_genesis rtl tb_rtl tb_compile

genesis: $(GENESIS_FILES)
	cd $(RTL) && \
	./genesis_clean.cmd && \
	Genesis2.pl -parse -generate -top ${TOP_MODULE} -inputlist $(TOP_MODULE).genesis.filelist

rdl: systemRDL/rdl_models/glc.rdl systemRDL/ordt_params/glc.parms
	../systemRDL/perlpp.pl systemRDL/rdl_models/glc.rdl -o systemRDL/rdl_models/glc.rdl.final

html: rdl
	python ../systemRDL/gen_html.py systemRDL/rdl_models/glc.rdl.final

rtl: rdl genesis
	java -jar ../systemRDL/Ordt.jar -parms systemRDL/ordt_params/glc.parms -systemverilog systemRDL/output/ systemRDL/rdl_models/glc.rdl.final
	$(GEN_RTL_FILELIST)

sim_genesis: $(TB_GENESIS_FILES)
	cd $(TB) && \
	./genesis_clean.cmd && \
	Genesis2.pl -parse -generate -top top -inputlist tb_$(TOP_MODULE).genesis.filelist

compile: rtl
	$(NCSIM) 

tb_compile: tb_rtl rtl sim_genesis
	$(TB_NCSIM)

sim: tb_compile
	$(SIMV)

clean:
	rm -rf coverage.vdb csrc DVEfiles inter.vpd simv simv.daidir ucli.key vc_hdrs.h vcs.log INCA_libs irun.history irun.log $(TOP_MODULE).filelist
	cd $(RTL); ./genesis_clean.cmd
