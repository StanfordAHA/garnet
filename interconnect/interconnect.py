from abc import ABC, abstractmethod
import enum


def manhattan_distance(i0, j0, i1, j1):
    return abs(i0 - i1) + abs(j0 - j1)


class Side(enum.Enum):
    NORTH = 0
    SOUTH = 1
    EAST = 2
    WEST = 3


class SwitchNode:
    pass


class Switch(ABC):
    @abstractmethod
    def num_switch_nodes(self, side : Side) -> int:
        pass

    def inside(self, side : Side, index : int) -> bool:
        return index >= 0 and index < self.num_switch_nodes(side)

    @abstractmethod
    def get_switch_node(self, side : Side, index : int) -> SwitchNode:
        pass

    @abstractmethod
    def is_connected(self,
                     side0 : Side,
                     index0 : int,
                     side1 : Side,
                     index1 : int) -> bool:
        pass


class Tile(ABC):
    @abstractmethod
    def functional_unit(self):
        pass

    @abstractmethod
    def num_inputs(self) -> int:
        pass

    @abstractmethod
    def num_outputs(self) -> int:
        pass

    @abstractmethod
    def switch(self) -> Switch:
        pass


class Interconnect(ABC):
    @abstractmethod
    def size(self) -> (int, int):
        pass

    def inside(self, i : int, j : int) -> bool:
        size = self.size()
        return i >= 0 and j >= 0 and i < size[0] and j < size[1]

    @abstractmethod
    def tile(self, i : int, j : int) -> Tile:
        pass

    @abstractmethod
    def is_connected(self,
                     tile0 : Tile,
                     side0 : Side,
                     index0 : int,
                     tile1 : Tile,
                     side1 : Side,
                     index1 : int) -> bool:
        pass
