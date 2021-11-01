import argparse
from global_buffer.design.global_buffer import GlobalBuffer
from global_buffer.design.global_buffer_parameter import gen_global_buffer_params, gen_svh_files
from global_buffer.gen_global_buffer_rdl import gen_global_buffer_rdl, run_systemrdl, gen_glb_pio_wrapper
from systemrdl import RDLCompiler, RDLCompileError
from peakrdl.html import HTMLExporter
from systemRDL.gen_config_addrmap import convert_addrmap, convert_to_json, convert_to_header
import os
import sys
import pathlib
import kratos as k


def main():
    garnet_home = os.getenv('GARNET_HOME')
    if not garnet_home:
        garnet_home = pathlib.Path(__file__).parent.parent.resolve()

    parser = argparse.ArgumentParser(description='Garnet Global Buffer')
    parser.add_argument('--num_glb_tiles', type=int, default=16)
    parser.add_argument('--num_cgra_cols', type=int, default=32)
    parser.add_argument('--glb_tile_mem_size', type=int, default=256)
    parser.add_argument("-v", "--verilog", action="store_true")
    parser.add_argument("-p", "--parameter", action="store_true")
    parser.add_argument("-r", "--rdl", action="store_true")

    args = parser.parse_args()
    params = gen_global_buffer_params(num_glb_tiles=args.num_glb_tiles,
                                      num_cgra_cols=args.num_cgra_cols,
                                      glb_tile_mem_size=args.glb_tile_mem_size)

    if args.parameter:
        svh_filename = os.path.join(
            garnet_home, "global_buffer/header/global_buffer_param.svh")
        gen_svh_files(params=params,
                      filename=svh_filename,
                      header_name="global_buffer")

    if args.rdl:
        # Generate default RDL
        top_name = "glb"
        glb_rdl = gen_global_buffer_rdl(name=top_name, params=params)

        # Dump rdl file
        rdl_file = os.path.join(garnet_home, "global_buffer/systemRDL/glb.rdl")
        glb_rdl.dump_rdl(rdl_file)

        # Run ORDT to generate RTL
        ordt_path = os.path.join(garnet_home, 'systemRDL', 'Ordt.jar')
        rdl_parms_file = os.path.join(
            garnet_home, "global_buffer/systemRDL/ordt_params/glb.parms")
        rdl_output_folder = os.path.join(
            garnet_home, "global_buffer/systemRDL/output/")
        run_systemrdl(ordt_path, top_name, rdl_file,
                      rdl_parms_file, rdl_output_folder)

        # Create wrapper of glb_pio.sv
        pio_file = rdl_output_folder + top_name + "_pio.sv"
        pio_wrapper_file = rdl_output_folder + top_name + "_pio_wrapper.sv"
        gen_glb_pio_wrapper(src_file=pio_file, dest_file=pio_wrapper_file)

        # Generate HTML and addressmap header
        addrmap_output_folder = os.path.join(
            garnet_home, "global_buffer/header")
        rdlc = RDLCompiler()
        try:
            rdlc.compile_file(rdl_file)
            # Elaborate the design
            root = rdlc.elaborate()
        except RDLCompileError:
            # A compilation error occurred. Exit with error code
            sys.exit(1)
        root = rdlc.elaborate()
        exporter = HTMLExporter()
        exporter.export(root, os.path.join(addrmap_output_folder, "html"))
        rdl_json = convert_addrmap(rdlc, root.top)
        convert_to_json(rdl_json, os.path.join(
            addrmap_output_folder, f"{top_name}.json"))
        convert_to_header(rdl_json, os.path.join(
            addrmap_output_folder, top_name))

    if args.verilog:
        glb = GlobalBuffer(_params=params)
        k.verilog(glb, filename=os.path.join(
            garnet_home, "global_buffer", "glb.sv"))


if __name__ == "__main__":
    main()
