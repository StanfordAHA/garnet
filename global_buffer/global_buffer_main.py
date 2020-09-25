import magma
import argparse
from .global_buffer_magma import GlobalBuffer


def main():
    parser = argparse.ArgumentParser(description='Garnet Global Buffer')
    parser.add_argument('--num_glb_tiles', type=int, default=16)
    parser.add_argument('--num_cgra_cols', type=int, default=32)
    parser.add_argument("-v", "--verilog", action="store_true")
    parser.add_argument("-p", "--parameter_only", action="store_true")
    args = parser.parse_args()

    if args.parameter_only:
        assert not args.verilog

    global_buffer = GlobalBuffer(num_glb_tiles=args.num_glb_tiles,
                                 num_cgra_cols=args.num_cgra_cols,
                                 parameter_only=args.parameter_only)

    if args.verilog:
        global_buffer_circ = global_buffer.circuit()
        magma.compile("global_buffer", global_buffer_circ, output="coreir-verilog")

if __name__ == "__main__":
    main()
