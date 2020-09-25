#!/bin/bash
RTL_ROOT = ./rtl
TB_ROOT = ./sim
TOP_MODULE = global_buffer
TILE_MODULE = glb_tile

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
	   +access+rw \
	   +maxdelays \
	   $(XRUNARGS) \
	   $(DESIGNARGS)

VCS = vcs \
	  -debug_acc+all \
	  -sverilog \
	  -timescale=100ps/1ps \
	  -v2k_generate \
	  -full64 \
	  -ldflags "-Wl,--no-as-needed" \
	  -CFLAGS "-m64" \
	  -top top \
	  +lint=TFIPC-L \
	  +vcs+lic+wait \
	  +vcs+initreg+random \
	  +overlap \
	  +v2k \
	  +memcbk \
	  $(VCSARGS) \
	  $(DESIGNARGS)

SIMV = ./simv \
	+vcs+initmem+0 \
	+vcs+initreg+0

RDL_DIR = systemRDL/output
RTL_DIR := rtl
RTLS :=\
	$(RTL_DIR)/cfg_ifc.sv \
	$(RTL_DIR)/global_buffer_pkg.svh \
	$(RTL_DIR)/global_buffer.sv \
	$(RTL_DIR)/glb_tile.sv \
	$(RTL_DIR)/glb_tile_int.sv \
	$(RTL_DIR)/glb_tile_cfg.sv \
	$(RTL_DIR)/glb_tile_cfg_ctrl.sv \
	$(RTL_DIR)/glb_tile_pc_switch.sv \
	$(RTL_DIR)/glb_core_proc_router.sv \
	$(RTL_DIR)/glb_core_strm_router.sv \
	$(RTL_DIR)/glb_core_pc_router.sv \
	$(RTL_DIR)/glb_dummy_start.sv \
	$(RTL_DIR)/glb_dummy_end.sv \
	$(RTL_DIR)/glb_core.sv \
	$(RTL_DIR)/glb_bank.sv \
	$(RTL_DIR)/glb_core_store_dma.sv \
	$(RTL_DIR)/glb_core_load_dma.sv \
	$(RTL_DIR)/glb_core_pc_dma.sv \
	$(RTL_DIR)/glb_core_switch.sv \
	$(RTL_DIR)/glb_core_strm_mux.sv \
	$(RTL_DIR)/glb_core_sram_cfg_ctrl.sv \
	$(RTL_DIR)/glb_bank_memory.sv \
	$(RTL_DIR)/glb_bank_ctrl.sv \
	$(RTL_DIR)/glb_bank_sram_gen.sv \
	$(RTL_DIR)/glb_shift.sv \
	$(RTL_DIR)/TS1N16FFCLLSBLVTC2048X64M8SW.sv

param = systemRDL/rdl_models/glb.rdl.param rtl/global_buffer_param.svh
$(param): global_buffer_main.py global_buffer_magma_helper.py
	cd .. && python -m global_buffer.global_buffer_main -p

rdl_pre = systemRDL/rdl_models/glb.rdl.pre
$(rdl_pre): $(param) systemRDL/rdl_models/glb.rdl
	cat systemRDL/rdl_models/glb.rdl.param systemRDL/rdl_models/glb.rdl > systemRDL/rdl_models/glb.rdl.pre

rdl_post = systemRDL/rdl_models/glb.rdl.post
$(rdl_post): $(rdl_pre)
	../systemRDL/perlpp.pl systemRDL/rdl_models/glb.rdl.pre -o systemRDL/rdl_models/glb.rdl.post

rdl_gen = $(RDL_DIR)/glb_jrdl_decode.sv $(RDL_DIR)/glb_jrdl_logic.sv $(RDL_DIR)/glb_pio.sv
$(rdl_gen): $(rdl_post)
	java -jar ../systemRDL/Ordt.jar -parms systemRDL/ordt_params/glb.parms -systemverilog systemRDL/output/ systemRDL/rdl_models/glb.rdl.post

$(RTLS): $(rdl_gen)

.PHONY: rtl
rtl: $(RTLS)

.PHONY: html
html: $(rdl_post)
	python ../systemRDL/gen_html.py systemRDL/rdl_models/glb.rdl.post

# sim-tile
# run testbench of glb-tile with vcs/xcelium
.PHONY: sim-tile
sim-tile: TOP_MODULE=glb_tile
sim-tile: TB_ROOT=sim_glb_tile
sim-tile: VCSARGS+=+notimingcheck
sim-tile: DESIGNARGS += -F $(RTL_ROOT)/$(TOP_MODULE).filelist -F $(TB_ROOT)/tb_$(TOP_MODULE).filelist
sim-tile: $(RTLS) 
	$(VCS)
	$(SIMV)

# sim-tile-pnr
# run testbench of glb-tile with vcs/xcelium with sdf back annotation
.PHONY: sim-til-gl
sim-tile-gl: TOP_MODULE=glb_tile
sim-tile-gl: TB_ROOT=sim_glb_tile
sim-tile-gl: VCSARGS += +define+PNR +sdfverbose +csdf+precompile +multisource_int_delays +neg_tchk -negdelay -P sdf.tab
sim-tile-gl: XRUNARGS += +define+PNR
sim-tile-gl: DESIGNARGS += \
	`find /tsmc16/TSMCHOME/digital/Front_End/verilog/ -name '*.v' | grep -v "pwr" | sed -e 's/^/-v /' | xargs` \
	-v /sim/ajcars/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/VERILOG/*.v \
	/sim/kongty/pnr_annotate/glb_tile.vcs.v \
	$(RTL_ROOT)/global_buffer_param.svh \
	-F $(TB_ROOT)/tb_$(TOP_MODULE).filelist
sim-tile-gl: $(RTLS) 
	$(VCS)
	$(SIMV)

# run testbench of glb with vcs/xcelium
.PHONY: sim
#sim: VCSARGS+=+notimingcheck
#sim: XRUNARGS+=+define+DEBUG
sim: DESIGNARGS += -F $(RTL_ROOT)/$(TOP_MODULE).filelist -F $(TB_ROOT)/tb_$(TOP_MODULE).filelist
sim: $(RTLS) 
	$(XRUN)

.PHONY: sim-gl
# sim-gl: VCSARGS += +sdfverbose +multisource_int_delays +neg_tchk -negdelay +define+PNR -P sdf.tab +oldsdf
# sim-gl: VCSARGS += +define+PNR +sdfverbose +csdf+precompile +multisource_int_delays +neg_tchk -negdelay -P sdf.tab
sim-gl: VCSARGS += +sdfverbose +multisource_int_delays +neg_tchk -negdelay +define+PNR +compsdf
sim-gl: DESIGNARGS += \
	$(RTL_ROOT)/global_buffer_param.svh \
	$(RTL_ROOT)/global_buffer_pkg.svh \
	-F $(TB_ROOT)/tb_$(TOP_MODULE).filelist \
	`find /tsmc16/TSMCHOME/digital/Front_End/verilog/ -name '*.v' | grep -v "pwr" | sed -e 's/^/-v /' | xargs` \
	`find /sim/ajcars/mc -name '*.v' | grep -v pwr | sed -e 's/^/-v /' | xargs` \
	/sim/kongty/pnr_annotate/global_buffer.vcs.v \
	/sim/kongty/pnr_annotate/glb_tile.vcs.v
sim-gl: $(RTLS)
	$(XRUN)

.PHONY: clean
clean:
	rm -rf coverage.vdb csrc DVEfiles inter.vpd simv simv.daidir ucli.key vc_hdrs.h vcs.log INCA_libs irun.history irun.log
