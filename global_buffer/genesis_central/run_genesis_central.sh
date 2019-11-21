#!/bin/bash

DESIGN=global_buffer_int

DIR=`pwd`

Genesis2.pl                                        \
    -parse                                                                                          \
    -generate                                                                                       \
    -top ${DESIGN}                                                                                    \
    -input bank_controller.svp \
    cfg_address_generator.svp \
    cfg_controller_central.svp \
    glbuf_memory_core.svp \
    global_buffer_int.svp \
    host_bank_interconnect.svp \
    io_address_generator.svp \
    io_controller_central.svp \
    memory_bank.svp \
    memory.svp \
    sram_controller.svp \
    sram_gen.svp \
    TS1N16FFCLLSBLVTC2048X64M8SW.sv

