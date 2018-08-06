import itertools
import magma as m
from generator import Generator
from tile import Tile
from side import Side


class Interconnect(Generator):
    def __init__(self, m_, n_):
        super().__init__()
        self.__m = m_
        self.__n = n_
        self.__tiles = self.__empty_tiles()

    @staticmethod
    def __wire_name(i, j, side_):
        return f"tile_{i}_{j}_{side_.name}"

    def __empty_tiles(self):
        return [[None for _ in range(self.__n)] for _ in range(self.__m)]

    def indices(self):
        return itertools.product(range(self.__m), range(self.__n))

    def set_tile(self, i, j, tile):
        if self.__tiles[i][j] is not None:
            raise ValueError(f"({i}, {j}) already occupied")
        self.__tiles[i][j] = tile

    def all_tiles_set(self):
        return all([all(t) for t in self.__tiles])

    def map(self, in_, fn):
        out = self.__empty_tiles()
        for i, j in self.indices():
            out[i][j] = fn(in_[i][j])
        return out

    def __build_connectivity(self):
        connectivity = self.__empty_tiles()
        for i, j in self.indices():
            tile = self.__tiles[i][j]
            neighbors = {side_ : None for side_ in tile.sides}
            if i > 0:
                neighbors[Side.WEST] = ((i - 1, j), Side.EAST)
            if i < (self.__m - 1):
                neighbors[Side.EAST] = ((i + 1, j), Side.WEST)
            if j > 0:
                neighbors[Side.NORTH] = ((i, j - 1), Side.SOUTH)
            if j < (self.__n - 1):
                neighbors[Side.SOUTH] = ((i, j + 1), Side.NORTH)
            connectivity[i][j] = neighbors
        return connectivity

    def _generate_impl(self):
        assert self.all_tiles_set()
        connectivity = self.__build_connectivity()

        # Generate tile circuits.
        circuits = self.map(self.__tiles, lambda t : t.generate())

        # Build interface to the circuit.
        interface = []
        for i, j in self.indices():
            T = self.__tiles[i][j].data_type
            neighbors = connectivity[i][j]
            for side_, neighbor in neighbors.items():
                name = Interconnect.__wire_name(i, j, side_)
                if neighbor is not None:
                    continue
                interface += [f"{name}_I", m.In(T), f"{name}_O", m.Out(T)]

        class _Interconnect(m.Circuit):
            IO = interface

            @classmethod
            def definition(io):
                # Instance tiles.
                insts = self.map(circuits, lambda t : t())

                for i, j in self.indices():
                    inst = insts[i][j]
                    neighbors = connectivity[i][j]
                    for side_, neighbor in neighbors.items():
                        name = Interconnect.__wire_name(i, j, side_)
                        if neighbor is None:
                            m.wire(getattr(io, f"{name}_I"),
                                   getattr(inst, f"{side_.name}_I"))
                            m.wire(getattr(io, f"{name}_O"),
                                   getattr(inst, f"{side_.name}_O"))
                        else:
                            ((i_other, j_other), side_other) = neighbor
                            inst_other = insts[i_other][j_other]
                            m.wire(getattr(inst, f"{side_.name}_O"),
                                   getattr(inst_other, f"{side_other.name}_I"))

        return _Interconnect
