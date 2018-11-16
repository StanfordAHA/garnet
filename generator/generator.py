from abc import ABC, abstractmethod
from ordered_set import OrderedSet
import magma
from common.collections import DotDict
from generator.port_reference import PortReference, PortReferenceBase


class Generator(ABC):
    def __init__(self):
        self.ports = DotDict()
        self.wires = []

    @abstractmethod
    def name(self):
        pass

    def add_port(self, name, T):
        if name in self.ports:
            raise ValueError(f"{name} is already a port")
        self.ports[name] = PortReference(self, name, T)

    def add_ports(self, **kwargs):
        for name, T in kwargs.items():
            self.add_port(name, T)

    def wire(self, port0, port1):
        assert isinstance(port0, PortReferenceBase)
        assert isinstance(port1, PortReferenceBase)
        self.wires.append((port0, port1))

    def remove_wire(self, port0, port1):
        assert isinstance(port0, PortReferenceBase)
        assert isinstance(port1, PortReferenceBase)
        if (port0, port1) in self.wires:
            self.wires.remove((port0, port1))
        elif (port1, port0) in self.wires:
            self.wires.remove((port1, port0))

    def decl(self):
        io = []
        for name, port in self.ports.items():
            io += [name, port.base_type()]
        return io

    def children(self):
        children = OrderedSet()
        for ports in self.wires:
            for port in ports:
                if port.owner() == self:
                    continue
                children.add(port.owner())
        return children

    def circuit(self):
        children = self.children()
        circuits = {}
        for child in children:
            circuits[child] = child.circuit()

        class _Circ(magma.Circuit):
            name = self.name()
            IO = self.decl()

            @classmethod
            def definition(io):
                instances = {}
                for child in children:
                    instances[child] = circuits[child]()
                instances[self] = io
                for port0, port1 in self.wires:
                    inst0 = instances[port0.owner()]
                    inst1 = instances[port1.owner()]
                    wire0 = port0.get_port(inst0)
                    wire1 = port1.get_port(inst1)
                    magma.wire(wire0, wire1)

        return _Circ
