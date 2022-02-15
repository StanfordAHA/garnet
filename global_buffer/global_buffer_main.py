import argparse
from global_buffer.design.global_buffer import GlobalBuffer
from global_buffer.design.global_buffer_parameter import gen_global_buffer_params, gen_header_files
from systemRDL.util import gen_rdl_header
import os
import pathlib
import kratos as k


def gen_param_header(top_name, params, output_folder):
    svh_filename = os.path.join(output_folder, f"{top_name}.svh")
    h_filename = os.path.join(output_folder, f"{top_name}.h")
    gen_header_files(params=params,
                     svh_filename=svh_filename,
                     h_filename=h_filename,
                     header_name="global_buffer")


def main():
    garnet_home = os.getenv('GARNET_HOME')
    if not garnet_home:
        garnet_home = pathlib.Path(__file__).parent.parent.resolve()

    parser = argparse.ArgumentParser(description='Garnet Global Buffer')
    parser.add_argument('--num_glb_tiles', type=int, default=16)
    parser.add_argument('--num_cgra_cols', type=int, default=32)
    parser.add_argument('--glb_tile_mem_size', type=int, default=256)
    parser.add_argument("--sram_stub", action="store_true")
    parser.add_argument("-v", "--verilog", action="store_true")
    parser.add_argument("-p", "--parameter", action="store_true")
    parser.add_argument("-r", "--rdl", action="store_true")

    args = parser.parse_args()
    params = gen_global_buffer_params(num_glb_tiles=args.num_glb_tiles,
                                      num_cgra_cols=args.num_cgra_cols,
                                      # FIXME: We assume num_prr is same as num_glb_tiles
                                      num_prr=args.num_glb_tiles,
                                      is_sram_stub=args.sram_stub,
                                      glb_tile_mem_size=args.glb_tile_mem_size)

    glb = GlobalBuffer(_params=params)

    if args.parameter:
        gen_param_header(top_name="global_buffer_param",
                         params=params,
                         output_folder=os.path.join(garnet_home, "global_buffer/header"))

    if args.rdl:
        gen_rdl_header(top_name="glb",
                       rdl_file=os.path.join(garnet_home, "global_buffer/systemRDL/glb.rdl"),
                       output_folder=os.path.join(garnet_home, "global_buffer/header"))

    if args.verilog:
        k.verilog(glb, filename=os.path.join(garnet_home, "global_buffer", "global_buffer.sv"))


if __name__ == "__main__":
    main()
