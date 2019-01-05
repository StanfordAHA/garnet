from .circuit import SwitchBoxMux, Circuit
from .cyclone import Switch as GSwitch, SwitchBoxSide
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

        self.sb_muxs: List[List[List[SwitchBoxMux]]] = [[[None] * num_track] *
                                                        num_ios] * num_sides
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

    def name(self):
        return SwitchBoxMux.create_name(str(self.g_switch))

    def realize(self):
        for sides in self.sb_muxs:
            for io in sides:
                for sb in io:
                    self.muxs.append(sb.create_circuit())

    def remove_side_sbs(self, side: SwitchBoxSide, io: SwitchBoxIO):
        # clear the muxs
        self.sb_muxs[side.value][io.value].clear()
        self.g_switch.remove_side_sbs(side, io)


@enum.unique
class SwitchBoxType(enum.Enum):
    Disjoint = enum.auto()
    Wilton = enum.auto()
    Imran = enum.auto()


def mod(a, b):
    while a < 0:
        a += b
    return a % b


class SwitchBoxHelper:
    """A helper class to create switch box internal connections
    Implementation is copied from Cyclone
    https://github.com/Kuree/cgra_pnr/blob/dev/cyclone/src/util.cc
    """

    @staticmethod
    def get_disjoint_sb_wires(num_tracks: int) -> List[Tuple[int,
                                                             SwitchBoxSide,
                                                             int,
                                                             SwitchBoxSide]]:
        result = []
        for track in range(num_tracks):
            for side_from in range(GSwitch.NUM_SIDES):
                for side_to in range(GSwitch.NUM_SIDES):
                    if side_from == side_to:
                        continue
                    for io in range(GSwitch.NUM_IOS):
                        result.append((track, SwitchBoxSide(side_from),
                                       track, SwitchBoxSide(side_to)))
        return result

    @staticmethod
    def get_wilton_sb_wires(num_tracks: int)-> List[Tuple[int,
                                                          SwitchBoxSide,
                                                          int,
                                                          SwitchBoxSide]]:
        w = num_tracks
        result = []
        # t_i is defined as
        #     3
        #   -----
        # 2 |   | 0
        #   -----
        #     1
        for track in range(num_tracks):
            result.append((track, SwitchBoxSide.WEST,
                           track, SwitchBoxSide.EAST))
            result.append((track, SwitchBoxSide.EAST,
                           track, SwitchBoxSide.WEST))
            # t_1, t_3
            result.append((track, SwitchBoxSide.SOUTH,
                           track, SwitchBoxSide.NORTH))
            result.append((track, SwitchBoxSide.NORTH,
                           track, SwitchBoxSide.SOUTH))
            # t_0, t_1
            result.append((track, SwitchBoxSide.WEST,
                           mod(w - track, w), SwitchBoxSide.SOUTH))
            result.append((mod(w - track, w), SwitchBoxSide.SOUTH,
                           track, SwitchBoxSide.WEST))
            # t_1, t_2
            result.append((track, SwitchBoxSide.SOUTH,
                           mod(track + 1, w), SwitchBoxSide.EAST))
            result.append((mod(track + 1, w), SwitchBoxSide.EAST,
                           track, SwitchBoxSide.SOUTH))
            # t_2, t_3
            result.append((track, SwitchBoxSide.EAST,
                           mod(2 * w - 2 - track, w), SwitchBoxSide.NORTH))
            result.append((mod(2 * w - 2 - track, w), SwitchBoxSide.NORTH,
                           track, SwitchBoxSide.EAST))
            # t3, t_0
            result.append((track, SwitchBoxSide.NORTH,
                          mod(track + 1, w), SwitchBoxSide.WEST))
            result.append((mod(track + 1, w), SwitchBoxSide.WEST,
                           track, SwitchBoxSide.NORTH))
        return result

    @staticmethod
    def get_imran_sb_wires(num_tracks: int)-> List[Tuple[int,
                                                         SwitchBoxSide,
                                                         int,
                                                         SwitchBoxSide]]:
        w = num_tracks
        result = []

        for track in range(num_tracks):
            # f_e1
            result.append((track, SwitchBoxSide.WEST,
                           mod(w - track, w), SwitchBoxSide.NORTH))
            result.append((mod(w - track, w), SwitchBoxSide.NORTH,
                           track, SwitchBoxSide.WEST))
            # f_e2
            result.append((track, SwitchBoxSide.NORTH,
                           mod(track + 1, w), SwitchBoxSide.EAST))
            result.append((mod(track + 1, w), SwitchBoxSide.EAST,
                           track, SwitchBoxSide.NORTH))
            # f_e3
            result.append((track, SwitchBoxSide.SOUTH,
                           mod(w - track - 2, w), SwitchBoxSide.EAST))
            result.append((mod(w - track - 2, w), SwitchBoxSide.EAST,
                           track, SwitchBoxSide.SOUTH))
            # f_e4
            result.append((track, SwitchBoxSide.WEST,
                           mod(track - 1, w), SwitchBoxSide.SOUTH))
            result.append((mod(track - 1, w), SwitchBoxSide.SOUTH,
                           track, SwitchBoxSide.WEST))
            # f_e5
            result.append((track, SwitchBoxSide.WEST,
                           track, SwitchBoxSide.EAST))
            result.append((track, SwitchBoxSide.EAST,
                           track, SwitchBoxSide.WEST))
            # f_e6
            result.append((track, SwitchBoxSide.SOUTH,
                           track, SwitchBoxSide.NORTH))
            result.append((track, SwitchBoxSide.NORTH,
                           track, SwitchBoxSide.SOUTH))
        return result


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
