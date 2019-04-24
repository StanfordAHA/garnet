from generator.from_verilog import FromVerilog
from .PDConfig import PDCGRAConfig
from generator.generator import Generator
import os
from typing import List
from power_domain.PDConfig import PDCGRAConfig
from canal.circuit import InterconnectConfigurable
from gemstone.common.configurable import Configurable, ConfigurationType
import magma


class PowerDomainConfigReg(InterconnectConfigurable):
    def __init__(self,config_addr_width: int,
                 config_data_width: int):
        super().__init__(config_addr_width, config_data_width)
        self.config = PDCGRAConfig() 
        # ps
        self.add_config(self.config.ps_config_name, config_data_width)
        self.add_ports(
                 config=magma.In(ConfigurationType(config_addr_width,
                                                   config_data_width)),
        )
        self._setup_config()

    def name(self):
        return "PowerDomainConfigReg"

