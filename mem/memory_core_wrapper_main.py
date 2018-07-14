"""
This program generates the verilog for the memory core and parses it into a
Magma circuit. The circuit declaration is printed at the end of the program.
"""
import argparse
from mem.memory_core_wrapper import define_memory_core_wrapper


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("in_file_or_files",
                        help="file or list of files for memory",
                        nargs="+")
    parser.add_argument("--data-width", type=int, default=16)
    parser.add_argument("--data-depth", type=int, default=1024)
    return parser


def main(args):
    memory_core = define_memory_core_wrapper(args.data_width, args.data_depth,
                                             args.in_file_or_files)
    print(memory_core)


if __name__ == "__main__":
    # These functions are unit tested directly, so no need to cover them
    parser = create_parser()  # pragma: no cover
    main(parser.parse_args())  # pragma: no cover
