"""Useful pass on interconnect that doesn't deal with the routing network"""
import magma
import mantle
from common.transform import pass_signal_through, or_reduction
from generator.const import Const
from generator.from_magma import FromMagma
from .interconnect import Interconnect


def apply_global_fanout_wiring(interconnect: Interconnect):
    # straight-forward fanout for global signals
    global_ports = interconnect.globals
    interconnect_read_data_or = \
        FromMagma(mantle.DefineOr(interconnect.x_max - interconnect.x_min + 1,
                                  interconnect.config_data_width))
    # this is connected on a per-column bases
    for x in range(interconnect.x_min, interconnect.x_max + 1):
        column = interconnect.get_column(x)
        # handle the read config
        column_read_data_or = \
            FromMagma(mantle.DefineOr(len(column),
                      interconnect.config_data_width))
        for idx, tile in enumerate(column):
            for signal_name in global_ports:
                interconnect.wire(interconnect.ports[signal_name],
                                  tile.ports[signal_name])
            # connect the tile to the column read_data inputs
            interconnect.wire(column_read_data_or.ports[f"I{idx}"],
                              tile.ports.read_config_data)

        # wire it to the interconnect_read_data_or
        idx = x - interconnect.x_min
        interconnect.wire(interconnect_read_data_or.ports[f"I{idx}"],
                          column_read_data_or.ports.O)

    # wiring the read_config_data
    interconnect.wire(interconnect.ports.read_config_data,
                      interconnect_read_data_or.ports.O)

    return interconnect_read_data_or


def apply_global_meso_wiring(interconnect: Interconnect):
    # "river routing" for global signal
    global_ports = interconnect.globals
    interconnect_read_data_or = \
        FromMagma(mantle.DefineOr(interconnect.x_max - interconnect.x_min + 1,
                                  interconnect.config_data_width))

    # looping through on a per-column bases
    for x in range(interconnect.x_min, interconnect.x_max + 1):
        column = interconnect.get_column(x)
        # wire global inputs to first tile in column
        for signal in global_ports:
            interconnect.wire(interconnect.ports[signal],
                              column[0].ports[signal])
        # first pass to make signals pass through
        # pre_ports keep track of ports created by pass_signal_through
        pre_ports = {}
        for signal in global_ports:
            pre_ports[signal] = []
            for tile in column:
                # use the transform pass
                pre_port = pass_signal_through(tile, signal)
                pre_ports[signal].append(pre_port)
        # second pass to wire them up
        for i in range(len(column) - 1):
            next_tile = column[i + 1]
            for signal in global_ports:
                pre_port = pre_ports[signal][i]
                interconnect.wire(pre_port,
                                  next_tile.ports[signal])

        # read_config_data
        # Call tile function that adds input for read_data,
        # along with OR gate to reduce input read_data with
        # that tile's read_data
        # ports_in keep track of new ports created by or_reduction
        ports_in = []
        for tile in column:
            port_in = or_reduction(tile, "read_data_mux", "read_config_data",
                                   interconnect.config_data_width)
            ports_in.append(port_in)

        # Connect 0 to first tile's read_data input
        interconnect.wire(ports_in[0],
                          Const(magma.bits(0, interconnect.config_data_width)))

        # connect each tile's read_data output to next tile's
        # read_data input
        for i, tile in enumerate(column[:-1]):
            interconnect.wire(tile.ports.read_config_data,
                              ports_in[i + 1])
        # Connect the last tile's read_data output to the global OR
        idx = x - interconnect.x_min
        interconnect.wire(interconnect_read_data_or.ports[f"I{idx}"],
                          column[-1].ports.read_config_data)

    # wiring the read_config_data
    interconnect.wire(interconnect.ports.read_config_data,
                      interconnect_read_data_or.ports.O)

    return interconnect_read_data_or
