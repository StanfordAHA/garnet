from abc import abstractmethod
import math
import generator
import magma
import mantle
from from_magma import FromMagma
from configurable import Configurable, ConfigurationType
from const import Const


class FeatureGenerator(Configurable):
    def __init__(self):
        super().__init__()


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


class TileGeneratorBase(Configurable):
    class _FeatureContainer(dict):
        def __getattr__(self, name):
            return self[name]

    def __init__(self):
        super().__init__()

        self.features = TileGeneratorBase._FeatureContainer()

    def add_feature(self, name, feature):
        assert name not in self.features
        self.features[name] = feature

    def add_features(self, **kwargs):
        for name, feature in kwargs.items():
            self.add_feature(name, feature)


class TileGenerator(TileGeneratorBase):
    def __init__(self, width, num_tracks):
        super().__init__()

        self.width = width
        self.num_tracks = num_tracks
        core = PECoreGenerator(self.width)
        sb = SBGenerator(self.width, self.num_tracks, len(core.outputs()))
        self.add_features(
            core=core,
            sb=sb,
        )
        for i in range(len(self.features.core.inputs())):
            cb = CBGenerator(self.width, self.num_tracks)
            self.add_feature(f"cb{i}", cb)
        T = magma.Array(self.num_tracks, magma.Bits(self.width))

        self.add_ports(
            I=magma.In(T),
            O=magma.Out(T),
        )

        self.wire(self.I, self.features.sb.I)
        for i in range(len(self.features.core.inputs())):
            cb = getattr(self.features, f"cb{i}")
            self.wire(self.I, cb.I)
        for i, core_in in enumerate(self.features.core.inputs()):
            cb = getattr(self.features, f"cb{i}")
            self.wire(cb.O, core_in)
        for i, core_out in enumerate(self.features.core.outputs()):
            self.wire(core_out, self.features.sb.core_in[i])
        self.wire(self.features.sb.O, self.O)

    def name(self):
        return f"Tile_{self.width}_{self.num_tracks}"


class TopGenerator(Configurable):
    def __init__(self):
        super().__init__()

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

        # for tile in self.tiles:
        #    self.wire(self.config_addr, tile.config_addr)
        #    self.wire(self.config_data, tile.config_data)
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

    from bit_vector import BitVector as BV
    addr_map = {}
    for tile_idx, tile in enumerate(top_gen.tiles):
        addr_map[tile] = BV(tile_idx, 16)
        for feature_idx, (feature_name, feature) in enumerate(tile.features.items()):
            if feature_name in addr_map:
                continue
            addr_map[feature_name] = BV(feature_idx, 8)
            for reg_idx, (reg_name, reg) in enumerate(feature.registers.items()):
                qualified_name = ".".join((feature_name, reg_name))
                if qualified_name in addr_map:
                    continue
                addr_map[qualified_name] = BV(reg_idx, 8)
    print (addr_map)
    exit()

    def top_to_tile(top, tile, tile_idx):
        tile.add_ports(
            config=magma.In(ConfigurationType(32, 32)),
            tile_id=magma.In(magma.Bits(16)),
        )
        top.wire(top.config, tile.config)
        top.wire(Const(magma.bits(tile_idx, 16)), tile.tile_id)
        tile_eq = FromMagma(mantle.DefineEQ(16))
        tile.wire(tile.tile_id, tile_eq.I0)
        tile.wire(tile.config.config_addr[0:16], tile_eq.I1)
        return tile_eq

    def tile_to_feature(tile, tile_eq, feature, feature_idx):
        feature.add_ports(
            config=magma.In(ConfigurationType(8, 32)),
            config_en=magma.In(magma.Bit),
        )
        tile.wire(tile.config.config_addr[24:], feature.config.config_addr)
        tile.wire(tile.config.config_data, feature.config.config_data)
        feature_eq = FromMagma(mantle.DefineEQ(8))
        tile.wire(tile.config.config_addr[16:24], feature_eq.I0)
        tile.wire(Const(magma.bits(feature_idx, 8)), feature_eq.I1)
        feature_en = FromMagma(mantle.DefineAnd())
        tile.wire(feature_eq.O, feature_en.I0)
        tile.wire(tile_eq.O, feature_en.I1)
        tile.wire(feature_en.O, feature.config_en)

    def feature_to_reg(feature, reg, idx):
        reg.finalize(idx, idx, 8, 32)
        feature.wire(feature.config.config_addr, reg._register.addr_in)
        feature.wire(feature.config.config_data, reg._register.data_in)
        return idx + 1

    top_gen.add_ports(config=magma.In(ConfigurationType(32, 32)))
    idx = 0
    for tile_idx, tile in enumerate(top_gen.tiles):
        tile_eq = top_to_tile(top_gen, tile, tile_idx)
        features = (tile.sb, tile.core, *(cb for cb in tile.cbs))
        for feature_idx, feature in enumerate(features):
            tile_to_feature(tile, tile_eq, feature, feature_idx)
            for name, reg in feature.registers.items():
                idx = feature_to_reg(feature, reg, idx)

    # def _fn(gen):
    #     if isinstance(gen, Configurable):
    #         for name, reg in gen.registers.items():
    #             print (name, reg._global_addr)
    #     for child in gen.children():
    #         _fn(child)
    # _fn(top_gen)
    # exit()

    top_circ = top_gen.circuit()
    magma.compile("top", top_circ, output="coreir")
    print(open("top.json").read())
