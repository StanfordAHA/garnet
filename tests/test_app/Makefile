#!/bin/bash

# -------------------------------------------------------------------
# Variables
# -------------------------------------------------------------------
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
mkfile_dir := $(dir $(mkfile_path))
garnet_dir := $(mkfile_dir)/../..
netlist_dir := $(mkfile_dir)/netlist
glb_dir := $(garnet_dir)/global_buffer
glc_dir := $(garnet_dir)/global_controller
APP_ARGS ?= +APP0=app0

# -------------------------------------------------------------------
# Compile Parameters
# -------------------------------------------------------------------
CGRA_WIDTH ?= 32
AXI_ADDR_WIDTH ?= 13
AXI_DATA_WIDTH ?= 32
GLB_TILE_MEM_SIZE ?= 256
CLK_PERIOD ?= 1.1ns
TOP_NAME ?= top
RTL_FILES ?= -v $(garnet_dir)/garnet.v -v $(glb_dir)/rtl/TS1N16FFCLLSBLVTC2048X64M8SW.sv -v $(garnet_dir)/tests/AN2D0BWP16P90.sv -v $(garnet_dir)/tests/AO22D0BWP16P90.sv \
			 -F $(glb_dir)/rtl/global_buffer.filelist -F $(glc_dir)/global_controller.filelist
# RTL_FILES ?= -v /home/kongty/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/VERILOG/ts1n16ffcllsblvtc2048x64m8sw_130a.v -v /home/kongty/mc/ts1n16ffcllsblvtc512x32m4s_130a/VERILOG/ts1n16ffcllsblvtc512x32m4s_130a.v -v $(garnet_dir)/virtual_conv33_harris/18-rtl/outputs/design.v -v $(garnet_dir)/tests/AN2D0BWP16P90.sv -v $(garnet_dir)/tests/AO22D0BWP16P90.sv
COMPILE_ARGS ?= -elaborate

# -------------------------------------------------------------------
# GLS Parameters
# -------------------------------------------------------------------
GLB_TOP ?= glb_top
GLB_TILE ?= glb_tile
TILE_ARRAY ?= tile_array
TILE_PE ?= Tile_PE
TILE_MEM ?= Tile_MemCore
NETLIST_FILES ?= -v $(garnet_dir)/garnet.v -v $(netlist_dir)/glb_top.vcs.v -v $(netlist_dir)/glb_tile.vcs.v \
				 -v $(netlist_dir)/global_controller.vcs.v -v $(netlist_dir)/tile_array.vcs.v -v $(netlist_dir)/Tile_PE.vcs.v -v $(netlist_dir)/Tile_MemCore.vcs.v \
				 -v $(netlist_dir)/sram.v -v $(netlist_dir)/tile_array.sram.v -v $(netlist_dir)/stdcells.v -v $(netlist_dir)/stdcells-lvt.v -v $(netlist_dir)/stdcells-ulvt.v -v $(netlist_dir)/stdcells-pm.v



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
.PHONY: libcgra.so
libcgra.so: map.c map.h gen.c gen.h parser.c parser.h
	gcc -Wno-error -Wall parser.c map.c gen.c -shared -o libcgra.so -fPIC -DGLB_TILE_MEM_SIZE=$(GLB_TILE_MEM_SIZE)

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
compile: XRUN_ARGS += -notimingchecks
compile: XRUN_ARGS += +define+NON_STOP_IF_INPUT_PIN_Z
compile: XRUN_ARGS += +define+TSMC_CM_NO_WARNING
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
	xrun -R -sv_lib libcgra.so $(RUN_ARGS) $(APP_ARGS) +VCD_ON

# -------------------------------------------------------------------
# GLS Compile
# -------------------------------------------------------------------
# compile testbench of garnet with xcelium
.PHONY: compile-gl
compile-gl: XRUN_ARGS += -top $(TOP_NAME)
compile-gl: XRUN_ARGS += +define+CLK_PERIOD=$(CLK_PERIOD)
compile-gl: XRUN_ARGS += +define+CGRA_WIDTH=$(CGRA_WIDTH) +define+AXI_ADDR_WIDTH=$(AXI_ADDR_WIDTH) +define+AXI_DATA_WIDTH=$(AXI_DATA_WIDTH) +define+GLB_TILE_MEM_SIZE=$(GLB_TILE_MEM_SIZE)
compile-gl: XRUN_ARGS += -F tb_garnet.filelist
compile-gl: XRUN_ARGS += -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/ \
				      	 -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CWTECH/ \
					     +libext+.v+.sv 
compile-gl: XRUN_ARGS += $(NETLIST_FILES)
compile-gl: libcgra.so top.sv garnet_param.svh garnet_test.sv kernel.sv proc_driver.sv axil_driver.sv axil_ifc.sv proc_ifc.sv environment.sv
	$(XRUN_COMPILE)

# -------------------------------------------------------------------
# Clean
# -------------------------------------------------------------------
.PHONY: clean
clean:
	rm -rf xrun.log xrun.history xcelium.d
