def next_tck(n=1):
    tester.eval()
    for _ in range(n):
        tester.circuit.jtag_tck = 1
        tester.eval()
        tester.circuit.jtag_tck = 0
        tester.eval()

def reset_jtag(use_trst_n=False):
    if use_trst_n:
        tester.circuit.jtag_tms = 1
        tester.circuit.jtag_trst_n = 0
        next_tck()
        tester.circuit.jtag_trst_n = 1
        next_tck()
    else:
        # clear jtag signals
        tester.circuit.jtag_trst_n = 1
        tester.circuit.jtag_tdi = 0
        tester.circuit.jtag_tms = 0
        next_tck()

        # reset jtag
        tester.circuit.jtag_tms = 1
        next_tck(5)

def shift_dr(data, length):
    # TODO for now we assume we are in run-test/idle state

    # Move to Select-DR-Scan state
    tester.circuit.jtag_tms = 1
    next_tck()

    # Move to Capture-DR state
    tester.circuit.jtag_tms = 0
    next_tck()

    # Move to Shift-DR state
    tester.circuit.jtag_tms = 0
    next_tck()

    # Remain in Shift-DR state andn shift in data
    res = 0
    for l in range(length):
        tester.circuit.jtag_tdi = (data & (1 << l)) >> l
        tester.circuit.jtag_tms = (l == length - 1)  # Move to Exit1-DR
        next_tck()
        # res |= tester.circuit.jtag_tdo << l  # TODO not supported yet

    # Move to Update-DR state
    tester.circuit.jtag_tms = 1
    next_tck()

    # Move to Run-Test/Idle state
    tester.circuit.jtag_tms = 0
    next_tck()

    # TODO not supported yet
    # # Return DR
    # return res

def shift_ir(data, length):
    # TODO for now we assume we are in run-test/idle state

    # Move to Select-DR-Scan state
    tester.circuit.jtag_tms = 1
    next_tck()

    # Move to Select-IR-Scan state
    tester.circuit.jtag_tms = 1
    next_tck()

    # Move to Capture-IR state
    tester.circuit.jtag_tms = 0
    next_tck()

    # Move to Shift-IR state
    tester.circuit.jtag_tms = 0
    next_tck()

    # Remain in Shift-IR state andn shift in data
    res = 0
    for l in range(length):
        tester.circuit.jtag_tdi = (data & (1 << l)) >> l
        tester.circuit.jtag_tms = (l == length - 1)  # Move to Exit1-IR
        next_tck()
        # res |= tester.circuit.jtag_tdo << l  # TODO not supported yet

    # Move to Update-IR state
    tester.circuit.jtag_tms = 1
    next_tck()

    # Move to Run-Test/Idle state
    tester.circuit.jtag_tms = 0
    next_tck()

    # TODO not supported yet
    # # Return IR
    # return res

# # Test-Logic-Reset
# reset_jtag()

# # Run-Test/Idle
# tester.circuit.jtag_tms = 0
# next_tck()

# sc_cfg_data = 8
# sc_cfg_inst = 9
# sc_cfg_addr = 10

# JTAG_WRITE_A050 = 4
# JTAG_SWITCH_CLK = 12

# jtag_inst_bits = 5

# def jtag_addr_data(addr, data):
#     shift_ir(sc_cfg_inst, jtag_inst_bits)
#     shift_dr(addr, jtag_inst_bits)
#     shift_ir(sc_cfg_data, jtag_inst_bits)
#     # TODO not sure if always 32 for all registers
#     shift_dr(data, 32)

# def jtag_data_addr(data, addr):
#     shift_ir(sc_cfg_data, jtag_inst_bits)
#     # TODO not sure if always 32 for all registers
#     shift_dr(data, 32)
#     shift_ir(sc_cfg_inst, jtag_inst_bits)
#     shift_dr(addr, jtag_inst_bits)

# # Test A050
# jtag_addr_data(JTAG_WRITE_A050, 0xC0DE)

# # Switch clocks
# jtag_data_addr(1, JTAG_SWITCH_CLK)

# # wait until the system clock stabilizes
# loop = tester.rawloop('top->v__DOT__GlobalController_32_32_inst0__DOT__global_controller_inst0__DOT__sys_clk_activated == 0')  # noqa
# loop.eval()
# loop.poke(tester._circuit.jtag_tck, 1)
# loop.eval()
# loop.poke(tester._circuit.jtag_tck,  0)
# loop.eval()

# tester.circuit.clk_in = 0

# # wait some more
# tester.step(10)
