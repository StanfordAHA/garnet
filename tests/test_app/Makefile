# -------------------------------------------------------------------
# Variables
# -------------------------------------------------------------------
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
mkfile_dir := $(dir $(mkfile_path))
garnet_dir := $(mkfile_dir)/../..
gemstone_dir := $(realpath $(garnet_dir))/../gemstone
netlist_dir := $(mkfile_dir)/netlist
glc_dir := $(garnet_dir)/global_controller
APP_ARGS ?= +APP0=app0

# I.e. if APP_ARGS="+APP0=/aha/Halide-to-Hardware/apps/hardware_benchmarks/apps/pointwise"
# then APP0_NAME="/aha/Halide-to-Hardware/apps/hardware_benchmarks/apps/pointwise"
APP0_NAME = $(shell echo $(APP_ARGS) | awk '{print $1}' | sed 's/.*=//')

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
NETLIST_FILES ?= -v $(garnet_dir)/garnet.v -v $(netlist_dir)/glb_top.vcs.v -v $(netlist_dir)/glb_tile.vcs.v \
				 -v $(netlist_dir)/global_controller.vcs.v -v $(netlist_dir)/tile_array.vcs.v -v $(netlist_dir)/Tile_PE.vcs.v -v $(netlist_dir)/Tile_MemCore.vcs.v \
				 -v $(netlist_dir)/sram.v -v $(netlist_dir)/tile_array.sram.v -v $(netlist_dir)/stdcells.v -v $(netlist_dir)/stdcells-lvt.v -v $(netlist_dir)/stdcells-ulvt.v -v $(netlist_dir)/stdcells-pm.v

# -------------------------------------------------------------------
# Run Parameters
# -------------------------------------------------------------------
RUN_ARGS ?=
RUN_LOG ?= run.log

# -------------------------------------------------------------------
# Command
# -------------------------------------------------------------------

ifeq ($(WAVEFORM), 1)
WAVEFORM_ARGS = -debug_access+all -kdb +vpi +memcbk +vcsd
VERILATOR_WAVEFORM_ARGS = --trace
endif

ifeq ($(WHICH_SOC), amber)
TIMESCALE = -timescale=100ps/1ps
else
TIMESCALE = -timescale=1ps/1ps
endif

VCS = vcs \
	  -sverilog \
	  $(TIMESCALE) \
	  -full64 \
	  -ldflags "-Wl,--no-as-needed" \
	  -CFLAGS "-m64" \
	  -top top \
	  +vcs+lic+wait \
	  +vcs+initreg+random \
	  +overlap \
	  +v2k \
	  -l vcs.log \
	  $(WAVEFORM_ARGS) \
	  $(COMPILE_ARGS) \
	  $(INPUT_ARGS)

VERILATOR = verilator $(VERILATOR_WARN) --timing --cc --exe tb/CGRA.cpp \
	  --timescale 1ps/1ps \
	  --top-module top \
	  $(VERILATOR_WAVEFORM_ARGS) \
	  $(INPUT_ARGS) \
	  -F tb/tb_cgra.f

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
# TOP_LEVEL DEPENDENCE: "MAKE" == "MAKE SIM"
# -------------------------------------------------------------------
.phony: all
all: sim


# -------------------------------------------------------------------
# C API
# -------------------------------------------------------------------
$(garnet_dir)/global_buffer/header/global_buffer_param.h:
	@echo 'ERROR Oops oh no cannot find e.g. "global_buffer_param.h"'
	@echo
	@echo You may need to build garnet verilog i.e. do something like
	@echo '  % cd /aha'
	@echo '  % aha garnet --width 28 --height 16 --verilog --use_sim_sram --glb_tile_mem_size 128 --dense-only'
	@echo
	@exit 13

# .PHONY: libcgra.so -- why is this phony?
libcgra.so: $(shell find lib -type f) $(garnet_dir)/global_buffer/header/global_buffer_param.h $(garnet_dir)/global_buffer/header/glb.h $(garnet_dir)/global_controller/header/glc.h
	gcc -Wno-error -Wall lib/*.c -I$(garnet_dir)/global_buffer/header -I$(garnet_dir)/global_controller/header -shared -o libcgra.so -fPIC


# -------------------------------------------------------------------
# Compile & Run
# -------------------------------------------------------------------
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
    RUN = ./simv -lca -l $(RUN_LOG) +vcs+initmem+0 +vcs+initreg+0 -sv_lib libcgra -exitstatus
else ifeq ($(TOOL), VERILATOR)
    COMPILE = $(VERILATOR)
    # COMPILE_RTL_ARGS += +nospecify
    RUN = obj_dir/Vtop $(APP_ARGS)
else
    @echo "TOOL must be either XCELIUM or VCS"
endif

ifeq ($(TOOL), XCELIUM)
	DUMP_ARGS = -input dump_shm.tcl
else ifeq ($(TOOL), VCS)
	DUMP_ARGS = -ucli -i dump_fsdb.tcl
endif

$(APP0_NAME)/bin/design_meta.json:
	@echo ERROR oops cannot find design_meta.json
	@echo Suggest you do something like
	@echo '  test=apps/pointwise'
	@echo '  app_path=/aha/Halide-to-Hardware/apps/hardware_benchmarks/$test'
	@echo '  (cd $app_path; make clean)'
	@echo '  aha map $test --chain'
	@echo '  aha pnr $test --width 28 --height 16 --dense-only'
	@exit 13

.PHONY: compile
compile: COMPILE_ARGS = $(COMPILE_RTL_ARGS)
compile: INPUT_ARGS = $(DESIGN_FILES) $(TB_FILES) $(IP_FILES)
compile:
	$(COMPILE)

.PHONY: run
run: $(APP0_NAME)/bin/design_meta.json
	@rm -rf *.txt; rm -rf ../../SPARSE_TESTS/batch_*
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
	@rm -rf $(SDF_LOG); mkdir $(SDF_LOG)
	$(COMPILE)


# -------------------------------------------------------------------
# Clean
# -------------------------------------------------------------------
.PHONY: clean
clean:
	rm -rf xrun.log xrun.history xcelium.d simv simv.daidir csrc vcs.log cgra.shm cgra.fsdb sdf_stats.txt sdf_logs

.PHONY: clean_sparse_outputs
clean_sparse_outputs:
	rm -f tensor_*
