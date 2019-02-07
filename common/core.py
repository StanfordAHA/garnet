from abc import abstractmethod
from generator.configurable import Configurable, ConfigurationType
from generator.from_magma import FromMagma
from generator.generator import Generator
import magma
from typing import List, Union
import mantle


class Core(Configurable):
    @abstractmethod
    def inputs(self):
        pass

    @abstractmethod
    def outputs(self):
        pass

    def features(self) -> List[Union["Core", "CoreFeature"]]:
        return [self]


class CoreFeature(Generator):
    def __init__(self,
                 parent_core: "Core",
                 index: int,
                 config_addr_width: int = 8,
                 config_data_width: int = 32):
        super().__init__()
        self.add_ports(
            config=magma.In(ConfigurationType(config_addr_width,
                                              config_data_width)),
            read_config_data=magma.Out(magma.Bits(config_data_width)),
            read_config_data_in=magma.In(magma.Bits(config_data_width)),
            config_en=magma.Out(magma.Bit),
            config_out=magma.Out(ConfigurationType(config_addr_width,
                                                   config_data_width))
        )

        self.__index = index
        self.__parent = parent_core
        self.__or_gate = FromMagma(mantle.DefineOr(2, 1))
        self.wire(self.__or_gate.ports.I0, self.ports.config.read)
        self.wire(self.__or_gate.ports.I1, self.ports.config.write)
        self.wire(self.ports.config_en, self.__or_gate.ports.O[0])
        self.wire(self.ports.read_config_data_in, self.ports.read_config_data)

        # pass through config
        self.wire(self.ports.config, self.ports.config_out)

    def name(self):
        return f"{self.__parent.name()}_FEATURE_{self.__index}"

    def parent(self):
        return self.__parent

    def index(self):
        return self.__index
