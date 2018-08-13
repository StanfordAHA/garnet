from abc import ABC, abstractmethod
import magma


class Generator(ABC):
    class _PortReference:
        def __init__(self, owner, name, T):
            self._owner = owner
            self._name = name
            self._T = T
            self._ops = []

        # NOTE(rsetaluri): These are hacks!!
        def __getitem__(self, index):
            def _fn(obj):
                return type(obj).__getitem__(obj, index)
            clone = self.__clone()
            clone._ops.append(_fn)
            return clone

        def __getattr__(self, name):
            def _fn(obj):
                return getattr(obj, name)
            clone = self.__clone()
            clone._ops.append(_fn)
            return clone

        def __clone(self):
            clone = Generator._PortReference(self._owner, self._name, self._T)
            clone._ops = self._ops.copy()
            return clone

    def __init__(self):
        self.__generated = False
        self._ports = {}
        self.__wires = []

    def __getattr__(self, name):
        return self._ports[name]

    @abstractmethod
    def name(self):
        pass

    def add_port(self, name, T):
        assert name not in self._ports
        self._ports[name] = Generator._PortReference(self, name, T)

    def add_ports(self, **kwargs):
        for name, T in kwargs.items():
            self.add_port(name, T)

    def wire(self, port0, port1):
        assert isinstance(port0, Generator._PortReference)
        assert isinstance(port1, Generator._PortReference)
        self.__wires.append((port0, port1))

    def decl(self):
        io = []
        for name, port in self._ports.items():
            io += [name, port._T]
        return io

    def children(self):
        children = set()
        for ports in self.__wires:
            for port in ports:
                if port._owner == self:
                    continue
                children.add(port._owner)
        return children

    @staticmethod
    def __get_port(circ, name, ops):
        # NOTE(raj): This is a hack!!
        port = getattr(circ, name)
        for op in ops:
            port = op(port)
        return port

    def circuit(self):
        children = self.children()
        circuits = {}
        for child in children:
            circuits[child] = child.circuit()
        circ = magma.DefineCircuit(self.name(), *self.decl())
        instances = {}
        for child in children:
            instances[child] = circuits[child]()
        instances[self] = circ
        for port0, port1 in self.__wires:
            inst0 = instances[port0._owner]
            inst1 = instances[port1._owner]
            wire0 = Generator.__get_port(inst0, port0._name, port0._ops)
            wire1 = Generator.__get_port(inst1, port1._name, port1._ops)
            magma.wire(wire0, wire1)
        magma.EndCircuit()
        return circ
