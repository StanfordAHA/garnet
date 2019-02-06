from abc import abstractmethod
from generator.configurable import Configurable, ConfigurationType
from generator.generator import Generator
import magma
from typing import List, Union


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
                 core_name: str,
                 index: int,
                 config_addr_width: int = 8,
                 config_data_width: int = 32):
        super().__init__()
        self.add_ports(
            config=magma.In(ConfigurationType(config_addr_width,
                                              config_data_width)),
            read_config_data=magma.Out(magma.Bits(config_data_width)),
            config_en=magma.In)

        self.__index = index
        self.__core_name = core_name

    def name(self):
        return f"{self.__core_name}_FEATURE_{self.__index}"
