import argparse
from common.genesis_wrapper import define_genesis_generator


define_io1bit_wrapper = define_genesis_generator(
    top_name="io1bit",
    input_files=["genesis/io1bit.vp"],
    io_group=-1,
    side=0
)


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", type=str)
    parser.add_argument("--io_group", type=int, default=-1)
    parser.add_argument("--side", type=int, default=0)
    return parser


def main(args):
    # Check some of the inputs.
    assert args.side in range(3)
    io1bit = define_io1bit_wrapper(io_group=args.io_group, side=args.side, input_files=[args.infile])

    print(io1bit)

"""
This program generates the verilog for io1bit and parses it into a
Magma circuit. The circuit declaration is printed at the end of the program.
"""
if __name__ == "__main__":
    # These functions are unit tested directly, so no need to cover them
    parser = create_parser()  # pragma: no cover
    main(parser.parse_args())  # pragma: no cover
