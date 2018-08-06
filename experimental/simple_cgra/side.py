from enum import Enum, auto


class Side(Enum):
    NORTH = auto()
    EAST = auto()
    SOUTH = auto()
    WEST = auto()

    def mirror(self):
        if self == self.NORTH:
            return self.SOUTH
        if self == self.EAST:
            return self.WEST
        if self == self.SOUTH:
            return self.NORTH
        if self == self.WEST:
            return self.EAST
        raise NotImplementedError(self)
