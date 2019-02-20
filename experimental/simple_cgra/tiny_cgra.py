from abc import abstractmethod
import math
import generator
import magma
import mantle
from from_magma import FromMagma
from from_verilog import FromVerilog
from configurable import Configurable, ConfigurationType
from const import Const


class MuxWrapper(gemstone.generator.Generator):
    def __init__(self, height, width):
        super().__init__()

        self.height = height
        self.width = width
        MuxCls = mantle.DefineMux(self.height, self.width)
        self.mux = FromMagma(MuxCls)

        T = magma.Bits(width)
        sel_bits = magma.bitutils.clog2(self.height)

        self.add_ports(
            I=magma.In(magma.Array(self.height, T)),
            S=magma.In(magma.Bits(sel_bits)),
            O=magma.Out(T),
        )

        for i in range(self.height):
            self.wire(self.I[i], getattr(self.mux, f"I{i}"))
        self.wire(self.S, self.mux.S)
        self.wire(self.mux.O, self.O)

    def name(self):
        return f"GenMux_{self.height}_{self.width}"


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
        self.muxs = [MuxWrapper(self.num_tracks, self.width) \
                     for _ in range(self.num_tracks)]
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
                self.wire(mux_in, mux.I[j])
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
        self.mux = MuxWrapper(self.num_tracks, self.width)

        T = magma.Bits(self.width)
        sel_bits = magma.bitutils.clog2(self.num_tracks)

        self.add_ports(
            I=magma.In(magma.Array(self.num_tracks, T)),
            O=magma.Out(T),
        )
        self.add_configs(
            sel=sel_bits,
        )

        self.wire(self.I, self.mux.I)
        self.wire(self.sel, self.mux.S)
        self.wire(self.mux.O, self.O)

    def name(self):
        return f"CB_{self.width}_{self.num_tracks}"


class PECoreGenerator(CoreGenerator):
    def __init__(self, width):
        super().__init__()

        self.width = width
        self.impl = FromVerilog("experimental/simple_cgra/tiny_pe_core.v")

        T = magma.Bits(self.width)
        self.add_ports(
            I0=magma.In(T),
            I1=magma.In(T),
            O=magma.Out(T),
        )
        self.add_configs(
            op=5,
        )

        self.wire(self.I0, self.impl.data0)
        self.wire(self.I1, self.impl.data1)
        self.wire(self.op, self.impl.op)
        self.wire(self.impl.res, self.O)

    def inputs(self):
        return [self.I0, self.I1]

    def outputs(self):
        return [self.O]

    def name(self):
        return f"PECore_{self.width}"


class MemCoreGenerator(CoreGenerator):
    def __init__(self, width):
        super().__init__()

        self.width = width
        self.impl = FromVerilog("experimental/simple_cgra/tiny_mem_core.v")

        T = magma.Bits(self.width)
        self.add_ports(
            I=magma.In(T),
            O=magma.Out(T),
        )
        self.add_configs(
            wr_en=1,
        )

        self.wire(self.I, self.impl.in_)
        self.wire(self.wr_en, self.impl.wr_en)
        self.wire(self.impl.out, self.O)

    def inputs(self):
        return [self.I]

    def outputs(self):
        return [self.O]

    def name(self):
        return f"MemCore_{self.width}"


class TileGenerator(Configurable):
    def __init__(self, width, num_tracks, core):
        super().__init__()

        self.width = width
        self.num_tracks = num_tracks
        self.core = core
        self.sb = SBGenerator(
            self.width, self.num_tracks, len(self.core.outputs()))
        self.cbs = [CBGenerator(self.width, self.num_tracks) \
                    for _ in range(len(self.core.inputs()))]
        T = magma.Array(self.num_tracks, magma.Bits(self.width))

        self.add_ports(
            I=magma.In(T),
            O=magma.Out(T),
        )

        self.wire(self.I, self.sb.I)
        for cb in self.cbs:
            self.wire(self.I, cb.I)
        for i, core_in in enumerate(self.core.inputs()):
            self.wire(self.cbs[i].O, core_in)
        for i, core_out in enumerate(self.core.outputs()):
            self.wire(core_out, self.sb.core_in[i])
        self.wire(self.sb.O, self.O)

    def features(self):
        return (tile.sb, tile.core, *(cb for cb in tile.cbs))

    def name(self):
        return f"Tile_{self.width}_{self.num_tracks}_{self.core.name()}"


class TopGenerator(Configurable):
    def __init__(self):
        super().__init__()

        width = 16
        num_tracks = 4
        num_tiles = 10
        T = magma.Array(num_tracks, magma.Bits(width))

        self.tiles = []
        for i in range(num_tiles):
            if i % 2 == 0:
                core = PECoreGenerator(width)
            else:
                core = MemCoreGenerator(width)
            self.tiles.append(TileGenerator(width, num_tracks, core))

        self.add_ports(
            I=magma.In(T),
            O=magma.Out(T),
        )

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

    def top_to_tile(top, tile, tile_idx):
        tile.add_ports(tile_id=magma.In(magma.Bits(16)))
        top.wire(Const(magma.bits(tile_idx, 16)), tile.tile_id)
        tile_eq = FromMagma(mantle.DefineEQ(16))
        tile.wire(tile.tile_id, tile_eq.I0)
        tile.wire(tile.config.config_addr[0:16], tile_eq.I1)
        return tile_eq

    def tile_to_feature(tile, tile_eq, feature, feature_idx):
        feature.add_ports(config_en=magma.In(magma.Bit))
        feature_eq = FromMagma(mantle.DefineEQ(8))
        tile.wire(tile.config.config_addr[16:24], feature_eq.I0)
        tile.wire(Const(magma.bits(feature_idx, 8)), feature_eq.I1)
        feature_en = FromMagma(mantle.DefineAnd())
        tile.wire(feature_eq.O, feature_en.I0)
        tile.wire(tile_eq.O, feature_en.I1)
        tile.wire(feature_en.O, feature.config_en)

    def get_global_addr(parts):
        ret = 0
        for value, width in parts:
            ret = (ret << width) | value
        return ret

    top_gen.add_ports(config=magma.In(ConfigurationType(32, 32)))
    top_gen.fanout(top_gen.config, top_gen.tiles)
    for tile_idx, tile in enumerate(top_gen.tiles):
        tile_eq = top_to_tile(top_gen, tile, tile_idx)
        for feature_idx, feature in enumerate(tile.features()):
            tile.fanout(tile.config.config_addr[24:], tile.features())
            tile.fanout(tile.config.config_data, tile.features())
            tile_to_feature(tile, tile_eq, feature, feature_idx)
            registers = feature.registers.values()
            for reg_idx, reg in enumerate(registers):
                parts = ((reg_idx, 8), (feature_idx, 8), (tile_idx, 16),)
                global_addr = get_global_addr(parts)
                reg.addr = reg_idx
                reg.global_addr = global_addr
            feature.fanout(feature.config_addr, registers)
            feature.fanout(feature.config_data, registers)
            feature.fanout(feature.config_en, registers)

    top_circ = top_gen.circuit()
    magma.compile("top", top_circ, output="coreir")
    print(open("top.json").read())
