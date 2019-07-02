# TODO: would be nice to add a debug option that checks addresses on
# write_reg/write_data in the c code


# TODO: add a few flags that let you toggle between using global
# buffer and global controller to configure cgra, enable and disable
# use of interrupts, etc.


from inspect import currentframe
import re
import numpy as np


DMA = True
MEMCPY = False
TLX = True

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


def FR_ADDR_REG(n):
    return int(f'10{n:04b}{0:04b}00', 2)


def FR_SIZE_REG(n):
    return int(f'10{n:04b}{1:04b}00', 2)


def FR_SWITCH_REG(n):
    return int(f'10{n:04b}{2:04b}00', 2)


class Command:
    def ser(self):
        return []

    def sim(self, target):
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
        tester.zero_inputs()
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
        loop.poke(tester._circuit.axi4_ctrl_awvalid, 0)

        # tester.circuit.axi4_ctrl_wready.expect(1)
        tester.expect(tester._circuit.axi4_ctrl_wready, 1)

        tester.eval()

        tester.step(2)  # HACK
        # tester.circuit.axi4_ctrl_wvalid = 0
        tester.poke(tester._circuit.axi4_ctrl_wvalid, 0)

        tester.eval()

        tester.step(2)

    def compile(self, _globals):
        return f"*(volatile uint32_t*)(CGRA_REG_BASE + 0x{self.addr:08x}) = 0x{self.data:x};"

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
        tester.zero_inputs()
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
        return f"errors += *(volatile uint32_t*)(CGRA_REG_BASE + 0x{self.addr:08x}) != 0x{self.data:x}"

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
            tester.zero_inputs()
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
        print(len(data))

        array_id = f"data_{new_id()}"
        vals = []
        for k in range(len(data)):
            vals.append(f"0x{data[k]:x}")
        _globals['src'] += [f"uint64_t {array_id}[] = {{" , ",\n".join(vals), "};"]
        _globals['ids'] += [array_id]

        if TLX:
            array_id = f"tlx_{array_id}"

        if DMA:
            if MEMCPY:
                return f"""
                aha_memcpy((uint64_t*)(CGRA_DATA_BASE + 0x{self.dst:08x}), &({array_id}[0]), {len(data)});
                """
            else:
                print(array_id, self.size//8, len(data))
                num_beats = len(data)
                num_burst_16 = num_beats // 16
                num_burst_end = num_beats % 16
                print(num_beats, num_burst_16, num_burst_end)
                src = []
                if num_burst_16 // 256 > 0 :
                    src.append(f"""
                    for (size_t k = 0; k < {num_burst_16 // 256}; k++) {{
                        start_dma0((uint64_t*)(CGRA_DATA_BASE + 0x{self.dst:08x} + k*8*16*256), &({array_id}[k*16*256]), 16, 256);
                        wait_dma0();
                    }}
                    """)

                if num_burst_16 % 256 > 0:
                    src.append(f"""
                    start_dma0((uint64_t*)(CGRA_DATA_BASE + 0x{self.dst:08x} + {num_burst_16 // 256}*8*16*256), &({array_id}[{num_burst_16 // 256}*16*256]), 16, {num_burst_16 % 256});
                    wait_dma0();
                    """)

                if num_burst_end > 0:
                    src.append(f"""
                    start_dma0((uint64_t*)(CGRA_DATA_BASE + 0x{self.dst:08x} + {num_beats - num_burst_end}*8), &({array_id}[{num_beats - num_burst_end}]), {num_burst_end}, 1);
                    wait_dma0();
                    """)

                return "\n".join(src)
        else:
            return f"""
            for (size_t k = 0; k < {self.size}; k += 8) {{
                *(volatile uint64_t*)(CGRA_DATA_BASE + 0x{self.dst:08x} + k) = {array_id}[k/8];
            }}
           """

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
        # outfile = tester.file_open(self._file, "wb", 8)
        outfile = tester.file_open(self._file, "w", 8)

        for k in range(0, self.size, 8):
            # drive inputs
            tester.zero_inputs()
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
            tester.file_write(outfile, tester._circuit.soc_data_rd_data)

    def compile(self, _globals):
        if DMA:
            array_id = f"data_{new_id()}"
            size = self.size//8
            _globals['src'].append(f"uint64_t {array_id}[{size}];")
            _globals['ids'].append(array_id)
            src = []
            if MEMCPY:
                src.append(f"""
                aha_memcpy(&({array_id}[0]), (uint64_t*)(CGRA_DATA_BASE + 0x{self.src:08x}), {self.size//8});
                """)
            else:
                num_beats = size
                num_burst_16 = num_beats // 16
                num_burst_end = num_beats % 16
                print(num_beats, num_burst_16, num_burst_end)
                if num_burst_16 // 256 > 0 :
                    src.append(f"""
                    for (size_t k = 0; k < {num_burst_16 // 256}; k++) {{
                        start_dma1(&({array_id}[k*16*256]), (uint64_t*)(CGRA_DATA_BASE + 0x{self.src:08x} + k*8*16*256), 16, 256);
                        wait_dma1();
                    }}
                    """)

                if num_burst_16 % 256 > 0:
                    src.append(f"""
                    start_dma1(&({array_id}[{num_burst_16 // 256}*16*256]), (uint64_t*)(CGRA_DATA_BASE + 0x{self.src:08x} + {num_burst_16 // 256}*8*16*256), 16, {num_burst_16 % 256});
                    wait_dma1();
                    """)

                if num_burst_end > 0:
                    src.append(f"""
                    start_dma1(&({array_id}[{num_beats - num_burst_end}]), (uint64_t*)(CGRA_DATA_BASE + 0x{self.src:08x} + {num_beats - num_burst_end}*8), {num_burst_end}, 1);
                    wait_dma1();
                    """)

            src.append(f"""
            for (size_t k = 0; k < {self.size//8}; k++) {{
                print_hex64({array_id}[k]);
            }}
            """)

            return "\n".join(src)
        else:
            src = []
            for k in range(0, self.size, 8):
                src.append(f"print_hex64(*(volatile uint64_t*)(CGRA_DATA_BASE + 0x{self.src + k:08x}));")
            return "\n".join(src)

    @staticmethod
    def interpret():
        return """
        // memcpy(ARG_1, ARG_2, ARG_3);
        """


# TODO: this should probably be collapsed into wait by making the
# interrupt handler permanent.
class PEND(Command):
    opcode = None

    def __init__(self, mask, sem_id):
        self.mask = mask
        self.sem_id = f"sem_{sem_id}"

    def ser(self):
        return []

    def sim(self, tester):
        pass

    def compile(self, _globals):
        wait_id = f"wait_{new_id()}"

        # TODO: just resets the interrupt status register for now,
        # should tie to event and semaphores better. Needs to compare
        # to make sure that the status is what we are expecting if we
        # want to update this semaphore, and not block other
        # interrupts like if we want to wait for config but there is a
        # done signal that comes through. Also should install the
        # interrupt handler prior to starting the application,
        # probably.
        _globals['src'].append(f"""
        volatile uint32_t {self.sem_id} = 0;

        void {wait_id}(void) {{
            printf("Hello from {wait_id}!\\n");
            *(volatile uint32_t*)(CGRA_REG_BASE + 0x{INTERRUPT_STATUS_REG:x}) = *(volatile uint32_t*)(CGRA_REG_BASE + 0x{INTERRUPT_STATUS_REG:x});
            {self.sem_id} += 1;
            __SEV();
        }}
        """)

        return f"*(interrupt_handler_t*)(112) = &{wait_id};"



class WAIT(Command):
    opcode = new_opcode()

    def __init__(self, mask, sem_id):
        # TODO: should take an enum instead of a mask
        self.mask = mask
        # HACK: remove this for real semaphores
        self.sem_id = f"sem_{sem_id}"

    def ser(self):
        return []

    def sim(self, tester):
        # HACK: assumes that the correct interrupt is coming, doesn't
        # handle out of order interrupts.

        # for waiting on the interrupt from the cgra, the port will go
        # high and stay high. you need to write a 1 to toggle the
        # value back to a 0.

        # TODO: only waits on cgra done, doesn't wait on dma, etc. yet

        tester.print("Waiting for interrupt...\n")

        tester.zero_inputs()

        # Wait for the interrupt to come from the CGRA
        loop = tester._while(tester.peek(tester._circuit.axi4_ctrl_interrupt) == 0)
        loop.step(2)

        # TODO: clean way of clearing interrupts is reading it and then writing that value back
        WRITE_REG(INTERRUPT_STATUS_REG, self.mask).sim(tester)

    def compile(self, _globals):
        # if self.mask == 0b01:
        #     return f"""
        #     for (int k = 0; k < 100000; k++);
        #     while (!{self.sem_id}) {{
        #         if (*(volatile uint32_t*)(CGRA_REG_BASE + 0x{INTERRUPT_STATUS_REG:x})) {{
        #             printf("INTERRUPT_STATUS went high but semaphore wasn't signaled.\\n");
        #             break;
        #         }}
        #         if (*(volatile uint32_t*)(CGRA_REG_BASE + 0x{CGRA_START_REG:x}) == 0) {{
        #             printf("CGRA_START went low but semaphore wasn't signaled.\\n");
        #             break;
        #         }}
        #     }}
        #     """
        # else:
        #     return f"""
        #     for (int k = 0; k < 100000; k++);
        #     while (!{self.sem_id}) {{
        #         if (*(volatile uint32_t*)(CGRA_REG_BASE + 0x{INTERRUPT_STATUS_REG:x})) {{
        #             printf("INTERRUPT_STATUS went high but semaphore wasn't signaled.\\n");
        #             break;
        #         }}
        #         if (*(volatile uint32_t*)(CGRA_REG_BASE + 0x{CONFIG_START_REG:x}) == 0) {{
        #             printf("CONFIG_START went low but semaphore wasn't signaled.\\n");
        #             break;
        #         }}
        #     }}
        #     """

        return f"""
        while (!{self.sem_id}) {{
            __WFE(); // wait for event
        }}
        // TODO: should disable interrupts around this decrement
        {self.sem_id} -= 1;
        """


    @staticmethod
    def interpret():
        pass


class PRINT(Command):
    opcode = None

    def __init__(self, string):
        self.string = string

    def sim(self, tester):
        tester.print(self.string + "\\n")

    def compile(self, _globals):
        return f'printf("{self.string}\\n");'


class STALL(Command):
    opcode = None

    def __init__(self, cycles):
        self.cycles = cycles

    def sim(self, tester):
        tester.zero_inputs()
        loop = tester.loop(self.cycles)
        loop.step(2)

    def compile(self, _globals):
        # TODO: try to wait for some number of cycles on the M3?
        return f'printf("{self.cycles}\\n");'


ops = [
    NOP,
    WRITE_REG,
    WRITE_DATA,
]


def configure_io(mode, addr, size, io_ctrl=None, mask=None, width=32):
    bank_size = 2**17

    # 1 IO Controller per 4 Tile Width
    num_io_controllers = width // 4

    # Bank number is top 5 bits of 22-bit address
    lo_bank_num = (addr >> 17) & 0b11111

    # There are always 32 banks of memory
    banks_per_io_controller = 32 // num_io_controllers

    if io_ctrl is None:
        # Figure out which IO Controller handles this bank
        io_ctrl = lo_bank_num // banks_per_io_controller

    if mask is None:
        if (io_ctrl + 1) * banks_per_io_controller - 1 < lo_bank_num:
            print(f"IO controller {io_ctrl} is smaller than specified address, special case.")
            print((io_ctrl + 1) * banks_per_io_controller - 1)
            print(lo_bank_num)
            mask = 0b1000
        else:
            # We use the size to compute how many banks we need
            # control over and set the rest to 0. This can be
            # overridden by manually specifying the mask in the
            # function arguments.
            hi_bank_num = (addr+size >> 17) & 0b11111

            # Compute the mask
            mask_start = lo_bank_num % banks_per_io_controller
            mask_end = hi_bank_num % banks_per_io_controller

            mask = 0
            for k in range(mask_start, mask_end+1):
                mask |= 1 << k

    print(f"Configuring io controller {io_ctrl} with mask 0b{mask:04b}:")
    print(f"    ADDR: 0x{addr:x}")
    print(f"    SIZE: 0x{size:x}")

    return [
        WRITE_REG(IO_MODE_REG(io_ctrl), mode),
        WRITE_REG(IO_ADDR_REG(io_ctrl), addr),
        WRITE_REG(IO_SIZE_REG(io_ctrl), size),
        WRITE_REG(IO_SWITCH_REG(io_ctrl), mask),
    ]


# TODO: make this distribute the bitstream across the global buffer
def configure_fr(addr, size, fr_ctrl=None, mask=None, width=32):
    bank_size = 2**17

    # 1 FR Controller per 4 Tile Width
    num_fr_controllers = width // 4

    # Bank number is top 5 bits of 22-bit address
    lo_bank_num = (addr >> 17) & 0b11111

    # There are always 32 banks of memory
    banks_per_fr_controller = 32 // num_fr_controllers

    if fr_ctrl is None:
        # Figure out which FR Controller handles this bank
        fr_ctrl = lo_bank_num // banks_per_fr_controller
    else:
        assert mask is not None

    if mask is None:
        # We use the size to compute how many banks we need
        # control over and set the rest to 0. This can be
        # overridden by manually specifying the mask in the
        # function arguments.
        nbytes = size * 8  # size passed in is number of 64-bit entries
        hi_bank_num = (addr+nbytes >> 17) & 0b11111

        # Compute the mask
        mask_start = lo_bank_num % banks_per_fr_controller
        mask_end = hi_bank_num % banks_per_fr_controller

        mask = 0
        for k in range(mask_start, mask_end+1):
            mask |= 1 << k

    print(f"Configuring fast reconfig controller {fr_ctrl} with mask 0b{mask:04b}:")
    print(f"    ADDR: 0x{addr:x}")
    print(f"    SIZE: 0x{size:x}")

    return [
        WRITE_REG(FR_ADDR_REG(fr_ctrl), addr),
        WRITE_REG(FR_SIZE_REG(fr_ctrl), size),
        WRITE_REG(FR_SWITCH_REG(fr_ctrl), mask),
    ]


def gc_config_bitstream(filename):
    commands = []
    with open(filename, 'r') as f:
        for line in f:
            # TODO: might just make this use numpy instead
            addr, data = (int(x, 16) for x in line.strip().split(' '))
            commands += [
                WRITE_REG(CGRA_CONFIG_ADDR_REG, addr),
                WRITE_REG(CGRA_CONFIG_DATA_REG, data),
                # WRITE_REG(CGRA_CONFIG_ADDR_REG, addr),
                # READ_REG(CGRA_CONFIG_DATA_REG, data),
            ]
    return commands


def gb_config_bitstream(filename, width=8):
    # TODO: only writes things to address 0 for now
    commands = []
    with open(filename, 'r') as f:
        bitstream = []
        for line in f:
            # TODO: might just make this use numpy instead
            addr, data = (int(x, 16) for x in line.strip().split(' '))
            bitstream += [data, addr]

        bitstream = np.array(bitstream, dtype=np.uint32).view(np.uint64)

        config_id = f"config_{new_id()}"
        commands += [
            WRITE_DATA(0, 0xc0ffee, bitstream.nbytes, bitstream),
            *configure_fr(0, len(bitstream), mask=0b1111, width=width),
            PEND(0b10, f"{config_id}"),
            WRITE_REG(CONFIG_START_REG, 1),
            WAIT(0b10, f"{config_id}"),
        ]
    return commands

def create_command_bitstream(commands):
     return [arg for command in commands for arg in command.ser()]


def create_testbench(tester, commands):
    # Generate Fault testbench
    for command in commands:
        tester.print(f"command: {command}\n")
        command.sim(tester)

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
    _globals = {
        'src': [],
        'ids': [],
    }
    test_body = "\n".join([op.compile(_globals) for op in ops])

    src = """
    #include "AHASOC.h"
    #include "stdio.h"
    #include "stdint.h"
    #include "inttypes.h"
    #include "uart_stdout.h"
    """

    if DMA:
        src += """
        #include "dma_utils.h"
        """

    #     src += """
    #     #define DMA0_BASE            0x40007000
    #     #define DMA0_DBGCMD          ((volatile uint32_t*)(DMA0_BASE + 0xD04))
    #     #define DMA0_DBGINST0        ((volatile uint32_t*)(DMA0_BASE + 0xD08))
    #     #define DMA0_DBGINST1        ((volatile uint32_t*)(DMA0_BASE + 0xD0C))
    #     #define DMA0_INTEN           ((volatile uint32_t*)(DMA0_BASE + 0x020))
    #     #define DMA0_INTCLR          ((volatile uint32_t*)(DMA0_BASE + 0x02C))

    #     #define DMA1_BASE            0x40008000
    #     #define DMA1_DBGCMD          ((volatile uint32_t*)(DMA1_BASE + 0xD04))
    #     #define DMA1_DBGINST0        ((volatile uint32_t*)(DMA1_BASE + 0xD08))
    #     #define DMA1_DBGINST1        ((volatile uint32_t*)(DMA1_BASE + 0xD0C))
    #     #define DMA1_INTEN           ((volatile uint32_t*)(DMA1_BASE + 0x020))
    #     #define DMA1_INTCLR          ((volatile uint32_t*)(DMA1_BASE + 0x02C))

    #     static volatile unsigned int dma_irq_counter0;
    #     void DMA0_Handler(void) {
    #       dma_irq_counter0++;
    #       *DMA0_INTCLR = 0x00000001;
    #       __SEV();
    #     }

    #     static volatile unsigned int dma_irq_counter1;
    #     void DMA1_Handler(void) {
    #       dma_irq_counter1++;
    #       *DMA1_INTCLR = 0x00000001;
    #       __SEV();
    #     }
    #     """

    if TLX:
        src += """
        #define TLX_BASE 0x60000000
        #define TLX_SIZE 0x40000000
        """

    src += """
    #define CGRA_REG_BASE 0x40010000
    #define CGRA_DATA_BASE 0x20400000

    typedef void(*interrupt_handler_t)(void);
    """

    src += "\n".join(_globals['src'])

    src += """
    int main() {
    """

    if TLX:
        src += """
        volatile uint64_t* tlx_base = (volatile uint64_t*)TLX_BASE;
        """

        for gid in _globals['ids']:
            src += f"""
            volatile uint64_t* tlx_{gid} = tlx_base;
            for(size_t k = 0; k < sizeof({gid}) / sizeof({gid}[0]); k++) {{
                *(tlx_base++) = {gid}[k];
            }}
            """

    src += """
        // UART init
        UartStdOutInit();

        // Enable interrupts
        NVIC_EnableIRQ(CGRA_IRQn);

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
