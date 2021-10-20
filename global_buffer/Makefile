#!/bin/bash
RTL_DIR := ./rtl
RDL_DIR := systemRDL/output
TB_DIR := ./sim

TOP_MODULE := global_buffer

CGRA_WIDTH ?= 32
NUM_GLB_TILES ?= $(shell expr $(CGRA_WIDTH) / 2 )
GLB_TILE_MEM_SIZE ?= 256

RUNARGS = 
# RUNARGS += +TEST_GLB_MEM_SIMPLE
# RUNARGS += +TEST_GLB_CFG
# RUNARGS += +CFG_TEST_NUM_TILE=2
RUNARGS += +TEST_GLB_G2F_STREAM
# RUNARGS += +TEST_GLB_F2G_STREAM
# RUNARGS += +TEST_PCFG_STREAM

GLB_TILE_NETLIST := ./netlist/glb_tile.vcs.v
GLB_TOP_NETLIST := ./netlist/global_buffer.vcs.v
SRAM_RTL := /sim/kongty/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/VERILOG/ts1n16ffcllsblvtc2048x64m8sw_130a.v
SRAM_STUB := ./rtl/TS1N16FFCLLSBLVTC2048X64M8SW.sv

RTL_LISTS := `cat $(RTL_DIR)/global_buffer.f | sed -e 's/^/$(RTL_DIR)\//' | xargs readlink -f`

FIX_SYSTEMRDL = \
    sed -i '/pio_dec_write_data_d1 <=/d' ./systemRDL/output/glb_jrdl_decode.sv; \
    sed -i '/pio_dec_address_d1 <=/d' ./systemRDL/output/glb_jrdl_decode.sv; \
    sed -i '/endmodule/d' ./systemRDL/output/glb_jrdl_decode.sv; \
    printf "always_ff @ (posedge clk) begin \n pio_dec_address_d1 <= pio_dec_address; \n pio_dec_write_data_d1 <= pio_dec_write_data; \nend \nendmodule" >> ./systemRDL/output/glb_jrdl_decode.sv

DUMP_PIO_WRAPPER = \
    sed '/\.\*/d' ./systemRDL/output/glb_pio.sv > ./systemRDL/output/glb_pio_wrapper.sv

GENERATE_TV = python glb_test_gen.py

XRUN = xrun \
	   -64bit \
	   -sv \
	   -sysv \
	   -l xrun.log \
	   -debug \
	   -covoverwrite \
	   -top top \
	   -timescale 100ps/1ps \
	   -unbuffered \
	   -svseed random \
	   $(XRUNARGS) \
	   $(DESIGNARGS)

VCS = vcs \
	  -debug_acc+all \
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
	  +memcbk \
	  -l vcs.log \
	  $(VCSARGS) \
	  $(DESIGNARGS)

# -------------------------------------------------------------------
# RTL
# -------------------------------------------------------------------
# param target generates global_buffer_param.svh
.PHONY: param
param: global_buffer_main.py global_buffer_magma_helper.py
	cd .. && python -m global_buffer.global_buffer_main -p --num_cgra_cols=$(CGRA_WIDTH) --num_glb_tiles=$(NUM_GLB_TILES) --glb_tile_mem_size=$(GLB_TILE_MEM_SIZE)

# rtl target always runs param target
rdl_pre = systemRDL/rdl_models/glb.rdl.pre
$(rdl_pre): param systemRDL/rdl_models/glb.rdl
	cat systemRDL/rdl_models/glb.rdl.param systemRDL/rdl_models/glb.rdl > systemRDL/rdl_models/glb.rdl.pre

rdl_post = systemRDL/rdl_models/glb.rdl.post
$(rdl_post): $(rdl_pre)
	../systemRDL/perlpp.pl systemRDL/rdl_models/glb.rdl.pre -o systemRDL/rdl_models/glb.rdl.post

rdl_gen = $(RDL_DIR)/glb_jrdl_decode.sv $(RDL_DIR)/glb_jrdl_logic.sv $(RDL_DIR)/glb_pio.sv
$(rdl_gen): $(rdl_post)
	java -jar ../systemRDL/Ordt.jar -reglist systemRDL/output/glb.reglist -parms systemRDL/ordt_params/glb.parms -systemverilog systemRDL/output/ systemRDL/rdl_models/glb.rdl.post
	python ../systemRDL/gen_config_addrmap.py --rdl systemRDL/rdl_models/glb.rdl.post --output systemRDL/output --name glb_addrmap --header --html --json

$(RTL_LISTS): $(rdl_gen)

.PHONY: rtl
rtl: $(RTL_LISTS)
	$(FIX_SYSTEMRDL);
	$(DUMP_PIO_WRAPPER)

# -------------------------------------------------------------------
# Compile & Run
# -------------------------------------------------------------------
.PHONY: compile
compile: XRUNARGS+= -notimingchecks
compile: VCSARGS+= +nospecify
compile: DESIGNARGS += -v $(SRAM_STUB) -F $(RTL_DIR)/$(TOP_MODULE).f -F $(TB_DIR)/tb_$(TOP_MODULE).f
compile:
	$(GENERATE_TV); 
	$(VCS)

.PHONY: run
run: compile
	./simv -ucli -i vcs_cmd.tcl $(RUNARGS)

# -------------------------------------------------------------------
# GLS Compile & Run
# -------------------------------------------------------------------
.PHONY: compile-gl
compile-gl: DESIGNARGS += \
	$(RTL_DIR)/global_buffer_param.svh \
	$(RTL_DIR)/global_buffer_pkg.svh \
	-F $(TB_DIR)/tb_$(TOP_MODULE).filelist \
	-F netlist/netlist.filelist
# compile-gl: XRUNARGS += +define+PWR
compile-gl: XRUNARGS += +define+NON_STOP_IF_INPUT_Z
compile-gl: XRUNARGS += +define+PNR +define+TSMC_CM_NO_WARNING
compile-gl: XRUNARGS += +define+TSMC_CM_UNIT_DELAY
compile-gl: XRUNARGS += +define+TSMC_INITIALIZE_MEM_USING_DEFAULT_TASKS +define+TSMC_MEM_LOAD_0
compile-gl: XRUNARGS += -negdelay
compile-gl: XRUNARGS += -sdf_cmd_file netlist/sdf_cmd.cmd
compile-gl: XRUNARGS += -sdfstats sdf_stats.txt -sdf_verbose -xminitialize 0 -xminit_log init.log
compile-gl:
	$(XRUN)

.PHONY: clean
clean:
	rm -rf xrun.log xrun.history xcelium.d
