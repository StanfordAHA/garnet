import generator
import magma
from config_register import ConfigRegister
from port_reference import PortReferenceBase


def ConfigurationType(addr_width, data_width):
    return magma.Tuple(config_addr=magma.Bits(addr_width),
                       config_data=magma.Bits(data_width))


class Configurable(generator.Generator):
    def __init__(self):
        super().__init__()

        self.registers = {}

    def __getattr__(self, name):
        if name in self.registers:
            return self.registers[name].O
        return super().__getattr__(name)

    def add_config(self, name, width):
        assert name not in self.ports
        assert name not in self.registers
        register = ConfigRegister(width, self)
        self.registers[name] = register

    def add_configs(self, **kwargs):
        for name, width in kwargs.items():
            self.add_config(name, width)
