from .circuit import SwitchBoxMux, Circuit
from .cyclone import SwitchBox as GSwitch, SwitchBoxSide
from .cyclone import SwitchBoxIO
from generator import generator
from typing import List, Tuple, Union
import enum


class SB(generator.Generator):
    def __init__(self, switchbox: GSwitch):
        super().__init__()
        self.x = switchbox.x
        self.y = switchbox.y
        self.num_track = switchbox.num_track
        self.track_width = switchbox.width

        self.g_switch = switchbox

        num_track = switchbox.num_track
        num_ios = GSwitch.NUM_IOS
        num_sides = GSwitch.NUM_SIDES

        # pre-allocating space
        self.sb_muxs: List[List[List[SwitchBoxMux]]] = \
            [[[None for _ in range(num_track)]for _ in range(num_ios)]
             for _ in range(num_sides)]

        self.muxs: List[Circuit] = []
        for side in range(GSwitch.NUM_SIDES):
            for io in range(num_ios):
                for track in range(num_track):
                    sb = switchbox[(SwitchBoxSide(side),
                                    track,
                                    SwitchBoxIO(io))]
                    self.sb_muxs[side][io][track] = SwitchBoxMux(sb)

    def __getitem__(self, item: Union[int, SwitchBoxSide]):
        if isinstance(item, SwitchBoxSide):
            return self.sb_muxs[item.value]
        else:
            return self.sb_muxs[item]

    def __contains__(self, item: Circuit):
        if isinstance(item, SwitchBoxMux):
            side = item.node.side
            io = item.node.io
            track = item.node.track
            if self.num_track > track:
                return self.sb_muxs[side.value][io.value][track] == item
        else:
            return False

    def name(self):
        return SwitchBoxMux.__create_name(str(self.g_switch))

    def realize(self):
        for sides in self.sb_muxs:
            for io in sides:
                for sb in io:
                    sb_mux: Circuit = sb.realize()
                    self.muxs.append(sb_mux)
        return self.muxs

    def remove_side_sbs(self, side: SwitchBoxSide, io: SwitchBoxIO):
        # clear the muxs
        self.sb_muxs[side.value][io.value].clear()
        self.g_switch.remove_side_sbs(side, io)


@enum.unique
class SwitchBoxType(enum.Enum):
    Disjoint = enum.auto()
    Wilton = enum.auto()
    Imran = enum.auto()








# subclassing so that user doesn't have to deal with the graph node
class DisjointSB(SB):
    def __init__(self, x: int, y: int, bit_width: int,
                 num_tracks: int):
        internal_wires = SwitchBoxHelper.get_disjoint_sb_wires(num_tracks)
        switchbox = GSwitch(x, y, num_tracks, bit_width, internal_wires)
        super().__init__(switchbox)


class WiltonSB(SB):
    def __init__(self, x: int, y: int, bit_width: int,
                 num_tracks: int):
        internal_wires = SwitchBoxHelper.get_wilton_sb_wires(num_tracks)
        switchbox = GSwitch(x, y, num_tracks, bit_width, internal_wires)
        super().__init__(switchbox)


class ImranSB(SB):
    def __init__(self, x: int, y: int, bit_width: int,
                 num_tracks: int):
        internal_wires = SwitchBoxHelper.get_imran_sb_wires(num_tracks)
        switchbox = GSwitch(x, y, num_tracks, bit_width, internal_wires)
        super().__init__(switchbox)
