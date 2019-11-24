#!/bin/bash
all: glb

glb: verilator \
	global_buffer.v \
	global_buffer/genesis/genesis_verif/io_address_generator.sv \
	global_buffer/genesis/genesis_verif/cfg_address_generator.sv \
	global_buffer/genesis/genesis_verif/memory_bank.sv \
	--top-module global_buffer \
	-cc -O3 \
	-Wno-fatal \
	-exe test_global_buffer.cpp \
	--trace \
	-CFLAGS "-std=c++11"
