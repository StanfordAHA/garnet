#!/bin/bash

DESIGN=global_buffer

Genesis2.pl \
    -parse \
    -generate \
    -top ${DESIGN} \
    -input \
        global_buffer.svp \
        memory_bank.sv \
        bank_controller.sv \
        memory_core.sv \
        sram_controller.sv \
        memory.v \
        sram_stub.v
