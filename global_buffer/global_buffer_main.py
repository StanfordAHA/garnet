import magma
import argparse
from global_buffer.design.glb_core_proc_router import GlbCoreProcRouter
from global_buffer.design.glb_tile_cfg_ctrl import GlbTileCfgCtrl
from global_buffer.design.glb_tile_cfg import GlbTileCfg
# from global_buffer.design.global_buffer_parameter import gen_global_buffer_params, gen_systemrdl_param_files, gen_svh_files
from global_buffer.design.global_buffer_parameter import gen_global_buffer_params
from global_buffer.gen_global_buffer_rdl import gen_global_buffer_rdl, run_systemrdl, gen_glb_pio_wrapper
# from global_buffer.design.global_buffer_magma import GlobalBuffer
import kratos as k


def main():
    parser = argparse.ArgumentParser(description='Garnet Global Buffer')
    parser.add_argument('--num_glb_tiles', type=int, default=16)
    parser.add_argument('--num_cgra_cols', type=int, default=32)
    parser.add_argument('--glb_tile_mem_size', type=int, default=256)
    parser.add_argument("-v", "--verilog", action="store_true")
    parser.add_argument("-p", "--parameter", action="store_true")
    parser.add_argument("-c", "--config_only", action="store_true")
    parser.add_argument("-r", "--rdl", action="store_true")

    args = parser.parse_args()
    params = gen_global_buffer_params(num_glb_tiles=args.num_glb_tiles,
                                      num_cgra_cols=args.num_cgra_cols,
                                      glb_tile_mem_size=args.glb_tile_mem_size)
        # Ultimately, these are not needed.
        # gen_systemrdl_param_files(params=params,
        #                           filename="global_buffer/systemRDL/rdl_models/glb.rdl.param")
        # gen_svh_files(params=params,
        #               filename="global_buffer/rtl/global_buffer_param.svh",
        #               header_name="global_buffer")

    # global_buffer = GlobalBuffer(num_glb_tiles=args.num_glb_tiles,
    #                              num_cgra_cols=args.num_cgra_cols,
    #                              glb_tile_mem_size=args.glb_tile_mem_size,
    #                              parameter_only=args.parameter_only)

    if args.rdl:
        top_rdl_name = "glb"
        rdl_file = "global_buffer/systemRDL/glb.rdl"
        glb_rdl = gen_global_buffer_rdl(top_rdl_name, params)
        glb_rdl.dump_rdl(rdl_file)

        rdl_parms_file = "global_buffer/systemRDL/ordt_params/glb.parms"
        rdl_output_folder = "global_buffer/systemRDL/output/"
        run_systemrdl(rdl_file,  rdl_parms_file, rdl_output_folder)

        output_pio = rdl_output_folder + top_rdl_name + "_pio.sv"
        gen_glb_pio_wrapper(output_pio)
    
    if args.verilog:
        glb_tile_cfg_ctrl = GlbTileCfg(params=params)
        k.verilog(glb_tile_cfg_ctrl, filename="glb_tile_cfg.sv")
        glb_core_proc_router = GlbCoreProcRouter(params=params)
        k.verilog(glb_core_proc_router, filename="glb_core_proc_router.sv")

    # if args.verilog:
    #     global_buffer_circ = global_buffer.circuit()
    #     magma.compile("global_buffer",
    #                   global_buffer_circ,
    #                   output="coreir-verilog",
    #                   inline=False)


if __name__ == "__main__":
    main()