import argparse
import fault
import magma
import textwrap
import re
import types


class NOP:
    opcode = 0

    def __init__(self):
        pass

    def ser(self):
        return [NOP.opcode]

    def sim(self, circuit):
        pass

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
    opcode = 1

    def __init__(self, addr, data):
        self.addr = addr
        self.data = data

    def ser(self):
        return [WRITE_REG.opcode, self.addr, self.data]

    def sim(self, tester):
        # drive inputs
        tester.clear_inputs()
        tester.circuit.axi4_ctrl_awaddr = self.addr
        tester.circuit.axi4_ctrl_awvalid = 1
        tester.circuit.axi4_ctrl_wdata = self.data
        tester.circuit.axi4_ctrl_wvalid = 1

        # propagate inputs
        tester.eval()

        # loop = tester._while(tester.circuit.axi4_ctrl_awready.expect(0))
        # loop.step(2)
        tester.step(30)  # HACK replace with while

        tester.circuit.axi4_ctrl_awready.expect(1)

        # HACK seems like there might be a bug in either controller or this
        tester.step(2)  # HACK
        tester.circuit.axi4_ctrl_awvalid = 0
        tester.circuit.axi4_ctrl_wready.expect(1)

        tester.eval()

        tester.step(2)  # HACK
        tester.circuit.axi4_ctrl_wvalid = 0

        tester.eval()

        tester.step(2)

    @staticmethod
    def interpret():
        return """
        *ARG_1 = ARG_2;
        """


class READ_REG:
    opcode = 1

    def __init__(self, addr, expected):
        self.addr = addr
        self.expected = expected

    def ser(self):
        return [WRITE_REG.opcode, self.addr]

    def sim(self, tester):
        # drive inputs
        tester.clear_inputs()
        tester.circuit.axi4_ctrl_araddr = self.addr
        tester.circuit.axi4_ctrl_arvalid = 1
        tester.circuit.axi4_ctrl_rready = 1

        tester.eval()

        tester.step(8)  # HACK replace with while
        tester.circuit.axi4_ctrl_rvalid.expect(1)
        tester.circuit.axi4_ctrl_rdata.expect(self.expected)

        tester.step(2)  # HACK
        tester.arvalid = 0

        tester.eval()

        tester.step(2)

    @staticmethod
    def interpret():
        pass


class WRITE_DATA:
    opcode = 2

    def __init__(self, dst, src, size):
        self.dst = dst
        self.src = src
        self.size = size

    def ser(self):
        return [WRITE_DATA.opcode, self.dst, self.src, self.size]

    def sim(self, circuit):
        pass

    @staticmethod
    def interpret():
        return """
        // memcpy(ARG_1, ARG_2, ARG_3);
        """


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


def test_flow(from_verilog=True):
    if from_verilog:
        dut = magma.DefineFromVerilogFile(
            'garnet.v',
            target_modules=['Garnet'],
            type_map={
                "clk_in": magma.In(magma.Clock)
            }
        )[0]
    else:
        # this import is kinda slow so only do it if needed
        from garnet import Garnet
        dut = Garnet(width=4, height=2, add_pd=False).circuit

    print(dut)

    tester = fault.Tester(dut, clock=dut.clk_in)

    # Reset the CGRA (active high)
    def reset_cgra():
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

    # Test-Logic-Reset
    reset_jtag()

    # Run-Test/Idle
    tester.circuit.jtag_tms = 0
    next_tck()

    sc_cfg_data = 8
    sc_cfg_inst = 9
    sc_cfg_addr = 10

    JTAG_WRITE_A050 = 4
    JTAG_SWITCH_CLK = 12

    jtag_inst_bits = 5

    # Test A050
    shift_ir(sc_cfg_inst, jtag_inst_bits)
    shift_dr(JTAG_WRITE_A050, jtag_inst_bits)
    shift_ir(sc_cfg_data, jtag_inst_bits)
    shift_dr(0xC0DE, 32)

    # Switch clocks
    shift_ir(sc_cfg_data, jtag_inst_bits)
    shift_dr(1, 32)
    shift_ir(sc_cfg_inst, jtag_inst_bits)
    shift_dr(JTAG_SWITCH_CLK, jtag_inst_bits)

    # wait a bit
    next_tck(5)

    tester.circuit.clk_in = 0

    # wait some more
    tester.step(10)

    commands = [
        # Verify AXI working with TEST_REG
        WRITE_REG(0xF1, 0xDEADBEEF),
        READ_REG(0xF1, 0xDEADBEEF),
        # Stall the CGRA
        # WRITE_REG(0xF3, 0xF),
    ]

    bitstream = [arg for command in commands for arg in command.ser()]
    print(bitstream)

    def clear_inputs(circuit):
        circuit.jtag_tck = 0
        circuit.jtag_tdi = 0
        circuit.jtag_tms = 0
        circuit.jtag_trst_n = 1

        circuit.axi4_ctrl_araddr = 0
        circuit.axi4_ctrl_arvalid = 0
        circuit.axi4_ctrl_rready = 0
        circuit.axi4_ctrl_awaddr = 0
        circuit.axi4_ctrl_awvalid = 0
        circuit.axi4_ctrl_wdata = 0
        circuit.axi4_ctrl_wvalid = 0

    # HACK add clear_inputs to tester.circuit
    tester.clear_inputs = types.MethodType(clear_inputs, tester.circuit)

    # TODO reset_in
    # tester.circuit.reset_in = 0
    # tester.step(2)
    # tester.circuit.reset_in = 1
    # tester.step(2)

    PC = 0
    for command in commands:
        command.sim(tester)
        PC += 1

    # cd tests/build
    # ln -s ../../genesis_verif/* .
    # ln -s ../../garnet.v .
    # wget https://raw.githubusercontent.com/StanfordAHA/garnet/master/global_buffer/genesis/TS1N16FFCLLSBLVTC2048X64M8SW.sv # noqa
    # wget https://raw.githubusercontent.com/StanfordAHA/lassen/master/tests/build/add.v # noqa
    # wget https://raw.githubusercontent.com/StanfordAHA/lassen/master/tests/build/mul.v # noqa
    # wget https://raw.githubusercontent.com/StanfordAHA/lassen/master/tests/build/CW_fp_add.v # noqa
    # wget https://raw.githubusercontent.com/StanfordAHA/lassen/master/tests/build/CW_fp_mul.v # noqa
    # wget https://raw.githubusercontent.com/StanfordAHA/garnet/7257ed48e089c7f7df0061a51f55f92b31614fec/tests/test_memory_core/sram_stub.v # noqa
    # mv sram_stub.v sram_512w_16b.v

    # get the actual DW_tap.v from /cad or Alex
    # TODO might be able to bypass that if we could switch to
    # system_clk without having to do it over jtag...

    tester.compile_and_run(target="verilator",
                           directory="tests/build/",
                           # circuit_name="Garnet",
                           include_verilog_libraries=["garnet.v"],
                           flags=['-Wno-UNUSED',
                                  '-Wno-PINNOCONNECT',
                                  '-Wno-fatal',
                                  '--trace'],
                           # flags=['-Wno-fatal'],
                           skip_compile=True,  # turn on to skip DUT compilation
                           magma_output='verilog',
                           magma_opts={"verilator_debug": True},)


def main():
    parser = argparse.ArgumentParser(description="""
    A simple SoC stub to test application flow of the CGRA.
    """)

    parser.add_argument('--width', type=int, default=4)
    parser.add_argument('--height', type=int, default=2)
    parser.add_argument("--input-netlist", type=str, default="", dest="input")
    parser.add_argument("--output-bitstream", type=str, default="",
                        dest="output")
    parser.add_argument("-v", "--verilog", action="store_true")
    parser.add_argument("--no-pd", "--no-power-domain", action="store_true")
    args = parser.parse_args()

    # assert args.width % 4 == 0 and args.width >= 4
    # garnet = Garnet(width=args.width, height=args.height, add_pd=not args.no_pd) # noqa
    test_flow()

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
