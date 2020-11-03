#!/bin/bash

H2H := /sim/kongty/aha/Halide-to-Hardware/apps/hardware_benchmarks
DESIGN := /sim/kongty/garnet/virtualization/build-fullchip/9-rtl/outputs/design.v
XRUN = xrun \
	   -64bit \
	   -sv \
	   -sysv \
	   -l xrun.log \
	   -notimingchecks \
	   -covoverwrite \
	   -timescale 1ns/1ps \
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
	gcc -Wno-error -Wall map.c -shared -o map.so -fPIC

parser.so: parser.c parser.h
	gcc -Wno-error -Wall parser.c -shared -o parser.so -fPIC

test: test.c parser.so map.so gen.so
	gcc -Wno-error -Wall test.c gen.so map.so parser.so -o test

test-all: test
	LD_LIBRARY_PATH=. ./test

# run testbench of glb with xcelium
.PHONY: sim
sim: XRUN_ARGS += +libext+.v+.sv -top top
sim: XRUN_ARGS += -sv_lib parser.so map.so gen.so
sim: XRUN_ARGS += +VCD_ON
sim: DESIGN_ARGS += -F tb_garnet.filelist 
sim: DESIGN_ARGS += -v $(DESIGN)
sim: DESIGN_ARGS += -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/ \
				    -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CWTECH/ \
				   	-v /home/kongty/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/VERILOG/ts1n16ffcllsblvtc2048x64m8sw_130a.v \
				   	-v /home/kongty/mc/ts1n16ffcllsblvtc512x32m4s_130a/VERILOG/ts1n16ffcllsblvtc512x32m4s_130a.v
sim: APP_ARGS += +APP0=$(H2H)/tests/conv_3_3
sim: $(DESIGN) map.so gen.so parser.so top.sv garnet_param.svh garnet_test.sv kernel.sv
	$(XRUN)

.PHONY: clean
clean:
	rm -rf xrun.log xrun.history xcelium.d
