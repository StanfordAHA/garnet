from canal.interconnect import Interconnect
import magma as m
from mantle import FF
from mantle import DefineRegister
from gemstone.generator.generator import Generator
from gemstone.common.configurable import ConfigurationType

# This pass inserts pipeline registers on the pass
# through configuration signals after every
# <interval> rows of tiles.

# Circuit Definition for set of pipeline registers
class PipelineStage(m.Generator2):
    def __init__(self, config_addr_width: int,
                 config_data_width: int):
        self.name = "ConfigPipeStage"
        self.config_addr_width = config_addr_width
        self.config_data_width = config_data_width
        config_type = ConfigurationType(config_addr_width,
                                        config_data_width)
        self.io = m.IO(
            clk=m.In(m.Clock),
            config=m.In(config_type),
            config_out=m.Out(config_type)
        )
        # Pipeline registers
        config_addr_reg = DefineRegister(config_addr_width)
        config_data_reg = DefineRegister(config_data_width)
        config_read_reg = DefineRegister(1)
        config_write_reg = DefineRegister(1)

        # Wire pipeline reg inputs
        m.wire(self.io.config.config_addr, config_addr_reg.io.I)
        m.wire(self.io.config.config_data, config_data_reg.io.I)
        m.wire(self.io.config.read, config_read_reg.io.I)
        m.wire(self.io.config.write, config_write_reg.io.I)

        # Wire pipeline reg outputs
        m.wire(config_addr_reg.O, self.io.config_out.config_addr)
        m.wire(config_data_reg.O, self.io.config_out.config_data)
        m.wire(config_read_reg.O, self.io.config_out.read)
        m.wire(config_write_reg.O, self.io.config_out.write)


# Pass to insert pipeline registers
def pipeline_config_signals(interconnect: Interconnect, interval):
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
                with interconnect.open():
                    tile_below = interconnect.tile_circuits[(x, y+1)]
                    pipe_stage = PipelineStage(config_addr_width, config_data_width)
                    # remove existing config wire
                    tile_below.io.config.unwire(tile.io.config_out)
                    # Now, wire config through the pipe stage
                    m.wire(tile.io.config_out, pipe_stage.io.config)
                    m.wire(pipe_stage.io.config_out, tile_below.io.config)
                    # Wire up pipe stage clock input to output clock
                    m.wire(tile.io.clk_out, pipe_stage.io.clk)
            
