from bit_vector import BitVector
from global_controller.global_controller import (gen_global_controller,
                                                 GC_reg_addr)
import fault
import random


def test_global_controller_functional_model():
    CONFIG_DATA_WIDTH = 32
    CONFIG_ADDR_WIDTH = 32
    CONFIG_OP_WIDTH = 5
    gc = gen_global_controller(CONFIG_DATA_WIDTH,
                               CONFIG_ADDR_WIDTH,
                               CONFIG_OP_WIDTH)
    gc_inst = gc()
    max_config_data = (2**CONFIG_DATA_WIDTH) - 1
    max_config_addr = (2**CONFIG_ADDR_WIDTH) - 1
    max_stall = (2**gc_inst.NUM_STALL_DOMAINS) - 1
    # Set some data to read later
    random_input = random.randint(1, max_config_data)
    gc_inst.set_config_data_in(random_input)
    random_addr = random.randint(1, max_config_addr)
    # read the random input data
    gc_inst.config_read(random_addr)
    # assert read immediately
    assert gc_inst.read[0] == 1
    # Read must be deasserted by the end of the top
    assert gc_inst.read[-1] == 0
    assert gc_inst.config_addr_out[0] == random_addr
    assert gc_inst.config_data_to_jtag[-1] == random_input

    # Try changing the read_delay
    new_rw_delay = random.randint(1, 20)
    gc_inst.write_GC_reg(GC_reg_addr.rw_delay_sel_addr, new_rw_delay)
    # assert that the register val was written properly
    assert gc_inst.rw_delay_sel[-1] == new_rw_delay

    # Now, verify that that change actually took effect
    # Perform a config write
    random_data = random.randint(1, max_config_data)
    random_addr = random.randint(1, max_config_addr)
    gc_inst.config_write(random_addr, random_data)
    # check that write was asserted and read wasn't
    assert len(gc_inst.write) == (new_rw_delay+1)
    assert all(gc_inst.write[0:new_rw_delay])
    assert gc_inst.write[-1] == 0
    assert len(gc_inst.read) == (new_rw_delay+1)
    assert all(rd == 0 for rd in gc_inst.read)
    assert all(addr == random_addr for addr in gc_inst.config_addr_out)
    assert all(data == random_data for data in gc_inst.config_data_out)

    # Now Try stalling
    new_stall = BitVector(random.randint(1, max_stall))
    gc_inst.write_GC_reg(GC_reg_addr.stall_addr, new_stall)
    assert gc_inst.stall[0] == new_stall
    assert len(gc_inst.stall) == 1

    # Now Try advancing the clk (Temporary stall deassertion)
    adv_clk_addr = BitVector.random(gc_inst.NUM_STALL_DOMAINS)
    adv_clk_duration = random.randint(1, 100)
    gc_inst.advance_clk(adv_clk_addr, adv_clk_duration)
    assert len(gc_inst.stall) == adv_clk_duration + 1
    # Make sure that we reverted back to original stall value at end
    assert gc_inst.stall[-1] == new_stall
    # Now check that stall was deasserted for the specified values
    for i in range(gc_inst.NUM_STALL_DOMAINS):
        if(adv_clk_addr[i] == 1):
            for j in range(adv_clk_duration):
                assert(gc_inst.stall[j][i] == 0)

    # Test Global Reset
    reset_duration = random.randint(1, 100)
    gc_inst.global_reset(reset_duration)
    assert len(gc_inst.reset_out) == reset_duration + 1
    assert all(gc_inst.reset_out[0:reset_duration])
