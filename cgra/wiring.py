import magma as m
from gemstone.common.configurable import ConfigurationType


"""Useful pass to connect all wires in global buffer"""
def glb_glc_wiring(garnet):
    # global controller <-> global buffer ports connection
    m.wire(garnet.global_controller.io.reset_out,
           garnet.global_buffer.io.reset)
    m.wire(garnet.global_controller.io.glb_stall,
           garnet.global_buffer.io.stall)
    m.wire(garnet.global_controller.io.cgra_config,
           garnet.global_buffer.io.cgra_cfg_jtag)
    m.wire(garnet.global_controller.io.glb_cfg,
           garnet.global_buffer.io.glb_cfg)
    m.wire(garnet.global_controller.io.sram_cfg,
           garnet.global_buffer.io.sram_cfg)
    m.wire(garnet.global_controller.io.strm_start_pulse,
           garnet.global_buffer.io.strm_start_pulse)
    m.wire(garnet.global_controller.io.pc_start_pulse,
           garnet.global_buffer.io.pc_start_pulse)
    m.wire(garnet.global_controller.io.strm_f2g_interrupt_pulse,
           garnet.global_buffer.io.strm_f2g_interrupt_pulse)
    m.wire(garnet.global_controller.io.strm_g2f_interrupt_pulse,
           garnet.global_buffer.io.strm_g2f_interrupt_pulse)
    m.wire(garnet.global_controller.io.pcfg_g2f_interrupt_pulse,
           garnet.global_buffer.io.pcfg_g2f_interrupt_pulse)
    m.wire(garnet.global_controller.io.soft_reset,
           garnet.global_buffer.io.cgra_soft_reset)
    m.wire(garnet.global_controller.io.cgra_stall,
           garnet.global_buffer.io.cgra_stall_in)

    return garnet


def glb_interconnect_wiring(garnet):

    # width of garnet
    width = garnet.width

    # parallel configuration ports wiring
    for i in range(width):
        m.wire(garnet.global_buffer.io.cgra_cfg_g2f[i],
               garnet.interconnect.io.config[i])

    # stall signal wiring
    for i in range(width):
        m.wire(garnet.global_buffer.io.cgra_stall[i],
               garnet.interconnect.io.stall[i])

    # input/output stream ports wiring
    for x in range(width):
        io2glb_16_port = f"io2glb_16_X{x:02X}_Y{0:02X}"
        io2glb_1_port = f"io2glb_1_X{x:02X}_Y{0:02X}"
        glb2io_16_port = f"glb2io_16_X{x:02X}_Y{0:02X}"
        glb2io_1_port = f"glb2io_1_X{x:02X}_Y{0:02X}"
        m.wire(garnet.global_buffer.io.stream_data_f2g[x],
               garnet.interconnect.io[io2glb_16_port])
        m.wire(garnet.global_buffer.io.stream_data_valid_f2g[x],
               garnet.interconnect.io[io2glb_1_port])
        m.wire(garnet.global_buffer.io.stream_data_g2f[x],
               garnet.interconnect.io[glb2io_16_port])
        m.wire(garnet.global_buffer.io.stream_data_valid_g2f[x],
                    garnet.interconnect.io[glb2io_1_port])

    return garnet

"""Useful pass to connect all wires in global controller"""
def glc_interconnect_wiring(garnet):
    # global controller <-> interconnect ports connection
    m.wire(garnet.global_controller.io.reset_out,
           garnet.interconnect.io.reset)
    m.wire(garnet.interconnect.io.read_config_data,
           garnet.global_controller.io.read_data_in)

    return garnet
