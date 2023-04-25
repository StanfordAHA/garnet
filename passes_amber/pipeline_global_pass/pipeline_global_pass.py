from canal.interconnect import Interconnect
import magma
from mantle import FF
from mantle import DefineRegister
from gemstone.generator.generator import Generator
from gemstone.generator.from_magma import FromMagma
from gemstone.common.configurable import ConfigurationType

# This pass inserts pipeline registers on the pass
# through configuration signals after every
# <interval> rows of tiles.

# Circuit Definition for set of pipeline registers
class PipelineStage(Generator):
    def __init__(self, config_addr_width: int,
                 config_data_width: int,
                 add_flush: bool):
        super().__init__()
        self.config_addr_width = config_addr_width
        self.config_data_width = config_data_width
        config_type = ConfigurationType(config_addr_width,
                                        config_data_width)
        self.add_ports(
            clk=magma.In(magma.Clock),
            config=magma.In(config_type),
            config_out=magma.Out(config_type)
        )
        if add_flush:
            self.add_ports(flush=magma.In(magma.Bits[1]),
                           flush_out=magma.Out(magma.Bits[1]))

        # Pipeline registers
        config_addr_reg = FromMagma(DefineRegister(config_addr_width))
        config_data_reg = FromMagma(DefineRegister(config_data_width))
        config_read_reg = FromMagma(DefineRegister(1))
        config_write_reg = FromMagma(DefineRegister(1))

        # Wire pipeline reg inputs
        self.wire(self.ports.config.config_addr, config_addr_reg.ports.I)
        self.wire(self.ports.config.config_data, config_data_reg.ports.I)
        self.wire(self.ports.config.read, config_read_reg.ports.I)
        self.wire(self.ports.config.write, config_write_reg.ports.I)

        # Wire pipeline reg outputs
        self.wire(config_addr_reg.ports.O, self.ports.config_out.config_addr)
        self.wire(config_data_reg.ports.O, self.ports.config_out.config_data)
        self.wire(config_read_reg.ports.O, self.ports.config_out.read)
        self.wire(config_write_reg.ports.O, self.ports.config_out.write)

        if add_flush:
            flush_reg = FromMagma(DefineRegister(1))
            self.wire(self.ports.flush, flush_reg.ports.I)
            self.wire(flush_reg.ports.O, self.ports.flush_out)

    def name(self):
        return "GlobalPipeStage"

# Pass to insert pipeline registers
def pipeline_global_signals(interconnect: Interconnect, interval):
    # Right now in canal, the width of config_addr and config_data
    # are hard-coded to be the same. This should be changed.
    config_data_width = interconnect.config_data_width
    config_addr_width = config_data_width
    for (x, y) in interconnect.tile_circuits:
        tile = interconnect.tile_circuits[(x, y)]
        tile_core = tile.core
        # We only want to do this on PE and memory tiles
        if tile_core is None or "config" not in tile_core.ports or y == 0:
            continue
        else:
            if interval != 0 and y % interval == 0 and ((x, y+1) in interconnect.tile_circuits):
                tile_below = interconnect.tile_circuits[(x, y+1)]
                has_flush = "flush" in tile_below.ports
                pipe_stage = PipelineStage(config_addr_width, config_data_width, has_flush)
                # remove existing config wire
                interconnect.remove_wire(tile.ports.config_out, tile_below.ports.config)
                # Now, wire config through the pipe stage
                interconnect.wire(tile.ports.config_out, pipe_stage.ports.config)
                interconnect.wire(pipe_stage.ports.config_out, tile_below.ports.config)
                # Wire up pipe stage clock input to output clock
                interconnect.wire(tile.ports.clk_out, pipe_stage.ports.clk)

                # if it has flush
                if has_flush:
                    interconnect.remove_wire(tile.ports.flush_out, tile_below.ports.flush)
                    interconnect.wire(tile.ports.flush_out, pipe_stage.ports.flush)
                    interconnect.wire(pipe_stage.ports.flush_out, tile_below.ports.flush)
            
