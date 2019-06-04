# TODO: would be nice to add a debug option that checks addresses on
# write_reg/write_data in the c code


# TODO: maybe the (uint8_t*) casts are not necessary in all the places
# I used them


from inspect import currentframe
import re
import numpy as np


next_opcode = -1
next_id = -1


def linum():
    cf = currentframe()
    return cf.f_back.f_lineno


def new_opcode():
    global next_opcode
    next_opcode += 1
    return next_opcode


def new_id():
    global next_id
    next_id += 1
    return next_id


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


def BANK_ADDR(n):
    return int(f'{n:05b}{0:017b}', 2)


def IO_MODE_REG(n):
    return int(f'01{n:04b}{0:04b}00', 2)


def IO_ADDR_REG(n):
    return int(f'01{n:04b}{1:04b}00', 2)


def IO_SIZE_REG(n):
    return int(f'01{n:04b}{2:04b}00', 2)


def IO_SWITCH_REG(n):
    return int(f'01{n:04b}{3:04b}00', 2)


class Command:
    def ser(self):
        return []

    def sim(self):
        pass

    def compile(self, _globals):
        return ""

    @staticmethod
    def interpret():
        pass


class NOP(Command):
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


class WRITE_REG(Command):
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

        # loop = tester._while(tester.circuit.axi4_ctrl_awready == 0)
        loop = tester._while(tester.peek(tester._circuit.axi4_ctrl_awready) == 0)
        loop.step(2)

        # tester.circuit.axi4_ctrl_awready.expect(1)
        tester.expect(tester._circuit.axi4_ctrl_awready, 1)

        # loop = tester._while(tester.circuit.axi4_ctrl_wready == 0)
        loop = tester._while(tester.peek(tester._circuit.axi4_ctrl_wready) == 0)
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

    def compile(self, _globals):
        return f"*(volatile uint32_t*)(uint8_t*)(CGRA_REG_BASE + 0x{self.addr:08x}) = 0x{self.data:x};"

    @staticmethod
    def interpret():
        # return [
        #     """
        #     #define CGRA_REG_BASE 0x40010000
        #     void WRITE_REG(uint32_t* REG_ADDR, uint32_t data) {
        #         *(volatile uint32_t*)(CGRA_REG_BASE + REG_ADDR) = data;
        #     }
        #     """,
        #     f"WRITE_REG(ARG_1, ARG_2);",
        # ]

        return """
        *ARG_1 = ARG_2;
        """


# HACK this function doesn't even really exist outside of simulation
class READ_REG(Command):
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

        # loop = tester._while(tester.circuit.axi4_ctrl_arready == 0)
        loop = tester._while(tester.peek(tester._circuit.axi4_ctrl_arready) == 0)
        loop.step(2)

        tester.print(f"_test_flow.py({linum()})\n")

        tester.step(2)  # HACK
        # tester.circuit.axi4_ctrl_arvalid = 0
        tester.poke(tester._circuit.axi4_ctrl_arvalid, 0)
        # tester.circuit.axi4_ctrl_rready = 1
        tester.poke(tester._circuit.axi4_ctrl_rready, 1)
        tester.eval()

        # loop = tester._while(tester.circuit.axi4_ctrl_rvalid & tester.circuit.axi4_ctrl_rready == 0)
        loop = tester._while(tester.peek(tester.circuit.axi4_ctrl_rvalid) & tester.peek(tester.circuit.axi4_ctrl_rready) == 0)
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

    def compile(self, _globals):
        return f"errors += *(volatile uint32_t*)(uint8_t*)(CGRA_REG_BASE + 0x{self.addr:08x}) != 0x{self.data:x}"

    @staticmethod
    def interpret():
        pass


# input [21:0] soc_data_rd_addr,
# output [63:0] soc_data_rd_data,
# input  soc_data_rd_en,

# input [21:0] soc_data_wr_addr,
# input [63:0] soc_data_wr_data,
# input [7:0] soc_data_wr_strb


class WRITE_DATA(Command):
    opcode = new_opcode()

    def __repr__(self):
        return f"writing {self.size} bytes from 0x{self.src:08x} to 0x{self.dst:08x}"  # noqa

    def __init__(self, dst, src, size, data):
        self.dst = dst
        self.src = src
        self.size = size  # in bytes
        self.data = data  # HACK only used for simulation

    def ser(self):
        return [WRITE_DATA.opcode, self.dst, self.src, self.size]

    def sim(self, tester):
        data = self.data.view(np.uint64)
        tester.print(f"{self}\n")  # noqa

        np.set_printoptions(formatter={'int': hex})

        for k in range(0, self.size, 8):
            # drive inputs
            tester.clear_inputs()
            # tester.circuit.soc_data_wr_addr = self.dst
            tester.poke(tester._circuit.soc_data_wr_addr, self.dst + k)
            # tester.circuit.soc_data_wr_data = self.data[k:k + 8]
            tester.poke(tester._circuit.soc_data_wr_data, int(data[k // 8]))
            # tester.circuit.soc_data_wr_strb = 0b11111111
            tester.poke(tester._circuit.soc_data_wr_strb, 0b11111111)

            # propagate inputs
            tester.eval()
            tester.step(2)

            # tester.circuit.soc_data_wr_strb = 0
            tester.poke(tester._circuit.soc_data_wr_strb, 0)
            tester.eval()
            tester.step(2)  # HACK

    def compile(self, _globals):
        data = self.data.view(np.uint64)
        array_id = f"data_{new_id()}"
        vals = []
        for k in range(len(data)):
            vals.append(f"0x{data[k]:x}")
        _globals += [f"uint64_t {array_id}[] = {{" , ",\n".join(vals), "};"]

        return f"""
        for (size_t k = 0; k < {len(self.data)}; k += 8) {{
            *(volatile uint64_t*)(uint8_t*)(CGRA_DATA_BASE + 0x{self.dst:08x} + k) = {array_id}[k/8];
        }}
        """

        # src = []
        # for k in range(0, len(self.data), 8):
        #     temp = bytearray(self.data[k:k + 8])
        #     temp.reverse()
        #     src.append(f"*(volatile uint64_t*)(CGRA_DATA_BASE + 0x{self.dst + k:08x}) = {array_id}[{k//8}];")
        # return "\n".join(src)

    @staticmethod
    def interpret():
        return """
        // memcpy(ARG_1, ARG_2, ARG_3);
        """


# HACK shouldn't exist outside of simulation, just switch src and dst.
class READ_DATA(Command):
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

        for k in range(0, self.size, 8):
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

            # Can't get this to work because sometimes you have only
            # 8-bit input but you need to compare against 16-bit
            # output and there's not a consistent way to specify which
            # bits you do and dont care about matching. It also varies
            # from application to application so this is kind of
            # messy.

            # tester.expect(tester._circuit.soc_data_rd_data, self.data[k:k + 8])  # noqa
            tester.file_write(self._file, tester._circuit.soc_data_rd_data)

    def compile(self, _globals):
        src = []
        for k in range(0, len(self.data), 8):
            temp_id = f"temp_{new_id()}"
            # src.append(f"uint64_t {temp_id} = *(volatile uint64_t*)(uint8_t*)(CGRA_DATA_BASE + 0x{self.src + k:08x});")
            # src.append(f'printf("0x%08x", {temp_id} >> 32);')
            # src.append(f'printf("%08x\\n", {temp_id});')
            src.append(f"print_hex64(*(volatile uint64_t*)(uint8_t*)(CGRA_DATA_BASE + 0x{self.src + k:08x}));")
            # src.append(f'printf("0x%" PRIx64 "\\n", *(volatile uint64_t*)(uint8_t*)(CGRA_DATA_BASE + 0x{self.src + k:08x}));')  # doesn't work on ARM, just prints '0xlx'
            # src.append(f"errors += *(volatile uint64_t*)(CGRA_DATA_BASE + 0x{self.src + k:08x}) != 0x{self.data[k:k + 8]:x};")
        return "\n".join(src)

    @staticmethod
    def interpret():
        return """
        // memcpy(ARG_1, ARG_2, ARG_3);
        """


class WAIT(Command):
    opcode = new_opcode()

    def __init__(self):
        pass

    def ser(self):
        return []

    def sim(self, tester):
        # TODO: only waits on cgra done, doesn't wait on dma, etc. yet

        # HACK: waits on cgra_done_pulse, should wait on the interrupt instead

        tester.print("Waiting for CGRA_START to go low...\n")

        # drive inputs
        tester.clear_inputs()
        # tester.circuit.axi4_ctrl_araddr = self.addr
        tester.poke(tester._circuit.axi4_ctrl_araddr, CGRA_START_REG)
        # tester.circuit.axi4_ctrl_arvalid = 1
        tester.poke(tester._circuit.axi4_ctrl_arvalid, 1)

        tester.eval()

        # loop = tester._while(tester.circuit.axi4_ctrl_arready == 0)
        loop = tester._while(tester.peek(tester._circuit.axi4_ctrl_arready) == 0)
        loop.step(2)

        tester.step(2)  # HACK
        # tester.circuit.axi4_ctrl_arvalid = 0
        tester.poke(tester._circuit.axi4_ctrl_arvalid, 0)
        # tester.circuit.axi4_ctrl_rready = 1
        tester.poke(tester._circuit.axi4_ctrl_rready, 1)
        tester.eval()

        # loop = tester._while(tester.circuit.axi4_ctrl_rvalid & tester.circuit.axi4_ctrl_rready == 0)
        loop = tester._while(tester.peek(tester._circuit.axi4_ctrl_rvalid) == 0)
        loop.step(2)

        # tester.circuit.axi4_ctrl_rvalid.expect(1)
        tester.expect(tester._circuit.axi4_ctrl_rvalid, 1)
        # tester.circuit.axi4_ctrl_rdata.expect(self.expected)
        # loop2 = tester._while(tester.circuit.axi4_ctrl_rdata != 0)
        loop2 = tester._while(tester.peek(tester._circuit.axi4_ctrl_rdata) != 0)
        loop2.step(2)  # HACK
        loop2.poke(tester._circuit.axi4_ctrl_rready, 0)

        loop2.eval()  # HACK
        loop2.step(2)  # HACK

        # drive inputs
        loop2.poke(tester._circuit.jtag_tck, 0)
        loop2.poke(tester._circuit.jtag_tdi, 0)
        loop2.poke(tester._circuit.jtag_tms, 0)
        loop2.poke(tester._circuit.jtag_trst_n, 1)

        loop2.poke(tester._circuit.axi4_ctrl_araddr, 0)
        loop2.poke(tester._circuit.axi4_ctrl_arvalid, 0)
        loop2.poke(tester._circuit.axi4_ctrl_rready, 0)
        loop2.poke(tester._circuit.axi4_ctrl_awaddr, 0)
        loop2.poke(tester._circuit.axi4_ctrl_awvalid, 0)
        loop2.poke(tester._circuit.axi4_ctrl_wdata, 0)
        loop2.poke(tester._circuit.axi4_ctrl_wvalid, 0)

        # loop2.circuit.axi4_ctrl_araddr = self.addr
        loop2.poke(tester._circuit.axi4_ctrl_araddr, CGRA_START_REG)
        loop2.poke(tester._circuit.axi4_ctrl_arvalid, 1)

        loop2.eval()

        # loop = loop2._while(tester.circuit.axi4_ctrl_arready == 0)
        loop = loop2._while(tester.peek(tester._circuit.axi4_ctrl_arready) == 0)
        loop.step(2)

        loop2.step(2)  # HACK
        loop2.poke(tester._circuit.axi4_ctrl_arvalid, 0)
        loop2.poke(tester._circuit.axi4_ctrl_rready, 1)
        loop2.eval()

        # loop = loop2._while(tester.circuit.axi4_ctrl_rvalid & tester.circuit.axi4_ctrl_rready == 0)
        loop = loop2._while(tester.peek(tester._circuit.axi4_ctrl_rvalid) == 0)
        loop.step(2)

        # loop2.circuit.axi4_ctrl_rvalid.expect(1)
        loop2.expect(tester._circuit.axi4_ctrl_rvalid, 1)


        tester.step(2)  # HACK
        # tester.circuit.axi4_ctrl_rready = 0
        tester.poke(tester._circuit.axi4_ctrl_rready, 0)

        tester.eval()  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK
        tester.step(2)  # HACK

    def compile(self, _globals):
        return f"while(*(volatile uint32_t*)(uint8_t*)(CGRA_REG_BASE + 0x{CGRA_START_REG:x}));"

    @staticmethod
    def interpret():
        pass


ops = [
    NOP,
    WRITE_REG,
    WRITE_DATA,
]


def create_command_bitstream(commands):
     return [arg for command in commands for arg in command.ser()]


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


def create_straightline_code(ops):
    _globals = []
    test_body = "\n".join([op.compile(_globals) for op in ops])

    src = """
    #include "AHASOC.h"
    #include "stdio.h"
    #include "stdint.h"
    #include "inttypes.h"
    #include "uart_stdout.h"

    #define CGRA_REG_BASE 0x40010000
    #define CGRA_DATA_BASE 0x20400000
    """

    src += "\n".join(_globals)

    src += """
    int main() {
        // UART init
        UartStdOutInit();

        uint32_t errors = 0;
        printf("Starting test...\\n");
    """

    src += test_body

    src += """
        if(errors) printf("TEST FAILED (%u errors)\\n", errors);
        else printf("TEST PASSED!\\n");

        // End simulation
        UartEndSimulation();

        return 0;
    }
    """

    return src



print(create_interpreter(ops))
