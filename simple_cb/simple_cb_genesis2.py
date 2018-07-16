import argparse
from common.genesis_wrapper import define_genesis_generator


define_simple_cb_wrapper = define_genesis_generator(
    top_name="simple_cb",
    input_files=["genesis/simple_cb.vp"],
    width=16,
    num_tracks=10,
)


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", type=str)
    parser.add_argument("--width", type=int, default=32)
    parser.add_argument("--num_tracks", type=int, default=10)
    return parser


def main(args):
    simple_cb = define_simple_cb_wrapper(
        width=args.width,
        num_tracks=args.num_tracks,
        input_files=[args.infile])
    print(simple_cb)


"""
This program generates the verilog for the connect box and parses it into a
Magma circuit. The circuit declaration is printed at the end of the program.
"""
if __name__ == "__main__":
    # These functions are unit tested directly, so no need to cover them
    parser = create_parser()  # pragma: no cover
    main(parser.parse_args())  # pragma: no cover
