#!/bin/bash
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(abspath $(dir $(mkfile_path)))

# -------------------------------------------------------------------
# Parameters
# -------------------------------------------------------------------
# time control
CLK_PERIOD ?= 1500ps
CLK_SRC_LATENCY ?= -500ps
TIMEUNIT ?= 100ps
TIMEPRECISION ?= 1ps
TIMEUNIT_NUMBER_ONLY = $(shell echo $(TIMEUNIT) | rev | cut -c 3- | rev)
CLK_PERIOD_NUMBER_ONLY = $(shell echo $(CLK_PERIOD) | rev | cut -c 3- | rev)
CLK_SRC_LATENCY_NUMBER_ONLY = $(shell echo $(CLK_SRC_LATENCY) | rev | cut -c 3- | rev)
CLK_PERIOD_TIMEUNIT = $(shell echo "scale=2; $(CLK_PERIOD_NUMBER_ONLY) / $(TIMEUNIT_NUMBER_ONLY)" | bc) 
CLK_SRC_LATENCY_TIMEUNIT = $(shell echo "scale=2; $(CLK_SRC_LATENCY_NUMBER_ONLY) / $(TIMEUNIT_NUMBER_ONLY)" | bc) 

# architecture
CGRA_WIDTH ?= 32
NUM_GLB_TILES ?= $(shell expr $(CGRA_WIDTH) / 2 )
GLB_TILE_MEM_SIZE ?= 256

# tool chain
TOOL ?= VCS
SRAM_STUB ?= 0
export WAVEFORM ?= 0
export SAIF ?= 0

# GLS 
SDF ?= 0
MTM ?= MAXIMUM
SDF_CMD_FILE ?= sdf_cmd.cmd
SDF_LOG ?= sdf_logs
GLB_TOP_SDF ?= gls/glb.sdf
GLB_TILE_SDF ?= gls/glb_tile.sdf

# runtime
RUN_ARGS ?= +test01 +test02 +test03 +test04 +test05 +test06 +test07 +test08 +test09 +test10 +test11
RUN_ARGS += +MAX_NUM_TEST=11
RUN_ARGS += +DEBUG
RUN_LOG ?= run.log

# design files
HEADER_FILES ?= header/global_buffer_param.svh header/glb.svh 
DESIGN_FILES ?= global_buffer.sv systemRDL/output/glb_pio.sv systemRDL/output/glb_jrdl_decode.sv systemRDL/output/glb_jrdl_logic.sv
#FIXME: pm cells should be removed!
NETLIST_FILES ?= gls/glb.vcs.v gls/glb_tile.vcs.v gls/glb_tile_sram.v gls/stdcells.v gls/stdcells-pm.v
TB_FILES ?= -F sim/tb_global_buffer.f 

# -------------------------------------------------------------------
# Commands
# -------------------------------------------------------------------
GENERATE_TV = \
    python testvectors/gen_glb_test.py --data testvectors/64_v0.dat --num 64 --seed 0; \
    python testvectors/gen_glb_test.py --data testvectors/512_v0.dat --num 512 --seed 0; \
    python testvectors/gen_glb_test.py --data testvectors/512_v1.dat --num 512 --seed 1; \
    python testvectors/gen_glb_test.py --data testvectors/4096_v0.dat --num 4096 --seed 0; \
    python testvectors/gen_glb_test.py --data testvectors/4096_v1.dat --num 4096 --seed 1; \
    python testvectors/gen_glb_test.py --data testvectors/1024_v0.dat --num 1024 --seed 0; \
    python testvectors/gen_glb_test.py --data testvectors/1024_v1.dat --num 1024 --seed 1; \
    python testvectors/gen_glb_test.py --data testvectors/3844_v0.dat --num 3844 --seed 0;

XRUN = xrun \
	   -64bit \
	   -sv \
	   -sysv \
	   -superlint \
	   -l xrun.log \
	   -debug \
	   +access+rwc \
	   -covoverwrite \
	   -elaborate \
	   -top top \
	   -timescale 100ps/1ps \
	   -unbuffered \
	   -svseed random \
	   $(COMPILE_ARGS) \
	   $(INPUT_ARGS)

VCS = vcs \
	  -debug_accss+all \
	  -sverilog \
	  -timescale=100ps/1ps \
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
	  $(COMPILE_ARGS) \
	  $(INPUT_ARGS)

GEN_SDF_CMD = python gls/gen_sdf_cmd.py \
              -f $(SDF_CMD_FILE) -n $(NUM_GLB_TILES) --top $(GLB_TOP_SDF) --tile $(GLB_TILE_SDF) -l $(SDF_LOG) -t $(MTM) --tool $(TOOL)

# -------------------------------------------------------------------
# RTL
# -------------------------------------------------------------------
.PHONY: rtl
ifneq ($(SRAM_STUB), 0)
    SRAM_STUB_ARG = --sram_stub
else
    SRAM_STUB_ARG =
endif
rtl: export GARNET_HOME := $(current_dir)/..
rtl: export PYTHONPATH = $(GARNET_HOME):$$PYTHONPATH
rtl: 
	python global_buffer_main.py -r -v -p --num_cgra_cols=$(CGRA_WIDTH) --num_glb_tiles=$(NUM_GLB_TILES) --glb_tile_mem_size=$(GLB_TILE_MEM_SIZE) $(SRAM_STUB_ARG)

# -------------------------------------------------------------------
# Compile & Run
# -------------------------------------------------------------------
COMPILE_RTL_ARGS += +define+CLK_PERIOD=$(CLK_PERIOD_TIMEUNIT) +define+TIMEUNIT=$(TIMEUNIT) +define+TIMEPRECISION=$(TIMEPRECISION) +define+CLK_SRC_LATENCY=$(CLK_SRC_LATENCY_TIMEUNIT) 
COMPILE_GLS_ARGS += +define+CLK_PERIOD=$(CLK_PERIOD_TIMEUNIT) +define+TIMEUNIT=$(TIMEUNIT) +define+TIMEPRECISION=$(TIMEPRECISION) +define+CLK_SRC_LATENCY=$(CLK_SRC_LATENCY_TIMEUNIT) 
ifeq ($(TOOL), XCELIUM)
    COMPILE = $(XRUN)
    COMPILE_RTL_ARGS += -xminitialize 0 -xminit_log init.log -nospecify
    COMPILE_GLS_ARGS += -xminitialize 0 -xminit_log init.log
    COMPILE_GLS_ARGS += -ALLOWREDEFINITION
    RUN = xrun -R -l $(RUN_LOG)
else ifeq ($(TOOL), VCS)
    COMPILE = $(VCS)
    COMPILE_RTL_ARGS += +nospecify
    COMPILE_RTL_ARGS += +nbaopt
    COMPILE_RTL_ARGS += +lint=TFIPC-L
    COMPILE_GLS_ARGS += +neg_tchk
    COMPILE_GLS_ARGS += -negdelay
    RUN = ./simv -lca -l $(RUN_LOG) +vcs+initmem+0 +vcs+initreg+0 -exitstatus
else
    @echo "TOOL must be either XCELIUM or VCS"
endif

ifeq ($(TOOL), XCELIUM)
	DUMP_ARGS = -input sim/dump_shm.tcl
else ifeq ($(TOOL), VCS)
	DUMP_ARGS = -ucli -i sim/dump_fsdb.tcl
endif

ifneq ($(SDF), 0)
    $(shell $(GEN_SDF_CMD))
    ifeq ($(TOOL), XCELIUM)
        SDF_ARGS += -sdf_cmd_file $(SDF_CMD_FILE)
        SDF_ARGS += -sdfstats sdf_stats.txt -sdf_verbose
        COMPILE_GLS_ARGS += $(SDF_ARGS)
    else ifeq ($(TOOL), VCS)
        SDF_ARGS += $(shell cat $(SDF_CMD_FILE))
        SDF_ARGS += +sdfverbose
        COMPILE_GLS_ARGS += $(SDF_ARGS)
    endif
endif

.PHONY: compile
compile: COMPILE_ARGS = $(COMPILE_RTL_ARGS)
compile: INPUT_ARGS = $(HEADER_FILES) $(DESIGN_FILES) $(TB_FILES)
compile:
	$(COMPILE)

.PHONY: run
run:
	$(GENERATE_TV)
	$(RUN) $(DUMP_ARGS) $(RUN_ARGS)

.PHONY: sim
sim: compile run

# -------------------------------------------------------------------
# GLS Compile
# -------------------------------------------------------------------
.PHONY: compile-gls
compile-gls: COMPILE_GLS_ARGS += +define+NON_STOP_IF_INPUT_Z
compile-gls: COMPILE_GLS_ARGS += +define+TSMC_CM_NO_WARNING
compile-gls: COMPILE_GLS_ARGS += +define+TSMC_CM_UNIT_DELAY
compile-gls: COMPILE_GLS_ARGS += +define+TSMC_INITIALIZE_MEM_USING_DEFAULT_TASKS
compile-gls: COMPILE_GLS_ARGS += +define+TSMC_MEM_LOAD_0
compile-gls: COMPILE_ARGS = $(COMPILE_GLS_ARGS)
compile-gls: INPUT_ARGS = $(HEADER_FILES) $(NETLIST_FILES) $(TB_FILES)
compile-gls:
	@rm -rf $(SDF_LOG); mkdir $(SDF_LOG)
	$(COMPILE)

.PHONY: clean
clean:
	rm -rf xrun.log xrun.history xcelium.d simv simv.daidir csrc vcs.log global_buffer.shm global_buffer.fsdb sdf_stats.txt sdf_logs
