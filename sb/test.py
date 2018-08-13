import math


## TEMP ASSIGNMENTS ## 
feedthrough_outputs = "00"
registered_outputs = "11"
sides = 4
num_tracks = 2
pe_output_count = 1
######################

CONFIG_DATA_WIDTH = 32

feedthrough_count = feedthrough_outputs.count("1")
registered_count = registered_outputs.count("1")
outputs_driven_per_side = num_tracks - feedthrough_count
mux_height = (sides - 1) + pe_output_count
mux_sel_bits = math.ceil(math.log(mux_height, 2))
config_bit_count = mux_sel_bits*sides*outputs_driven_per_side
config_bit_count += registered_count*sides
print("config_bit_count", config_bit_count)
num_config_regs = math.ceil(config_bit_count / CONFIG_DATA_WIDTH)
print("num_config_regs", num_config_regs)
for i in range(0, sides):
    for j in range(0, num_tracks):
        print ("sides is", sides)
        print ("Tracks is", num_tracks)
        print ("i & j are", i,j)
        temp = i+j
        print("tmp", temp)
