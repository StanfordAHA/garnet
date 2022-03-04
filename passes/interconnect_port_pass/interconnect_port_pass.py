from canal.interconnect import Interconnect
from gemstone.common.configurable import ConfigurationType
from gemstone.common.mux_wrapper import MuxWrapper
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


def wire_core_flush_pass(interconnect: Interconnect):
    TBit = magma.Bits[1]
    need_global_flush = False
    for tile in interconnect.tile_circuits.values():
        cores = [tile.core] + tile.additional_cores
        # first pass to determine if we need to add the flush or not
        add_flush = False
        for core in cores:
            if "flush" in core.ports:
                add_flush = True
                break
        if not add_flush:
            # usually IO tiles or a column of tiles that doesn't have flush signals
            continue
        # need to add a global port
        need_global_flush = True

        tile.add_ports(flush=magma.In(TBit))
        for core in cores:
            if "flush" in core.ports:
                # we just add a 1-bit config reg to control the flush
                flush_mux = MuxWrapper(2, 1, name="flush_mux")
                core.add_config("flush_mux_sel", 1)
                core.wire(flush_mux.ports.S, core.registers["flush_mux_sel"].ports.O)
                # adding a top level port that needs to be directly chained at the top
                core.add_ports(flush_core=magma.In(TBit))
                # by default, we use the global flush signals
                core.wire(flush_mux.ports.I[0], core.ports.flush_core)
                core.wire(flush_mux.ports.I[1], core.ports.flush)
                # disconnect the core flush first
                core.disconnect(core.underlying.ports.flush)
                core.wire(flush_mux.ports.O, core.underlying.ports.flush)

                tile.wire(tile.ports.flush, core.ports.flush_core)

    if need_global_flush:
        interconnect.add_ports(flush=magma.In(TBit))
        # add the flush signal to global signals
        interconnect.globals = list(interconnect.globals) + [interconnect.ports.flush.qualified_name()]
        for tile in interconnect.tile_circuits.values():
            if "flush" not in tile.ports:
                # add them so that it can be wired properly later
                tile.add_ports(flush=magma.In(TBit))
                # add a floating flush to the core so that it can be processed correctly in the downstream
                if tile.core is not None:
                    tile.core.add_ports(flush=magma.In(TBit))
                    tile.wire(tile.ports.flush, tile.core.ports.flush)
                    setattr(tile, "__remove_flush_cleanup", True)
            interconnect.wire(interconnect.ports.flush, tile.ports.flush)


def cleanup_flush_ports(interconnect: Interconnect):
    # remove floating flush wire. essentially this is a hack, but it requires lots of work to properly get around
    # the optimization logic that removes unused port in Canal
    for tile in interconnect.tile_circuits.values():
        if hasattr(tile, "__remove_flush_cleanup"):
            print("has attr")
            tile.disconnect(tile.core.ports.flush)
            tile.core.remove_port("flush")
