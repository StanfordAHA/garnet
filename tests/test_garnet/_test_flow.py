import argparse
import fault
import magma
import textwrap
import re
import types
import struct
from inspect import currentframe
import json
import random
import sys
import time


def linum():
    cf = currentframe()
    return cf.f_back.f_lineno


next_opcode = -1
def new_opcode():
    global next_opcode
    next_opcode = next_opcode + 1
    return next_opcode

class NOP:
    opcode = new_opcode()

    def __init__(self):
        pass

    def ser(self):
        return [NOP.opcode]

    def sim(self, tester):
        tester.step(2)

    @staticmethod
    def interpret():
        return """
        // poke DMA to copy commands over
        """

# input        axi4_ctrl_rready,
# input [31:0] axi4_ctrl_araddr,
# input        axi4_ctrl_arvalid,

# input [31:0] axi4_ctrl_awaddr,
# input        axi4_ctrl_awvalid,
# input [31:0] axi4_ctrl_wdata,
# input        axi4_ctrl_wvalid,

# output        axi4_ctrl_arready,
# output [31:0] axi4_ctrl_rdata,
# output  [1:0] axi4_ctrl_rresp,
# output        axi4_ctrl_rvalid,

# output        axi4_ctrl_awready,
# output        axi4_ctrl_wready,

# output        axi4_ctrl_interrupt,



class WRITE_REG:
    opcode = new_opcode()

    def __repr__(self):
        return f"writing 0x{self.data:08x} to 0x{self.addr:08x}"

    def __init__(self, addr, data):
        self.addr = addr
        self.data = data

    def ser(self):
        return [WRITE_REG.opcode, self.addr, self.data]

    def sim(self, tester):
        tester.print(f"{self}\n")
        # drive inputs
        tester.clear_inputs()
        # tester.circuit.axi4_ctrl_wvalid = 1
        tester.poke(tester._circuit.axi4_ctrl_wvalid, 1)
        # tester.circuit.axi4_ctrl_wdata = self.data
        tester.poke(tester._circuit.axi4_ctrl_wdata, self.data)
        # tester.circuit.axi4_ctrl_awvalid = 1
        tester.poke(tester._circuit.axi4_ctrl_awvalid, 1)
        # tester.circuit.axi4_ctrl_awaddr = self.addr
        tester.poke(tester._circuit.axi4_ctrl_awaddr, self.addr)

        # propagate inputs
        tester.eval()

        # loop = tester._while(
        #     tester.expect(tester._circuit.axi4_ctrl_awready, 0))
        # loop.step(2)
        loop = tester.rawloop(
            '(top->axi4_ctrl_awvalid & top->axi4_ctrl_awready) == 0')
        loop.step(2)

        # tester.circuit.axi4_ctrl_awready.expect(1)
        tester.expect(tester._circuit.axi4_ctrl_awready, 1)

        # loop = tester._while(
        #     tester.expect(tester._circuit.axi4_ctrl_wready, 0))
        # loop.step(2)
        loop = tester.rawloop(
            '(top->axi4_ctrl_wvalid & top->axi4_ctrl_wready) == 0')
        loop.step(2)

        # tester.circuit.axi4_ctrl_awvalid = 0
        tester.poke(tester._circuit.axi4_ctrl_awvalid, 0)
        # tester.circuit.axi4_ctrl_wready.expect(1)
        tester.expect(tester._circuit.axi4_ctrl_wready, 1)

        tester.eval()

        tester.step(2)  # HACK
        # tester.circuit.axi4_ctrl_wvalid = 0
        tester.poke(tester._circuit.axi4_ctrl_wvalid, 0)

        tester.eval()

        tester.step(2)

    @staticmethod
    def interpret():
        return """
        *ARG_1 = ARG_2;
        """


# HACK this function doesn't even really exist outside of simulation
class READ_REG:
    opcode = None

    def __repr__(self):
        return f"expecting 0x{self.expected:08x} at 0x{self.addr:08x}"

    def __init__(self, addr, expected):
        self.addr = addr
        self.expected = expected  # HACK only used for simulation

    def ser(self):
        return [WRITE_REG.opcode, self.addr]

    def sim(self, tester):
        # drive inputs
        tester.clear_inputs()
        # tester.circuit.axi4_ctrl_araddr = self.addr
        tester.poke(tester._circuit.axi4_ctrl_araddr, self.addr)
        # tester.circuit.axi4_ctrl_arvalid = 1
        tester.poke(tester._circuit.axi4_ctrl_arvalid, 1)

        tester.eval()

        # loop = tester._while(
        #     tester.expect(tester._circuit.axi4_ctrl_arready, 0))
        # loop.step(2)
        loop = tester.rawloop(
            '(top->axi4_ctrl_arvalid & top->axi4_ctrl_arready) == 0')
        loop.step(2)

        tester.print(f"_test_flow.py({linum()})\n")

        tester.step(2)  # HACK
        # tester.circuit.axi4_ctrl_arvalid = 0
        tester.poke(tester._circuit.axi4_ctrl_arvalid, 0)
        # tester.circuit.axi4_ctrl_rready = 1
        tester.poke(tester._circuit.axi4_ctrl_rready, 1)
        tester.eval()

        loop = tester.rawloop(
            '(top->axi4_ctrl_rvalid & top->axi4_ctrl_rready) == 0')
        loop.step(2)

        # tester.circuit.axi4_ctrl_rvalid.expect(1)
        tester.expect(tester._circuit.axi4_ctrl_rvalid, 1)
        # tester.circuit.axi4_ctrl_rdata.expect(self.expected)
        tester.expect(tester._circuit.axi4_ctrl_rdata, self.expected)

        tester.step(2)  # HACK
        # tester.circuit.axi4_ctrl_rready = 0
        tester.poke(tester._circuit.axi4_ctrl_rready, 0)

        tester.eval()  # HACK
        tester.step(2)  # HACK

    @staticmethod
    def interpret():
        pass


# input [21:0] soc_data_rd_addr,
# output [63:0] soc_data_rd_data,
# input  soc_data_rd_en,

# input [21:0] soc_data_wr_addr,
# input [63:0] soc_data_wr_data,
# input [7:0] soc_data_wr_strb


class WRITE_DATA:
    opcode = new_opcode()

    def __repr__(self):
        return f"writing {self.size} bytes from 0x{self.src:08x} to 0x{self.dst:08x}"

    def __init__(self, dst, src, size, data):
        self.dst = dst
        self.src = src
        self.size = size  # in bytes
        self.data = data  # HACK only used for simulation

    def ser(self):
        return [WRITE_DATA.opcode, self.dst, self.src, self.size]

    def sim(self, tester):
        tester.print(f"{self}\n")  # noqa

        for k in range(0, len(self.data), 8):
            # drive inputs
            tester.clear_inputs()
            # tester.circuit.soc_data_wr_addr = self.dst
            tester.poke(tester._circuit.soc_data_wr_addr, self.dst + k)
            # tester.circuit.soc_data_wr_data = self.data[k:k + 8]
            tester.poke(tester._circuit.soc_data_wr_data, self.data[k:k + 8])
            # tester.circuit.soc_data_wr_strb = 0b11111111
            tester.poke(tester._circuit.soc_data_wr_strb, 0b11111111)

            # propagate inputs
            tester.eval()
            tester.step(2)

            # tester.circuit.soc_data_wr_strb = 0
            tester.poke(tester._circuit.soc_data_wr_strb, 0)
            tester.eval()
            tester.step(2)  # HACK

    @staticmethod
    def interpret():
        return """
        // memcpy(ARG_1, ARG_2, ARG_3);
        """


# HACK shouldn't exist outside of simulation, just switch src and dst.
class READ_DATA:
    opcode = None

    def __repr__(self):
        return f"reading {self.size} bytes from 0x{self.src:08x}"

    def __init__(self, src, size, data, _file=None):
        self.src = src
        self.size = size  # in bytes
        self.data = data  # HACK only used for simulation
        self._file = _file

    def ser(self):
        return []

    def sim(self, tester):
        tester.print(f"{self}\n")

        for k in range(0, len(self.data), 8):
            # drive inputs
            tester.clear_inputs()
            # tester.circuit.soc_data_rd_addr = self.src
            tester.poke(tester._circuit.soc_data_rd_addr, self.src + k)
            # tester.circuit.soc_data_rd_en = 1
            tester.poke(tester._circuit.soc_data_rd_en, 1)

            # propagate inputs
            tester.eval()
            tester.step(2)

            # tester.circuit.soc_data_rd_en = 0
            tester.poke(tester._circuit.soc_data_rd_en, 0)
            tester.eval()
            tester.step(2)

            # tester.circuit.soc_data_rd_data.expect(self.data)
            # HACK might not work in fault because of 64-bit comparison
            # tester.expect(tester._circuit.soc_data_rd_data, self.data[k:k + 8])
            tester.print("%016llx\n", tester._circuit.soc_data_rd_data)
            tester.file_write(self._file, tester._circuit.soc_data_rd_data)

    @staticmethod
    def interpret():
        return """
        // memcpy(ARG_1, ARG_2, ARG_3);
        """


class WAIT:
    opcode = new_opcode()

    def __init__(self):
        pass

    def ser(self):
        return []

    def sim(self, tester):
        tester.print("Waiting for CGRA done pulse...\n")

        # TODO only waits on cgra done, doesn't wait on dma, etc. yet
        # HACK waits on cgra_done_pulse, should wait on the interrupt instead
        loop = tester.rawloop(
            '(top->v__DOT__GlobalBuffer_32_2_2_17_32_32_32_12_inst0__DOT__global_buffer_inst0___05Fcgra_done_pulse) == 0')
        loop.step(2)

        tester.step(2)
        tester.step(2)
        tester.step(2)
        tester.step(2)
        tester.step(2)
        tester.step(2)

    @staticmethod
    def interpret():
        pass


ops = [
    NOP,
    WRITE_REG,
    WRITE_DATA,
]


def create_interpreter(ops):
    defines = """
    #define OPCODE (*PC)
    #define ARG_1  (*(PC+1))
    #define ARG_2  (*(PC+2))
    #define ARG_3  (*(PC+3))
    #define ARG_4  (*(PC+4))
    """

    src = """
    switch (OPCODE) {
    """

    for op in ops:
        args_used = [int(x) for x in re.findall(r"ARG_(\d+)", op.interpret())]
        incr = 1 + max([0] + args_used)
        src += f"""
        case {op.opcode}: // {op}
            {op.interpret()}
            PC += {incr};
            break;
        """

    src += """
    }
    """

    return src


print(create_interpreter(ops))


def pack_data(data):
    """
    Converts an array of Python ints to a bytestring to be passed into Fault.
    """
    return struct.pack("{}I".format(len(data)), *data)


def test_flow(args):
    if args.from_verilog:
        dut = magma.DefineFromVerilogFile(
            'garnet.v',
            target_modules=['Garnet'],
            type_map={
                "clk_in": magma.In(magma.Clock)
            },
            shallow=True,
        )[0]
    else:
        # this import is kinda slow so only do it if needed
        from garnet import Garnet
        dut = Garnet(width=8, height=4, add_pd=False).circuit

    print(dut)

    tester = fault.Tester(dut, clock=dut.clk_in)

    # Reset the CGRA (active high)
    def reset_cgra():
        tester.circuit.reset_in = 0
        tester.eval()
        tester.step(2)

        tester.circuit.reset_in = 1
        tester.eval()
        tester.step(2)

        tester.circuit.reset_in = 0
        tester.eval()
        tester.step(2)

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

    reset_cgra()

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
    # loop = tester.rawloop('top->v__DOT__GlobalController_32_32_inst0__DOT__global_controller_inst0__DOT__sys_clk_activated == 0')
    # loop.eval()
    # loop.poke(tester._circuit.jtag_tck, 1)
    # loop.eval()
    # loop.poke(tester._circuit.jtag_tck,  0)
    # loop.eval()

    # tester.circuit.clk_in = 0

    # # wait some more
    # tester.step(10)

    TEST_REG = 0x000
    GLOBAL_RESET_REG = 0x004
    STALL_REG = 0x008
    RD_DELAY_REG = 0x00c
    SOFT_RESET_DELAY_REG = 0x10
    CGRA_START_REG = 0x14
    CGRA_AUTO_RESTART_REG = 0x18
    CONFIG_START_REG = 0x1c
    INTERRUPT_ENABLE_REG = 0x20
    INTERRUPT_STATUS_REG = 0x24
    CGRA_SOFT_RESET_EN_REG = 0x28
    CGRA_CONFIG_ADDR_REG = 0x2c
    CGRA_CONFIG_DATA_REG = 0x30

    IO_INPUT_STREAM = 1
    IO_OUTPUT_STREAM = 2

    def IO_MODE_REG(n):
        return int(f'01{n:04b}{0:04b}00', 2)

    def IO_ADDR_REG(n):
        return int(f'01{n:04b}{1:04b}00', 2)

    def IO_SIZE_REG(n):
        return int(f'01{n:04b}{2:04b}00', 2)

    def IO_SWITCH_REG(n):
        return int(f'01{n:04b}{3:04b}00', 2)

    # each configuration controller has the following 3 registers
    # start_addr  # 32-bit
    # num_bitstream  # 32-bit
    # switch  # 32-bit

    # to write to controller, you should set the switch to 4'b1111
    # the bits are masks for the banks to be used.

    # if switch is 4'b1111 for configuration bank 0, it has access to
    # all 32 banks
    # - for bank 1, it would have access to 28 banks
    # - for bank 7 it would have access to 4 banks

    # in the simple case you just select the first controller and use
    # that to fan out to all columns, so controller[0] = 4'b1111, and
    # all the others are 4'b0000

    # IO Controller

    # change io controller to out stream mode
    # set start address for destination in global buffer
    # set size of expected output (in 16-bit words)

    # Configuration Controller

    # configuration is done through configuration controller
    # - size register in that controller which is in size of 64-bit
    #   addr/data pairs
    # msb 32-bits is address
    # lsb 32-bits is data

    # Address Mapping

    # Register space:
    # top 2-bits:
    #  00 -> register in global controller
    #  01 -> register in io controller
    #  10 -> register in parallel configuration controller

    # io controller
    #  01 aaaa bbbb 00
    #  aaaa -> select the io controller
    #  bbbb ->
    #   0 -> mode (controls direction, etc)
    #   1 -> start address
    #   2 -> number of words
    #   3 -> io switch
    #   4 -> delay for done signal (default/min = 0)

    # global controller
    # 00 aaaa bbbb 00

    # Global buffer addresses are 32 bits. The top 10 bits must be set
    # to 0. The next 5-bits of the remaining 22-bits indicate the bank
    # we are addressing, and the remaining 17-bits are an offset
    # within the bank.
    def BANK_ADDR(n):
        return int(f'{n:05b}{0:017b}', 2)

    seed = random.randrange(sys.maxsize)
    rng = random.seed(seed)
    print("Seed was:", seed)

    commands = [
        # Verify AXI working with TEST_REG
        WRITE_REG(TEST_REG, 0xDEADBEEF),
        READ_REG(TEST_REG, 0xDEADBEEF),
    ]

    # commands = []
    # with open('config.json', 'r') as f:
    #     reglist = json.load(f)
    #     for reg in reglist:
    #         for _ in range(10):
    #             val = random.randrange(reg['range'])
    #             commands += [
    #                 WRITE_REG(CGRA_CONFIG_ADDR_REG, reg['addr']),
    #                 WRITE_REG(CGRA_CONFIG_DATA_REG, val),
    #                 # WRITE_REG(CGRA_CONFIG_ADDR_REG, reg['addr']),
    #                 READ_REG(CGRA_CONFIG_DATA_REG, val),
    #             ]

    def gc_config_bitstream(filename):
        commands = []
        with open(filename, 'r') as f:
            for line in f:
                addr, data = (int(x,16) for x in line.strip().split(' '))
                commands += [
                    WRITE_REG(CGRA_CONFIG_ADDR_REG, addr),
                    WRITE_REG(CGRA_CONFIG_DATA_REG, data),
                    # WRITE_REG(CGRA_CONFIG_ADDR_REG, addr),
                    # READ_REG(CGRA_CONFIG_DATA_REG, data),
                ]
        return commands

    def gb_config_bitstream(filename):
        commands = []
        # # Write the bitstream to the global buffer
        # WRITE_DATA(0x1234, 0xc0ffee, 8, pack_data([0x00000003, 0x17070101])),
        # # Check the write
        # READ_DATA(0x1234, 8, pack_data([0x00000003, 0x17070101])),

        # # Set up global buffer for configuration
        # # TODO

        # # Configure the CGRA
        # # TODO
        raise NotImplementedError("Configuring bitstream through global buffer not yet implemented.")

    import numpy as np
    np.set_printoptions(formatter={'int':hex})
    im = np.fromfile('applications/conv_1_2/conv_1_2_input.raw', dtype=np.uint8).astype(np.uint16)
    gold = np.fromfile('applications/conv_1_2/conv_1_2_gold.raw', dtype=np.uint8).astype(np.uint16)

    def compare_results(gold, result):
        result = np.array(result, dtype=np.uint64)

        lo = np.bitwise_and(result, 0x00000000FFFFFFFF)
        hi = np.right_shift(np.bitwise_and(result, 0xFFFFFFFF00000000), 32)
        result = np.dstack((lo, hi)).flatten().astype(np.uint32)

        lo = np.bitwise_and(result, 0x0000FFFF)
        hi = np.right_shift(np.bitwise_and(result, 0xFFFF0000), 16)
        result = np.dstack((lo, hi)).flatten().astype(np.uint16)

        result = result.astype(np.uint8)

        for x,y in zip(gold, result):
            assert x == y

    result = np.loadtxt('result.raw', dtype=np.uint64, converters={0: lambda x: int(x, 16)})
    print(result)
    compare_results(gold, result)

    print(im[0:2])
    print(gold[0:2])

    commands = [
        WRITE_REG(GLOBAL_RESET_REG, 1),
        # Stall the CGRA
        WRITE_REG(STALL_REG, 0b1111),

        # Configure the CGRA
        *gc_config_bitstream('applications/conv_1_2/conv_1_2.bs'),

        # Set up global buffer for pointwise
        # IO controller 0 handles input
        WRITE_REG(IO_MODE_REG(0), IO_INPUT_STREAM),
        WRITE_REG(IO_ADDR_REG(0), BANK_ADDR(0)),
        WRITE_REG(IO_SIZE_REG(0), len(im)),
        WRITE_REG(IO_SWITCH_REG(0), 0b1111),
        # IO controller 1 handles output
        WRITE_REG(IO_MODE_REG(1), IO_OUTPUT_STREAM),
        # WRITE_REG(IO_ADDR_REG(1), BANK_ADDR(4)),
        WRITE_REG(IO_ADDR_REG(1), BANK_ADDR(16)),
        WRITE_REG(IO_SIZE_REG(1), len(gold)),
        WRITE_REG(IO_SWITCH_REG(1), 0b1111),

        # Put image into global buffer
        WRITE_DATA(BANK_ADDR(0), 0xc0ffee, im.nbytes, bytes(im)),

        # Start the application
        WRITE_REG(CGRA_SOFT_RESET_EN_REG, 1),
        WRITE_REG(SOFT_RESET_DELAY_REG, 2),
        NOP(),
        NOP(),
        NOP(),
        NOP(),
        NOP(),
        NOP(),
        WRITE_REG(STALL_REG, 0),
        NOP(),
        NOP(),
        NOP(),
        NOP(),
        WRITE_REG(CGRA_START_REG, 1),

        # TODO Wait a bit
        WAIT(),
        READ_DATA(BANK_ADDR(16), gold.nbytes, bytes(gold), _file=tester.file_open("logs/result.raw", "wb")),
    ]

    cmd_bitstream = [arg for command in commands for arg in command.ser()]
    print(cmd_bitstream)

    def clear_inputs(tester):
        # circuit.jtag_tck = 0
        tester.poke(tester._circuit.jtag_tck, 0)
        # circuit.jtag_tdi = 0
        tester.poke(tester._circuit.jtag_tdi, 0)
        # circuit.jtag_tms = 0
        tester.poke(tester._circuit.jtag_tms, 0)
        # circuit.jtag_trst_n = 1
        tester.poke(tester._circuit.jtag_trst_n, 1)

        # circuit.axi4_ctrl_araddr = 0
        tester.poke(tester._circuit.axi4_ctrl_araddr, 0)
        # circuit.axi4_ctrl_arvalid = 0
        tester.poke(tester._circuit.axi4_ctrl_arvalid, 0)
        # circuit.axi4_ctrl_rready = 0
        tester.poke(tester._circuit.axi4_ctrl_rready, 0)
        # circuit.axi4_ctrl_awaddr = 0
        tester.poke(tester._circuit.axi4_ctrl_awaddr, 0)
        # circuit.axi4_ctrl_awvalid = 0
        tester.poke(tester._circuit.axi4_ctrl_awvalid, 0)
        # circuit.axi4_ctrl_wdata = 0
        tester.poke(tester._circuit.axi4_ctrl_wdata, 0)
        # circuit.axi4_ctrl_wvalid = 0
        tester.poke(tester._circuit.axi4_ctrl_wvalid, 0)

    # HACK add clear_inputs to tester.circuit
    tester.clear_inputs = types.MethodType(clear_inputs, tester)

    # TODO reset_in
    # tester.circuit.reset_in = 0
    # tester.step(2)
    # tester.circuit.reset_in = 1
    # tester.step(2)

    print(f"Command list has {len(commands)} commands.")
    print("Generating testbench...")
    start = time.time()

    PC = 0
    for command in commands:
        tester.print(f"command: {command}\n")
        command.sim(tester)
        PC += 1

    tester.print("Success!\n")

    print(f"Testbench generation done. (Took {time.time() - start}s)")
    print("Running test...")

    tester.compile_and_run(
        target="verilator",
        directory="tests/build/",
        # circuit_name="Garnet",
        # include_verilog_libraries=["garnet.v"],
        flags=[
            '-Wno-UNUSED',
            '-Wno-PINNOCONNECT',
            '-Wno-fatal',
            '--trace' if args.debug else '',
            f'--trace-max-array {2**17}' if args.trace_mem else '',
            # '--no-debug-leak',
        ],
        skip_compile=not args.recompile,  # turn on to skip DUT compilation
        skip_verilator=not args.recompile,  # turn on to skip DUT compilation
        magma_output='verilog',
        magma_opts={"verilator_debug": True},
    )


def main():
    parser = argparse.ArgumentParser(description="""
    A simple SoC stub to test application flow of the CGRA.
    """)

    parser.add_argument('--recompile', action='store_true')
    parser.add_argument('--from-verilog', action='store_true')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--trace-mem', action='store_true')
    parser.add_argument('--profile', action='store_true')
    # parser.add_argument('--width', type=int, default=4)
    # parser.add_argument('--height', type=int, default=2)
    # parser.add_argument("--input-netlist", type=str, default="", dest="input")
    # parser.add_argument("--output-bitstream", type=str, default="",
    #                     dest="output")
    # parser.add_argument("-v", "--verilog", action="store_true")
    # parser.add_argument("--no-pd", "--no-power-domain", action="store_true")
    args = parser.parse_args()

    # assert args.width % 4 == 0 and args.width >= 4
    # garnet = Garnet(width=args.width, height=args.height, add_pd=not args.no_pd) # noqa
    if args.profile:
        cProfile.run('test_flow(args)', 'flow.prof')
    else:
        test_flow(args)

    # if args.verilog:
    #     garnet_circ = garnet.circuit()
    #     magma.compile("garnet", garnet_circ, output="coreir-verilog")
    # if len(args.input) > 0 and len(args.output) > 0:
    #     # do PnR and produce bitstream
    #     bitstream = garnet.compile(args.input)
    #     with open(args.output, "w+") as f:
    #         bs = ["{0:08X} {1:08X}".format(entry[0], entry[1]) for entry
    #               in bitstream]
    #         f.write("\n".join(bs))


if __name__ == "__main__":
    main()
