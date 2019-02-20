import generator.generator as generator
from generator.port_reference import PortReferenceBase


class ConstGenerator(generator.Generator):
    def __init__(self):
        super().__init__()

    def name(self):
        return "ConstGenerator"

    def circuit(self):
        return lambda: None


class ConstPortReference(PortReferenceBase):
    def __init__(self, value):
        super().__init__()
        self._value = value
        self._owner = ConstGenerator()

    def get_port(self, inst):
        assert inst is None
        return self._value

    def owner(self):
        return self._owner

    def clone(self):
        clone = ConstPortReference(self._value)
        clone._ops = self._ops.copy()
        clone._owner = self._owner
        return clone

    def base_type(self):
        return type(self._value)


def Const(value):
    return ConstPortReference(value)
