from random import random
import math
import numpy as np
import binascii
import struct
import os

def main():
    def get_hex (x, l):
      return str(binascii.hexlify(struct.pack('>I', x)))[10-l:10] # I is for unsigned int -- 32 bits

    cycles = 0
    config_cycles = 2
    first_stall = False

    # INPUTS
    f = open("test_vectors.txt", "w")
    raw = open("raw_input.csv", "r")

    # first flip the inputs so we can use the same defines
    flipped = open("flipped.csv", "w")
    while True:
        line = raw.readline().strip()
        if not line:
            break

        str_nums = line.split(",")
        nums = [thing for thing in str_nums]

        for i in range(20):
            temp = nums[2*i];
            nums[2*i] = nums[2*i+1]
            nums[2*i+1] = temp

        flipped.write(",".join(nums)+"\n")

    flipped.close();
    raw.close();
    raw = open("flipped.csv", "r")

    fields = raw.readline().split(",")
    while True:
        line = raw.readline().strip()
        if not line:
            break

        cycles += 1
        str_nums = line.split(",")
        nums = [int(thing) for thing in str_nums]

        to_write = ""

        for i, num in enumerate(nums):
            width = 16
            if 'config_config' in fields[i]:
                width = 32
            elif 'read_config_data_in' == fields[i]:
                width = 32

            if 'stall' in fields[i]:
                if num == 1:
                    if not first_stall:
                        first_stall = True
                    config_cycles += 1
                elif not first_stall:
                    config_cycles += 1

            hex_num = get_hex(num, int(width/4))
            if width == 32:
                hex_num = hex_num[0:4] + "_" + hex_num[4:8]
            to_write = "_" + hex_num + to_write
        f.write(to_write[1:])
        f.write("\n")
    
    f.close()
    raw.close()

    # OUTPUTS
    f = open("test_outputs.txt", "w")
    raw = open("raw_output.csv", "r") 

    # first flip the inputs so we can use the same defines
    flipped = open("flipped.csv", "w")
    while True:
        line = raw.readline().strip()
        if not line:
            break

        str_nums = line.split(",")
        nums = [thing for thing in str_nums]

        for i in range(20):
            temp = nums[2*i];
            nums[2*i] = nums[2*i+1]
            nums[2*i+1] = temp

        flipped.write(",".join(nums)+"\n")

    flipped.close();
    raw.close();
    raw = open("flipped.csv", "r")

    fields = raw.readline().split(",")
    while True:
        line = raw.readline().strip()
        if not line:
            break

        str_nums = line.split(",")
        nums = [int(thing) for thing in str_nums]

        to_write = ""

        for i, num in enumerate(nums):
            if 'hi' == fields[i] or 'lo' == fields[i]:
                continue

            width = 16
            if 'config_out_config' in fields[i]:
                width = 32
            elif 'read_config_data' == fields[i]:
                width = 32

            hex_num = get_hex(num, int(width/4))
            if width == 32:
                hex_num = hex_num[0:4] + "_" + hex_num[4:8]
            to_write = "_" + hex_num + to_write
        f.write(to_write[1:])
        f.write("\n")

    f.close()
    raw.close()
    
    # DEFINES
    defines = open('defines.v', 'w')
    clk_period = float(os.getenv('clock_period'))
    assignment_delay = 0.2
    #config_time = math.ceil(config_cycles*clk_period)
    #finish_time = math.floor(cycles*clk_period+clk_period/2)
    config_time = math.ceil(21294*clk_period)
    finish_time = math.floor((21294+4300)*clk_period+clk_period/2)
    defines.write(f"`define CONFIG_TIME {config_time}\n")
    #defines.write(f"`define CLK_PERIOD {clk_period}\n")
    defines.write(f"`define ASSIGNMENT_DELAY {assignment_delay}\n")
    defines.write(f"`define RUN_TIME {finish_time-config_time}\n")
    defines.write(f"`define NUM_TEST_VECTORS {cycles}\n")
    defines.close()

    # NCSIM TCL
    tcl = open('cmd.tcl', 'w')
    tcl.write(f'database -open -vcd vcddb -into verilog.vcd -default -timescale ps\n')
    tcl.write(f'probe -create -all -vcd -depth all\n')
    tcl.write(f'run {config_time}\n')
    tcl.write(f'dumpsaif -scope TilePETb -hierarchy -internal -output outputs/run.saif -overwrite\n')
    tcl.write(f'run {finish_time-config_time}\n')
    tcl.write('dumpsaif -end\n')
    tcl.write('quit\n')
    tcl.close()

if __name__ == '__main__':
    main()
