# -------------------------------------------------------------------
# Variables
# -------------------------------------------------------------------
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
mkfile_dir := $(dir $(mkfile_path))
garnet_dir := $(mkfile_dir)/../..
gemstone_dir := $(realpath $(garnet_dir))/../gemstone
netlist_dir := $(mkfile_dir)/netlist
genesis_tb_dir := $(mkfile_dir)/genesis_tb
glc_dir := $(garnet_dir)/global_controller
APP_ARGS ?= +APP0=app0

# I.e. if APP_ARGS="+APP0=/aha/Halide-to-Hardware/apps/hardware_benchmarks/apps/pointwise"
# then APP0_NAME="/aha/Halide-to-Hardware/apps/hardware_benchmarks/apps/pointwise"
# APP0_NAME = $(shell echo $(APP_ARGS) | awk '{print $1}' | sed 's/.*=//')
APP0_NAME = $(shell echo $(APP_ARGS) | sed -n 's/.*APP0=\([^ ]*\).*/\1/p')


TOOL ?= VCS
export WAVEFORM ?= 0
export WAVEFORM_GLB_ONLY ?= 0
export SAIF ?= 0

export USING_MATRIX_UNIT ?= 0
export INCLUDE_MU_GLB_HW ?= 0
export BEHAVIORAL_MATRIX_UNIT ?= 0

# -------------------------------------------------------------------
# Compile Parameters
# -------------------------------------------------------------------
CLK_PERIOD ?= 1ns

DESIGN_FILES += $(garnet_dir)/global_buffer/header/global_buffer_param.svh \
				$(garnet_dir)/global_buffer/header/glb.svh \
				$(garnet_dir)/global_controller/header/glc.svh \
				$(garnet_dir)/matrix_unit/header/matrix_unit_param.svh \
				$(garnet_dir)/matrix_unit/header/matrix_unit_regspace.svh \
				$(garnet_dir)/garnet.v \
				$(garnet_dir)/global_buffer/systemRDL/output/glb_pio.sv \
				$(garnet_dir)/global_buffer/systemRDL/output/glb_jrdl_decode.sv \
				$(garnet_dir)/global_buffer/systemRDL/output/glb_jrdl_logic.sv \
				$(garnet_dir)/global_controller/systemRDL/output/glc_pio.sv \
				$(garnet_dir)/global_controller/systemRDL/output/glc_jrdl_decode.sv \
				$(garnet_dir)/global_controller/systemRDL/output/glc_jrdl_logic.sv \
				$(garnet_dir)/genesis_verif/*.sv

ifeq ($(USING_MATRIX_UNIT), 1)
	ifneq ($(BEHAVIORAL_MATRIX_UNIT), 1)
		DESIGN_FILES +=	$(garnet_dir)/MatrixUnit_sim_sram.v \
						$(garnet_dir)/MatrixUnitWrapper_sim.v \
						$(garnet_dir)/zircon_wrapper/zircon.v
	endif
endif

TB_FILES += -F tb/tb_cgra.f

# If official cadence libs are available, use those; else use the stubs that I wrote
CADENCE_VLIBS    = /cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog
OFFICIAL_CW_LIBS = -y $(CADENCE_VLIBS)/CW/ -y $(CADENCE_VLIBS)/CWTECH/
BACKUP_CW_LIBS   = -y CW/
CW_LIBS  ?= $(shell test -d $(CADENCE_VLIBS) && echo $(OFFICIAL_CW_LIBS) || echo $(BACKUP_CW_LIBS))
IP_FILES += $(CW_LIBS) +libext+.v+.sv

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
	  -Wno-fatal -Wno-UNOPTFLAT \
	  --timescale 1ps/1ps \
	  --top-module top \
	  $(VERILATOR_WAVEFORM_ARGS) \
	  $(INPUT_ARGS) \
	  $(shell pwd)/libcgra.so

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
# INSTALL VERILATOR 5.028
# -------------------------------------------------------------------

NPROC = $(shell nproc)

# Because *some people* are stoopid (that's me, I'm the stoopid)
.PHONY: verilator-setup
verilator-setup: setup-verilator

.PHONY: setup-verilator
setup-verilator:
	# Assumes running from inside docker etc.
	/aha/garnet/tests/install-verilator.sh
	verilator --version

# -------------------------------------------------------------------
# C API
# -------------------------------------------------------------------
libcgra.so: $(shell find lib -type f) \
            $(garnet_dir)/global_buffer/header/global_buffer_param.h \
            $(garnet_dir)/global_buffer/header/glb.h \
            $(garnet_dir)/global_controller/header/glc.h \
			$(garnet_dir)/matrix_unit/header/matrix_unit_param.h \
			$(garnet_dir)/matrix_unit/header/matrix_unit_regspace.h
	gcc -Wno-error -Wall lib/*.c -I$(garnet_dir)/global_buffer/header -I$(garnet_dir)/global_controller/header -I$(garnet_dir)/matrix_unit/header -shared -o libcgra.so -fPIC

# -------------------------------------------------------------------
# Compile & Run
# -------------------------------------------------------------------
$(garnet_dir)/global_buffer/header/global_buffer_param.h:
	@echo 'ERROR Oops oh no cannot find e.g. "global_buffer_param.h"'
	@echo
	@echo You may need to build garnet verilog i.e. do something like
	@echo '  % cd /aha'
	@echo '  % aha garnet --width 28 --height 16 --verilog --use_sim_sram --glb_tile_mem_size 128 --dense-only'
	@echo
	@exit 13

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
    RUN = obj_dir/Vtop $(APP_ARGS)
else
    @echo "TOOL env var must be one of: VCS, VERILATOR, or XCELIUM"
endif

ifeq ($(TOOL), XCELIUM)
	DUMP_ARGS = -input dump_shm.tcl
else ifeq ($(TOOL), VCS)
	DUMP_ARGS = -ucli -i dump_fsdb.tcl
endif

$(APP0_NAME)/bin/design_meta.json:
	@echo $(APP_ARGS)
	@echo 'ERROR oops cannot find design_meta.json in $(APP0_NAME)/bin'
	@echo ERROR oops cannot find design_meta.json
	@echo Suggest you do something like
	@echo '  test=apps/pointwise'
	@echo '  app_path=/aha/Halide-to-Hardware/apps/hardware_benchmarks/$test'
	@echo '  (cd $app_path; make clean)'
	@echo '  aha map $$test --chain'
	@echo '  aha pnr $$test --width 28 --height 16 --dense-only'
	@exit 13

.PHONY: compile
compile: COMPILE_ARGS = $(COMPILE_RTL_ARGS)
compile: INPUT_ARGS = $(DESIGN_FILES) $(TB_FILES) $(IP_FILES)
compile:
	echo '##[endgroup]'; echo '##[group]make compile (verilator => Vtop.mk) or (vcs => simv)' `date +%H:%M`
	echo '--- MAKE COMPILE (verilator => Vtop.mk) or (vcs => simv)' `date +%H:%M`
	$(COMPILE)
ifeq ($(TOOL), VERILATOR)
	echo '##[endgroup]'; echo '##[group]make vtop (make -f Vtop.mk => Vtop)' `date +%H:%M`
	echo '--- MAKE VTOP (make -f Vtop.mk => Vtop)' `date +%H:%M`
	make -C obj_dir/ -f Vtop.mk
endif
	echo '##[endgroup]'

generate:
	echo '##[endgroup]'; echo '##[group]make generate (genesis testbench/top.svp)' `date +%H:%M`
	Genesis2.pl -parse -generate -top top -input $(genesis_tb_dir)/top.svp -parameter top.using_matrix_unit=$(USING_MATRIX_UNIT) top.include_mu_glb_hw=$(INCLUDE_MU_GLB_HW) top.behavioral_matrix_unit=$(BEHAVIORAL_MATRIX_UNIT)
	mv genesis_verif/top.sv tb/top.sv
	echo '##[endgroup]'

.PHONY: run
# Print log info in both buildkite and github-action format
run: $(APP0_NAME)/bin/design_meta.json

	echo '##[endgroup]'; echo '##[group]aha run (e.g. Vtop or simv)' `date +%H:%M`
	echo '--- MAKE RUN (e.g. Vtop or simv)' `date +%H:%M`
	@rm -rf *.txt; rm -rf ../../SPARSE_TESTS/batch_*
	$(RUN) $(DUMP_ARGS) $(RUN_ARGS) $(APP_ARGS)

	echo '##[endgroup]'; echo '##[group]PASSED maybe' `date +%H:%M`
	echo '+++ PASSED maybe' `date +%H:%M`
	echo '##[endgroup]'

.PHONY: sim
sim: libcgra.so generate compile run


# -------------------------------------------------------------------
# Test(s)
# -------------------------------------------------------------------

# Use little gaussian as default
TESTNAME  ?= apps/gaussian
CGRA_SIZE ?= --width 4 --height 16
GARNET_BUILD_PARMS ?= $(CGRA_SIZE) --verilog --use_sim_sram --glb_tile_mem_size 128
APP_PATH ?= /aha/Halide-to-Hardware/apps/hardware_benchmarks/$(TESTNAME)

.PHONY: gaussian
gaussian: CGRA_SIZE = --width 4 --height 16
gaussian: TESTNAME = apps/gaussian
gaussian: test

.PHONY: pointwise
pointwise: CGRA_SIZE = --width 28 --height 16 --dense-only
pointwise: TESTNAME = apps/pointwise
pointwise: test

# FIXME for now "make test" is hardwired to VERILATOR but it really doesn't have to be that way
.PHONY: test
test:
	echo '--- MAKE TEST $(TESTNAME): aha garnet' `date +%H:%M`
	aha garnet $(GARNET_BUILD_PARMS)                         # 5 minutes (kiwi)
	cd $(APP_PATH); make clean
	echo '--- MAKE $(TESTNAME): aha map' `date +%H:%M`
	aha map $(TESTNAME) --chain                              # 1 minutes
	echo '--- MAKE $(TESTNAME): aha pnr' `date +%H:%M`
	aha pnr $(TESTNAME) $(CGRA_SIZE)  # 2 minutes
	echo '--- MAKE $(TESTNAME): aha test' `date +%H:%M`
	TOOL=VERILATOR stdbuf -oL -eL aha test $(TESTNAME)       # 1.5 hours
	date

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
