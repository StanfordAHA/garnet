import magma
import mantle
import generator.generator as generator
from global_controller.global_controller_magma import GlobalController
from interconnect.interconnect_magma import Interconnect
from column.column_magma import ColumnMeso
from tile.tile_magma import Tile
from pe_core.pe_core_magma import PECore
from memory_core.memory_core_magma import MemCore
from common.side_type import SideType
from common.jtag_type import JTAGType
from generator.from_magma import FromMagma
from generator.const import Const
from tile.tile_magma import PDTileConfig
from tile.tile_magma import Tile_PD
from tile.tile_magma import Tile_PDDaisyChain
from tile.tile_magma import Tile_PDFanout


class PDCGRAConfig:
    def __init__(self):
        # Enable Low Power Design
        self.en_pd = 1
        # Power domain boundary.
        # The domain type changes from the boundary value specified
        self.pd_bndry_loc = 0
        # PS connection pattern; 0:Daisy Chain; 1:Fanout
        self.connection = 0


class CGRA_PD(generator.Generator):
    def __init__(self, width, height, PDCGRAConfig):
        super().__init__()
        self.Params = PDCGRAConfig()
        self.global_controller = GlobalController(32, 32)
        columns = []
        self.column_labels = [None] * width
        for i in range(width):
            tiles = []
            for j in range(height):
                core = MemCore(16, 1024) if (i % 2) else PECore()
                if (self.Params.en_pd == 1 and i >= self.Params.pd_bndry_loc):
                    self.column_labels[i] = "SD"
                    if (self.Params.connection == 0):
                        tiles.append(Tile_PDDaisyChain(core, PDTileConfig))
                    else:
                        tiles.append(Tile_PDFanout(core, PDTileConfig))
                else:
                    tiles.append(Tile(core))
                    self.column_labels[i] = "AON"
            columns.append(ColumnMeso(tiles))
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
        self.wire(self.global_controller.ports.stall,
                  self.interconnect.ports.stall)

        self.wire(self.interconnect.ports.read_config_data,
                  self.global_controller.ports.read_data_in)

    def name(self):
        return "PD_CGRA"
