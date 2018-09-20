import magma
import mantle
import generator.generator as generator
from global_controller.global_controller_magma import GlobalController
from interconnect.interconnect_magma import Interconnect
from column.column_magma import Column
from tile.tile_magma import Tile
from pe_core.pe_core_magma import PECore
from memory_core.memory_core_magma import MemCore
from common.side_type import SideType
from common.jtag_type import JTAGType
from generator.from_magma import FromMagma
from generator.const import Const


class CGRA(generator.Generator):
    def __init__(self, width, height):
        super().__init__()

        self.global_controller = GlobalController(32, 32)
        columns = []
        for i in range(width):
            tiles = []
            for j in range(height):
                core = MemCore(16, 1024) if (i % 2) else PECore()
                tiles.append(Tile(core))
            columns.append(Column(tiles))
        self.interconnect = Interconnect(columns)

        side_type = self.interconnect.side_type
        self.add_ports(
            north=magma.Array(width, side_type),
            south=magma.Array(width, side_type),
            west=magma.Array(height, side_type),
            east=magma.Array(height, side_type),
            jtag=JTAGType,
            clk_in=magma.In(magma.Clock),
            reset_in=magma.In(magma.AsyncReset),
        )

        self.wire(self.ports.north, self.interconnect.ports.north)
        self.wire(self.ports.south, self.interconnect.ports.south)
        self.wire(self.ports.west, self.interconnect.ports.west)
        self.wire(self.ports.east, self.interconnect.ports.east)

        self.wire(self.ports.jtag, self.global_controller.ports.jtag)
        self.wire(self.ports.clk_in, self.global_controller.ports.clk_in)
        self.wire(self.ports.reset_in, self.global_controller.ports.reset_in)

        self.wire(self.global_controller.ports.config,
                  self.interconnect.ports.config)
        self.wire(self.global_controller.ports.clk_out,
                  self.interconnect.ports.clk)
        self.wire(self.global_controller.ports.reset_out,
                  self.interconnect.ports.reset)

        self.wire(self.interconnect.ports.read_config_data,
                  self.global_controller.ports.read_data_in)

    def name(self):
        return "CGRA"
