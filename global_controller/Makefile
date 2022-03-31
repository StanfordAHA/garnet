#!/bin/bash
RTL = ./rtl
TB = ./sim
GENESIS_DIR = $(RTL)/genesis
TB_GENESIS_DIR = $(TB)/genesis
RTL_DIR = rtl_genesis_verif
TB_RTL_DIR = sim_genesis_verif
GENESIS_FILES := $(wildcard $(GENESIS_DIR)/*.svp)
TB_GENESIS_FILES := $(wildcard $(TB_GENESIS_DIR)/*.svp)
TOP_MODULE = global_controller
CGRA_WIDTH ?= 32
NUM_GLB_TILES := $(shell expr $(CGRA_WIDTH) / 2 )
GLB_TILE_MEM_SIZE ?= 256

XRUN = xrun \
       -64bit \
       -sv \
       -sysv \
       -l xrun.log \
       -notimingchecks \
       -covoverwrite \
       -top top \
       -timescale 100ps/1ps \
       +loadpli1=debpli:deb_PLIPtr \
       -initmem0 \
       -initreg0 \
       +access+rwc \
       +maxdelays \
	   -vcdextend \
	   -input "$(TB)/cmd.tcl" \
       $(XRUNARGS) \
       $(DESIGNARGS)

NCSIM = irun \
		-timescale 1ns/1ps \
		-l irun.log \
		-sv \
		-sysv \
		-access +rwc \
		-64bit \
		-vcdextend \
		-input "$(TB)/cmd.tcl" \
		-top top \
		-F tb_$(TOP_MODULE).filelist 
		# -coverage all \

SIMV = ./simv \
	   +vcs+lic+wait \
	   +vcs+flush+log \
	   -assert nopostproc \
	   -l vcs.log

GEN_RTL_FILELIST = \
	find $(RTL_DIR) -type f -name '*.sv' | xargs realpath  > $(TOP_MODULE).filelist; \
	find ./systemRDL/output -type f -name '*.sv' | xargs realpath  >> $(TOP_MODULE).filelist; \
	echo "/cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/CW_tap.v" >> $(TOP_MODULE).filelist

GEN_TB_FILELIST = \
	find $(TB_RTL_DIR) -type f -name '*.sv' | xargs realpath  > tb_$(TOP_MODULE).filelist; \
	find ./systemRDL/output -type f -name '*.sv' | xargs realpath  >> tb_$(TOP_MODULE).filelist; \
	echo "/cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/CW_tap.v" >> tb_$(TOP_MODULE).filelist


.PHONY: rdl clean html genesis sim_genesis rtl 

genesis: $(GENESIS_FILES)
	rm -rf $(RTL_DIR)
	Genesis2.pl -parse -generate -top ${TOP_MODULE} -inputlist $(RTL)/$(TOP_MODULE).genesis.filelist -parameter global_controller.num_glb_tiles=$(NUM_GLB_TILES) global_controller.cgra_width=$(CGRA_WIDTH) global_controller.glb_tile_mem_size=$(GLB_TILE_MEM_SIZE)
	mv genesis_verif $(RTL_DIR)

rdl: systemRDL/rdl_models/glc.rdl systemRDL/ordt_params/glc.parms
	../systemRDL/perlpp.pl systemRDL/rdl_models/glc.rdl -o systemRDL/rdl_models/glc.rdl.final

html: rdl
	python ../systemRDL/gen_html.py systemRDL/rdl_models/glc.rdl.final

rtl: rdl genesis
	java -jar ../systemRDL/Ordt.jar -parms systemRDL/ordt_params/glc.parms -systemverilog systemRDL/output/ systemRDL/rdl_models/glc.rdl.final
	$(GEN_RTL_FILELIST)

sim_genesis: $(TB_GENESIS_FILES)
	rm -rf $(TB_RTL_DIR)
	Genesis2.pl -parse -generate -top top -inputlist $(TB)/tb_$(TOP_MODULE).genesis.filelist $(RTL)/$(TOP_MODULE).genesis.filelist
	mv genesis_verif $(TB_RTL_DIR)

sim: DESIGNARGS += \
    -F tb_$(TOP_MODULE).filelist
sim: rtl sim_genesis
	$(GEN_TB_FILELIST)
	$(XRUN)

clean:
	rm -rf coverage.vdb csrc DVEfiles inter.vpd simv simv.daidir ucli.key vc_hdrs.h vcs.log INCA_libs irun.history irun.log $(TOP_MODULE).filelist tb_$(TOP_MODULE).filelist
	./genesis_clean.cmd
