from canal.interconnect import Interconnect
from gemstone.common.configurable import ConfigurationType
import magma

def config_port_pass(interconnect: Interconnect):
    # x coordinate of garnet
    x_min = interconnect.x_min
    x_max = interconnect.x_max
    width = x_max - x_min + 1

    # Add parallel configuration ports to interconnect
    # interconnect must have config port
    assert "config" in interconnect.ports

    interconnect.remove_port("config")
    config_data_width = interconnect.config_data_width
    # config_addr_width is same as config_data_width
    interconnect.add_port(
            "config",
            magma.In(magma.Array[width,
                                 ConfigurationType(config_data_width,
                                                   config_data_width)]))

    # looping through on a per-column bases
    for x_coor in range(x_min, x_min + width):
        column = interconnect.get_column(x_coor)
        # skip tiles with no config
        column = [entry for entry in column if "config" in entry.ports]
        # wire configuration ports to first tile in column
        interconnect.wire(interconnect.ports.config[x_coor],
                          column[0].ports.config)


def stall_port_pass(interconnect: Interconnect):
    # x coordinate of garnet
    x_min = interconnect.x_min
    x_max = interconnect.x_max
    width = x_max - x_min + 1

    # Add cgra stall
    assert "stall" in interconnect.ports
    stall_signal_width = interconnect.stall_signal_width

    # Currently stall signal is 1 bit
    assert stall_signal_width == 1

    interconnect.remove_port("stall")
    interconnect.add_port("stall",
                          magma.In(magma.Bits[width * interconnect.stall_signal_width]))

    # looping through on a per-column bases
    for x_coor in range(x_min, x_min + width):
        column = interconnect.get_column(x_coor)
        # skip tiles with no stall
        column = [entry for entry in column if "stall" in entry.ports]
        # wire configuration ports to first tile in column
        interconnect.wire(interconnect.ports.stall[x_coor],
                          column[0].ports.stall[0])
