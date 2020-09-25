import dataclasses
import magma as m


@dataclasses.dataclass(eq=True, frozen=True)
class GlobalBufferParams:
    # Tile parameters
    NUM_GLB_TILES: int = 16
    TILE_SEL_ADDR_WIDTH: int = m.bitutils.clog2(NUM_GLB_TILES)

    # CGRA Tiles
    NUM_CGRA_TILES: int = 32

    # CGRA tiles per GLB tile
    CGRA_PER_GLB: int = NUM_CGRA_TILES // NUM_GLB_TILES # 2

    # Bank parameters
    BANKS_PER_TILE: int = 2
    BANK_SEL_ADDR_WIDTH: int = m.bitutils.clog2(BANKS_PER_TILE)
    BANK_DATA_WIDTH: int = 64
    BANK_ADDR_WIDTH: int = 17
    BANK_BYTE_OFFSET: int = m.bitutils.clog2(BANK_DATA_WIDTH // 8)

    # Glb parameters
    GLB_ADDR_WIDTH: int = (BANK_ADDR_WIDTH
                           + BANK_SEL_ADDR_WIDTH
                           + TILE_SEL_ADDR_WIDTH)

    # CGRA data parameters
    CGRA_DATA_WIDTH: int = 16
    CGRA_BYTE_OFFSET: int = m.bitutils.clog2(CGRA_DATA_WIDTH // 8)

    # Glb config parameters
    AXI_ADDR_WIDTH: int = 12
    AXI_DATA_WIDTH: int = 32
    AXI_STRB_WIDTH: int = (AXI_DATA_WIDTH // 8)
    AXI_BYTE_OFFSET: int = m.bitutils.clog2(AXI_DATA_WIDTH // 8)

    # Max number of words in dma header
    MAX_NUM_WORDS_WIDTH: int = (GLB_ADDR_WIDTH
                                - BANK_BYTE_OFFSET
                                + m.bitutils.clog2(BANK_DATA_WIDTH
                                                   // CGRA_DATA_WIDTH))
    MAX_STRIDE_WIDTH: int = AXI_DATA_WIDTH - MAX_NUM_WORDS_WIDTH

    # Max number of bitstream in dma header
    MAX_NUM_CFGS_WIDTH: int = GLB_ADDR_WIDTH - BANK_BYTE_OFFSET

    # CGRA config parameters
    CGRA_CFG_ADDR_WIDTH: int = 32
    CGRA_CFG_DATA_WIDTH: int = 32

    # DMA address generator
    QUEUE_DEPTH: int = 4
    LOOP_LEVEL: int = 4

    # DMA latency
    LATENCY_WIDTH: int = 1 + m.bitutils.clog2(NUM_GLB_TILES)

def _get_raw_interface(params: GlobalBufferParams):
    return dict(
        clk                               = m.In(m.Clock),
        stall                             = m.In(m.Bit),
        cgra_stall_in                     = m.In(m.Bit),
        reset                             = m.In(m.Reset),
        cgra_soft_reset                   = m.In(m.Bit),

        # proc
        proc_wr_en                        = m.In(m.Bit),
        proc_wr_strb                      = m.In(m.Bits[params.BANK_DATA_WIDTH // 8]),
        proc_wr_addr                      = m.In(m.Bits[params.GLB_ADDR_WIDTH]),
        proc_wr_data                      = m.In(m.Bits[params.BANK_DATA_WIDTH]),
        proc_rd_en                        = m.In(m.Bit),
        proc_rd_addr                      = m.In(m.Bits[params.GLB_ADDR_WIDTH]),
        proc_rd_data                      = m.Out(m.Bits[params.BANK_DATA_WIDTH]),
        proc_rd_data_valid                = m.Out(m.Bit),

        # configuration of glb from glc
        if_cfg_wr_en                      = m.In(m.Bit),
        if_cfg_wr_clk_en                  = m.In(m.Bit),
        if_cfg_wr_addr                    = m.In(m.Bits[params.AXI_ADDR_WIDTH]),
        if_cfg_wr_data                    = m.In(m.Bits[params.AXI_DATA_WIDTH]),
        if_cfg_rd_en                      = m.In(m.Bit),
        if_cfg_rd_clk_en                  = m.In(m.Bit),
        if_cfg_rd_addr                    = m.In(m.Bits[params.AXI_ADDR_WIDTH]),
        if_cfg_rd_data                    = m.Out(m.Bits[params.AXI_DATA_WIDTH]),
        if_cfg_rd_data_valid              = m.Out(m.Bit),

        # configuration of sram from glc
        if_sram_cfg_wr_en                 = m.In(m.Bit),
        if_sram_cfg_wr_clk_en             = m.In(m.Bit),
        if_sram_cfg_wr_addr               = m.In(m.Bits[params.GLB_ADDR_WIDTH]),
        if_sram_cfg_wr_data               = m.In(m.Bits[params.AXI_DATA_WIDTH]),
        if_sram_cfg_rd_en                 = m.In(m.Bit),
        if_sram_cfg_rd_clk_en             = m.In(m.Bit),
        if_sram_cfg_rd_addr               = m.In(m.Bits[params.GLB_ADDR_WIDTH]),
        if_sram_cfg_rd_data               = m.Out(m.Bits[params.AXI_DATA_WIDTH]),
        if_sram_cfg_rd_data_valid         = m.Out(m.Bit),

        # cgra to glb streaming word
        stream_data_f2g                   = m.In(m.Array[params.NUM_GLB_TILES, m.Array[params.CGRA_PER_GLB, m.Bits[params.CGRA_DATA_WIDTH]]]),
        stream_data_valid_f2g             = m.In(m.Array[params.NUM_GLB_TILES, m.Bits[params.CGRA_PER_GLB]]),

        # glb to cgra streaming word
        stream_data_g2f                   = m.Out(m.Array[params.NUM_GLB_TILES, m.Array[params.CGRA_PER_GLB, m.Bits[params.CGRA_DATA_WIDTH]]]),
        stream_data_valid_g2f             = m.Out(m.Array[params.NUM_GLB_TILES, m.Bits[params.CGRA_PER_GLB]]),

        # cgra configuration from global controller
        cgra_cfg_jtag_gc2glb_wr_en        = m.In(m.Bits[1]),
        cgra_cfg_jtag_gc2glb_rd_en        = m.In(m.Bits[1]),
        cgra_cfg_jtag_gc2glb_addr         = m.In(m.Bits[params.CGRA_CFG_ADDR_WIDTH]),
        cgra_cfg_jtag_gc2glb_data         = m.In(m.Bits[params.CGRA_CFG_DATA_WIDTH]),

        # cgra configuration to cgra
        cgra_cfg_g2f_cfg_wr_en            = m.Out(m.Array[params.NUM_GLB_TILES, m.Bits[params.CGRA_PER_GLB]]),
        cgra_cfg_g2f_cfg_rd_en            = m.Out(m.Array[params.NUM_GLB_TILES, m.Bits[params.CGRA_PER_GLB]]),
        cgra_cfg_g2f_cfg_addr             = m.Out(m.Array[params.NUM_GLB_TILES, m.Array[params.CGRA_PER_GLB, m.Bits[params.CGRA_CFG_ADDR_WIDTH]]]),
        cgra_cfg_g2f_cfg_data             = m.Out(m.Array[params.NUM_GLB_TILES, m.Array[params.CGRA_PER_GLB, m.Bits[params.CGRA_CFG_DATA_WIDTH]]]),

        cgra_stall                        = m.Out(m.Array[params.NUM_GLB_TILES, m.Bits[params.CGRA_PER_GLB]]),

        strm_start_pulse                  = m.In(m.Bits[params.NUM_GLB_TILES]),
        pc_start_pulse                    = m.In(m.Bits[params.NUM_GLB_TILES]),
        strm_f2g_interrupt_pulse          = m.Out(m.Bits[params.NUM_GLB_TILES]),
        strm_g2f_interrupt_pulse          = m.Out(m.Bits[params.NUM_GLB_TILES]),
        pcfg_g2f_interrupt_pulse          = m.Out(m.Bits[params.NUM_GLB_TILES]),
    )


def _flatten(types):

    def _map(t):
        # Don't need to flatten non-array typess, or even Bits types since they
        # are already flat.
        if not issubclass(t, m.Array) or issubclass(t, m.Bits):
            return t
        size = t.N
        t = t.T
        while not issubclass(t, m.Digital):
            size *= t.N
            t = t.T
        return m.Bits[size].qualify(t.direction)

    return {k: _map(t) for k, t in types.items()}


class GlobalBufferDeclarationGenerator(m.Generator2):
    def __init__(self, params: GlobalBufferParams = None):

        # if parameters are not passed, use the default parameters
        if params is None:
            params = GlobalBufferParams()
        self.params = params
        self.name = "global_buffer"

        args = _flatten(_get_raw_interface(self.params))
        self.io = m.IO(**args)

    def gen_param_files(self):
        if self.params is None:
            self.params = GlobalBufferParams()
        mod_params = dataclasses.asdict(self.params)

        # parameter pass to systemverilog package
        with open("global_buffer/rtl/global_buffer_param.svh", "w") as f:
            f.write(f"`ifndef GLOBAL_BUFFER_PARAM\n")
            f.write(f"`define GLOBAL_BUFFER_PARAM\n")
            f.write(f"package global_buffer_param;\n")
            for k, v in mod_params.items():
                f.write(f"localparam int {k} = {v};\n")
            f.write(f"endpackage\n")
            f.write(f"`endif\n")

        # paramter pass to systemRDL
        with open("global_buffer/systemRDL/rdl_models/glb.rdl.param", "w") as f:
            f.write(f"// Perl Embedding\n")
            f.write(f"<%\n")
            for k, v in mod_params.items():
                f.write(f"use constant {k} => {v};\n")
            f.write(f"%>\n")
