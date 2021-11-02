#!/bin/bash
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(abspath $(dir $(mkfile_path)))

CGRA_WIDTH ?= 32
NUM_GLB_TILES ?= $(shell expr $(CGRA_WIDTH) / 2 )
GLB_TILE_MEM_SIZE ?= 256

RUNARGS = 
RUNARGS += +TEST_GLB_MEM_SIMPLE
RUNARGS += +TEST_GLB_CFG
RUNARGS += +TEST_GLB_G2F_STREAM
RUNARGS += +TEST_GLB_F2G_STREAM
RUNARGS += +TEST_PCFG_STREAM

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
	  -full64 \
	  -ldflags "-Wl,--no-as-needed" \
	  -CFLAGS "-m64" \
	  -top top \
	  -kdb \
	  +lint=TFIPC-L \
	  +vcs+lic+wait \
	  +vcs+initreg+random \
	  +overlap \
	  +v2k \
	  +memcbk \
	  -cm_seqnoconst \
	  -l vcs.log \
	  $(VCSARGS) \
	  $(DESIGNARGS)

# -------------------------------------------------------------------
# RTL
# -------------------------------------------------------------------
.PHONY: rtl
rtl: export GARNET_HOME := $(current_dir)/..
rtl: export PYTHONPATH = $(GARNET_HOME):$$PYTHONPATH
rtl: 
	python global_buffer_main.py -r -v -p
	$(FIX_SYSTEMRDL)
	cat systemRDL/output/glb_pio.sv >> global_buffer.sv
	cat systemRDL/output/glb_jrdl_decode.sv >> global_buffer.sv
	cat systemRDL/output/glb_jrdl_logic.sv >> global_buffer.sv

# -------------------------------------------------------------------
# Compile & Run
# -------------------------------------------------------------------
.PHONY: compile
compile: XRUNARGS+= -notimingchecks
compile: VCSARGS+= +nospecify
compile: DESIGNARGS += header/global_buffer_param.svh header/glb.svh -F sim/tb_global_buffer.f global_buffer.sv
compile:
	$(GENERATE_TV); 
	$(VCS)

.PHONY: run
run: compile
	./simv $(RUNARGS)

.PHONY: dump
dump: compile
	./simv -ucli -i top-ucli.tcl $(RUNARGS)

# -------------------------------------------------------------------
# GLS Compile & Run
# -------------------------------------------------------------------
# .PHONY: compile-gl
# compile-gl: DESIGNARGS += \
# 	$(RTL_DIR)/global_buffer_param.svh \
# 	$(RTL_DIR)/global_buffer_pkg.svh \
# 	-F $(TB_DIR)/tb_$(TOP_MODULE).filelist \
# 	-F netlist/netlist.filelist
# # compile-gl: XRUNARGS += +define+PWR
# compile-gl: XRUNARGS += +define+NON_STOP_IF_INPUT_Z
# compile-gl: XRUNARGS += +define+PNR +define+TSMC_CM_NO_WARNING
# compile-gl: XRUNARGS += +define+TSMC_CM_UNIT_DELAY
# compile-gl: XRUNARGS += +define+TSMC_INITIALIZE_MEM_USING_DEFAULT_TASKS +define+TSMC_MEM_LOAD_0
# compile-gl: XRUNARGS += -negdelay
# compile-gl: XRUNARGS += -sdf_cmd_file netlist/sdf_cmd.cmd
# compile-gl: XRUNARGS += -sdfstats sdf_stats.txt -sdf_verbose -xminitialize 0 -xminit_log init.log
# compile-gl:
# 	$(XRUN)

.PHONY: clean
clean:
	rm -rf xrun.log xrun.history xcelium.d simv simv.daidir csrc vcs.log
