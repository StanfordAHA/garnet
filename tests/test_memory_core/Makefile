#!/bin/bash

# -------------------------------------------------------------------
# Variables
# -------------------------------------------------------------------
# mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
# mkfile_dir := $(dir $(mkfile_path))
garnet_dir := $(mkfile_dir)/../..
# gemstone_dir := $(realpath $(garnet_dir))/../gemstone
# netlist_dir := $(mkfile_dir)/netlist
# glc_dir := $(garnet_dir)/global_controller
# APP_ARGS ?= +APP0=app0

TOOL ?= XCELIUM
export WAVEFORM ?= 0
export BITSTREAM_SIZE ?= 0
# export WAVEFORM_GLB_ONLY ?= 0
# export SAIF ?= 0

# -------------------------------------------------------------------
# Compile Parameters
# -------------------------------------------------------------------
CLK_PERIOD ?= 1ns

DESIGN_FILES += sparse_tb.sv \
				SparseTBBuilder.v \
				CW_fp_add.v \
				CW_fp_mult.v \
				AN_CELL.sv \
				AO_CELL.sv \
				glb_read.sv \
				glb_write.sv \
				PE.v

# cfg_and_dbg_unq1.sv
# glc_jtag_ctrl.sv
# flop_unq3.sv
# glc_axi_ctrl.sv
# flop_unq2.sv
# flop_unq1.sv
# global_controller.sv 
# jtag.sv
# tap_unq1.sv
# glc_axi_addrmap.sv

# TB_FILES += -F tb/tb_cgra.f

# IP_FILES += -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/ \
# 			-y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CWTECH/ \
# 			+libext+.v+.sv 

# -------------------------------------------------------------------
# GLS Parameters
# -------------------------------------------------------------------
# GLB_TOP ?= glb_top
# GLB_TILE ?= glb_tile
# TILE_ARRAY ?= tile_array
# TILE_PE ?= Tile_PE
# TILE_MEM ?= Tile_MemCore
# NETLIST_FILES ?= -v $(garnet_dir)/garnet.v -v $(netlist_dir)/glb_top.vcs.v -v $(netlist_dir)/glb_tile.vcs.v \
# 				 -v $(netlist_dir)/global_controller.vcs.v -v $(netlist_dir)/tile_array.vcs.v -v $(netlist_dir)/Tile_PE.vcs.v -v $(netlist_dir)/Tile_MemCore.vcs.v \
# 				 -v $(netlist_dir)/sram.v -v $(netlist_dir)/tile_array.sram.v -v $(netlist_dir)/stdcells.v -v $(netlist_dir)/stdcells-lvt.v -v $(netlist_dir)/stdcells-ulvt.v -v $(netlist_dir)/stdcells-pm.v

# -------------------------------------------------------------------
# Run Parameters
# -------------------------------------------------------------------
# RUN_ARGS ?=
# RUN_LOG ?= run.log

# -------------------------------------------------------------------
# Command
# -------------------------------------------------------------------
# VCS = vcs \
# 	  -debug_accss+all \
# 	  -sverilog \
# 	  -timescale=100ps/1ps \
# 	  -full64 \
# 	  -ldflags "-Wl,--no-as-needed" \
# 	  -CFLAGS "-m64" \
# 	  -top top \
# 	  -kdb \
# 	  +vpi \
# 	  +memcbk \
# 	  +vcsd \
# 	  +vcs+lic+wait \
# 	  +vcs+initreg+random \
# 	  +overlap \
# 	  +v2k \
# 	  -l vcs.log \
# 	  $(COMPILE_ARGS) \
# 	  $(INPUT_ARGS)

XRUN = xrun \
	   -64bit \
	   -sv \
	   -timescale 1ns/1ns \
	   -debug \
	   -sysv \
	   -top SparseTBBuilder_tb \
	   -elaborate \
	   -l xrun.log \
	   -covoverwrite \
	   +maxdelays \
	   -access r \
	   -notimingchecks \
	   $(COMPILE_ARGS) \
	   $(INPUT_ARGS)

#    -initmem0 
#    -initreg0 
# -------------------------------------------------------------------
# C API
# -------------------------------------------------------------------
# .PHONY: libcgra.so
# libcgra.so: $(shell find lib -type f) $(garnet_dir)/global_buffer/header/global_buffer_param.h $(garnet_dir)/global_buffer/header/glb.h $(garnet_dir)/global_controller/header/glc.h
# 	gcc -Wno-error -Wall lib/*.c -I$(garnet_dir)/global_buffer/header -I$(garnet_dir)/global_controller/header -shared -o libcgra.so -fPIC

# -------------------------------------------------------------------
# Compile & Run
# -------------------------------------------------------------------
COMPILE_RTL_ARGS += +define+CLK_PERIOD=$(CLK_PERIOD)
COMPILE_GLS_ARGS += +define+CLK_PERIOD=$(CLK_PERIOD)
ifeq ($(TOOL), XCELIUM)
    COMPILE = $(XRUN)
    # COMPILE_RTL_ARGS += -xminitialize 0 -xminit_log init.log -nospecify
    # COMPILE_GLS_ARGS += -xminitialize 0 -xminit_log init.log
    # COMPILE_GLS_ARGS += -ALLOWREDEFINITION
    # RUN = xrun -R -l $(RUN_LOG) -sv_lib libcgra.so
    RUN = xrun -R
# else ifeq ($(TOOL), VCS)
#     COMPILE = $(VCS)
#     COMPILE_RTL_ARGS += +nospecify
#     RUN = ./simv -lca -l $(RUN_LOG) +vcs+initmem+0 +vcs+initreg+0 -sv_lib libcgra -exitstatus
else
    @echo "TOOL must be XCELIUM"
endif

ifeq ($(TOOL), XCELIUM)
# DUMP_ARGS = -input dump_shm.tcl
	DUMP_ARGS = -input run_sim.tcl
else ifeq ($(TOOL), VCS)
	DUMP_ARGS = -ucli -i dump_fsdb.tcl
endif

TEST_DIR?=/home/max/Documents/SPARSE/garnet/VEC_IDENTITY/
COMPARISON_SCRIPT?=/home/max/Documents/SPARSE/garnet/tests/test_memory_core/build_tb.py
UNROLL?=1

.PHONY: compile
compile: COMPILE_ARGS = $(COMPILE_RTL_ARGS)
compile: INPUT_ARGS = $(DESIGN_FILES) $(TB_FILES) $(IP_FILES)
compile:
	$(COMPILE)

.PHONY: run
run: TEST_ARGS = $(TEST_DIR)/COLLAT_DIR/PARGS.txt
run: TMP_PARGS = $(shell cat $(TEST_ARGS))
run:
# $(RUN) $(DUMP_ARGS) $(RUN_ARGS) $(APP_ARGS)
	rm -f $(TEST_DIR)/OUTPUT_DIR/*
	$(RUN) $(DUMP_ARGS) $(TMP_PARGS)
	python $(COMPARISON_SCRIPT) --do_comparison --gold_mat_dir=$(TEST_DIR)/GLB_DIR --sim_mat_dir=$(TEST_DIR)/OUTPUT_DIR/ --unroll $(UNROLL)

.PHONY: sim
# sim: libcgra.so compile run
sim: compile run

# -------------------------------------------------------------------
# GLS Compile
# -------------------------------------------------------------------
# compile testbench of garnet with xcelium
.PHONY: compile-gls
compile-gls: COMPILE_GLS_ARGS += +define+NON_STOP_IF_INPUT_Z
compile-gls: COMPILE_GLS_ARGS += +define+TSMC_CM_NO_WARNING
compile-gls: COMPILE_GLS_ARGS += +define+TSMC_CM_UNIT_DELAY
compile-gls: COMPILE_GLS_ARGS += +define+TSMC_INITIALIZE_MEM_USING_DEFAULT_TASKS
compile-gls: COMPILE_GLS_ARGS += +define+TSMC_MEM_LOAD_0
compile-gls: COMPILE_GLS_ARGS += -negdelay
compile-gls: COMPILE_ARGS = $(COMPILE_GLS_ARGS)
compile-gls: INPUT_ARGS = $(NETLIST_FILES) $(TB_FILES) $(IP_FILES)
compile-gls:
	@rm -rf $(SDF_LOG); mkdir $(SDF_LOG)
	$(COMPILE)


# -------------------------------------------------------------------
# Clean
# -------------------------------------------------------------------
.PHONY: clean
clean:
	rm -rf xrun.log xrun.history xcelium.d simv simv.daidir csrc vcs.log cgra.shm cgra.fsdb sdf_stats.txt sdf_logs