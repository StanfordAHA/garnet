#!/bin/bash

# -------------------------------------------------------------------
# Variables
# -------------------------------------------------------------------
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
mkfile_dir := $(dir $(mkfile_path))
garnet_dir := $(mkfile_dir)/../..
netlist_dir := $(mkfile_dir)/netlist
glc_dir := $(garnet_dir)/global_controller
APP_ARGS ?= +APP0=app0

TOOL ?= VCS
export WAVEFORM ?= 0
export WAVEFORM_GLB_ONLY ?= 0
export SAIF ?= 0

# -------------------------------------------------------------------
# Compile Parameters
# -------------------------------------------------------------------
CLK_PERIOD ?= 1ns

DESIGN_FILES += $(garnet_dir)/global_buffer/header/global_buffer_param.svh \
				$(garnet_dir)/global_buffer/header/glb.svh \
				$(garnet_dir)/global_controller/header/glc.svh \
				$(garnet_dir)/garnet.v \
				$(garnet_dir)/global_buffer/systemRDL/output/glb_pio.sv \
				$(garnet_dir)/global_buffer/systemRDL/output/glb_jrdl_decode.sv \
				$(garnet_dir)/global_buffer/systemRDL/output/glb_jrdl_logic.sv \
				$(garnet_dir)/global_controller/systemRDL/output/glc_pio.sv \
				$(garnet_dir)/global_controller/systemRDL/output/glc_jrdl_decode.sv \
				$(garnet_dir)/global_controller/systemRDL/output/glc_jrdl_logic.sv \
				-v $(garnet_dir)/tests/SC7P5T_AN2X0P5_SSC14R.sv -v $(garnet_dir)/tests/SC7P5T_AO22X0P5_SSC14R.sv \
				$(garnet_dir)/genesis_verif/*.sv \
				$(garnet_dir)/glb_sram.v \
				$(garnet_dir)/tile_array_sram.v

TB_FILES += -F tb/tb_cgra.f

IP_FILES += -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/ \
			-y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CWTECH/ \
			+libext+.v+.sv 

# -------------------------------------------------------------------
# GLS Parameters
# -------------------------------------------------------------------
GLB_TOP ?= glb_top
GLB_TILE ?= glb_tile
TILE_ARRAY ?= tile_array
TILE_PE ?= Tile_PE
TILE_MEM ?= Tile_MemCore
NETLIST_FILES += $(garnet_dir)/global_buffer/header/global_buffer_param.svh \
				$(garnet_dir)/global_buffer/header/glb.svh \
				$(garnet_dir)/global_controller/header/glc.svh \
                                $(garnet_dir)/garnet.v \
				$(netlist_dir)/glb_top.vcs.v \
				$(netlist_dir)/glb_tile.vcs.v \
				$(netlist_dir)/global_controller.vcs.v \
				$(netlist_dir)/tile_array.vcs.v \
				$(netlist_dir)/Tile_PE.vcs.v \
			       	$(netlist_dir)/Tile_MemCore.vcs.v \
				$(netlist_dir)/Tile_MemCore.sram.v \
				$(netlist_dir)/tile_array.sram.v \
			       	$(netlist_dir)/stdcells.v \
			       	$(netlist_dir)/stdcells-lvt.v \
				$(netlist_dir)/stdcells-ulvt.v \
				$(netlist_dir)/stdcells-pm.v \
				$(netlist_dir)/stdcells-prim.v

# -------------------------------------------------------------------
# Run Parameters
# -------------------------------------------------------------------
RUN_ARGS ?=
RUN_LOG ?= run.log

# -------------------------------------------------------------------
# Command
# -------------------------------------------------------------------
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
	  +vcs+lic+wait \
	  +vcs+initreg+random \
	  +overlap \
	  +v2k \
	  -l vcs.log \
	  $(COMPILE_ARGS) \
	  $(INPUT_ARGS)

XRUN = xrun \
	   -64bit \
	   -sv \
	   -timescale 100ps/1ps \
	   -debug \
	   -sysv \
	   -top top \
	   -elaborate \
	   -l xrun.log \
	   -covoverwrite \
	   -initmem0 \
	   -initreg0 \
	   +maxdelays \
	   $(COMPILE_ARGS) \
	   $(INPUT_ARGS)

# -------------------------------------------------------------------
# C API
# -------------------------------------------------------------------
.PHONY: libcgra.so
libcgra.so: $(shell find lib -type f) $(garnet_dir)/global_buffer/header/global_buffer_param.h $(garnet_dir)/global_buffer/header/glb.h $(garnet_dir)/global_controller/header/glc.h
	gcc -Wno-error -Wall lib/*.c -I$(garnet_dir)/global_buffer/header -I$(garnet_dir)/global_controller/header -shared -o libcgra.so -fPIC

# -------------------------------------------------------------------
# Compile & Run
# ------------------------------------------------------------------
# GLS throws an error, remove exit status
COMPILE_RTL_ARGS += +define+CLK_PERIOD=$(CLK_PERIOD)
COMPILE_GLS_ARGS += +define+CLK_PERIOD=$(CLK_PERIOD)
ifeq ($(TOOL), XCELIUM)
    COMPILE = $(XRUN)
    COMPILE_RTL_ARGS += -xminitialize 0 -xminit_log init.log -nospecify
    COMPILE_GLS_ARGS += -xminitialize 0 -xminit_log init.log
    COMPILE_GLS_ARGS += -ALLOWREDEFINITION
    RUN = xrun -R -l $(RUN_LOG) -sv_lib libcgra.so
else ifeq ($(TOOL), VCS)
    COMPILE = $(VCS)
    COMPILE_RTL_ARGS += +nospecify
    COMPILE_GLS_ARGS += +define+SAIF=1
    COMPILE_GLS_ARGS += +define+IVCS_CYCLE_SIM
    COMPILE_GLS_ARGS += +notimingcheck
    COMPILE_RTL_ARGS += +define+IVCS_CYCLE_SIM
    RUN = ./simv -lca -l $(RUN_LOG) +vcs+initmem+0 +vcs+initreg+0 +notimingcheck -sv_lib libcgra -exitstatus
	RUN_GLS = ./simv -lca -l $(RUN_LOG) +vcs+initmem+0 +vcs+initreg+0 +notimingcheck -sv_lib libcgra 
else
    @echo "TOOL must be either XCELIUM or VCS"
endif

ifeq ($(TOOL), XCELIUM)
	DUMP_ARGS = -input dump_shm.tcl
else ifeq ($(TOOL), VCS)
	DUMP_ARGS = -ucli -i dump_fsdb.tcl
endif


.PHONY: compile
compile: COMPILE_ARGS = $(COMPILE_RTL_ARGS)
compile: INPUT_ARGS = $(DESIGN_FILES) $(TB_FILES) $(IP_FILES)
compile:
	$(COMPILE)

.PHONY: run
run:
	$(RUN) $(DUMP_ARGS) $(RUN_ARGS) $(APP_ARGS)

.PHONY: sim
sim: libcgra.so compile run

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
	$(COMPILE)

.PHONY: run-gls
run-gls:
	$(RUN_GLS) $(RUN_ARGS) $(APP_ARGS) $(DUMP_ARGS)

.PHONY: sim-gls
sim-gls: libcgra.so compile-gls run-gls 

# -------------------------------------------------------------------
# Clean
# -------------------------------------------------------------------
.PHONY: clean
clean:
	rm -rf xrun.log xrun.history xcelium.d simv simv.daidir csrc vcs.log cgra.shm cgra.fsdb sdf_stats.txt sdf_logs
