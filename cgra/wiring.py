"""Useful pass to connect all wires in global buffer"""
def glb_glc_wiring(garnet):
    # global controller <-> global buffer ports connection
    garnet.wire(garnet.global_controller.ports.clk_out,
                garnet.global_buffer.ports.clk)
    garnet.wire(garnet.global_controller.ports.reset_out,
                garnet.global_buffer.ports.reset)
    garnet.wire(garnet.global_controller.ports.glb_stall,
                garnet.global_buffer.ports.stall)
    garnet.wire(garnet.global_controller.ports.cgra_config,
                garnet.global_buffer.ports.cgra_cfg_jtag)
    garnet.wire(garnet.global_controller.ports.glb_cfg,
                garnet.global_buffer.ports.glb_cfg)
    garnet.wire(garnet.global_controller.ports.sram_cfg,
                garnet.global_buffer.ports.sram_cfg)
    garnet.wire(garnet.global_controller.ports.strm_start_pulse,
                garnet.global_buffer.ports.strm_start_pulse)
    garnet.wire(garnet.global_controller.ports.pc_start_pulse,
                garnet.global_buffer.ports.pc_start_pulse)
    garnet.wire(garnet.global_controller.ports.interrupt_pulse,
                garnet.global_buffer.ports.interrupt_pulse)

    return garnet


def glb_interconnect_wiring(garnet):
    # width of garnet
    width = garnet.width

    # parallel configuration ports wiring
    for i in range(width):
        garnet.wire(garnet.global_buffer.ports.cgra_cfg_g2f[i],
                    garnet.interconnect.ports.config[i])

    # input/output stream ports wiring
    for x in range(width):
        io2glb_16_port = f"io2glb_16_X{x:02X}_Y{0:02X}"
        io2glb_1_port = f"io2glb_1_X{x:02X}_Y{0:02X}"
        glb2io_16_port = f"glb2io_16_X{x:02X}_Y{0:02X}"
        glb2io_1_port = f"glb2io_1_X{x:02X}_Y{0:02X}"
        garnet.wire(garnet.global_buffer.ports.stream_data_f2g[x],
                    garnet.interconnect.ports[io2glb_16_port])
        garnet.wire(garnet.global_buffer.ports.stream_data_valid_f2g[x],
                    garnet.interconnect.ports[io2glb_1_port])
        garnet.wire(garnet.global_buffer.ports.stream_data_g2f[x],
                    garnet.interconnect.ports[glb2io_16_port])
        garnet.wire(garnet.global_buffer.ports.stream_data_valid_g2f[x],
                    garnet.interconnect.ports[glb2io_1_port])

    return garnet

"""Useful pass to connect all wires in global controller"""
def glc_interconnect_wiring(garnet):
    # global controller <-> interconnect ports connection
    garnet.wire(garnet.global_controller.ports.clk_out,
                garnet.interconnect.ports.clk)
    garnet.wire(garnet.global_controller.ports.reset_out,
                garnet.interconnect.ports.reset)
    garnet.wire(garnet.global_controller.ports.stall,
                garnet.interconnect.ports.stall)

    # soft_reset signal wiring
    cgra_soft_reset_port = f"glb2io_1_X{garnet.interconnect.x_max:02X}_Y{0:02X}"
    garnet.wire(garnet.global_controller.ports.soft_reset,
                garnet.interconnect.ports[cgra_soft_reset_port][0])
    garnet.wire(garnet.interconnect.ports.read_config_data,
                garnet.global_controller.ports.read_data_in)

    return garnet
