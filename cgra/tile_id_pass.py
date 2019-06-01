from gemstone.common.transform import replace, Generator, FromMagma
from io_core.io_core_magma import IOCore
from canal.interconnect import Interconnect
from gemstone.common.configurable import Configurable, ConfigurationType
import magma
import mantle
from gemstone.generator.const import Const


def add_hi_lo_outputs(interconnect: Interconnect):
    tile_id_width = interconnect.tile_id_width
    tie_hi_width = (tile_id_width // 2) + 1
    if (tile_id_width % 2) == 0 :
        tie_lo_width = tile_id_width // 2
    else:
        tie_lo_width = (tile_id_width // 2) + 1
    for (x, y) in interconnect.tile_circuits:
        tile = interconnect.tile_circuits[(x, y)]
        tile_core = tile.core
        if isinstance(tile_core, IOCore) or tile_core is None:
            continue
        tile.add_ports(
            hi=magma.Out(magma.Bits[tie_hi_width]),
            lo=magma.Out(magma.Bits[tie_lo_width])
        )
        tile.wire(tile.ports.hi, Const((2 ** tie_hi_width) - 1))
        tile.wire(tile.ports.lo, Const(0))
