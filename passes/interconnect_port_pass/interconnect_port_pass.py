from canal.interconnect import Interconnect
from gemstone.common.configurable import ConfigurationType
from gemstone.common.mux_wrapper import MuxWrapper
from gemstone.common.transform import FromMagma
from gemstone.common.transform import pipeline_wire
import magma
import mantle
from canal.util import IOSide
from typing import Tuple, Dict, List


def config_port_pass(interconnect: Interconnect, pipeline=False):
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
        in_port = interconnect.ports.config[x_coor]
        out_port = column[0].ports.config
        if pipeline==True:
            pipeline_wire(interconnect,
                          in_port,
                          out_port,
                          clk=interconnect.ports.clk)
        else:
            interconnect.wire(in_port, out_port)


def stall_port_pass(interconnect: Interconnect, port_name: str, port_width=1, col_offset=1, pipeline=False, io_sides: List[IOSide] = [IOSide.None_]):
    # x coordinate of garnet

    x_min = interconnect.x_min
    x_max = interconnect.x_max

    width = x_max - x_min + 1


    assert port_name in interconnect.ports
    # MO: Got rid of this b/c it will not be true if I/O tiles are on West side, resulting in odd width
    #assert width % col_offset == 0 
    num_ports = width // col_offset

    interconnect.disconnect(port_name)
    interconnect.remove_port(port_name)
    interconnect.add_port(port_name,
                          magma.In(magma.Bits[num_ports * port_width]))
    
    # looping through columns and wire port every col_offset
    for i, x_coor in enumerate(range(x_min, x_min + width)):
        column = interconnect.get_column(x_coor)
        # skip tiles with no port_name
        column = [entry for entry in column if port_name in entry.ports]
        # wire configuration ports to first tile in column every col_offset
        # Shift everything right by 1 if have West IO tiles (only applies to flush)

        # MO: hack
        dividend_index = 0
        #dividend_index = max(0, i-1) if IOSide.West in io_sides else i

        in_port = interconnect.ports[port_name][(dividend_index // col_offset) 
                  * port_width:((dividend_index // col_offset) + 1) * port_width]
        out_port = column[0].ports[port_name]
        if pipeline==True:
            pipeline_wire(interconnect,
                          in_port,
                          out_port,
                          clk=interconnect.ports.clk)
        else:
            interconnect.wire(in_port, out_port)


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

        try:
            tile.add_ports(flush=magma.In(TBit))
        except:
            pass
        for core in cores:
            if "flush" in core.ports:
                # adding a top level port that needs to be directly chained at the top
                core.add_ports(flush_core=magma.In(TBit))
                tile.wire(tile.ports.flush, core.ports.flush_core)
                # disconnect the core flush first
                core.disconnect(core.underlying.ports.flush)
                if core.name() == "PondCore":
                    # for pond, OR the flush signals instead of Muxing
                    flush_or = FromMagma(mantle.DefineOr(2, 1))
                    core.wire(flush_or.ports.I0, core.ports.flush_core)
                    core.wire(flush_or.ports.I1, core.ports.flush)
                    core.wire(flush_or.ports.O, core.underlying.ports.flush)
                else:
                    # we just add a 1-bit config reg to control the flush
                    flush_mux = MuxWrapper(2, 1, name="flush_mux")
                    core.add_config("flush_mux_sel", 1)
                    core.wire(flush_mux.ports.S, core.registers["flush_mux_sel"].ports.O)
                    # by default, we use the global flush signals
                    core.wire(flush_mux.ports.I[0], core.ports.flush_core)
                    core.wire(flush_mux.ports.I[1], core.ports.flush)
                    core.wire(flush_mux.ports.O, core.underlying.ports.flush)

    if need_global_flush:
        interconnect.add_ports(flush=magma.In(TBit))
        # add the flush signal to global signals
        interconnect.globals = list(interconnect.globals) + [interconnect.ports.flush.qualified_name()]
        for tile in interconnect.tile_circuits.values():
            if "flush" not in tile.ports:
                continue
            interconnect.wire(interconnect.ports.flush, tile.ports.flush)
