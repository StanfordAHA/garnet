import generator
import magma
from config_register import ConfigRegister


def ConfigurationType(addr_width, data_width):
    return magma.Tuple(config_addr=magma.Bits(addr_width),
                       config_data=magma.Bits(data_width))


class Configurable(generator.Generator):
    def __init__(self, addr_width, data_width):
        super().__init__()

        self.registers = {}
        self.addr_width = addr_width
        self.data_width = data_width

        self.add_ports(
            clk=magma.In(magma.Clock),
            config_addr=magma.In(magma.Bits(self.addr_width)),
            config_data=magma.In(magma.Bits(self.data_width)),
        )

    def __getattr__(self, name):
        if name in self.registers:
            return self.registers[name].O
        return super().__getattr__(name)

    def add_config(self, name, width):
        assert name not in self.ports
        assert name not in self.registers
        register = ConfigRegister(width, self.addr_width, self.data_width)
        self.wire(self.config_addr, register.addr_in)
        self.wire(self.config_data, register.data_in)
        self.registers[name] = register

    def add_configs(self, **kwargs):
        for name, width in kwargs.items():
            self.add_config(name, width)
