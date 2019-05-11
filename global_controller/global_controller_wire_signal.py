"""Useful pass to connect all wires in global controller"""
import magma

def glc_interconnect_wiring(garnet):
    # global controller <-> interconnect ports connection
    garnet.wire(garnet.global_controller.ports.clk_out,
                garnet.interconnect.ports.clk)
    garnet.wire(garnet.global_controller.ports.reset_out,
                garnet.interconnect.ports.reset)
    garnet.wire(garnet.global_controller.ports.stall,
                garnet.interconnect.ports.stall)

    # cgra_soft_reset signal wiring
    cgra_soft_reset_port = f"glb2io_1_X{garnet.interconnect.x_max:02X}_Y{0:02X}"
    garnet.wire(garnet.global_controller.ports.cgra_soft_reset,
                garnet.interconnect.ports[cgra_soft_reset_port][0])
    garnet.wire(garnet.interconnect.ports.read_config_data,
                garnet.global_controller.ports.read_data_in)

    return garnet
