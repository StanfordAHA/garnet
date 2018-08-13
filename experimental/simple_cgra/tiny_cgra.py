from abc import abstractmethod
import math
import generator
import magma
import mantle
from from_magma import FromMagma
from configurable import Configurable


class FeatureGenerator(Configurable):
    def __init__(self):
        super().__init__(16, 32)


class CoreGenerator(FeatureGenerator):
    @abstractmethod
    def inputs(self):
        pass

    @abstractmethod
    def outputs(self):
        pass


class SBGenerator(FeatureGenerator):
    def __init__(self, width, num_tracks, core_inputs):
        super().__init__()

        self.width = width
        self.num_tracks = num_tracks
        assert core_inputs == 1
        self.core_inputs = core_inputs
        MuxCls = mantle.DefineMux(self.num_tracks, self.width)
        self.muxs = [FromMagma(MuxCls) for _ in range(self.num_tracks)]
        T = magma.Array(self.num_tracks, magma.Bits(self.width))
        bits_per_sel = math.ceil(math.log(self.num_tracks, 2))

        self.add_ports(
            I=magma.In(T),
            core_in=magma.In(magma.Array(self.core_inputs, T.T)),
            O=magma.Out(T),
        )
        for i in range(self.num_tracks):
            self.add_config(f"sel_{i}", bits_per_sel)
        self.selects = [getattr(self, f"sel_{i}") \
                        for i in range(self.num_tracks)]

        for i in range(self.num_tracks):
            mux = self.muxs[i]
            for j in range(self.num_tracks):
                mux_in = self.I[j] if i != j else self.core_in[0]
                self.wire(mux_in, getattr(mux, f"I{j}"))
            self.wire(self.selects[i], mux.S)
            self.wire(mux.O, self.O[i])

    def name(self):
        return f"SB_{self.width}_{self.num_tracks}_{self.core_inputs}"


class CBGenerator(FeatureGenerator):
    def __init__(self, width, num_tracks):
        super().__init__()

        self.width = width
        self.num_tracks = num_tracks
        is_power_of_two = lambda x: x != 0 and ((x & (x - 1)) == 0)
        assert is_power_of_two(self.num_tracks)
        self.mux = FromMagma(mantle.DefineMux(self.num_tracks, self.width))
        T = magma.Bits(self.width)
        sel_bits = math.ceil(math.log(self.num_tracks, 2))

        self.add_ports(
            I=magma.In(magma.Array(self.num_tracks, T)),
            O=magma.Out(T),
        )
        self.add_configs(
            sel=sel_bits,
        )

        for i in range(self.num_tracks):
            self.wire(self.I[i], getattr(self.mux, f"I{i}"))
        self.wire(self.sel, self.mux.S)
        self.wire(self.mux.O, self.O)

    def name(self):
        return f"CB_{self.width}_{self.num_tracks}"


class PECoreGenerator(CoreGenerator):
    def __init__(self, width):
        super().__init__()

        self.width = width
        T = magma.Bits(self.width)

        self.add_ports(
            I0=magma.In(T),
            I1=magma.In(T),
            O=magma.Out(T),
        )
        self.add_configs(
            op=5,
        )

        import const
        zero = const.Const(magma.bits(0, self.width))
        self.wire(zero, self.O)
        del const

    def inputs(self):
        return [self.I0, self.I1]

    def outputs(self):
        return [self.O]

    def name(self):
        return f"PECore_{self.width}"


class TileGenerator(Configurable):
    def __init__(self, width, num_tracks):
        super().__init__(32, 32)

        self.width = width
        self.num_tracks = num_tracks
        self.core = PECoreGenerator(self.width)
        self.sb = SBGenerator(self.width,
                              self.num_tracks,
                              len(self.core.outputs()))
        self.cbs = [CBGenerator(self.width, self.num_tracks) \
                    for _ in range(len(self.core.inputs()))]
        T = magma.Array(self.num_tracks, magma.Bits(self.width))
        features = (self.sb, self.core, *(cb for cb in self.cbs))

        self.add_ports(
            I=magma.In(T),
            O=magma.Out(T),
        )

        for feature in features:
            self.wire(self.config_addr[16:], feature.config_addr)
            self.wire(self.config_data, feature.config_data)
        self.wire(self.I, self.sb.I)
        for cb in self.cbs:
            self.wire(self.I, cb.I)
        for i, core_in in enumerate(self.core.inputs()):
            self.wire(self.cbs[i].O, core_in)
        for i, core_out in enumerate(self.core.outputs()):
            self.wire(core_out, self.sb.core_in[i])
        self.wire(self.sb.O, self.O)

    def name(self):
        return f"Tile_{self.width}_{self.num_tracks}"


class TopGenerator(Configurable):
    def __init__(self):
        super().__init__(32, 32)

        width = 16
        num_tracks = 4
        num_tiles = 10
        T = magma.Array(num_tracks, magma.Bits(width))

        self.tiles = [TileGenerator(width, num_tracks) \
                      for _ in range(num_tiles)]

        self.add_ports(
            I=magma.In(T),
            O=magma.Out(T),
        )

        for tile in self.tiles:
           self.wire(self.config_addr, tile.config_addr)
           self.wire(self.config_data, tile.config_data)
        self.wire(self.I, self.tiles[0].I)
        self.wire(self.tiles[-1].O, self.O)
        for i in range(1, len(self.tiles)):
           t0 = self.tiles[i - 1]
           t1 = self.tiles[i]
           self.wire(t0.O, t1.I)

    def name(self):
        return "Top"


if __name__ == "__main__":
    top_gen = TopGenerator()
    top_circ = top_gen.circuit()
    magma.compile("top", top_circ, output="coreir")
    print(open("top.json").read())
