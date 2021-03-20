#!/bin/bash
RTL_DIR := ./rtl
RDL_DIR := systemRDL/output
TB_DIR := ./sim

TOP_MODULE := global_buffer

CGRA_WIDTH ?= 32
NUM_GLB_TILES ?= $(shell expr $(CGRA_WIDTH) / 2 )
GLB_TILE_MEM_SIZE ?= 256
XRUNARGS = 
# XRUNARGS += +TEST_PROC_SIMPLE
# XRUNARGS += +TEST_PROC_ALL
# XRUNARGS += +TEST_JTAG
# XRUNARGS += +TEST_CONFIG
XRUNARGS += +TEST_PCFG
# XRUNARGS += +TEST_STRM
# XRUNARGS += +TEST_STRM_CHAIN
XRUNARGS += +VCD_ON


GLB_TILE_NETLIST := ./netlist/glb_tile.vcs.v
GLB_TOP_NETLIST := ./netlist/global_buffer.vcs.v
SRAM_RTL := /sim/kongty/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/VERILOG/ts1n16ffcllsblvtc2048x64m8sw_130a.v
SRAM_STUB := ./rtl/TS1N16FFCLLSBLVTC2048X64M8SW.sv

RTL_LISTS := `cat $(RTL_DIR)/global_buffer.filelist | sed -e 's/^/$(RTL_DIR)\//' | xargs readlink -f`

FIX_SYSTEMRDL = \
    sed -i '/pio_dec_write_data_d1 <=/d' ./systemRDL/output/glb_jrdl_decode.sv; \
    sed -i '/pio_dec_address_d1 <=/d' ./systemRDL/output/glb_jrdl_decode.sv; \
    sed -i '/endmodule/d' ./systemRDL/output/glb_jrdl_decode.sv; \
    printf "always_ff @ (posedge clk) begin \n pio_dec_address_d1 <= pio_dec_address; \n pio_dec_write_data_d1 <= pio_dec_write_data; \nend \nendmodule" >> ./systemRDL/output/glb_jrdl_decode.sv

GENERATE_TV = python glb_test_gen.py

XRUN = xrun \
	   -64bit \
	   -sv \
	   -sysv \
	   -l xrun.log \
	   -debug \
	   -covoverwrite \
	   -top top \
	   -timescale 100ps/1ps \
	   -unbuffered \
	   -svseed random \
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

# -------------------------------------------------------------------
# RTL
# -------------------------------------------------------------------
# param target generates global_buffer_param.svh
.PHONY: param
param: global_buffer_main.py global_buffer_magma_helper.py
	cd .. && python -m global_buffer.global_buffer_main -p --num_cgra_cols=$(CGRA_WIDTH) --num_glb_tiles=$(NUM_GLB_TILES) --glb_tile_mem_size=$(GLB_TILE_MEM_SIZE)

# rtl target always runs param target
rdl_pre = systemRDL/rdl_models/glb.rdl.pre
$(rdl_pre): param systemRDL/rdl_models/glb.rdl
	cat systemRDL/rdl_models/glb.rdl.param systemRDL/rdl_models/glb.rdl > systemRDL/rdl_models/glb.rdl.pre

rdl_post = systemRDL/rdl_models/glb.rdl.post
$(rdl_post): $(rdl_pre)
	../systemRDL/perlpp.pl systemRDL/rdl_models/glb.rdl.pre -o systemRDL/rdl_models/glb.rdl.post

rdl_gen = $(RDL_DIR)/glb_jrdl_decode.sv $(RDL_DIR)/glb_jrdl_logic.sv $(RDL_DIR)/glb_pio.sv
$(rdl_gen): $(rdl_post)
	java -jar ../systemRDL/Ordt.jar -reglist systemRDL/output/glb.reglist -parms systemRDL/ordt_params/glb.parms -systemverilog systemRDL/output/ systemRDL/rdl_models/glb.rdl.post

$(RTL_LISTS): $(rdl_gen)

.PHONY: rtl
rtl: $(RTL_LISTS)
	$(FIX_SYSTEMRDL)

# html target generates html for systemRDL table
.PHONY: html
html: $(rdl_post)
	python ../systemRDL/gen_html.py systemRDL/rdl_models/glb.rdl.post

# -------------------------------------------------------------------
# GLB TILE
# -------------------------------------------------------------------
# sim-tile
# run testbench of glb-tile with xcelium
.PHONY: sim-tile
sim-tile: TOP_MODULE=glb_tile
sim-tile: TB_DIR=sim-tile
sim-tile: DESIGNARGS += -F $(RTL_DIR)/$(TOP_MODULE).filelist -F $(TB_DIR)/tb_$(TOP_MODULE).filelist -v $(SRAM_STUB)
sim-tile: rtl
	$(XRUN)

# sim-tile-pnr
# run testbench of glb-tile with xcelium with sdf back annotation
.PHONY: sim-til-gl
sim-tile-gl: TOP_MODULE=glb_tile
sim-tile-gl: TB_DIR=sim-tile
sim-tile-gl: XRUNARGS += +define+PNR
sim-tile-gl: DESIGNARGS += \
	`find /tsmc16/TSMCHOME/digital/Front_End/verilog/ -name '*.v' | grep -v "pwr" | sed -e 's/^/-v /' | xargs` \
	-v $(SRAM_RTL) \
	$(GLB_TILE_NETLIST) \
	$(RTL_DIR)/global_buffer_param.svh \
	-F $(TB_DIR)/tb_$(TOP_MODULE).filelist
sim-tile-gl: $(GLB_TILE_NETLIST)
	$(XRUN)

# -------------------------------------------------------------------
# GLB TOP
# -------------------------------------------------------------------
.PHONY: sim
sim: XRUNARGS+= -notimingchecks
sim: DESIGNARGS += -v $(SRAM_STUB) -F $(RTL_DIR)/$(TOP_MODULE).filelist -F $(TB_DIR)/tb_$(TOP_MODULE).filelist 
sim:
	$(GENERATE_TV); 
	$(XRUN)

# gate-level simulation
.PHONY: sim-gl
sim-gl: DESIGNARGS += \
	$(RTL_DIR)/global_buffer_param.svh \
	$(RTL_DIR)/global_buffer_pkg.svh \
	-F $(TB_DIR)/tb_$(TOP_MODULE).filelist \
	-F netlist/netlist.filelist
# sim-gl: XRUNARGS += +define+PWR
sim-gl: XRUNARGS += +define+NON_STOP_IF_INPUT_Z
sim-gl: XRUNARGS += +define+PNR +define+TSMC_CM_NO_WARNING
sim-gl: XRUNARGS += +define+TSMC_CM_UNIT_DELAY
sim-gl: XRUNARGS += +define+TSMC_INITIALIZE_MEM_USING_DEFAULT_TASKS +define+TSMC_MEM_LOAD_0
sim-gl: XRUNARGS += -negdelay
sim-gl: XRUNARGS += -sdf_cmd_file netlist/sdf_cmd.cmd
sim-gl: XRUNARGS += -sdfstats sdf_stats.txt -sdf_verbose -xminitialize 0 -xminit_log init.log
sim-gl:
	$(XRUN)

.PHONY: clean
clean:
	rm -rf xrun.log xrun.history xcelium.d
