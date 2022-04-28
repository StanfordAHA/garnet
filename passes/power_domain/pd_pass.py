from gemstone.common.mux_wrapper_aoi import AOIMuxWrapper, AOIMuxType
from gemstone.common.transform import replace, Generator, FromMagma
from io_core.io_core_magma import IOCoreBase
from canal.interconnect import Interconnect
from gemstone.common.configurable import Configurable, ConfigurationType
from canal.circuit import flatten_mux
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
        self.add_port("ps_en_out", magma.Out(magma.Bits[1]))
        self.wire(self.ports.ps_en_out, self.registers.ps_en.ports.O)

    def name(self):
        return "PowerDomainConfigReg"

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

    # interconnect for default uses AOI mux. we don't need to replace
    # the inefficient coreir mux anymore
    for (x, y) in interconnect.tile_circuits:
        tile = interconnect.tile_circuits[(x, y)]
        # cb is const aoi
        for _, cb in tile.cbs.items():
            old_mux = cb.mux
            new_mux = AOIMuxWrapper(old_mux.height, cb.node.width,
                                    AOIMuxType.Const, cb.instance_name)
            new_mux = flatten_mux(new_mux)
            # replace it!
            replace(cb, old_mux, new_mux)


class PowerDomainOR(Generator):
    def __init__(self, config_data_width: int):
        super().__init__("PowerDomainOR")

        self.not_gate = FromMagma(mantle.DefineInvert(1))
        self._and_gate = [None] * config_data_width

        for i in range(config_data_width):
            self._and_gate[i] = FromMagma(mantle.DefineAnd(2, 1))

        for i in range(config_data_width):
            self.wire(self._and_gate[i].ports.I1[0], self.not_gate.ports.O[0])

        self._or_gate = FromMagma(mantle.DefineOr(2, config_data_width))

        for i in range(config_data_width):
            self.wire(self._and_gate[i].ports.O[0], self._or_gate.ports.I0[i])

        # only add necessary ports here so that we can replace without
        # problem
        self.add_ports(
            I0=magma.In(magma.Bits[config_data_width]),
            I1=magma.In(magma.Bits[config_data_width]),
            O=magma.Out(magma.Bits[config_data_width])
        )
        for i in range(config_data_width):
            self.wire(self.ports.I0[i], self._and_gate[i].ports.I0[0])

        self.wire(self.ports.I1, self._or_gate.ports.I1)
        self.wire(self._or_gate.ports.O, self.ports.O)

    def name(self):
        return "PowerDomainOR"


def add_aon_read_config_data(interconnect: Interconnect):
    # we need to replace each read_config_data_or with more circuits
    # it should be in the children
    for (x, y) in interconnect.tile_circuits:
        tile = interconnect.tile_circuits[(x, y)]
        if isinstance(tile.core, IOCoreBase):
            # io core is always on
            continue
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
                pd_or.add_port("I_not", magma.In(magma.Bits[1]))
                tile.wire(pd_or.ports.I_not, pd_feature.ports.ps_en_out)
                pd_or.wire(pd_or.ports.I_not, pd_or.not_gate.ports.I)
                break
