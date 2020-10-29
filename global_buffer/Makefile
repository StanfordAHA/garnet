#!/bin/bash
RTL_DIR := ./rtl
RDL_DIR := systemRDL/output
TB_DIR := ./sim

TOP_MODULE := global_buffer

CGRA_WIDTH := 32
NUM_GLB_TILES := 16

GLB_TILE_NETLIST := /sim/kongty/pnr_annotate/glb_tile.vcs.v
GLB_TOP_NETLIST := /sim/kongty/pnr_annotate/global_buffer.vcs.v
SRAM_RTL := /sim/kongty/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/VERILOG/ts1n16ffcllsblvtc2048x64m8sw_130a.v

RTL_LISTS := `cat $(RTL_DIR)/global_buffer.filelist | sed -e 's/^/$(RTL_DIR)\//' | xargs readlink -f`

FIX_SYSTEMRDL = \
    sed -i '/pio_dec_write_data_d1 <=/d' ./systemRDL/output/glb_jrdl_decode.sv; \
    sed -i '/pio_dec_address_d1 <=/d' ./systemRDL/output/glb_jrdl_decode.sv; \
    sed -i '/endmodule/d' ./systemRDL/output/glb_jrdl_decode.sv; \
    echo -e "always_ff @ (posedge clk) begin \n pio_dec_address_d1 <= pio_dec_address; \n pio_dec_write_data_d1 <= pio_dec_write_data; \nend \nendmodule" >> ./systemRDL/output/glb_jrdl_decode.sv

XRUN = xrun \
	   -64bit \
	   -sv \
	   -sysv \
	   -l xrun.log \
	   -notimingchecks \
	   -covoverwrite \
	   -top top \
	   -timescale 100ps/1ps \
	   +loadpli1=debpli:deb_PLIPtr \
	   -initmem0 \
	   -initreg0 \
	   +access+rw \
	   +maxdelays \
	   $(XRUNARGS) \
	   $(DESIGNARGS)

VCS = vcs \
	  -debug_acc+all \
	  -sverilog \
	  -timescale=100ps/1ps \
	  -v2k_generate \
	  -full64 \
	  -ldflags "-Wl,--no-as-needed" \
	  -CFLAGS "-m64" \
	  -top top \
	  +lint=TFIPC-L \
	  +vcs+lic+wait \
	  +vcs+initreg+random \
	  +overlap \
	  +v2k \
	  +memcbk \
	  $(VCSARGS) \
	  $(DESIGNARGS)

# param target generates global_buffer_param.svh
.PHONY: param
param: global_buffer_main.py global_buffer_magma_helper.py
	cd .. && python -m global_buffer.global_buffer_main -p --num_cgra_cols=$(CGRA_WIDTH) --num_glb_tiles=$(NUM_GLB_TILES)


# rtl target always runs param target
rdl_pre = systemRDL/rdl_models/glb.rdl.pre
$(rdl_pre): param systemRDL/rdl_models/glb.rdl
	cat systemRDL/rdl_models/glb.rdl.param systemRDL/rdl_models/glb.rdl > systemRDL/rdl_models/glb.rdl.pre

rdl_post = systemRDL/rdl_models/glb.rdl.post
$(rdl_post): $(rdl_pre)
	../systemRDL/perlpp.pl systemRDL/rdl_models/glb.rdl.pre -o systemRDL/rdl_models/glb.rdl.post

rdl_gen = $(RDL_DIR)/glb_jrdl_decode.sv $(RDL_DIR)/glb_jrdl_logic.sv $(RDL_DIR)/glb_pio.sv
$(rdl_gen): $(rdl_post)
	java -jar ../systemRDL/Ordt.jar -parms systemRDL/ordt_params/glb.parms -systemverilog systemRDL/output/ systemRDL/rdl_models/glb.rdl.post

$(RTL_LISTS): $(rdl_gen)

.PHONY: rtl
rtl: $(RTL_LISTS)
	$(FIX_SYSTEMRDL)

# html target generates html for systemRDL table
.PHONY: html
html: $(rdl_post)
	python ../systemRDL/gen_html.py systemRDL/rdl_models/glb.rdl.post

# sim-tile
# run testbench of glb-tile with xcelium
.PHONY: sim-tile
sim-tile: TOP_MODULE=glb_tile
sim-tile: TB_DIR=sim-tile
sim-tile: DESIGNARGS += -F $(RTL_DIR)/$(TOP_MODULE).filelist -F $(TB_DIR)/tb_$(TOP_MODULE).filelist -v $(SRAM_RTL)
sim-tile: rtl
	$(XRUN)

# sim-tile-pnr
# run testbench of glb-tile with xcelium with sdf back annotation
.PHONY: sim-til-gl
sim-tile-gl: TOP_MODULE=glb_tile
sim-tile-gl: TB_DIR=sim-tile
sim-tile-gl: XRUNARGS += +define+PNR
sim-tile-gl: DESIGNARGS += \
	`find /tsmc16/TSMCHOME/digital/Front_End/verilog/ -name '*.v' | grep -v "pwr" | sed -e 's/^/-v /' | xargs` \
	-v $(SRAM_RTL) \
	$(GLB_TILE_NETLIST) \
	$(RTL_DIR)/global_buffer_param.svh \
	-F $(TB_DIR)/tb_$(TOP_MODULE).filelist
sim-tile-gl: $(GLB_TILE_NETLIST)
	$(XRUN)

# run testbench of glb with xcelium
.PHONY: sim
#sim: XRUNARGS+=+define+DEBUG
sim: DESIGNARGS += -v $(SRAM_RTL) -F $(RTL_DIR)/$(TOP_MODULE).filelist -F $(TB_DIR)/tb_$(TOP_MODULE).filelist 
sim: rtl
	$(XRUN)

.PHONY: sim-gl
sim-gl: DESIGNARGS += \
	$(RTL_DIR)/global_buffer_param.svh \
	$(RTL_DIR)/global_buffer_pkg.svh \
	-F $(TB_DIR)/tb_$(TOP_MODULE).filelist \
	`find /tsmc16/TSMCHOME/digital/Front_End/verilog/ -name '*.v' | grep -v "pwr" | sed -e 's/^/-v /' | xargs` \
	-v $(SRAM_RTL) \
	$(GLB_TOP_NETLIST) \
	$(GLB_TILE_NETLIST)
sim-gl: XRUNARGS += +define+PNR
sim-gl: $(GLB_TOP_NETLIST) $(GLB_TILE_NETLIST)
	$(XRUN)

.PHONY: clean
clean:
	rm -rf xrun.log xrun.history xcelium.d
