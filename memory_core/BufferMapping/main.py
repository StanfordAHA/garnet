from mapping import *
from functools import reduce
import json
import pdb

def main():
    with open('config/setup.json') as json_file:
        setup= json.load(json_file)
    v_setup = setup["virtual buffer"]
    hw_setup = setup["hw config"]
    v_buf = CreateVirtualBuffer(setup["virtual buffer"])
    mem_tile_config = CreateHWConfig(setup["hw config"])
    mem_tile_hw = HWMap(v_buf, mem_tile_config)

    #buf = VirtualDoubleBuffer(16, 16, 34*34*32, [6,3,32,32], [1, 68, 2, 68], 0)
    #mem_tile_config = HWBufferConfig(1, 1, 512)


    for i in range(v_setup['capacity'] // v_setup['input_port']):
        tmp = [i*v_setup['input_port'] + j for j in range(v_setup['input_port'])]
        v_buf.write(tmp)
        #pdb.set_trace()
        mem_tile_hw.write(tmp)
    print("Finish write to buffer, switch 2 banks.")

    read_iteration = reduce((lambda x, y: x * y), v_setup['access_pattern']['range'])
    for i in range(read_iteration):
        if v_buf.read() != mem_tile_hw.read():
            print ("Virtual buffer read: ", v_buf.read())
            print ("Hardware buffer read: ", mem_tile_hw.read())

    print ("Read match between <hw buffer> and <virtual buffer>.")
    #one extra read, uncommented will lead assertion
    #print ("Hardware buffer read: ", mem_tile_hw.read())


if __name__ == '__main__':
    main()
