#!/bin/bash
ROOT = ../../..
TOP = "global_buffer"
all: glb

glb: make
	./obj_dir/V${TOP}

make: comp
	make -C ./obj_dir -f V${TOP}.mk

comp:
	verilator \
	${ROOT}/global_buffer.v \
	${ROOT}/global_buffer/global_buffer.sv \
	${ROOT}/global_buffer/genesis/genesis_verif/bank_controller.sv \
	${ROOT}/global_buffer/genesis/genesis_verif/cfg_address_generator.sv \
	${ROOT}/global_buffer/genesis/genesis_verif/cfg_controller.sv \
	${ROOT}/global_buffer/genesis/genesis_verif/glbuf_memory_core.sv \
	${ROOT}/global_buffer/genesis/genesis_verif/host_bank_interconnect.sv \
	${ROOT}/global_buffer/genesis/genesis_verif/io_address_generator.sv \
	${ROOT}/global_buffer/genesis/genesis_verif/io_controller.sv \
	${ROOT}/global_buffer/genesis/genesis_verif/memory_bank.sv \
	${ROOT}/global_buffer/genesis/genesis_verif/memory.sv \
	${ROOT}/global_buffer/genesis/genesis_verif/sram_controller.sv \
	${ROOT}/global_buffer/genesis/genesis_verif/sram_gen.sv \
	${ROOT}/global_buffer/genesis/TS1N16FFCLLSBLVTC2048X64M8SW.sv \
	--top-module ${TOP} \
	-cc -O3 \
	-Wno-fatal \
	-exe test_global_buffer.cpp \
	--trace \
	-CFLAGS "-std=c++11"
