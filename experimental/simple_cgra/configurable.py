import generator
import magma
from config_register import ConfigRegister
from port_reference import PortReferenceBase


def ConfigurationType(addr_width, data_width):
    return magma.Tuple(config_addr=magma.Bits(addr_width),
                       config_data=magma.Bits(data_width))


class ConfigurationPortReference(PortReferenceBase):
    def __init__(self, width, parent):
        super().__init__()
        self._width = width
        self._parent = parent
        self._register = None
        self._underlying = None
        self._global_addr = None
        self._finalized = False

    def finalize(self, addr, global_addr, addr_width,
                 data_width, config_en):
        assert not self._finalized
        self._global_addr = global_addr
        self._register = ConfigRegister(
            self._width, addr_width, data_width, addr, config_en)
        self._underlying = self._register.O
        self._finalized = True

    def get_port(self, inst):
        port = self._underlying.get_port(inst)
        for op in self._ops:
            port = op(port)
        return port

    def owner(self):
        return self._underlying.owner()

    def clone(self):
        assert not self._finalized
        clone = ConfigurationPortReference(self._width, self._parent)
        clone._register = self._register
        clone._underlying = self._underlying
        clone._global_addr = self._global_addr
        clone._ops = self._ops.copy()
        return clone

    def base_type(self):
        return self._underlying.base_type()


class Configurable(generator.Generator):
    def __init__(self):
        super().__init__()

        self.registers = {}

    def __getattr__(self, name):
        if name in self.registers:
            return self.registers[name]
        return super().__getattr__(name)

    def add_config(self, name, width):
        assert name not in self.ports
        assert name not in self.registers
        register = ConfigurationPortReference(width, self)
        self.registers[name] = register

    def add_configs(self, **kwargs):
        for name, width in kwargs.items():
            self.add_config(name, width)
