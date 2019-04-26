from gemstone.common.mux_wrapper_aoi import AOIMuxWrapper, AOIMuxType
from gemstone.common.transform import replace
from io_core.io1bit_magma import IO1bit
from io_core.io16bit_magma import IO16bit
from canal.interconnect import Interconnect
from gemstone.common.configurable import Configurable, ConfigurationType
import magma


class PowerDomainConfigReg(Configurable):
    def __init__(self, config_addr_width: int,
                 config_data_width: int):
        super().__init__(config_addr_width, config_data_width)
        ps_config_name = "ps_en"
        # ps
        self.add_config(ps_config_name, config_data_width)
        self.add_ports(
            config=magma.In(ConfigurationType(config_addr_width,
                                              config_data_width)),
        )
        self._setup_config()

    def name(self):
        return "PowerDomainConfigReg"


def add_power_domain(interconnect: Interconnect):
    # add features first
    for (x, y) in interconnect.tile_circuits:
        tile = interconnect.tile_circuits[(x, y)]
        tile_core = tile.core
        if isinstance(tile_core, (IO16bit, IO1bit)) or tile_core is None:
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
