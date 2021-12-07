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

# -------------------------------------------------------------------
# Compile Parameters
# -------------------------------------------------------------------
CLK_PERIOD ?= 1ns
TOP_NAME ?= top
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

# -------------------------------------------------------------------
# Command
# -------------------------------------------------------------------
VCS = vcs \
	  -debug_accss+designer \
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
	  -l vcs.log \
	  $(VCSARGS) \
	  $(DESIGNARGS)

XRUN = xrun \
	   -64bit \
	   -sv \
	   -timescale 100ps/1ps \
	   -debug \
	   -sysv \
	   -elaborate \
	   -l xrun.log \
	   -covoverwrite \
	   -initmem0 \
	   -initreg0 \
	   +maxdelays \
	   $(XRUN_ARGS) \
	   $(DESIGNARGS) \
	   $(COMPILE_ARGS)

# -------------------------------------------------------------------
# C API
# -------------------------------------------------------------------
.PHONY: libcgra.so
libcgra.so: $(shell find lib -type f) $(garnet_dir)/global_buffer/header/global_buffer_param.h $(garnet_dir)/global_buffer/header/glb.h $(garnet_dir)/global_controller/header/glc.h
	gcc -Wno-error -Wall lib/*.c -I$(garnet_dir)/global_buffer/header -I$(garnet_dir)/global_controller/header -shared -o libcgra.so -fPIC

# -------------------------------------------------------------------
# Compile 
# -------------------------------------------------------------------
DESIGNARGS += $(garnet_dir)/global_buffer/header/global_buffer_param.svh $(garnet_dir)/global_buffer/header/glb.svh \
			  $(garnet_dir)/global_controller/header/glc.svh \
			  $(garnet_dir)/garnet.v \
			  $(garnet_dir)/global_buffer/systemRDL/output/glb_pio.sv \
			  $(garnet_dir)/global_buffer/systemRDL/output/glb_jrdl_decode.sv \
			  $(garnet_dir)/global_buffer/systemRDL/output/glb_jrdl_logic.sv \
			  $(garnet_dir)/global_controller/systemRDL/output/glc_pio.sv \
			  $(garnet_dir)/global_controller/systemRDL/output/glc_jrdl_decode.sv \
			  $(garnet_dir)/global_controller/systemRDL/output/glc_jrdl_logic.sv \
			  -v $(garnet_dir)/tests/AN2D0BWP16P90.sv -v $(garnet_dir)/tests/AO22D0BWP16P90.sv \
			  $(garnet_dir)/genesis_verif/*.sv -F tb/tb_cgra.f

# compile testbench of garnet with VCS
# -------------------------------------------------------------------
# Compile VCS 
# -------------------------------------------------------------------
.PHONY: compile-vcs
compile-vcs: VCSARGS += -top $(TOP_NAME)
compile-vcs: VCSARGS += +define+CLK_PERIOD=$(CLK_PERIOD)
compile-vcs: VCSARGS += +nospecify
compile-vcs: VCSARGS += +define+NON_STOP_IF_INPUT_PIN_Z
compile-vcs: VCSARGS += -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/ \
				        -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CWTECH/ \
					    +libext+.v+.sv 
compile-vcs: libcgra.so $(shell find tb -type f)
	$(VCS)

# -------------------------------------------------------------------
# Compile Xcelium
# -------------------------------------------------------------------
# compile testbench of garnet with xcelium
.PHONY: compile-xcel
compile-xcel: XRUN_ARGS += -top $(TOP_NAME)
compile-xcel: XRUN_ARGS += +define+CLK_PERIOD=$(CLK_PERIOD)
compile-xcel: XRUN_ARGS += -notimingchecks
compile-xcel: XRUN_ARGS += +define+NON_STOP_IF_INPUT_PIN_Z
compile-xcel: XRUN_ARGS += +define+TSMC_CM_NO_WARNING
compile-xcel: XRUN_ARGS += -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/ \
				      	   -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CWTECH/ \
					       +libext+.v+.sv 
compile-xcel: libcgra.so $(shell find tb -type f)
	$(XRUN)

# -------------------------------------------------------------------
# Run VCS
# -------------------------------------------------------------------
.PHONY: run
run: 
	./simv -sv_lib libcgra $(RUN_ARGS) $(APP_ARGS)

# -------------------------------------------------------------------
# Run Xcelium
# -------------------------------------------------------------------
.PHONY: run-xcel
run-xcel: 
	xrun -R -sv_lib libcgra.so $(RUN_ARGS) $(APP_ARGS)

# -------------------------------------------------------------------
# Simulation
# -------------------------------------------------------------------
.PHONY: sim
sim: libcgra.so compile-xcel run-xcel

# -------------------------------------------------------------------
# GLS Compile
# -------------------------------------------------------------------
# compile testbench of garnet with xcelium
.PHONY: compile-gl
compile-gl: XRUN_ARGS += -top $(TOP_NAME)
compile-gl: XRUN_ARGS += +define+CLK_PERIOD=$(CLK_PERIOD)
compile-gl: XRUN_ARGS += -F tb_garnet.filelist
compile-gl: XRUN_ARGS += -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/ \
				      	 -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CWTECH/ \
					     +libext+.v+.sv 
compile-gl: XRUN_ARGS += $(NETLIST_FILES)
compile-gl: libcgra.so top.sv garnet_test.sv kernel.sv proc_driver.sv axil_driver.sv axil_ifc.sv proc_ifc.sv environment.sv
	$(XRUN)

# -------------------------------------------------------------------
# Clean
# -------------------------------------------------------------------
.PHONY: clean
clean:
	rm -rf xrun.log xrun.history xcelium.d simv simv.daidir csrc vcs.log

