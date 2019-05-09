from memory_core.BufferMapping.mem.virtualbuffer import *
from memory_core.BufferMapping.mem.hardware import *

def CreateVirtualBuffer(setup):
    return VirtualDoubleBuffer(setup['input_port'],
                               setup['output_port'],
                               setup['capacity'],
                               setup['access_pattern']['range'],
                               setup['access_pattern']['stride'],
                               setup['access_pattern']['start'],
                               setup['manual_switch'])

def CreateHWConfig(setup):
    return HWBufferConfig(setup['input_port'],
                          setup['output_port'],
                          setup['capacity'])

def HWMap(buf: VirtualDoubleBuffer, mem_config):
    # return value hold the banking and chainer mem_tile
    mem_tile_list = []

    #check the bandwidth requirement to create banking
    input_multiplier = buf._input_port // mem_config._input_port
    output_multiplier = int(buf._output_port / mem_config._output_port)
    num_bank = max(input_multiplier, output_multiplier)

    #check capacity requirement to do chaining
    capacity_per_bank = buf._capacity / num_bank
    if capacity_per_bank > mem_config._capacity:
        #FIXME: need more test case to try if this heruistic based capacity assign is bug free
        # Assign the data with the granularity at the largest stride
        max_stride = max(buf.read_iterator._st)
        capacity_per_tile =int( mem_config._capacity / max_stride) * max_stride

        capacity_reminder = capacity_per_bank
        capacity_start_addr = 0

        #chaining the tile
        while capacity_reminder > capacity_per_tile:

            # create a memory tile instance and chained with the previous block if exist
            mem_tile = MemoryTile(mem_config, buf.read_iterator, capacity_start_addr, capacity_start_addr + capacity_per_tile, capacity_per_bank)
            mem_tile_list.append(mem_tile)

            capacity_reminder -= capacity_per_tile
            capacity_start_addr += capacity_per_tile

        #add last memory tile into list
        mem_tile = MemoryTile(mem_config, buf.read_iterator, capacity_start_addr, capacity_start_addr + capacity_per_tile, capacity_per_bank)
        mem_tile_list.append(mem_tile)

    else:
        mem_tile = MemoryTile(mem_config, buf.read_iterator, 0, capacity_per_bank, capacity_per_bank)
        mem_tile_list.append(mem_tile)

    #create the chained memory tile
    mem_chain = ChainedMemoryTile(mem_tile_list)

    #create the banking
    mem_chain_bank = BankedChainedMemoryTile(mem_chain, num_bank, buf._input_port, buf._output_port)

    return mem_chain_bank

