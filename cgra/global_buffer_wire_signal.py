"""Useful pass to connect all wires in global buffer"""
import magma
from gemstone.generator.const import Const


def glb_glc_wiring(garnet):
    # global controller <-> global buffer ports connection
    garnet.wire(garnet.global_controller.ports.clk_out,
                garnet.global_buffer.ports.clk)
    garnet.wire(garnet.global_controller.ports.reset_out,
                garnet.global_buffer.ports.reset)
    garnet.wire(garnet.global_controller.ports.glb_stall,
                garnet.global_buffer.ports.glc_to_io_stall)
    garnet.wire(garnet.global_controller.ports.config,
                garnet.global_buffer.ports.cgra_config)
    garnet.wire(garnet.global_controller.ports.glb_config,
                garnet.global_buffer.ports.glb_config)
    garnet.wire(garnet.global_controller.ports.glb_read_data_in,
                garnet.global_buffer.ports.glb_config_rd_data)
    garnet.wire(garnet.global_controller.ports.glb_sram_config,
                garnet.global_buffer.ports.glb_sram_config)
    garnet.wire(garnet.global_controller.ports.glb_sram_read_data_in,
                garnet.global_buffer.ports.glb_sram_config_rd_data)
    garnet.wire(garnet.global_controller.ports.cgra_start_pulse,
                garnet.global_buffer.ports.cgra_start_pulse)
    garnet.wire(garnet.global_controller.ports.cgra_done_pulse,
                garnet.global_buffer.ports.cgra_done_pulse)
    garnet.wire(garnet.global_controller.ports.config_start_pulse,
                garnet.global_buffer.ports.config_start_pulse)
    garnet.wire(garnet.global_controller.ports.config_done_pulse,
                garnet.global_buffer.ports.config_done_pulse)

    return garnet


def glb_interconnect_wiring(garnet, width: int, num_cfg: int):
    # parallel configuration ports wiring
    for i in range(num_cfg):
        garnet.wire(garnet.global_buffer.ports.glb_to_cgra_config[i],
                    garnet.interconnect.ports.config[i])

    # input/output stream ports wiring
    for x in range(width):
        io2glb_16_port = f"io2glb_16_X{x:02X}_Y{0:02X}"
        io2glb_1_port = f"io2glb_1_X{x:02X}_Y{0:02X}"
        glb2io_16_port = f"glb2io_16_X{x:02X}_Y{0:02X}"
        glb2io_1_port = f"glb2io_1_X{x:02X}_Y{0:02X}"
        i = int(x / 4)
        if x % 4 == 0:
            garnet.wire(garnet.global_buffer.ports.io_to_cgra_rd_data[i],
                        garnet.interconnect.ports[glb2io_16_port])
            garnet.wire(garnet.global_buffer.ports.io_to_cgra_rd_data_valid[i],
                        garnet.interconnect.ports[glb2io_1_port][0])
            garnet.wire(garnet.global_buffer.ports.cgra_to_io_rd_en[i],
                        garnet.interconnect.ports[io2glb_1_port][0])
        elif x % 4 == 1:
            garnet.wire(garnet.global_buffer.ports.cgra_to_io_wr_data[i],
                        garnet.interconnect.ports[io2glb_16_port])
            garnet.wire(garnet.global_buffer.ports.cgra_to_io_wr_en[i],
                        garnet.interconnect.ports[io2glb_1_port][0])
            garnet.wire(garnet.interconnect.ports[glb2io_16_port],
                        Const(magma.bits(0, 16)))
            garnet.wire(garnet.interconnect.ports[glb2io_1_port],
                        Const(magma.bits(0, 1)))
        elif x % 4 == 2:
            garnet.wire(garnet.global_buffer.ports.cgra_to_io_addr_high[i],
                        garnet.interconnect.ports[io2glb_16_port])
            garnet.wire(garnet.interconnect.ports[glb2io_16_port],
                        Const(magma.bits(0, 16)))
            garnet.wire(garnet.interconnect.ports[glb2io_1_port],
                        Const(magma.bits(0, 1)))
        else:
            garnet.wire(garnet.global_buffer.ports.cgra_to_io_addr_low[i],
                        garnet.interconnect.ports[io2glb_16_port])
            garnet.wire(garnet.interconnect.ports[glb2io_16_port],
                        Const(magma.bits(0, 16)))
            if x != garnet.interconnect.x_max:
                garnet.wire(garnet.interconnect.ports[glb2io_1_port],
                            Const(magma.bits(0, 1)))

    return garnet
