#!/bin/bash

# -------------------------------------------------------------------
# Variables
# -------------------------------------------------------------------
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
mkfile_dir := $(dir $(mkfile_path))
garnet_dir := $(mkfile_dir)/../..
netlist_dir := $(mkfile_dir)/netlist
glc_dir := $(garnet_dir)/global_controller

# New
APP_ARGS ?= +APP0=/home/mcoduoza/pointwise

# New
#TODO: Figure out how to set these
# ARM_IP_PATH					:= $(abspath $(ARM_IP_DIR))
AHA_IP_PATH					:= $(abspath $(AHA_IP_DIR))
# TOP_DIR 					:= $(abspath $(TOP_DIR))

AHA_IP_PATH ?= /nsim/mcoduoza/aham3soc/aham3soc


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
				-v $(garnet_dir)/tests/SC7P5T_AN2X0P5_SSC14R.sv -v $(garnet_dir)/tests/SC7P5T_AN2X0P5_SSC14R.sv \
				$(garnet_dir)/genesis_verif/*.sv

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
#				$(garnet_dir)/garnet.v 
# 				$(netlist_dir)/glb_top.vcs.v \
# 				$(netlist_dir)/glb_tile.vcs.v \
# 				$(netlist_dir)/global_controller.vcs.v \
# 				$(netlist_dir)/tile_array.vcs.v \
# 				$(netlist_dir)/Tile_PE.vcs.v \
# 			       	$(netlist_dir)/Tile_MemCore.vcs.v \
# 				$(netlist_dir)/Tile_MemCore.sram.v \
# 				$(netlist_dir)/tile_array.sram.v \
# 			       	$(netlist_dir)/stdcells.v \
# 			       	$(netlist_dir)/stdcells-lvt.v \
# 				$(netlist_dir)/stdcells-ulvt.v \
# 				$(netlist_dir)/stdcells-pm.v

# New
#/nsim/mcoduoza/glc_containing_design.v 
NETLIST_FILES +=  /nsim/pohan/garnet_build/1203/31-cadence-innovus-signoff/outputs/design.vcs.pg.v \
/nsim/pohan/garnet_build/1203/15-glb_top/25-cadence-innovus-signoff/outputs/design.vcs.pg.v \
/nsim/pohan/garnet_build/1203/15-glb_top/7-glb_tile/outputs/glb_tile.vcs.pg.v \
/nsim/pohan/garnet_build/1203/17-tile_array/outputs/tile_array.vcs.pg.v \
/nsim/pohan/garnet_build/1130/17-tile_array/14-Tile_PE/26-cadence-innovus-signoff/outputs/design.vcs.pg.v \
/nsim/pohan/garnet_build/1130/17-tile_array/13-Tile_MemCore/26-cadence-innovus-signoff/outputs/design.vcs.pg.v
#
# New
SRAM_FILES += /nsim/mcoduoza/Memory_Behavior_Models_for_GL/macro_4096x64b.sv \
/nsim/mcoduoza/Memory_Behavior_Models_for_GL/macro_512x32b.sv \
/nsim/mcoduoza/Memory_Behavior_Models_for_GL/macro_8192x32b.sv 

# New
STANDARD_CELLS += /nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-ldrseq-lplvt/stdcells-ldrseq-lplvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-spcl-nom/stdcells-spcl-nom.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supclk-nom/stdcells-supclk-nom.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-ldrseq-ulvt/stdcells-ldrseq-ulvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-suppwm-hp/stdcells-suppwm-hp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-seq-lvt/stdcells-seq-lvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-spcl-lvt/stdcells-spcl-lvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-clk-hp/stdcells-clk-hp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-dsclk1-hp/stdcells-dsclk1-hp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-seq-lp/stdcells-seq-lp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-base-hp/stdcells-base-hp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-ldrseq-lp/stdcells-ldrseq-lp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supclk-lvt/stdcells-supclk-lvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-suppwm-ulp/stdcells-suppwm-ulp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supseq-ulvt/stdcells-supseq-ulvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-dsclk1-ulp/stdcells-dsclk1-ulp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supbase-ulp/stdcells-supbase-ulp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-spcl-lp/stdcells-spcl-lp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-seq-nom/stdcells-seq-nom.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-ldrsupseq-lp/stdcells-ldrsupseq-lp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supbase-lplvt/stdcells-supbase-lplvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-spcl-ulp/stdcells-spcl-ulp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-pwm-lplvt/stdcells-pwm-lplvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-ldrsupseq-lplvt/stdcells-ldrsupseq-lplvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supclk-lplvt/stdcells-supclk-lplvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supbase-lp/stdcells-supbase-lp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-pwm-lp/stdcells-pwm-lp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supclk-ulp/stdcells-supclk-ulp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-suppwm-lvt/stdcells-suppwm-lvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-dsclk1-lvt/stdcells-dsclk1-lvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supbase-lvt/stdcells-supbase-lvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supseq-lplvt/stdcells-supseq-lplvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-dsclk1-ulvt/stdcells-dsclk1-ulvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-base-ulvt/stdcells-base-ulvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-clk-ulvt/stdcells-clk-ulvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-suppwm-nom/stdcells-suppwm-nom.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-dsclk1-nom/stdcells-dsclk1-nom.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-suppwm-ulvt/stdcells-suppwm-ulvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supbase-nom/stdcells-supbase-nom.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supseq-hp/stdcells-supseq-hp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-seq-ulp/stdcells-seq-ulp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supclk-lp/stdcells-supclk-lp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-ldrsupseq-hp/stdcells-ldrsupseq-hp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-ldrseq-nom/stdcells-ldrseq-nom.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supclk-ulvt/stdcells-supclk-ulvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supbase-hp/stdcells-supbase-hp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-pwm-hp/stdcells-pwm-hp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-clk-lvt/stdcells-clk-lvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-pwm-ulp/stdcells-pwm-ulp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-pwm-ulvt/stdcells-pwm-ulvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-spcl-ulvt/stdcells-spcl-ulvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-base-nom/stdcells-base-nom.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-dsclk1-lplvt/stdcells-dsclk1-lplvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-ldrsupseq-ulp/stdcells-ldrsupseq-ulp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supseq-nom/stdcells-supseq-nom.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-spcl-lplvt/stdcells-spcl-lplvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-ldrseq-lvt/stdcells-ldrseq-lvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-clk-nom/stdcells-clk-nom.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-ldrsupseq-ulvt/stdcells-ldrsupseq-ulvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-base-lvt/stdcells-base-lvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supseq-lvt/stdcells-supseq-lvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supseq-lp/stdcells-supseq-lp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supclk-hp/stdcells-supclk-hp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-ldrseq-ulp/stdcells-ldrseq-ulp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-base-lplvt/stdcells-base-lplvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-pwm-nom/stdcells-pwm-nom.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-base-ulp/stdcells-base-ulp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-ldrsupseq-nom/stdcells-ldrsupseq-nom.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-suppwm-lp/stdcells-suppwm-lp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-seq-ulvt/stdcells-seq-ulvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supseq-ulp/stdcells-supseq-ulp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-clk-lp/stdcells-clk-lp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-seq-hp/stdcells-seq-hp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-dsclk1-lp/stdcells-dsclk1-lp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-suppwm-lplvt/stdcells-suppwm-lplvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-ldrseq-hp/stdcells-ldrseq-hp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-clk-lplvt/stdcells-clk-lplvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-base-lp/stdcells-base-lp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-clk-ulp/stdcells-clk-ulp.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-pwm-lvt/stdcells-pwm-lvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-ldrsupseq-lvt/stdcells-ldrsupseq-lvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-seq-lplvt/stdcells-seq-lplvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-supbase-ulvt/stdcells-supbase-ulvt.v \
/nsim/pohan/garnet_build/1203/9-intel16-adk/stdcells-spcl-hp/stdcells-spcl-hp.v \


TAPEOUT_AND_PAD_FRAME_COLLATERALS += /intel16/ip/io/ip224_gpio_1v2/rtl/src/rtl/gpio_1v2_n1.sv \
/intel16/ip/io/ip224_gpio_1v2/rtl/src/rtl/gpio_1v2_e1.sv \
/nsim/pohan/garnet_build/1202/9-intel16-adk/pdk/intel22tic.v

# New
NETLIST_FILES += $(SRAM_FILES)
NETLIST_FILES += $(STANDARD_CELLS)
NETLIST_FILES += $(TAPEOUT_AND_PAD_FRAME_COLLATERALS)

# -------------------------------------------------------------------
# Run Parameters
# -------------------------------------------------------------------
RUN_ARGS ?=
RUN_LOG ?= run.log

# -------------------------------------------------------------------
# Command
# -------------------------------------------------------------------
VCS = vcs \
	  -debug_access+all \
	  -sverilog \
	  -timescale=1ps/1ps \
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
	  -debug_region+cell \
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
    RUN = ./simv -lca -l $(RUN_LOG) +vcs+initmem+0 +vcs+initreg+0 -sv_lib libcgra -exitstatus
	RUN_GLS = ./simv -lca -l $(RUN_LOG) +vcs+initmem+0 +vcs+initreg+0 -sv_lib libcgra
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

# New 
#  COMPILE_GLS_ARGS	+= -y $(AHA_IP_PATH)/hardware/logical/ProcessTech/SRAM/ASIC/INTEL
#  COMPILE_GLS_ARGS	+= -y $(AHA_IP_PATH)/hardware/logical/ProcessTech/StdCells/ASIC/INTEL
 COMPILE_GLS_ARGS	+= -y /home/mcoduoza/AhaM3SoC/hardware/logical/ProcessTech/SRAM/ASIC/INTEL
 COMPILE_GLS_ARGS	+= -y /home/mcoduoza/AhaM3SoC/hardware/logical/ProcessTech/StdCells/ASIC/INTEL
 COMPILE_GLS_ARGS	+= +define+IMPL_GATELEVEL
 COMPILE_GLS_ARGS	+= +define+SDF_ANNOTATION
 COMPILE_GLS_ARGS	+= +csdf+precompile
 COMPILE_GLS_ARGS	+= +overlap
 COMPILE_GLS_ARGS	+= +neg_tchk
# COMPILE_GLS_ARGS	+= -negdelay
 COMPILE_GLS_ARGS	+= +optconfigfile+~/AhaM3SoC/test-soc/compile_design/config.cfg 
 COMPILE_GLS_ARGS	+= +define+INTC_MEM_NOXHANDLING
 # NEW NEW
 COMPILE_GLS_ARGS       += -assert svaext

 # Missing gen_pwr_saif

# compile-gls: COMPILE_GLS_ARGS += +define+TSMC_CM_NO_WARNING
# compile-gls: COMPILE_GLS_ARGS += +define+TSMC_CM_UNIT_DELAY
# compile-gls: COMPILE_GLS_ARGS += +define+TSMC_INITIALIZE_MEM_USING_DEFAULT_TASKS
# compile-gls: COMPILE_GLS_ARGS += +define+TSMC_MEM_LOAD_0
compile-gls: COMPILE_GLS_ARGS += -negdelay
compile-gls: COMPILE_ARGS = $(COMPILE_GLS_ARGS)
compile-gls: INPUT_ARGS = $(NETLIST_FILES) $(TB_FILES) $(IP_FILES)
compile-gls:
	$(COMPILE)

.PHONY: run-gls
run-gls:
	$(RUN_GLS) $(DUMP_ARGS) $(RUN_ARGS) $(APP_ARGS)

.PHONY: sim-gls
sim-gls: libcgra.so compile-gls run-gls 

# -------------------------------------------------------------------
# Clean
# -------------------------------------------------------------------
.PHONY: clean
clean:
	rm -rf xrun.log xrun.history xcelium.d simv simv.daidir csrc vcs.log cgra.shm cgra.fsdb sdf_stats.txt sdf_logs
