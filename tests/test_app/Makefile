#!/bin/bash

# -------------------------------------------------------------------
# Variables
# -------------------------------------------------------------------
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
mkfile_dir := $(dir $(mkfile_path))
garnet_dir := $(mkfile_dir)/../..
glb_dir := $(garnet_dir)/global_buffer
glc_dir := $(garnet_dir)/global_controller

# -------------------------------------------------------------------
# Compile Parameters
# -------------------------------------------------------------------
CGRA_WIDTH ?= 8
AXI_ADDR_WIDTH ?= 13
AXI_DATA_WIDTH ?= 32
GLB_TILE_MEM_SIZE ?= 256
CLK_PERIOD ?= 1.1ns
TOP_NAME ?= top
RTL_FILES ?= -v $(garnet_dir)/garnet.v -v $(glb_dir)/rtl/TS1N16FFCLLSBLVTC2048X64M8SW.sv -v $(garnet_dir)/tests/AN2D0BWP16P90.sv -v $(garnet_dir)/tests/AO22D0BWP16P90.sv \
			 -F $(glb_dir)/rtl/global_buffer.filelist -F $(glc_dir)/global_controller.filelist
COMPILE_ARGS ?= -elaborate

# -------------------------------------------------------------------
# Run Parameters
# -------------------------------------------------------------------
RUN_ARGS ?= 
WAVEFORM ?= False
ifneq (, $(filter $(WAVEFORM), True true))
	VCD_FLAG := +VCD_ON
endif

# -------------------------------------------------------------------
# Command
# -------------------------------------------------------------------
XRUN_COMPILE = xrun \
	   		   -64bit \
	   		   -sv \
	   		   -timescale 100ps/1ps \
	   		   -debug \
	   		   -sysv \
	   		   -l xrun.log \
	   		   -covoverwrite \
	   		   -initmem0 \
	   		   -initreg0 \
	   		   +maxdelays \
	   		   $(XRUN_ARGS) \
	   		   $(COMPILE_ARGS) \
	   		   $(VCD_FLAG)

# -------------------------------------------------------------------
# Simulation
# -------------------------------------------------------------------
.PHONY: sim
sim: glb-rtl glc-rtl libcgra.so compile run

# -------------------------------------------------------------------
# C API
# -------------------------------------------------------------------
libcgra.so: map.c map.h gen.c gen.h parser.c parser.h
	gcc -Wno-error -Wall parser.c map.c gen.c -shared -o libcgra.so -fPIC

# -------------------------------------------------------------------
# RTL
# -------------------------------------------------------------------
.PHONY: glb-rtl glc-rtl
glb-rtl: 
	$(MAKE) -C $(glb_dir) rtl CGRA_WIDTH=$(CGRA_WIDTH)
glc-rtl:
	$(MAKE) -C $(glc_dir) rtl CGRA_WIDTH=$(CGRA_WIDTH)

# -------------------------------------------------------------------
# Compile
# -------------------------------------------------------------------
# compile testbench of garnet with xcelium
.PHONY: compile
compile: XRUN_ARGS += -top $(TOP_NAME)
compile: XRUN_ARGS += +define+CLK_PERIOD=$(CLK_PERIOD)
compile: XRUN_ARGS += +define+CGRA_WIDTH=$(CGRA_WIDTH) +define+AXI_ADDR_WIDTH=$(AXI_ADDR_WIDTH) +define+AXI_DATA_WIDTH=$(AXI_DATA_WIDTH) +define+GLB_TILE_MEM_SIZE=$(GLB_TILE_MEM_SIZE)
compile: XRUN_ARGS += -F tb_garnet.filelist
compile: XRUN_ARGS += -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/ \
				      -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CWTECH/ \
					  +libext+.v+.sv 
compile: XRUN_ARGS += $(RTL_FILES)
compile: libcgra.so top.sv garnet_param.svh garnet_test.sv kernel.sv proc_driver.sv axil_driver.sv axil_ifc.sv proc_ifc.sv environment.sv
	$(XRUN_COMPILE)

# -------------------------------------------------------------------
# Run
# -------------------------------------------------------------------
.PHONY: run
run:
	xrun -R -sv_lib libcgra.so $(RUN_ARGS) $(APP_ARGS)

# -------------------------------------------------------------------
# Clean
# -------------------------------------------------------------------
.PHONY: clean
clean:
	rm -rf xrun.log xrun.history xcelium.d
