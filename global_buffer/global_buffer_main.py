import magma
import argparse
from .design.global_buffer_parameter import gen_global_buffer_params, gen_systemrdl_param_files, gen_svh_files
from .design.global_buffer_magma import GlobalBuffer


def main():
    parser = argparse.ArgumentParser(description='Garnet Global Buffer')
    parser.add_argument('--num_glb_tiles', type=int, default=16)
    parser.add_argument('--num_cgra_cols', type=int, default=32)
    parser.add_argument('--glb_tile_mem_size', type=int, default=256)
    parser.add_argument("-v", "--verilog", action="store_true")
    parser.add_argument("-p", "--parameter", action="store_true")
    parser.add_argument("-c", "--config_only", action="store_true")

    args = parser.parse_args()
    if args.parameter:
        params = gen_global_buffer_params(num_glb_tiles=args.num_glb_tiles,
                                          num_cgra_cols=args.num_cgra_cols,
                                          glb_tile_mem_size=args.glb_tile_mem_size)
        gen_systemrdl_param_files(params=params,
                                  filename="global_buffer/systemRDL/rdl_models/glb.rdl.param")
        gen_svh_files(params=params,
                      filename="global_buffer/rtl/global_buffer_param.svh",
                      header_name="global_buffer")
    breakpoint()

    global_buffer = GlobalBuffer(num_glb_tiles=args.num_glb_tiles,
                                 num_cgra_cols=args.num_cgra_cols,
                                 glb_tile_mem_size=args.glb_tile_mem_size,
                                 parameter_only=args.parameter_only)

    # if args.verilog:
    #     global_buffer_circ = global_buffer.circuit()
    #     magma.compile("global_buffer",
    #                   global_buffer_circ,
    #                   output="coreir-verilog",
    #                   inline=False)


if __name__ == "__main__":
    main()
