import argparse
from common.genesis_wrapper import define_genesis_generator


define_gc_wrapper = define_genesis_generator(
    top_name="global_controller",
    input_files=["genesis/global_controller.vp", "genesis/jtag.vp",
                 "genesis/analog_regfile.vp", "genesis/tap.vp",
                 "genesis/flop.vp", "genesis/cfg_and_dbg.vp",
                 "/cad/synopsys/syn/M-2017.06-SP3/dw/sim_ver/DW_tap.v"],
    cfg_bus_width=32,
    cfg_addr_width=32,
    cfg_op_width=5,
    num_analog_regs=15
)


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_files", nargs="*",
                        default="global_controller/genesis/global_controller.vp "
                                "global_controller/genesis/jtag.vp "
                                "global_controller/genesis/analog_regfile.vp "
                                "global_controller/genesis/tap.vp "
                                "global_controller/genesis/flop.vp "
                                "global_controller/genesis/cfg_and_dbg.vp "
                                "/cad/synopsys/syn/M-2017.06-SP3/"
                                "dw/sim_ver/DW_tap.v")
    parser.add_argument("--cfg_bus_width", type=int, default=32)
    parser.add_argument("--cfg_addr_width", type=int, default=32)
    parser.add_argument("--cfg_op_width", type=int, default=5)
    parser.add_argument("--num_analog_regs", type=int, default=15)
    return parser


def main(args):

    gc = define_gc_wrapper(cfg_bus_width=args.cfg_bus_width,
                           cfg_addr_width=args.cfg_addr_width,
                           cfg_op_width=args.cfg_op_width,
                           num_analog_regs=args.num_analog_regs,
                           input_files=[args.input_files])
    print(gc)


"""
This program generates the verilog for the global controller and parses it into
a Magma circuit. The circuit declaration is printed at the end of the program.
"""
if __name__ == "__main__":
    # These functions are unit tested directly, so no need to cover them
    parser = create_parser()  # pragma: no cover
    main(parser.parse_args())  # pragma: no cover
