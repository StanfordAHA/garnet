#!/bin/bash
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(abspath $(dir $(mkfile_path)))

# -------------------------------------------------------------------
# Parameters
# -------------------------------------------------------------------
CLK_PERIOD ?= 800ps
CGRA_WIDTH ?= 4
NUM_GLB_TILES ?= $(shell expr $(CGRA_WIDTH) / 2 )
GLB_TILE_MEM_SIZE ?= 256

TOOL ?= XCELIUM

# GLS 
SDF ?= 0
MTM ?= MAXIMUM
SDF_CMD_FILE ?= sdf_cmd.cmd
SDF_LOG ?= sdf_logs
GLB_TOP_SDF ?= gls/glb.sdf
GLB_TILE_SDF ?= gls/glb_tile.sdf

RUNTIME_ARGS += +TEST_GLB_MEM_SIMPLE
RUNTIME_ARGS += +TEST_GLB_CFG
RUNTIME_ARGS += +TEST_GLB_G2F_STREAM
RUNTIME_ARGS += +TEST_GLB_F2G_STREAM
RUNTIME_ARGS += +TEST_PCFG_STREAM

HEADER_FILES ?= header/global_buffer_param.svh header/glb.svh 
DESIGN_FILES ?= global_buffer.sv systemRDL/output/glb_pio.sv systemRDL/output/glb_jrdl_decode.sv systemRDL/output/glb_jrdl_logic.sv
NETLIST_FILES ?= gls/glb.vcs.v gls/glb_tile.vcs.v gls/glb_tile_sram.v gls/stdcells.v gls/stdcells-pm.v
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

GEN_SDF_CMD = python gls/gen_sdf_cmd.py \
              -f $(SDF_CMD_FILE) -n $(NUM_GLB_TILES) --top $(GLB_TOP_SDF) --tile $(GLB_TILE_SDF) -l $(SDF_LOG) -t $(MTM)

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

COMPILE_RTL_ARGS += +define+CLK_PERIOD=$(CLK_PERIOD)
COMPILE_GLS_ARGS += +define+CLK_PERIOD=$(CLK_PERIOD)
ifeq ($(TOOL), XCELIUM)
    COMPILE = $(XRUN)
    COMPILE_RTL_ARGS += -xminitialize 0 -xminit_log init.log -nospecify
    RUN = xrun -R
    DUMP_ARGS = -input dump_shm.tcl
else ifeq ($(TOOL), VCS)
    COMPILE = $(VCS)
    COMPILE_RTL_ARGS += +nospecify
    RUN = ./simv
    DUMP_ARGS = -ucli -i dump_fsdb.tcl
else
    @echo "TOOL must be either XCELIUM or VCS"
endif

ifneq ($(SDF), 0)
    SDF_ARGS += -sdf_cmd_file $(SDF_CMD_FILE)
    SDF_ARGS += -sdfstats sdf_stats.txt -sdf_verbose
    COMPILE_GLS_ARGS += $(SDF_ARGS)
endif

.PHONY: compile
compile: COMPILE_ARGS = $(COMPILE_RTL_ARGS)
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
.PHONY: compile-gls
compile-gls: COMPILE_GLS_ARGS += +define+NON_STOP_IF_INPUT_Z
compile-gls: COMPILE_GLS_ARGS += +define+TSMC_CM_NO_WARNING
compile-gls: COMPILE_GLS_ARGS += +define+TSMC_CM_UNIT_DELAY
compile-gls: COMPILE_GLS_ARGS += +define+TSMC_INITIALIZE_MEM_USING_DEFAULT_TASKS
compile-gls: COMPILE_GLS_ARGS += +define+TSMC_MEM_LOAD_0
compile-gls: COMPILE_GLS_ARGS += -negdelay
compile-gls: COMPILE_GLS_ARGS += -ALLOWREDEFINITION
compile-gls: COMPILE_GLS_ARGS += -xminitialize 0 -xminit_log init.log
compile-gls: COMPILE_ARGS = $(COMPILE_GLS_ARGS)
compile-gls: INPUT_ARGS = $(HEADER_FILES) $(NETLIST_FILES) $(TB_FILES)
compile-gls:
	@rm -rf $(SDF_LOG); mkdir $(SDF_LOG)
	@if [ $(SDF) != 0 ]; then $(GEN_SDF_CMD); fi
	$(COMPILE)

.PHONY: clean
clean:
	rm -rf xrun.log xrun.history xcelium.d simv simv.daidir csrc vcs.log timestamp global_buffer.shm global_buffer.fsdb sdf_stats.txt sdf_logs
