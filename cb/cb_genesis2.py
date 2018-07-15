import argparse
from common.genesis_wrapper import define_genesis_generator


define_cb_wrapper = define_genesis_generator(
    top_name="cb",
    input_files=["cb.vp"],
    width=16,
    num_tracks=10,
    feedthrough_outputs="1111101111",
    has_constant=1,
    default_value=0
)


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", type=str)
    parser.add_argument("--width", type=int, default=32)
    parser.add_argument("--num_tracks", type=int, default=10)
    parser.add_argument("--feedthrough_outputs", type=str, default=("1"*10))
    parser.add_argument("--has_constant", type=int, default=0)
    parser.add_argument("--default_value", type=int, default=0)
    return parser


def main(args):
    # Check some of the inputs.
    for c in args.feedthrough_outputs:
        assert c == "1" or c == "0"

    cb = define_cb_wrapper(width=args.width,
                           num_tracks=args.num_tracks,
                           feedthrough_outputs=args.feedthrough_outputs,
                           has_constant=args.has_constant,
                           default_value=args.default_value,
                           input_files=[args.infile])
    print(cb)


"""
This program generates the verilog for the connect box and parses it into a
Magma circuit. The circuit declaration is printed at the end of the program.
"""
if __name__ == "__main__":
    # These functions are unit tested directly, so no need to cover them
    parser = create_parser()  # pragma: no cover
    main(parser.parse_args())  # pragma: no cover
