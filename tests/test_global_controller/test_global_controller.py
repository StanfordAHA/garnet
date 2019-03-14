from hwtypes import BitVector
from global_controller.global_controller import \
    gen_global_controller, GCOp, GCRegAddr
import random


# Function to read and write to global controller regs
# and perform checks
def check_gc_reg(gc_inst, reg: GCRegAddr):
    if (reg == GCRegAddr.TST_ADDR):
        rd_op = GCOp.READ_TST
        wr_op = GCOp.WRITE_TST
        width = gc_inst.TST[0].num_bits
    elif (reg == GCRegAddr.STALL_ADDR):
        rd_op = GCOp.READ_STALL
        wr_op = GCOp.WRITE_STALL
        width = gc_inst.stall[0].num_bits
    elif (reg == GCRegAddr.CLK_SEL_ADDR):
        rd_op = GCOp.READ_CLK_DOMAIN
        wr_op = GCOp.SWITCH_CLK
        width = 1
    elif (reg == GCRegAddr.RW_DELAY_SEL_ADDR):
        rd_op = GCOp.READ_RW_DELAY_SEL
        wr_op = GCOp.WRITE_RW_DELAY_SEL
        width = gc_inst.rw_delay_sel[0].num_bits
    elif (reg == GCRegAddr.CLK_SWITCH_DELAY_SEL_ADDR):
        rd_op = GCOp.READ_CLK_SWITCH_DELAY_SEL
        wr_op = GCOp.WRITE_CLK_SWITCH_DELAY_SEL
        width = 1
    random_data = BitVector.random(width)
    res = gc_inst(op=wr_op, data=random_data)
    # Now read it back
    res = gc_inst(op=rd_op)
    assert len(res.config_data_to_jtag) == 1
    assert res.config_data_to_jtag[0] == random_data


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
    max_stall = (2**gc_inst.num_stall_domains) - 1
    # Check wr_A050. What you'd do when you bring up the chip
    res = gc_inst(op=GCOp.WRITE_A050)
    assert len(res.config_data_to_jtag) == 1
    assert res.config_data_to_jtag[0] == 0xA050
    # Set some data to read later
    random_input = random.randint(1, max_config_data)
    gc_inst.set_config_data_in(random_input)
    random_addr = random.randint(1, max_config_addr)
    # read the random input data
    res = gc_inst(op=GCOp.CONFIG_READ, addr=random_addr)
    # assert read immediately
    assert res.read[0] == 1
    # Read must be deasserted by the end of the top
    assert res.read[-1] == 0
    assert res.config_addr_out[0] == random_addr
    assert res.config_data_to_jtag[-1] == random_input

    # Try changing the read_delay
    new_rw_delay = random.randint(1, 20)
    res = gc_inst(op=GCOp.WRITE_RW_DELAY_SEL, data=new_rw_delay)
    # assert that the register val was written properly
    assert res.rw_delay_sel[-1] == new_rw_delay

    # Now, verify that that change actually took effect
    # Perform a config write
    random_data = random.randint(1, max_config_data)
    random_addr = random.randint(1, max_config_addr)
    res = gc_inst(op=GCOp.CONFIG_WRITE, addr=random_addr, data=random_data)
    # check that write was asserted and read wasn't
    assert len(res.write) == (new_rw_delay + 1)
    assert all(res.write[0:new_rw_delay])
    assert res.write[-1] == 0
    assert len(res.read) == (new_rw_delay + 1)
    assert all(rd == 0 for rd in res.read)
    assert all(addr == random_addr for addr in res.config_addr_out)
    assert all(data == random_data for data in res.config_data_out)

    # Now Try stalling
    new_stall = BitVector(random.randint(1, max_stall))
    res = gc_inst(op=GCOp.WRITE_STALL, data=new_stall)
    assert res.stall[0] == new_stall
    assert len(res.stall) == 1

    # Now Try advancing the clk (Temporary stall deassertion)
    adv_clk_addr = BitVector.random(gc_inst.num_stall_domains)
    if (adv_clk_addr == 0):
        adv_clk_addr = adv_clk_addr + 1
    duration = random.randint(1, 100)
    res = gc_inst(op=GCOp.ADVANCE_CLK, addr=adv_clk_addr, data=duration)
    assert len(res.stall) == duration + 1
    # Make sure that we reverted back to original stall value at end
    assert res.stall[-1] == new_stall
    # Now check that stall was deasserted for the specified values
    for i in range(res.num_stall_domains):
        if(adv_clk_addr[i] == 1):
            for j in range(duration):
                assert(res.stall[j][i] == 0)

    # Test Global Reset
    reset_duration = random.randint(1, 100)
    res = gc_inst(op=GCOp.GLOBAL_RESET, data=reset_duration)
    assert len(res.reset_out) == reset_duration + 1

    # Write to and read from the rest of the GC regs
    for reg in GCRegAddr:
        check_gc_reg(gc_inst, reg)
