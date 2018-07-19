import argparse
from sb.sb_wrapper import define_sb_wrapper 


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", type=str)
    parser.add_argument("--width", type=int, default=16)
    parser.add_argument("--num_tracks", type=int, default=2)
    parser.add_argument("--sides", type=int, default=4)
    parser.add_argument("--feedthrough_outputs", type=str, default=("00"))
    parser.add_argument("--registered_outputs", type=str, default=("11"))
    parser.add_argument("--pe_output_count", type=int, default=1)
    parser.add_argument("--is_bidi", type=int, default=0)
    parser.add_argument("--sb_fs", type=str, default="10#10#10")
    return parser


def main(args):
    sb = define_sb_wrapper(width=args.width,
                           num_tracks=args.num_tracks,
                           sides=args.sides,
                           feedthrough_outputs=args.feedthrough_outputs,
                           registered_outputs=args.registered_outputs,
                           pe_output_count=args.pe_output_count,
                           is_bidi=args.is_bidi,
                           sb_fs=args.sb_fs,
                           input_files=[args.infile])
    print(sb)


if __name__ == "__main__":
    """
    This program generates the verilog for the memory core and parses it into a
    Magma circuit. The circuit declaration is printed at the end of the
    program.
    """
    # These functions are unit tested directly, so no need to cover them
    parser = create_parser()  # pragma: no cover
    main(parser.parse_args())  # pragma: no cover
