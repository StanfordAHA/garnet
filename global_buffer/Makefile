#!/bin/bash
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(abspath $(dir $(mkfile_path)))

# -------------------------------------------------------------------
# Parameters
# -------------------------------------------------------------------
TOOL ?= XCELIUM
CGRA_WIDTH ?= 4
NUM_GLB_TILES ?= $(shell expr $(CGRA_WIDTH) / 2 )
GLB_TILE_MEM_SIZE ?= 256

RUNTIME_ARGS += +TEST_GLB_MEM_SIMPLE
RUNTIME_ARGS += +TEST_GLB_CFG
RUNTIME_ARGS += +TEST_GLB_G2F_STREAM
RUNTIME_ARGS += +TEST_GLB_F2G_STREAM
RUNTIME_ARGS += +TEST_PCFG_STREAM

HEADER_FILES ?= header/global_buffer_param.svh header/glb.svh 
DESIGN_FILES ?= global_buffer.sv systemRDL/output/glb_pio.sv systemRDL/output/glb_jrdl_decode.sv systemRDL/output/glb_jrdl_logic.sv
NETLIST_FILES ?= netlist/glb.vcs.v netlist/glb_tile.vcs.v netlist/glb_tile_sram.v netlist/stdcells.v netlist/stdcells-pm.v
#FIXME: pm cells should be removed!
TB_FILES ?= -F sim/tb_global_buffer.f 

# -------------------------------------------------------------------
# Commands
# -------------------------------------------------------------------

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
	   +access+rwc \
	   -covoverwrite \
	   -elaborate \
	   -top top \
	   -timescale 100ps/1ps \
	   -unbuffered \
	   -svseed random \
	   $(COMPILE_ARGS) \
	   $(INPUT_ARGS)

VCS = vcs \
	  -debug_accss+all \
	  -sverilog \
	  -timescale=100ps/1ps \
	  -full64 \
	  -ldflags "-Wl,--no-as-needed" \
	  -CFLAGS "-m64" \
	  -top top \
	  -kdb \
	  +vpi \
	  +memcbk \
	  +vcsd \
	  +lint=TFIPC-L \
	  +vcs+lic+wait \
	  +vcs+initreg+random \
	  +overlap \
	  +v2k \
	  -l vcs.log \
	  $(COMPILE_ARGS) \
	  $(INPUT_ARGS)

# -------------------------------------------------------------------
# RTL
# -------------------------------------------------------------------
.PHONY: rtl
rtl: export GARNET_HOME := $(current_dir)/..
rtl: export PYTHONPATH = $(GARNET_HOME):$$PYTHONPATH
rtl: 
	python global_buffer_main.py -r -v -p --num_cgra_cols=$(CGRA_WIDTH) --num_glb_tiles=$(NUM_GLB_TILES) --glb_tile_mem_size=$(GLB_TILE_MEM_SIZE)
	$(FIX_SYSTEMRDL)

# -------------------------------------------------------------------
# Compile & Run
# -------------------------------------------------------------------

ifeq ($(TOOL), XCELIUM)
    COMPILE = $(XRUN)
    RUN = xrun -R
    DUMP_ARGS = -input dump_shm.tcl
else ifeq ($(TOOL), VCS)
    COMPILE = $(VCS)
    RUN = ./simv
    DUMP_ARGS = -ucli -i dump_fsdb.tcl
else
    @echo "TOOL must be either XCELIUM or VCS"
endif

.PHONY: compile
compile: COMPILE_ARGS += +nospecify
compile: INPUT_ARGS = $(HEADER_FILES) $(DESIGN_FILES) $(TB_FILES)
compile:
	$(COMPILE)

.PHONY: run
run:
	$(RUN) $(RUNTIME_ARGS)

.PHONY: sim
sim: compile
	$(RUN) $(RUNTIME_ARGS)

.PHONY: dump
dump:
	$(RUN) $(DUMP_ARGS) $(RUNTIME_ARGS)

# -------------------------------------------------------------------
# GLS Compile & Run
# -------------------------------------------------------------------
.PHONY: compile-gl
compile-gl: COMPILE_ARGS += +define+NON_STOP_IF_INPUT_Z
compile-gl: COMPILE_ARGS += +define+TSMC_CM_NO_WARNING
compile-gl: COMPILE_ARGS += +define+TSMC_CM_UNIT_DELAY
compile-gl: COMPILE_ARGS += +define+TSMC_INITIALIZE_MEM_USING_DEFAULT_TASKS
compile-gl: COMPILE_ARGS += +define+TSMC_MEM_LOAD_0
compile-gl: COMPILE_ARGS += -negdelay
compile-gl: COMPILE_ARGS += -ALLOWREDEFINITION
# compile-gl: VCS_ARGS += -sdf_cmd_file netlist/sdf_cmd.cmd
# compile-gl: XRUN_ARGS += -sdfstats sdf_stats.txt -sdf_verbose -xminitialize 0 -xminit_log init.log
compile-gl: INPUT_ARGS = $(HEADER_FILES) $(NETLIST_FILES) $(TB_FILES)
compile-gl:
	$(COMPILE)

.PHONY: clean
clean:
	rm -rf xrun.log xrun.history xcelium.d simv simv.daidir csrc vcs.log timestamp global_buffer.shm global_buffer.fsdb
