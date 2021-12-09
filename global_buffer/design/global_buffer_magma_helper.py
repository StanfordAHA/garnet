import magma as m
from global_buffer.design.global_buffer_parameter import GlobalBufferParams


def _get_raw_interface(params: GlobalBufferParams):
    return dict(
        clk=m.In(m.clock),
        stall=m.In(m.Bits[params.num_glb_tiles]),
        cgra_stall_in=m.In(m.Bits[params.num_glb_tiles]),
        reset=m.In(m.asyncreset),
        cgra_soft_reset=m.In(m.Bit),

        # proc
        proc_wr_en=m.In(m.Bit),
        proc_wr_strb=m.In(m.Bits[params.bank_data_width // 8]),
        proc_wr_addr=m.In(m.Bits[params.glb_addr_width]),
        proc_wr_data=m.In(m.Bits[params.bank_data_width]),
        proc_rd_en=m.In(m.Bit),
        proc_rd_addr=m.In(m.Bits[params.glb_addr_width]),
        proc_rd_data=m.Out(m.Bits[params.bank_data_width]),
        proc_rd_data_valid=m.Out(m.Bit),

        # configuration of glb from glc
        if_cfg_wr_en=m.In(m.Bit),
        if_cfg_wr_clk_en=m.In(m.Bit),
        if_cfg_wr_addr=m.In(m.Bits[params.axi_addr_width]),
        if_cfg_wr_data=m.In(m.Bits[params.axi_data_width]),
        if_cfg_rd_en=m.In(m.Bit),
        if_cfg_rd_clk_en=m.In(m.Bit),
        if_cfg_rd_addr=m.In(m.Bits[params.axi_addr_width]),
        if_cfg_rd_data=m.Out(m.Bits[params.axi_data_width]),
        if_cfg_rd_data_valid=m.Out(m.Bit),

        # configuration of sram from glc
        if_sram_cfg_wr_en=m.In(m.Bit),
        if_sram_cfg_wr_clk_en=m.In(m.Bit),
        if_sram_cfg_wr_addr=m.In(m.Bits[params.glb_addr_width]),
        if_sram_cfg_wr_data=m.In(m.Bits[params.axi_data_width]),
        if_sram_cfg_rd_en=m.In(m.Bit),
        if_sram_cfg_rd_clk_en=m.In(m.Bit),
        if_sram_cfg_rd_addr=m.In(m.Bits[params.glb_addr_width]),
        if_sram_cfg_rd_data=m.Out(m.Bits[params.axi_data_width]),
        if_sram_cfg_rd_data_valid=m.Out(m.Bit),

        # cgra to glb streaming word
        stream_data_f2g=m.In(m.Array[params.num_glb_tiles,
                             m.Array[params.cgra_per_glb, m.Bits[params.cgra_data_width]]]),
        stream_data_valid_f2g=m.In(m.Array[params.num_glb_tiles, m.Bits[params.cgra_per_glb]]),

        # glb to cgra streaming word
        stream_data_g2f=m.Out(m.Array[params.num_glb_tiles,
                              m.Array[params.cgra_per_glb, m.Bits[params.cgra_data_width]]]),
        stream_data_valid_g2f=m.Out(m.Array[params.num_glb_tiles, m.Bits[params.cgra_per_glb]]),

        # cgra configuration from global controller
        cgra_cfg_jtag_gc2glb_wr_en=m.In(m.Bits[1]),
        cgra_cfg_jtag_gc2glb_rd_en=m.In(m.Bits[1]),
        cgra_cfg_jtag_gc2glb_addr=m.In(m.Bits[params.cgra_cfg_addr_width]),
        cgra_cfg_jtag_gc2glb_data=m.In(m.Bits[params.cgra_cfg_data_width]),

        # cgra configuration to cgra
        cgra_cfg_g2f_cfg_wr_en=m.Out(m.Array[params.num_glb_tiles, m.Bits[params.cgra_per_glb]]),
        cgra_cfg_g2f_cfg_rd_en=m.Out(m.Array[params.num_glb_tiles, m.Bits[params.cgra_per_glb]]),
        cgra_cfg_g2f_cfg_addr=m.Out(
            m.Array[params.num_glb_tiles, m.Array[params.cgra_per_glb, m.Bits[params.cgra_cfg_addr_width]]]),
        cgra_cfg_g2f_cfg_data=m.Out(
            m.Array[params.num_glb_tiles, m.Array[params.cgra_per_glb, m.Bits[params.cgra_cfg_data_width]]]),

        cgra_stall=m.Out(m.Array[params.num_glb_tiles, m.Bits[params.cgra_per_glb]]),

        strm_start_pulse=m.In(m.Bits[params.num_glb_tiles]),
        pc_start_pulse=m.In(m.Bits[params.num_glb_tiles]),
        strm_f2g_interrupt_pulse=m.Out(m.Bits[params.num_glb_tiles]),
        strm_g2f_interrupt_pulse=m.Out(m.Bits[params.num_glb_tiles]),
        pcfg_g2f_interrupt_pulse=m.Out(m.Bits[params.num_glb_tiles]),
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
