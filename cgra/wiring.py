from gemstone.generator.const import Const


def glb_glc_wiring(garnet):
    """ global controller <-> global buffer ports connection """

    garnet.wire(garnet.global_controller.ports.reset_out,
                garnet.global_buffer.ports.reset)

    garnet.wire(garnet.global_controller.ports.glb_clk_en_master,
                garnet.global_buffer.ports.glb_clk_en_master)
    garnet.wire(garnet.global_controller.ports.glb_clk_en_bank_master,
                garnet.global_buffer.ports.glb_clk_en_bank_master)
    garnet.wire(garnet.global_controller.ports.glb_pcfg_broadcast_stall,
                garnet.global_buffer.ports.pcfg_broadcast_stall)
    garnet.wire(garnet.global_controller.ports.glb_flush_crossbar_sel,
                garnet.global_buffer.ports.flush_crossbar_sel)

    garnet.wire(garnet.global_controller.ports.cgra_config.config_addr,
                garnet.global_buffer.ports.cgra_cfg_jtag_gc2glb_addr)
    garnet.wire(garnet.global_controller.ports.cgra_config.config_data,
                garnet.global_buffer.ports.cgra_cfg_jtag_gc2glb_data)
    garnet.wire(garnet.global_controller.ports.cgra_config.read,
                garnet.global_buffer.ports.cgra_cfg_jtag_gc2glb_rd_en)
    garnet.wire(garnet.global_controller.ports.cgra_config.write,
                garnet.global_buffer.ports.cgra_cfg_jtag_gc2glb_wr_en)

    garnet.wire(garnet.global_controller.ports.glb_cfg.wr_en,
                garnet.global_buffer.ports.if_cfg_wr_en[0])
    garnet.wire(garnet.global_controller.ports.glb_cfg.wr_clk_en,
                garnet.global_buffer.ports.if_cfg_wr_clk_en[0])
    garnet.wire(garnet.global_controller.ports.glb_cfg.wr_addr,
                garnet.global_buffer.ports.if_cfg_wr_addr)
    garnet.wire(garnet.global_controller.ports.glb_cfg.wr_data,
                garnet.global_buffer.ports.if_cfg_wr_data)
    garnet.wire(garnet.global_controller.ports.glb_cfg.rd_en,
                garnet.global_buffer.ports.if_cfg_rd_en[0])
    garnet.wire(garnet.global_controller.ports.glb_cfg.rd_clk_en,
                garnet.global_buffer.ports.if_cfg_rd_clk_en[0])
    garnet.wire(garnet.global_controller.ports.glb_cfg.rd_addr,
                garnet.global_buffer.ports.if_cfg_rd_addr)
    garnet.wire(garnet.global_controller.ports.glb_cfg.rd_data,
                garnet.global_buffer.ports.if_cfg_rd_data)
    garnet.wire(garnet.global_controller.ports.glb_cfg.rd_data_valid,
                garnet.global_buffer.ports.if_cfg_rd_data_valid[0])

    garnet.wire(garnet.global_controller.ports.sram_cfg.wr_en,
                garnet.global_buffer.ports.if_sram_cfg_wr_en[0])
    garnet.wire(garnet.global_controller.ports.sram_cfg.wr_addr,
                garnet.global_buffer.ports.if_sram_cfg_wr_addr)
    garnet.wire(garnet.global_controller.ports.sram_cfg.wr_data,
                garnet.global_buffer.ports.if_sram_cfg_wr_data)
    garnet.wire(garnet.global_controller.ports.sram_cfg.rd_en,
                garnet.global_buffer.ports.if_sram_cfg_rd_en[0])
    garnet.wire(garnet.global_controller.ports.sram_cfg.rd_addr,
                garnet.global_buffer.ports.if_sram_cfg_rd_addr)
    garnet.wire(garnet.global_controller.ports.sram_cfg.rd_data,
                garnet.global_buffer.ports.if_sram_cfg_rd_data)
    garnet.wire(garnet.global_controller.ports.sram_cfg.rd_data_valid,
                garnet.global_buffer.ports.if_sram_cfg_rd_data_valid[0])

    garnet.wire(garnet.global_controller.ports.strm_g2f_start_pulse,
                garnet.global_buffer.ports.strm_g2f_start_pulse)
    garnet.wire(garnet.global_controller.ports.strm_f2g_start_pulse,
                garnet.global_buffer.ports.strm_f2g_start_pulse)
    garnet.wire(garnet.global_controller.ports.pc_start_pulse,
                garnet.global_buffer.ports.pcfg_start_pulse)
    garnet.wire(garnet.global_controller.ports.strm_f2g_interrupt_pulse,
                garnet.global_buffer.ports.strm_f2g_interrupt_pulse)
    garnet.wire(garnet.global_controller.ports.strm_g2f_interrupt_pulse,
                garnet.global_buffer.ports.strm_g2f_interrupt_pulse)
    garnet.wire(garnet.global_controller.ports.pcfg_g2f_interrupt_pulse,
                garnet.global_buffer.ports.pcfg_g2f_interrupt_pulse)

    return garnet


def glb_interconnect_wiring(garnet):

    # width of garnet
    width = garnet.width
    num_glb_tiles = garnet.glb_params.num_glb_tiles
    num_groups = garnet.glb_params.num_groups
    col_per_glb = width // num_glb_tiles
    assert width % num_glb_tiles == 0

    # parallel configuration ports wiring
    for i in range(num_glb_tiles):
        for j in range(col_per_glb):
            cfg_data_port_name = f"cgra_cfg_g2f_cfg_data_{i}_{j}"
            cfg_addr_port_name = f"cgra_cfg_g2f_cfg_addr_{i}_{j}"
            cfg_rd_en_port_name = f"cgra_cfg_g2f_cfg_rd_en_{i}_{j}"
            cfg_wr_en_port_name = f"cgra_cfg_g2f_cfg_wr_en_{i}_{j}"
            garnet.wire(garnet.global_buffer.ports[cfg_data_port_name],
                        garnet.interconnect.ports.config[i * col_per_glb + j].config_data)
            garnet.wire(garnet.global_buffer.ports[cfg_addr_port_name],
                        garnet.interconnect.ports.config[i * col_per_glb + j].config_addr)
            garnet.wire(garnet.global_buffer.ports[cfg_rd_en_port_name],
                        garnet.interconnect.ports.config[i * col_per_glb + j].read)
            garnet.wire(garnet.global_buffer.ports[cfg_wr_en_port_name],
                        garnet.interconnect.ports.config[i * col_per_glb + j].write)

    # input/output stream ports wiring
    for i in range(num_glb_tiles):
        for j in range(col_per_glb):
            x = i * col_per_glb + j
            io2glb_16_port = f"io2glb_17_X{x:02X}_Y{0:02X}"
            # FIXME
            io2glb_16_rdy_port = f"io2glb_17_X{x:02X}_Y{0:02X}_ready"
            io2glb_16_vld_port = f"io2glb_17_X{x:02X}_Y{0:02X}_valid"
            io2glb_1_port = f"io2glb_1_X{x:02X}_Y{0:02X}"
            io2glb_1_rdy_port = f"io2glb_1_X{x:02X}_Y{0:02X}_ready"
            io2glb_1_vld_port = f"io2glb_1_X{x:02X}_Y{0:02X}_valid"
            glb2io_16_port = f"glb2io_17_X{x:02X}_Y{0:02X}"
            glb2io_16_rdy_port = f"glb2io_17_X{x:02X}_Y{0:02X}_ready"
            glb2io_16_vld_port = f"glb2io_17_X{x:02X}_Y{0:02X}_valid"
            glb2io_1_port = f"glb2io_1_X{x:02X}_Y{0:02X}"
            glb2io_1_rdy_port = f"glb2io_1_X{x:02X}_Y{0:02X}_ready"
            glb2io_1_vld_port = f"glb2io_1_X{x:02X}_Y{0:02X}_valid"
            garnet.wire(garnet.global_buffer.ports[f"strm_data_f2g_{i}_{j}"],
                        garnet.interconnect.ports[io2glb_16_port][0:16])
            garnet.wire(garnet.global_buffer.ports[f"strm_data_f2g_vld_{i}_{j}"][0],
                        garnet.interconnect.ports[io2glb_16_vld_port])
            garnet.wire(garnet.global_buffer.ports[f"strm_data_f2g_rdy_{i}_{j}"][0],
                        garnet.interconnect.ports[io2glb_16_rdy_port])

            # Wire 1 to in' valid and out's ready
            garnet.wire(garnet.global_buffer.ports[f"strm_ctrl_f2g_{i}_{j}"],
                        garnet.interconnect.ports[io2glb_1_port])
            garnet.wire(Const(1),
                        garnet.interconnect.ports[io2glb_1_rdy_port])

            garnet.wire(garnet.global_buffer.ports[f"strm_data_g2f_{i}_{j}"],
                        garnet.interconnect.ports[glb2io_16_port][0:16])
            garnet.wire(Const(0),
                        garnet.interconnect.ports[glb2io_16_port][16])
            garnet.wire(garnet.global_buffer.ports[f"strm_data_g2f_vld_{i}_{j}"][0],
                        garnet.interconnect.ports[glb2io_16_vld_port])
            garnet.wire(garnet.global_buffer.ports[f"strm_data_g2f_rdy_{i}_{j}"][0],
                        garnet.interconnect.ports[glb2io_16_rdy_port])

            garnet.wire(garnet.global_buffer.ports[f"strm_ctrl_g2f_{i}_{j}"],
                        garnet.interconnect.ports[glb2io_1_port])
            # Wire 1 to in' valid and out's ready
            garnet.wire(Const(1),
                        garnet.interconnect.ports[glb2io_1_vld_port])

    # flush signal wiring
    if num_groups == 1:
        garnet.wire(garnet.global_buffer.ports.strm_data_flush_g2f,
                    garnet.interconnect.ports.flush)
    else:
        for i in range(num_groups):
            garnet.wire(garnet.global_buffer.ports[f"strm_data_flush_g2f_{i}"][0],
                        garnet.interconnect.ports.flush[i])

    return garnet


"""Useful pass to connect all wires in global controller"""


def glc_interconnect_wiring(garnet):
    # global controller <-> interconnect ports connection
    garnet.wire(garnet.global_controller.ports.reset_out,
                garnet.interconnect.ports.reset)
    garnet.wire(garnet.interconnect.ports.read_config_data,
                garnet.global_controller.ports.read_data_in)
    # stall signal wiring
    garnet.wire(garnet.global_controller.ports.cgra_stall,
                garnet.interconnect.ports.stall)

    return garnet
