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
    BANK_ADDR_BYTE_OFFSET: int = m.bitutils.clog2(BANK_DATA_WIDTH//8)

    # Glb parameters
    GLB_ADDR_WIDTH: int = BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH + TILE_SEL_ADDR_WIDTH

    # CGRA data parameters
    CGRA_DATA_WIDTH: int = 16

    # MAX_NUM_WORDS
    MAX_NUM_WORDS_WIDTH: int = GLB_ADDR_WIDTH - BANK_ADDR_BYTE_OFFSET + m.bitutils.clog2(BANK_DATA_WIDTH//CGRA_DATA_WIDTH) # 21
    # MAX_NUM_CFG
    MAX_NUM_CFGS_WIDTH: int = GLB_ADDR_WIDTH - BANK_ADDR_BYTE_OFFSET # 19

    # Glb config parameters
    AXI_ADDR_WIDTH: int = 12
    AXI_DATA_WIDTH: int = 32
    AXI_STRB_WIDTH: int = (AXI_DATA_WIDTH // 8)
    AXI_BYTE_OFFSET: int = m.bitutils.clog2(AXI_DATA_WIDTH//8)
    CFG_REG_SEL_WIDTH: int = AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH - AXI_BYTE_OFFSET

    # CGRA config parameters
    CGRA_CFG_ADDR_WIDTH: int = 32
    CGRA_CFG_DATA_WIDTH: int = 32

    # DMA header queue depth
    QUEUE_DEPTH: int = 4


def _get_raw_interface(params: GlobalBufferParams):
    return dict(
        clk                               = m.In(m.Clock),
        stall                             = m.In(m.Bit),
        reset                             = m.In(m.Reset),

        # proc
        proc2glb_wr_en                    = m.In(m.Bit),
        proc2glb_wr_strb                  = m.In(m.Bits[params.BANK_DATA_WIDTH // 8]),
        proc2glb_wr_addr                  = m.In(m.Bits[params.GLB_ADDR_WIDTH]),
        proc2glb_wr_data                  = m.In(m.Bits[params.BANK_DATA_WIDTH]),
        proc2glb_rd_en                    = m.In(m.Bit),
        proc2glb_rd_addr                  = m.In(m.Bits[params.GLB_ADDR_WIDTH]),
        glb2proc_rd_data                  = m.Out(m.Bits[params.BANK_DATA_WIDTH]),
        glb2proc_rd_data_valid            = m.Out(m.Bit),

        # configuration of glb from glc
        glb_cfg_wr_en                     = m.In(m.Bit),
        glb_cfg_wr_clk_en                 = m.In(m.Bit),
        glb_cfg_wr_addr                   = m.In(m.Bits[params.AXI_ADDR_WIDTH]),
        glb_cfg_wr_data                   = m.In(m.Bits[params.AXI_DATA_WIDTH]),
        glb_cfg_rd_en                     = m.In(m.Bit),
        glb_cfg_rd_clk_en                 = m.In(m.Bit),
        glb_cfg_rd_addr                   = m.In(m.Bits[params.AXI_ADDR_WIDTH]),
        glb_cfg_rd_data                   = m.Out(m.Bits[params.AXI_DATA_WIDTH]),
        glb_cfg_rd_data_valid             = m.Out(m.Bit),

        # configuration of sram from glc
        sram_cfg_wr_en                    = m.In(m.Bit),
        sram_cfg_wr_clk_en                = m.In(m.Bit),
        sram_cfg_wr_addr                  = m.In(m.Bits[params.GLB_ADDR_WIDTH]),
        sram_cfg_wr_data                  = m.In(m.Bits[params.AXI_DATA_WIDTH]),
        sram_cfg_rd_en                    = m.In(m.Bit),
        sram_cfg_rd_clk_en                = m.In(m.Bit),
        sram_cfg_rd_addr                  = m.In(m.Bits[params.GLB_ADDR_WIDTH]),
        sram_cfg_rd_data                  = m.Out(m.Bits[params.AXI_DATA_WIDTH]),
        sram_cfg_rd_data_valid            = m.Out(m.Bit),

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

        strm_start_pulse                  = m.In(m.Bits[params.NUM_GLB_TILES]),
        pc_start_pulse                    = m.In(m.Bits[params.NUM_GLB_TILES]),
        interrupt_pulse                   = m.Out(m.Bits[3 * params.NUM_GLB_TILES]),
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
    def __init__(self, params: GlobalBufferParams):
        self.params = params
        self.name = "global_buffer"
        args = _flatten(_get_raw_interface(params))
        self.io = m.IO(**args)
