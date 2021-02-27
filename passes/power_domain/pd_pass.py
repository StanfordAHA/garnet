from gemstone.common.mux_wrapper_aoi import AOIMuxWrapper, AOIMuxType
from gemstone.common.transform import replace, Generator, FromMagma
from io_core.io_core_magma import IOCoreValid
from canal.interconnect import Interconnect
from gemstone.common.configurable import Configurable, ConfigurationType
from canal.circuit import flatten_mux
import magma as m
import mantle


class PowerDomainConfigReg(Configurable):
    def __init__(self, config_addr_width: int,
                 config_data_width: int):
        super().__init__(config_addr_width, config_data_width)
        self.name = "PowerDomainConfigReg"
        ps_config_name = "ps_en"
        # ps
        self.add_config(ps_config_name, 1)
        self.io += m.IO(
            config=m.In(ConfigurationType(config_addr_width,
                                          config_data_width)),
            ps_en_out=m.Out(m.Bits[1])
        )
        m.wire(self.io.ps_en_out, self.registers.ps_en.O)
        self._setup_config()


    def configure(self, turn_off: bool):
        assert turn_off in {0, 1, True, False}
        return [0, int(turn_off)]


def add_power_domain(interconnect: Interconnect):
    # add features first
    for (x, y) in interconnect.tile_circuits:
        tile = interconnect.tile_circuits[(x, y)]
        tile_core = tile.core
        if tile_core is None or "config" not in tile_core.ports:
            continue
        # Add PS config register
        pd_feature = PowerDomainConfigReg(tile.config_addr_width,
                                          tile.config_data_width)
        tile.add_feature(pd_feature)

    # replace all the interconnect mux with aoi mux. cb mux to aoi const
    # mux
    # note that because we have an index to all mux created, it is fairly
    # straight-forward
    for (x, y) in interconnect.tile_circuits:
        tile = interconnect.tile_circuits[(x, y)]
        for bit_width, sb in tile.sbs.items():
            sb_muxs = sb.sb_muxs
            for _, (node, old_mux) in sb_muxs.items():
                assert node.width == bit_width
                new_mux = AOIMuxWrapper(old_mux.height, bit_width,
                                        AOIMuxType.Regular,
                                        old_mux.instance_name)
                new_mux = flatten_mux(new_mux)
                replace(sb, old_mux, new_mux)

            reg_mux = sb.reg_muxs
            for _, (node, old_mux) in reg_mux.items():
                assert node.width == bit_width
                new_mux = AOIMuxWrapper(old_mux.height, bit_width,
                                        AOIMuxType.Regular,
                                        old_mux.instance_name)
                new_mux = flatten_mux(new_mux)
                replace(reg_mux, old_mux, new_mux)

        # cb is const aoi
        for _, cb in tile.cbs.items():
            old_mux = cb.mux
            new_mux = AOIMuxWrapper(old_mux.height, cb.node.width,
                                    AOIMuxType.Const, cb.instance_name)
            new_mux = flatten_mux(new_mux)
            # replace it!
            replace(cb, old_mux, new_mux)


class PowerDomainOR(m.Generator2):
    def __init__(self, config_data_width: int):
        self.name = "PowerDomainOR"

        self.not_gate = mantle.DefineInvert(1)
        self._and_gate = [None] * config_data_width

        for i in range(config_data_width):
            self._and_gate[i] = mantle.DefineAnd(2, 1)

        for i in range(config_data_width):
            m.wire(self._and_gate[i].I1[0], self.not_gate.O[0])

        self._or_gate = mantle.DefineOr(2, config_data_width)

        for i in range(config_data_width):
            m.wire(self._and_gate[i].O[0], self._or_gate.I0[i])

        # only add necessary ports here so that we can replace without
        # problem
        self.io = m.IO(
            I0=m.In(m.Bits[config_data_width]),
            I1=m.In(m.Bits[config_data_width]),
            O=m.Out(m.Bits[config_data_width])
        )
        for i in range(config_data_width):
            m.wire(self.io.I0[i], self._and_gate[i].I0[0])

        m.wire(self.io.I1, self._or_gate.I1)
        m.wire(self._or_gate.O, self.io.O)


def add_aon_read_config_data(interconnect: Interconnect):
    # we need to replace each read_config_data_or with more circuits
    # it should be in the children
    for (x, y) in interconnect.tile_circuits:
        tile = interconnect.tile_circuits[(x, y)]
        children = tile.children()
        for child in children:
            if isinstance(child, FromMagma) and \
                    child.underlying.name == "read_config_data_or":
                pd_feature = None
                # usually the tile features are the last one
                for feature in reversed(tile.features()):
                    if isinstance(feature, PowerDomainConfigReg):
                        pd_feature = feature
                        break
                assert pd_feature is not None

                pd_or = PowerDomainOR(tile.config_data_width)
                replace(tile, child, pd_or)

                # add config input to the the module
                # TODO: Find a way to include this port in original
                # description without breaking replacement pass
                pd_or.add_port("I_not", m.In(m.Bits[1]))
                m.wire(pd_or.I_not, pd_feature.ps_en_out)
                m.wire(pd_or.I_not, pd_or.not_gate.I)
                break
