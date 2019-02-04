from abc import ABC, abstractmethod
from ordered_set import OrderedSet
import magma
from common.collections import DotDict
from generator.port_reference import PortReference, PortReferenceBase
import warnings


class Generator(ABC):
    def __init__(self, name=None):
        """
        name: Set this parameter to override default name for instance
        """
        self.ports = DotDict()
        self.wires = []
        self.instance_name = name

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
        connection = self.__sort_ports(port0, port1)
        if connection not in self.wires:
            self.wires.append(connection)
        else:
            warnings.warn(f"skipping duplicate connection: "
                          f"{port0.qualified_name()}, "
                          f"{port1.qualified_name()}")

    def remove_wire(self, port0, port1):
        assert isinstance(port0, PortReferenceBase)
        assert isinstance(port1, PortReferenceBase)
        connection = self.__sort_ports(port0, port1)
        if connection in self.wires:
            self.wires.remove(connection)

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
                    kwargs = {}
                    if child.instance_name:
                        kwargs["name"] = child.instance_name
                    instances[child] = circuits[child](**kwargs)
                instances[self] = io
                for port0, port1 in self.wires:
                    inst0 = instances[port0.owner()]
                    inst1 = instances[port1.owner()]
                    wire0 = port0.get_port(inst0)
                    wire1 = port1.get_port(inst1)
                    magma.wire(wire0, wire1)

        return _Circ

    def __sort_ports(self, port0, port1):
        if id(port0) < id(port1):
            return (port0, port1)
        else:
            return (port1, port0)
