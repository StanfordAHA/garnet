import magma
from gemstone.common.configurable import ConfigurationType


"""Useful pass to connect all wires in global buffer"""
def glb_glc_wiring(garnet):
    # global controller <-> global buffer ports connection
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
    garnet.wire(garnet.global_controller.ports.strm_f2g_interrupt_pulse,
                garnet.global_buffer.ports.strm_f2g_interrupt_pulse)
    garnet.wire(garnet.global_controller.ports.strm_g2f_interrupt_pulse,
                garnet.global_buffer.ports.strm_g2f_interrupt_pulse)
    garnet.wire(garnet.global_controller.ports.pcfg_g2f_interrupt_pulse,
                garnet.global_buffer.ports.pcfg_g2f_interrupt_pulse)
    garnet.wire(garnet.global_controller.ports.soft_reset,
                garnet.global_buffer.ports.cgra_soft_reset)
    garnet.wire(garnet.global_controller.ports.stall[0],
                garnet.global_buffer.ports.cgra_stall_in)

    return garnet


def glb_interconnect_wiring(garnet):

    # width of garnet
    width = garnet.width
    start_idx = garnet.interconnect.x_min

    # Add parallel configuration ports to interconnect
    # interconnect must have config port
    assert "config" in garnet.interconnect.ports

    garnet.interconnect.remove_port("config")
    config_addr_width = garnet.config_addr_width
    config_data_width = garnet.config_data_width
    garnet.interconnect.add_port(
            "config",
            magma.In(magma.Array[width,
                                 ConfigurationType(config_addr_width,
                                                   config_data_width)]))

    # looping through on a per-column bases
    for x_coor in range(start_idx, start_idx + width):
        column = garnet.interconnect.get_column(x_coor)
        # skip tiles with no config
        column = [entry for entry in column if "config" in entry.ports]
        # wire configuration ports to first tile in column
        garnet.interconnect.wire(garnet.interconnect.ports.config[x_coor],
                                 column[0].ports.config)

    # parallel configuration ports wiring
    for i in range(width):
        garnet.wire(garnet.global_buffer.ports.cgra_cfg_g2f[i],
                    garnet.interconnect.ports.config[i])

    # Add cgra stall
    assert "stall" in garnet.interconnect.ports
    stall_signal_width = garnet.interconnect.stall_signal_width

    garnet.interconnect.remove_port("stall")
    garnet.interconnect.add_port(
            "stall",
            magma.In(magma.Array[width, magma.Bits[stall_signal_width]]))

    # looping through on a per-column bases
    for x_coor in range(start_idx, start_idx + width):
        column = garnet.interconnect.get_column(x_coor)
        # skip tiles with no stall
        column = [entry for entry in column if "stall" in entry.ports]
        # wire configuration ports to first tile in column
        garnet.interconnect.wire(garnet.interconnect.ports.stall[x_coor],
                                 column[0].ports.stall)
    # Currently stall signal is 1 bit
    assert garnet.interconnect.stall_signal_width == 1
    for i in range(width):
        garnet.wire(garnet.global_buffer.ports.cgra_stall[i],
                    garnet.interconnect.ports.stall[i][0])

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
    garnet.wire(garnet.global_controller.ports.reset_out,
                garnet.interconnect.ports.reset)
    garnet.wire(garnet.interconnect.ports.read_config_data,
                garnet.global_controller.ports.read_data_in)

    return garnet
