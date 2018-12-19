from interconnect import *


class CGRASwitch(Switch):
    def __init__(self, num_tracks : int):
        self.num_tracks = num_tracks

    def num_switch_nodes(self, side : Side) -> int:
        return self.num_tracks

    def get_switch_node(self, side : Side, index : int) -> SwitchNode:
        if index >= self.num_tracks:
            raise ValueError(f"Invalid index {index}")
        return SwitchNode()

    def is_connected(self,
                     side0 : Side,
                     index0 : int,
                     side1 : Side,
                     index1 : int) -> bool:
        if index0 >= self.num_tracks:
            raise ValueError(f"Invalid index {index0}")
        if index1 >= self.num_tracks:
            raise ValueError(f"Invalid index {index1}")
        return side0 != side1 and index0 == index1


class CGRATile(Tile):
    def __init__(self, num_tracks : int):
        self.switch_ = CGRASwitch(num_tracks)
        
    def functional_unit(self):
        return None

    def num_inputs(self) -> int:
        return self.switch_.num_tracks * 2

    def num_outputs(self) -> int:
        return self.switch_.num_tracks * 4

    def switch(self) -> Switch:
        return self.switch_


class CGRAInterconnect(Interconnect):
    def __init__(self, m, n, num_tracks):
        self.m = m
        self.n = n
        self.tile_type = CGRATile(num_tracks)

    def size(self) -> (int, int):
        return (self.m, self.n)

    def tile(self, i : int, j : int) -> Tile:
        if not self.inside(i, j):
            raise ValueError(f"Invalid tile index {(i, j)}")
        return self.tile_type

    def is_connected(self,
                     tile0 : (int, int),
                     side0 : Side,
                     index0 : int,
                     tile1 : (int, int),
                     side1 : Side,
                     index1 : int) -> bool:
        if not self.inside(*tile0):
            raise ValueError(f"Invalid tile index {tile0}")
        if not self.inside(*tile1):
            raise ValueError(f"Invalid tile index {tile1}")
        if not self.tile(*tile0).switch().inside(side0, index0):
            raise ValueError(f"Invalid switch node index {(side0, index0)}")
        if not self.tile(*tile1).switch().inside(side1, index1):
            raise ValueError(f"Invalid switch node index {(side0, index0)}")
        if manhattan_distance(*tile0, *tile1) != 1:
            return False
        # TODO(rsetaluri): Move this elsewhere.
        opposite = {
            Side.NORTH: Side.SOUTH,
            Side.SOUTH: Side.NORTH,
            Side.EAST: Side.WEST,
            Side.WEST: Side.EAST,
        }
        # TODO(rsetaluri): Fix this logic. Need to also check that the axis is
        # correct.
        return side0 == opposite[side1] and index0 == index1

ic = CGRAInterconnect(4, 4, 5)
print (ic.is_connected((0, 0), Side.SOUTH, 0, (0, 1), Side.NORTH, 0))
