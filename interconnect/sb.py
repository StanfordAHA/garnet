from .muxblock import SwitchBoxMux
from .graph import Tile as GTile, Switch as GSwitch, SwitchBoxSide, SwitchBoxIO
from generator import generator
from typing import List
from common.mux_wrapper import MuxWrapper


class SB(generator):
    def __init__(self, tile: GTile):
        super().__init__()
        self.x = tile.x
        self.y = tile.y
        self.switch = tile.switchbox

        num_track = tile.switchbox.num_track
        num_ios = GSwitch.NUM_IOS
        num_sides = GSwitch.NUM_SIDES

        self.sb_muxs: List[List[List[SwitchBoxMux]]] = [[[None] * num_track] *
                                                        num_ios] * num_sides
        self.muxs: List[MuxWrapper] = []
        for side in range(GSwitch.NUM_SIDES):
            for io in range(num_ios):
                for track in range(num_track):
                    sb = tile.switchbox[(SwitchBoxSide(side),
                                         track,
                                         SwitchBoxIO(io))]
                    self.sb_muxs.append(SwitchBoxMux(sb))

    def name(self):
        return SwitchBoxMux.create_name(str(self.switch))

    def realize(self):
        for sides in self.sb_muxs:
            for io in sides:
                for sb in io:
                    self.muxs.append(sb.create_mux())
