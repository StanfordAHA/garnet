#!/bin/bash

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
	   $(XRUNARGS) \
	   $(DESIGNARGS)


# run testbench of glb with xcelium
.PHONY: sim
sim: XRUNARGS += +libext+.v+.sv -top top
sim: DESIGNARGS += -F tb_garnet.filelist 
sim: DESIGNARGS += -v $(DESIGN)
sim: DESIGNARGS += -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/ \
				   -y /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CWTECH/ \
				   -v /home/kongty/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/VERILOG/ts1n16ffcllsblvtc2048x64m8sw_130a.v \
				   -v /home/kongty/mc/ts1n16ffcllsblvtc512x32m4s_130a/VERILOG/ts1n16ffcllsblvtc512x32m4s_130a.v
sim: $(DESIGN)
	$(XRUN)

.PHONY: clean
clean:
	rm -rf xrun.log xrun.history xcelium.d
