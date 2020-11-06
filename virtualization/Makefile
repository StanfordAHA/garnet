#!/bin/bash

CGRA_WIDTH ?= 8
AXI_ADDR_WIDTH := 13
AXI_DATA_WIDTH := 32

mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
mkfile_dir := $(dir $(mkfile_path))
garnet_dir := $(mkfile_dir)/..
glb_dir := $(garnet_dir)/global_buffer
glc_dir := $(garnet_dir)/global_controller

XRUN = xrun \
	   -64bit \
	   -sv \
	   -debug \
	   -sysv \
	   -l xrun.log \
	   -notimingchecks \
	   -covoverwrite \
	   -timescale 100ps/1ps \
	   -initmem0 \
	   -initreg0 \
	   +access+rw \
	   +maxdelays \
	   $(XRUN_ARGS) \
	   $(APP_ARGS) \
	   $(DESIGN_ARGS)

gen.so: gen.c gen.h
	gcc -Wno-error -Wall gen.c -shared -o gen.so -fPIC

map.so: map.c map.h
	gcc -DNUM_COLS=$(CGRA_WIDTH) -Wno-error -Wall map.c -shared -o map.so -fPIC

parser.so: parser.c parser.h
	gcc -Wno-error -Wall parser.c -shared -o parser.so -fPIC

test: test.c parser.so map.so gen.so
	gcc -Wno-error -Wall test.c gen.so map.so parser.so -o test

test-all: test
	LD_LIBRARY_PATH=. ./test

# generate rtl
.PHONY: glb-rtl glc-rtl

glb-rtl: 
	$(MAKE) -C $(glb_dir) rtl CGRA_WIDTH=$(CGRA_WIDTH)

glc-rtl:
	$(MAKE) -C $(glc_dir) rtl CGRA_WIDTH=$(CGRA_WIDTH)

# run testbench of glb with xcelium
.PHONY: sim map.so
sim: XRUN_ARGS += +libext+.v+.sv -top top
sim: XRUN_ARGS += -sv_lib parser.so map.so gen.so
sim: XRUN_ARGS += +VCD_ON
sim: XRUN_ARGS += +define+CGRA_WIDTH=$(CGRA_WIDTH) +define+AXI_ADDR_WIDTH=$(AXI_ADDR_WIDTH) +define+AXI_DATA_WIDTH=$(AXI_DATA_WIDTH)
sim: DESIGN_ARGS += -v $(garnet_dir)/garnet.v -v $(glb_dir)/rtl/TS1N16FFCLLSBLVTC2048X64M8SW.sv -v $(garnet_dir)/tests/AN2D0BWP16P90.sv
sim: DESIGN_ARGS += -F tb_garnet.filelist -F $(glb_dir)/rtl/global_buffer.filelist -F $(glc_dir)/global_controller.filelist
sim: DESIGN_ARGS += -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/ \
				    -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CWTECH/ 

sim: APP_ARGS += +APP0=$(app0)
sim: glb-rtl glc-rtl map.so gen.so parser.so top.sv garnet_param.svh garnet_test.sv kernel.sv proc_driver.sv axil_driver.sv axil_ifc.sv proc_ifc.sv environment.sv
	$(XRUN)

.PHONY: clean
clean:
	rm -rf xrun.log xrun.history xcelium.d
