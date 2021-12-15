import dataclasses
import math
import os


@dataclasses.dataclass(eq=True, frozen=False)
class GlobalBufferParams:
    # cgra parameters
    num_prr: int = 16
    num_prr_width: int = math.ceil(math.log(num_prr, 2))
    cgra_axi_addr_width: int = 13
    cgra_axi_data_width: int = 32

    # tile parameters
    num_glb_tiles: int = 16
    tile_sel_addr_width: int = math.ceil(math.log(num_glb_tiles, 2))

    # cgra tiles
    num_cgra_tiles: int = 32

    # cgra tiles per glb tile
    cgra_per_glb: int = num_cgra_tiles // num_glb_tiles  # 2

    # bank parameters
    banks_per_tile: int = 2
    bank_sel_addr_width: int = math.ceil(math.log(banks_per_tile, 2))
    bank_data_width: int = 64
    sram_macro_depth: int = 2048
    bank_addr_width: int = 17
    bank_byte_offset: int = math.ceil(math.log(bank_data_width / 8, 2))

    # glb parameters
    glb_addr_width: int = (bank_addr_width
                           + bank_sel_addr_width
                           + tile_sel_addr_width)

    # cgra data parameters
    cgra_data_width: int = 16
    cgra_byte_offset: int = math.ceil(math.log(cgra_data_width / 8, 2))

    # glb config parameters
    axi_addr_width: int = 12
    axi_addr_reg_width: int = 6
    axi_data_width: int = 32
    axi_strb_width: int = math.ceil(axi_data_width / 8)
    axi_byte_offset: int = math.ceil(math.log(axi_data_width / 8, 2))

    # max number of words in dma header
    max_num_words_width: int = (glb_addr_width
                                - bank_byte_offset
                                + math.ceil(math.log((bank_data_width
                                                      / cgra_data_width), 2)))
    max_stride_width: int = 10

    # max number of bitstream in dma header
    max_num_cfg_width: int = glb_addr_width - bank_byte_offset

    # cgra config parameters
    cgra_cfg_addr_width: int = 32
    cgra_cfg_data_width: int = 32

    # dma address generator
    queue_depth: int = 1
    loop_level: int = 5

    # dma latency
    latency_width: int = 2 + math.ceil(math.log(num_glb_tiles, 2))

    # pipeline depth
    glb_switch_pipeline_depth: int = 1  # fixed
    glb_bank_memory_pipeline_depth: int = 0
    sram_gen_pipeline_depth: int = 0
    sram_gen_output_pipeline_depth: int = 0

    is_sram_stub: int = 0

    # cycle count data width
    cycle_count_width: int = 16


def gen_global_buffer_params(**kwargs):
    # User-defined parameters
    num_prr = kwargs.pop('num_prr', 16)
    num_glb_tiles = kwargs.pop('num_glb_tiles', 16)
    num_cgra_cols = kwargs.pop('num_cgra_cols', 32)
    glb_tile_mem_size = kwargs.pop('glb_tile_mem_size', 256)
    banks_per_tile = kwargs.pop('banks_per_tile', 2)
    bank_data_width = kwargs.pop('bank_data_width', 64)
    sram_macro_depth = kwargs.pop('sram_macro_depth', 2048)
    axi_addr_width = kwargs.pop('axi_addr_width', 12)
    cgra_axi_addr_width = kwargs.pop('cgra_axi_addr_width', 13)
    cgra_axi_data_width = kwargs.pop('cgra_axi_data_width', 32)
    # TODO: axi_addr_reg_width should be automatically calculated based on configuration space
    axi_addr_reg_width = kwargs.pop('axi_addr_reg_width', 6)
    axi_data_width = kwargs.pop('axi_data_width', 32)
    cfg_addr_width = kwargs.pop('cfg_addr_width', 32)
    cfg_data_width = kwargs.pop('cfg_data_width', 32)
    cgra_data_width = kwargs.pop('cgra_data_width', 16)
    max_stride_width = kwargs.pop('max_stride_width', 10)
    queue_depth = kwargs.pop('queue_depth', 1)
    loop_level = kwargs.pop('loop_level', 5)
    glb_bank_memory_pipeline_depth = kwargs.pop('glb_bank_memory_pipeline_depth', 0)
    sram_gen_pipeline_depth = kwargs.pop('sram_gen_pipeline_depth', 0)
    sram_gen_output_pipeline_depth = kwargs.pop('sram_gen_output_pipeline_depth', 0)
    is_sram_stub = kwargs.pop('is_sram_stub', 0)

    # Check if there is unused kwargs
    if kwargs:
        raise Exception(f"{kwargs.keys()} are not supported parameters")

    # the number of glb tiles is half the number of cgra columns
    assert 2 * num_glb_tiles == num_cgra_cols

    def _power_of_two(n):
        if n == 1:
            return True
        elif n % 2 != 0 or n == 0:
            return False
        return _power_of_two(n / 2)

    assert _power_of_two(glb_tile_mem_size) is True

    # Unit is KB, so we add 10
    bank_addr_width = (math.ceil(math.log(glb_tile_mem_size, 2))
                       - math.ceil(math.log(banks_per_tile, 2)) + 10)
    bank_byte_offset = math.ceil(math.log(bank_data_width / 8, 2))
    cgra_byte_offset = math.ceil(math.log(cgra_data_width / 8, 2))
    axi_strb_width = math.ceil(axi_data_width / 8)
    axi_byte_offset = math.ceil(math.log(axi_data_width / 8, 2))
    glb_addr_width = (bank_addr_width
                      + math.ceil(math.log(banks_per_tile, 2))
                      + math.ceil(math.log(num_glb_tiles, 2)))
    tile_sel_addr_width = math.ceil(math.log(num_glb_tiles, 2))
    cgra_per_glb = num_cgra_cols // num_glb_tiles
    bank_sel_addr_width = math.ceil(math.log(banks_per_tile, 2))
    max_num_words_width = (glb_addr_width - bank_byte_offset
                           + math.ceil(math.log((bank_data_width
                                                 / cgra_data_width), 2)))
    max_num_cfg_width = glb_addr_width - bank_byte_offset
    latency_width = 2 + math.ceil(math.log(num_glb_tiles, 2))

    params = GlobalBufferParams(num_prr=num_prr,
                                num_glb_tiles=num_glb_tiles,
                                tile_sel_addr_width=tile_sel_addr_width,
                                num_cgra_tiles=num_cgra_cols,
                                cgra_per_glb=cgra_per_glb,
                                banks_per_tile=banks_per_tile,
                                bank_sel_addr_width=bank_sel_addr_width,
                                bank_data_width=bank_data_width,
                                sram_macro_depth=sram_macro_depth,
                                bank_addr_width=bank_addr_width,
                                bank_byte_offset=bank_byte_offset,
                                glb_addr_width=glb_addr_width,
                                cgra_data_width=cgra_data_width,
                                cgra_byte_offset=cgra_byte_offset,
                                cgra_axi_addr_width=cgra_axi_addr_width,
                                cgra_axi_data_width=cgra_axi_data_width,
                                axi_addr_width=axi_addr_width,
                                axi_addr_reg_width=axi_addr_reg_width,
                                axi_data_width=axi_data_width,
                                axi_strb_width=axi_strb_width,
                                axi_byte_offset=axi_byte_offset,
                                max_num_words_width=max_num_words_width,
                                max_stride_width=max_stride_width,
                                max_num_cfg_width=max_num_cfg_width,
                                cgra_cfg_addr_width=cfg_addr_width,
                                cgra_cfg_data_width=cfg_data_width,
                                queue_depth=queue_depth,
                                loop_level=loop_level,
                                latency_width=latency_width,
                                glb_bank_memory_pipeline_depth=glb_bank_memory_pipeline_depth,
                                sram_gen_pipeline_depth=sram_gen_pipeline_depth,
                                sram_gen_output_pipeline_depth=sram_gen_output_pipeline_depth,
                                is_sram_stub=is_sram_stub
                                )
    return params


def gen_header_files(params, svh_filename, h_filename, header_name):
    mod_params = dataclasses.asdict(params)
    folder = svh_filename.rsplit('/', 1)[0]
    # parameter pass to systemverilog package
    if not os.path.exists(folder):
        os.makedirs(folder)

    with open(svh_filename, "w") as f:
        f.write(f"`ifndef {header_name.upper()}_PARAM\n")
        f.write(f"`define {header_name.upper()}_PARAM\n")
        f.write(f"package {header_name}_param;\n")
        for k, v in mod_params.items():
            v = int(v)
            f.write(f"localparam int {k.upper()} = {v};\n")
        f.write(f"endpackage\n")
        f.write(f"`endif\n")

    with open(h_filename, "w") as f:
        f.write(f"#pragma once\n")
        for k, v in mod_params.items():
            v = int(v)
            f.write(f"#define {k.upper()} {v}\n")
