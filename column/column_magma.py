import magma
import mantle
import gemstone.generator.generator as generator
from abc import abstractmethod
from gemstone.common.side_type import SideType
from gemstone.common.configurable import ConfigurationType
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.const import Const


class ColumnBase(gemstone.generator.Generator):
    def __init__(self, tiles):
        super().__init__()

        self.tiles = tiles
        self.height = len(tiles)

        self.add_ports(
            north=SideType(5, (1, 16)),
            south=SideType(5, (1, 16)),
            west=magma.Array(self.height, SideType(5, (1, 16))),
            east=magma.Array(self.height, SideType(5, (1, 16))),
            config=magma.In(ConfigurationType(32, 32)),
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
            read_config_data=magma.Out(magma.Bits(32)),
            column_num=magma.In(magma.Bits(8)),
            # TODO (alexcarsello): make number of stall domains a param
            stall=magma.In(magma.Bits(4))
        )

        self.wire(self.ports.north, self.tiles[0].ports.north)
        self.wire(self.ports.south, self.tiles[-1].ports.south)
        for i, tile in enumerate(self.tiles):
            self.wire(self.ports.west[i], tile.ports.west)
            self.wire(self.ports.east[i], tile.ports.east)
            # Wire upper 8 bits of tile ID to row number
            self.wire(tile.ports.tile_id[8:16], Const(magma.bits(i, 8)))
            # Wire lower 8 bits of tile ID to col number
            self.wire(tile.ports.tile_id[0:8], self.ports.column_num)
        for i in range(1, self.height):
            t0 = self.tiles[i - 1]
            t1 = self.tiles[i]
            self.wire(t1.ports.north.O, t0.ports.south.I)
            self.wire(t0.ports.south.O, t1.ports.north.I)

        # Call abstract functions
        # distribute global inputs to all tiles in column
        self.wire_global_signals()
        # OR-combine each tile's read_data to form column read_data
        self.combine_read_data_outputs()

    def name(self):
        return "Column_" + "_".join([t.name() for t in self.tiles])

    def globals(self):
        return (self.ports.clk, self.ports.config, self.ports.reset,
                self.ports.stall)

    @abstractmethod
    def wire_global_signals(self):
        pass

    @abstractmethod
    def combine_read_data_outputs(self):
        pass


# Column that uses "river routing" for global signal distribution
class ColumnMeso(ColumnBase):
    def wire_global_signals(self):
        # wire global inputs to first tile in column
        for signal in self.globals():
            self.wire(signal, self.tiles[0].ports[signal.qualified_name()])
        for i, tile in enumerate(self.tiles):
            for global_signal in self.globals():
                input_name = global_signal.qualified_name()
                output_port = tile.pass_signal_through(input_name)
                if i < len(self.tiles) - 1:
                    # Connect output port to input port of next tile
                    self.wire(output_port, self.tiles[i + 1].ports[input_name])

    def combine_read_data_outputs(self):
        # Call tile function that adds input for read_data,
        # along with OR gate to reduce input read_data with
        # that tile's read_data
        for tile in self.tiles:
            tile.read_data_reduction()
        # Connect 0 to first tile's read_data input
        self.wire(self.tiles[0].ports.read_config_data_in,
                  Const(magma.bits(0, 32)))
        # connect each tile's read_data output to next tile's
        # read_data input
        for i, tile in enumerate(self.tiles[:-1]):
            self.wire(tile.ports.read_config_data,
                      self.tiles[i + 1].ports.read_config_data_in)
        # Connect the last tile's read_data output to the column's
        # read_data output
        self.wire(self.tiles[-1].ports.read_config_data,
                  self.ports.read_config_data)


# Column that simply fans out all global signals to tiles
class ColumnFanout(ColumnBase):
    def wire_global_signals(self):
        for global_signal in self.globals():
            signal_name = global_signal.qualified_name()
            for tile in self.tiles:
                self.wire(global_signal, tile.ports[signal_name])

    def combine_read_data_outputs(self):
        self.read_data_OR = FromMagma(mantle.DefineOr(self.height, 32))
        self.wire(self.read_data_OR.ports.O, self.ports.read_config_data)
        for i, tile in enumerate(self.tiles):
            self.wire(tile.ports.read_config_data,
                      self.read_data_OR.ports[f"I{i}"])
