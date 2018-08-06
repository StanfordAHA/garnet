import magma as m
from generator import Generator
from side import Side


class Tile(Generator):
    def __init__(self, core, tracks=5, layers=(1, 16,)):
        super().__init__()
        self.__core = core
        self.__tracks = tracks
        self.__layers = layers
        layer_types = {f"layer_{l}" : m.Bits(l) for l in self.__layers}
        self.__data_type = m.Array(self.__tracks, m.Tuple(**layer_types))
        self.__sides = {s for s in Side}

    @property
    def data_type(self):
        return self.__data_type

    @property
    def sides(self):
        return self.__sides.copy()

    def _generate_impl(self):
        interface = []
        T = self.__data_type
        for s in self.__sides:
            interface += [f"{s.name}_I", m.In(T)]
            interface += [f"{s.name}_O", m.Out(T)]

        class _Tile(m.Circuit):
            name = "Tile"
            IO = interface

            @classmethod
            def definition(io):
                for side_ in self.__sides:
                    in_wire = getattr(io, f"{side_.name}_I")
                    out_wire = getattr(io, f"{side_.mirror().name}_O")
                    m.wire(in_wire, out_wire)

        return _Tile

    def __repr__(self):
        return f"Tile({self.__core.__repr__()})"
