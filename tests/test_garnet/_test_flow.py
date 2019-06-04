import argparse
import fault
import magma
import textwrap
import types
import struct
import json
import random
import sys
import time
from commands import *


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

    reset_cgra()

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
                # TODO might just make this use numpy instead
                addr, data = (int(x, 16) for x in line.strip().split(' '))
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
        # WRITE_DATA(0x1234, 0xc0ffee, 8, np.array([0x00000003, 0x17070101], dtype=np.uint32)),  # noqa
        # # Check the write
        # READ_DATA(0x1234, 8, bytes(np.array([0x00000003, 0x17070101], dtype=np.uint32))),  # noqa

        # # Set up global buffer for configuration
        # # TODO

        # # Configure the CGRA
        # # TODO
        raise NotImplementedError("Configuring bitstream through global buffer not yet implemented.")  # noqa

    import numpy as np
    np.set_printoptions(formatter={'int': hex})

    im = np.fromfile(
        'applications/conv_1_2/conv_1_2_input.raw',
        dtype=np.uint8
    ).astype(np.uint16)

    gold = np.fromfile(
        'applications/conv_1_2/conv_1_2_gold.raw',
        dtype=np.uint8
    ).astype(np.uint16)

    print(im[0:4])

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
        WRITE_DATA(BANK_ADDR(0), 0xc0ffee, im.nbytes, im),

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
        READ_DATA(
            BANK_ADDR(16),
            gold.nbytes,
            gold,
            _file=tester.file_open("logs/result.raw", "wb", 8)
        ),
    ]

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

    print(f"Command list has {len(commands)} commands.")
    print("Generating testbench...")
    start = time.time()

    # Generate Fault testbench
    PC = 0
    for command in commands:
        tester.print(f"command: {command}\n")
        command.sim(tester)
        PC += 1

    # Generate straightline C code
    _globals = []
    test_body = "\n".join([command.compile(_globals) for command in commands])
    with open("tests/build/test.c", "w") as f:
        f.write("""
        #include "AHASOC.h"
        #include "stdio.h"
        #include "stdint.h"
        #include "inttypes.h"
        #include "uart_stdout.h"

        #define CGRA_REG_BASE 0x40010000
        #define CGRA_DATA_BASE 0x20400000
        """)

        f.write("\n".join(_globals))

        f.write("""
        int main() {
            // UART init
            UartStdOutInit();

            uint32_t errors = 0;
            printf("Starting test...\\n");
        """)

        f.write(test_body)

        f.write("""
            if(errors) printf("TEST FAILED (%u errors)\\n", errors);
            else printf("TEST PASSED!\\n");

            // End simulation
            UartEndSimulation();

        return 0;
        }
        """)

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
            # '--debug',
            '--trace' if args.debug else '',
            f'--trace-max-array {2**17}' if args.trace_mem else '',
            # '--no-debug-leak',
        ],
        skip_compile=not args.recompile,  # turn on to skip DUT compilation
        skip_verilator=not args.recompile,  # turn on to skip DUT compilation
        magma_output='verilog',
        magma_opts={"verilator_debug": True},
    )

    print("Comparing outputs...")
    gold = np.fromfile(
        'applications/conv_1_2/conv_1_2_gold.raw',
        dtype=np.uint8
    )

    result = np.fromfile(
        'tests/build/logs/result.raw',
        dtype=np.uint16
    ).astype(np.uint8)

    def compare_results(gold, result):
        if not np.array_equal(gold, result):
            for k, (x, y) in enumerate(zip(gold, result)):
                if x != y:
                    print(f"ERROR: [{k}] expected 0x{x:x} but got 0x{y:x}")
            assert False

    compare_results(gold, result)

    print("Outputs match!")

    result = np.loadtxt(
        'soc.txt',
        dtype=np.uint64,
        converters={0: lambda x: int(x, 16)}
    ).view(np.uint16).astype(np.uint8)

    print(gold)
    print(result)

    print(len(gold))
    print(len(result))

    print(np.array_equal(gold, result))

    compare_results(gold, result)

    print("SoC outputs match!")


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
