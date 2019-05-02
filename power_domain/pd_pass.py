from gemstone.common.mux_wrapper_aoi import AOIMuxWrapper, AOIMuxType
from gemstone.common.transform import replace, Generator, FromMagma
from io_core.io_core_magma import IOCore
from canal.interconnect import Interconnect
from gemstone.common.configurable import Configurable, ConfigurationType
import magma
import mantle


class PowerDomainConfigReg(Configurable):
    def __init__(self, config_addr_width: int,
                 config_data_width: int):
        super().__init__(config_addr_width, config_data_width)
        ps_config_name = "ps_en"
        # ps
        self.add_config(ps_config_name, 1)
        self.add_ports(
            config=magma.In(ConfigurationType(config_addr_width,
                                              config_data_width)),
        )
        self.add_port("ps_en", magma.Out(magma.Bits[1]))
        self.wire(self.ports.ps_en, self.registers.ps_en.ports.O)
        self._setup_config()

    def name(self):
        return "PowerDomainConfigReg"


def add_power_domain(interconnect: Interconnect):
    # add features first
    for (x, y) in interconnect.tile_circuits:
        tile = interconnect.tile_circuits[(x, y)]
        tile_core = tile.core
        if isinstance(tile_core, IOCore) or tile_core is None:
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
                # replace it!
                replace(sb, old_mux, new_mux)
            reg_mux = sb.reg_muxs
            for _, (node, old_mux) in reg_mux.items():
                assert node.width == bit_width
                new_mux = AOIMuxWrapper(old_mux.height, bit_width,
                                        AOIMuxType.Regular,
                                        old_mux.instance_name)
                # replace it!
                replace(sb, old_mux, new_mux)
        # cb is const aoi
        for _, cb in tile.cbs.items():
            old_mux = cb.mux
            new_mux = AOIMuxWrapper(old_mux.height, cb.node.width,
                                    AOIMuxType.Const, cb.instance_name)
            # replace it!
            replace(cb, old_mux, new_mux)


def add_aon_read_config_data(interconnect: Interconnect):
    # we need to replace each read_config_data_or with more circuits
    # it should be in the children
    for (x, y) in interconnect.tile_circuits:
        tile = interconnect.tile_circuits[(x, y)]
        children = tile.children()
        for child in children:
            if isinstance(child, FromMagma) and \
                    child.underlying.name == "read_config_data_or":
                # we need to replace this one
                # see https://github.com/StanfordAHA/gemstone/pull/17
                pd_feature = None
                for feature in tile.features():
                    if isinstance(feature, PowerDomainConfigReg):
                        pd_feature = feature
                        break
                assert pd_feature is not None
                not_gate = FromMagma(mantle.DefineInvert(1))
                tile.wire(not_gate.ports.I, pd_feature.ports.ps_en)
                and_gate = FromMagma(mantle.DefineAnd(2,
                                                      tile.config_data_width))
                for i in range(tile.config_data_width):
                    tile.wire(and_gate.ports.I1[i], not_gate.ports.O[0])
                or_gate = FromMagma(mantle.DefineOr(2, tile.config_data_width))
                tile.wire(and_gate.ports.O, or_gate.ports.I0)

                # replace using groups
                replace(tile, child, [not_gate, and_gate, or_gate],
                        ignored_ports=[not_gate.ports.I])
