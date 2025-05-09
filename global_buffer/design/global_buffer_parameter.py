from dataclasses import dataclass, field, asdict
import math
import os


@dataclass(eq=True, frozen=False)
class GlobalBufferParams:
    @property
    def num_prr_width(self):
        return math.ceil(math.log(self.num_prr, 2))

    @property
    def tile_sel_addr_width(self):
        return math.ceil(math.log(self.num_glb_tiles, 2))

    @property
    def cgra_per_glb(self):
        return self.num_cgra_cols // self.num_glb_tiles  # 2

    @property
    def bank_sel_addr_width(self):
        return math.ceil(math.log(self.banks_per_tile, 2))

    @property
    def bank_strb_width(self):
        return math.ceil(self.bank_data_width / 8)

    @property
    def bank_byte_offset(self):
        return math.ceil(math.log(self.bank_data_width / 8, 2))

    @property
    def mu_word_byte_offset(self):
        return math.ceil(math.log(self.mu_word_width / 8, 2))

    @property
    def glb_addr_width(self):
        return self.bank_addr_width + self.bank_sel_addr_width + self.tile_sel_addr_width

    @property
    def mu_addr_width(self):
        return self.glb_addr_width
        # return self.glb_addr_width - math.ceil(math.log(self.mu_word_num_tiles, 2)) - self.bank_sel_addr_width

    @property
    def mu_rd_max_num_glb_reqs(self):
        return self.mu_rd_max_burst_size // (self.mu_word_width // 8)

    @property
    def mu_glb_rd_latency(self):
        return ((2*self.num_glb_tiles) - 1) + self.mu_rd_addr2tile0_delay + self.mu_sw2bank_mux_delay + self.bankmux2sram_rd_delay  + self.mu_sw2track_out_delay + self.mu_rd_data_tile0_2out_delay

    @property
    def mu_tl_resp_fifo_depth(self):
        return self.mu_tl_req_fifo_depth * self.mu_rd_max_num_glb_reqs

    @property
    def cgra_byte_offset(self):
        return math.ceil(math.log(self.cgra_data_width / 8, 2))

    @property
    def axi_addr_width(self):
        return self.cgra_axi_addr_width - 1

    @property
    def axi_addr_reg_width(self):
        return (self.axi_addr_width
                - math.ceil(math.log(self.num_glb_tiles, 2)) - math.ceil(math.log(self.cgra_axi_data_width / 8, 2)))

    @property
    def axi_strb_width(self):
        return math.ceil(self.axi_data_width / 8)

    @property
    def axi_byte_offset(self):
        return math.ceil(math.log(self.axi_data_width / 8, 2))

    # max number of bitstream in dma header
    @property
    def max_num_cfg_width(self):
        return self.glb_addr_width - self.bank_byte_offset

    @property
    def num_groups(self):
        return self.num_cgra_cols // self.num_cols_per_group

    @property
    def sram_macro_depth(self):
        if self.process == "TSMC":
            return 2048
        else:
            return 4096

    # architecture parameters
    num_prr: int = 16
    num_cgra_cols: int = 32
    num_cgra_cols_including_io: int = 32
    num_glb_tiles: int = 16
    num_cols_per_group: int = 4
    banks_per_tile: int = 2
    bank_addr_width: int = 17
    bank_data_width: int = 64
    cgra_data_width: int = 16
    axi_data_width: int = 32
    cgra_axi_addr_width: int = 13
    cgra_axi_data_width: int = 32
    cgra_cfg_addr_width: int = 32
    cgra_cfg_data_width: int = 32

    # zircon parameters
    include_E64_hw: bool = False
    include_multi_bank_hw: bool = False
    include_mu_glb_hw: bool = False
    include_glb_ring_switch: bool = False
    mu_word_num_tiles: int = 2
    mu_switch_num_tracks: int = 4
    mu_word_width: int = 256
    mu_tl_num_burst_bits: int = 4
    mu_tl_source_width: int = 7
    mu_tl_req_fifo_depth: int = 4
    mu_tl_opcode_width: int = 3
    mu_tl_rd_resp_opcode: int = 1
    input_scale_req_src_code: int = 1
    mu_tl_crossbar_source_id_width: int = 3

    # MU rd max burst (in bytes) = max(ic, oc) * 2. For 64x32 array, it is 64 * 2 = 128
    mu_rd_max_burst_size: int = 128

    # Not used by TSMC (yet)
    load_dma_fifo_depth: int = 16
    store_dma_fifo_depth: int = 4
    max_num_chain: int = 8

    # cell parameters
    process: str = "INTEL"
    tsmc_icg_name: str = "CKLNQD1BWP16P90"
    gf_icg_name: str = "SC7P5T_CKGPRELATNX1_SSC14R"
    intel_icg_name: str = "b0mcilb05hn1n16x5"  # b0mcilb05hn1n16x5 (nom), b0mcilb05as1n16x5 (ulvt)
    tsmc_sram_macro_prefix: str = "TS1N16FFCLLSBLVTC2048X64M8SW"
    gf_sram_macro_prefix: str = "IN12LP_S1DB_"

    # constant variables: not used by TSMC (yet)
    st_dma_valid_mode_valid: int = 0
    st_dma_valid_mode_sparse_ready_valid: int = 1
    st_dma_valid_mode_static: int = 2
    st_dma_valid_mode_dense_ready_valid: int = 3

    # zircon variables
    exchange_64_multibank_mode: int = 3

    ld_dma_valid_mode_static: int = 0
    ld_dma_valid_mode_valid: int = 1
    ld_dma_valid_mode_ready_valid: int = 2

    ld_dma_flush_mode_external: int = 0
    ld_dma_flush_mode_internal: int = 1

    # Same for TSMC, GF
    sram_macro_word_size: int = 64
    sram_macro_mux_size: int = 8
    sram_macro_num_subarrays: int = 2

    # dependent field
    num_prr_width: int = field(init=False, default=num_prr_width)
    tile_sel_addr_width: int = field(init=False, default=tile_sel_addr_width)
    cgra_per_glb: int = field(init=False, default=cgra_per_glb)
    bank_sel_addr_width: int = field(init=False, default=bank_sel_addr_width)
    bank_strb_width: int = field(init=False, default=bank_strb_width)
    bank_byte_offset: int = field(init=False, default=bank_byte_offset)
    glb_addr_width: int = field(init=False, default=glb_addr_width)
    mu_addr_width: int = field(init=False, default=mu_addr_width)
    mu_tl_resp_fifo_depth: int = field(init=False, default=mu_tl_resp_fifo_depth)
    mu_rd_max_num_glb_reqs: int = field(init=False, default=mu_rd_max_num_glb_reqs)
    mu_glb_rd_latency: int = field(init=False, default=mu_glb_rd_latency)
    cgra_byte_offset: int = field(init=False, default=cgra_byte_offset)
    axi_addr_width: int = field(init=False, default=axi_addr_width)
    axi_addr_reg_width: int = field(init=False, default=axi_addr_reg_width)
    axi_strb_width: int = field(init=False, default=axi_strb_width)
    axi_byte_offset: int = field(init=False, default=axi_byte_offset)
    max_num_cfg_width: int = field(init=False, default=max_num_cfg_width)
    num_groups: int = field(init=False, default=num_groups)

    # dma address generator
    queue_depth: int = 1
    load_dma_loop_level: int = 8
    store_dma_loop_level: int = 7
    loop_level: int = max(load_dma_loop_level, store_dma_loop_level)

    # dma latency
    chain_latency_overhead: int = 3
    latency_width: int = math.ceil(math.log(num_glb_tiles * 2 + chain_latency_overhead, 2))
    pcfg_latency_width: int = math.ceil(math.log(num_glb_tiles * 3 + chain_latency_overhead, 2))

    # pipeline depth
    sram_macro_read_latency: int = 1  # Constant
    glb_dma2bank_delay: int = 1  # Constant
    glb_sw2bank_pipeline_depth: int = 0
    glb_bank2sw_pipeline_depth: int = 1
    glb_bank_memory_pipeline_depth: int = 0
    sram_gen_pipeline_depth: int = 0
    sram_gen_output_pipeline_depth: int = 0
    gls_pipeline_depth: int = 0
    tile2sram_wr_delay: int = (glb_dma2bank_delay + glb_sw2bank_pipeline_depth
                               + glb_bank_memory_pipeline_depth + sram_gen_pipeline_depth)
    tile2sram_rd_delay: int = (glb_dma2bank_delay + glb_sw2bank_pipeline_depth + glb_bank_memory_pipeline_depth
                               + sram_gen_pipeline_depth + glb_bank2sw_pipeline_depth + sram_gen_output_pipeline_depth
                               + sram_macro_read_latency)

    bankmux2sram_wr_delay: int = glb_sw2bank_pipeline_depth + glb_bank_memory_pipeline_depth + sram_gen_pipeline_depth
    bankmux2sram_rd_delay: int = (glb_sw2bank_pipeline_depth + glb_bank_memory_pipeline_depth + sram_gen_pipeline_depth
                                  + glb_bank2sw_pipeline_depth + sram_gen_output_pipeline_depth
                                  + sram_macro_read_latency
                                  )
    mu_rd_addr2tile0_delay: int = 2
    mu_rd_data_tile0_2out_delay: int = 1
    mu_sw2bank_mux_delay: int = 1
    mu_sw2track_out_delay: int = 1

    # Not used by TSMC (yet)
    flush_crossbar_pipeline_depth: int = 1

    rd_clk_en_margin: int = 3
    wr_clk_en_margin: int = 3
    proc_clk_en_margin: int = 4
    mu_clk_en_margin: int = 5

    is_sram_stub: int = 0

    # Not used by TSMC (yet)
    config_port_pipeline_depth: int = 1

    # cycle count data width
    cycle_count_width: int = 16

    # interrupt cnt
    interrupt_cnt: int = 5

    # TSMC-specific tweaks
    if os.getenv('WHICH_SOC') == "amber":
        process = "TSMC"


def gen_global_buffer_params(**kwargs):
    # User-defined parameters
    num_prr = kwargs.pop('num_prr', 16)
    num_glb_tiles = kwargs.pop('num_glb_tiles', 16)
    num_cgra_cols = kwargs.pop('num_cgra_cols', 32)
    num_cgra_cols_including_io = kwargs.pop('num_cgra_cols_including_io', 32)
    glb_tile_mem_size = kwargs.pop('glb_tile_mem_size', 256)
    bank_data_width = kwargs.pop('bank_data_width', 64)
    banks_per_tile = kwargs.pop('banks_per_tile', 2)
    cgra_axi_addr_width = kwargs.pop('cgra_axi_addr_width', 13)
    axi_data_width = kwargs.pop('axi_data_width', 32)
    cfg_addr_width = kwargs.pop('cfg_addr_width', 32)
    cfg_data_width = kwargs.pop('cfg_data_width', 32)
    is_sram_stub = kwargs.pop('is_sram_stub', 0)

    # config_port_pipeline not used by TSMC (yet)
    # pop() returns True if config_port_pipeline not exists
    config_port_pipeline = kwargs.pop('config_port_pipeline', True)

    include_E64_hw = kwargs.pop('include_E64_hw', False)
    include_multi_bank_hw = kwargs.pop('include_multi_bank_hw', False)
    include_mu_glb_hw = kwargs.pop('include_mu_glb_hw', False)
    include_glb_ring_switch = kwargs.pop('include_glb_ring_switch', False)

    if config_port_pipeline is True:
        config_port_pipeline_depth = 1
    else:
        config_port_pipeline_depth = 0

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

    params = GlobalBufferParams(num_prr=num_prr,
                                num_glb_tiles=num_glb_tiles,
                                num_cgra_cols=num_cgra_cols,
                                num_cgra_cols_including_io=num_cgra_cols_including_io,
                                banks_per_tile=banks_per_tile,
                                bank_data_width=bank_data_width,
                                bank_addr_width=bank_addr_width,
                                cgra_axi_addr_width=cgra_axi_addr_width,
                                axi_data_width=axi_data_width,
                                cgra_cfg_addr_width=cfg_addr_width,
                                cgra_cfg_data_width=cfg_data_width,
                                is_sram_stub=is_sram_stub,
                                config_port_pipeline_depth=config_port_pipeline_depth,
                                include_E64_hw=include_E64_hw,
                                include_multi_bank_hw=include_multi_bank_hw,
                                include_mu_glb_hw=include_mu_glb_hw,
                                include_glb_ring_switch=include_glb_ring_switch)

    return params


def gen_header_files(params, svh_filename, h_filename, header_name):
    mod_params = asdict(params)
    folder = svh_filename.rsplit('/', 1)[0]
    # parameter pass to systemverilog package
    if not os.path.exists(folder):
        os.makedirs(folder)

    with open(svh_filename, "w") as f:
        f.write(f"`ifndef {header_name.upper()}_PARAM\n")
        f.write(f"`define {header_name.upper()}_PARAM\n")
        f.write(f"package {header_name}_param;\n")
        for k, v in mod_params.items():
            if type(v) is str:
                continue
            v = int(v)
            f.write(f"localparam int {k.upper()} = {v};\n")
        f.write("endpackage\n")
        f.write("`endif\n")

    with open(h_filename, "w") as f:
        f.write("#pragma once\n")
        for k, v in mod_params.items():
            if type(v) is str:
                continue
            v = int(v)
            f.write(f"#define {k.upper()} {v}\n")
