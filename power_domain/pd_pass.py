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
        self.add_port("ps_en_out", magma.Out(magma.Bits[1]))
        self.wire(self.ports.ps_en_out, self.registers.ps_en.ports.O)
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
            # we need more efficient implementation for a simple replacement
            # pass. in other words, instead of an O(n^2) implementation, we
            # hand-crafted an O(n) with smaller constants
            sb_muxs = sb.sb_muxs
            mux_table = {}
            for _, (node, old_mux) in sb_muxs.items():
                assert node.width == bit_width
                new_mux = AOIMuxWrapper(old_mux.height, bit_width,
                                        AOIMuxType.Regular,
                                        old_mux.instance_name)
                mux_table[old_mux] = new_mux

            reg_mux = sb.reg_muxs
            for _, (node, old_mux) in reg_mux.items():
                assert node.width == bit_width
                new_mux = AOIMuxWrapper(old_mux.height, bit_width,
                                        AOIMuxType.Regular,
                                        old_mux.instance_name)
                mux_table[old_mux] = new_mux

            assert len(mux_table) == len(sb_muxs) + len(reg_mux)
            wires = set()
            for conn1, conn2 in sb.wires:
                if conn1.owner() in mux_table or conn2.owner() in mux_table:
                    wires.add((conn1, conn2))
            for conn1, conn2 in wires:
                # avoid O(n) search to remove the wires. this is safe
                # since we directly load these connection in sorted order
                sb.wires.remove((conn1, conn2))

            for conn1, conn2 in wires:
                conn1_owner = conn1.owner()
                conn2_owner = conn2.owner()
                if conn1_owner in mux_table:
                    conn1 = conn1.get_port(mux_table[conn1_owner].ports)
                if conn2_owner in mux_table:
                    conn2 = conn2.get_port(mux_table[conn2_owner].ports)
                sb.wire(conn1, conn2)
        # cb is const aoi
        for _, cb in tile.cbs.items():
            old_mux = cb.mux
            new_mux = AOIMuxWrapper(old_mux.height, cb.node.width,
                                    AOIMuxType.Const, cb.instance_name)
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
