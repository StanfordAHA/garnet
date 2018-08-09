from abc import ABC, abstractmethod
import magma


class Generator(ABC):
    class _Port:
        def __init__(self, owner, name, T):
            self.owner = owner
            self.name = name
            self.T = T
            self.ops = []

        # NOTE(rsetaluri): These are hacks!!
        def __getitem__(self, index):
            clone = self.__clone()
            clone.ops.append(f"[{index}]")
            return clone

        def __getattr__(self, name):
            clone = self.__clone()
            clone.ops.append(f".{name}")
            return clone

        def __clone(self):
            clone = Generator._Port(self.owner, self.name, self.T)
            clone.ops = self.ops.copy()
            return clone

    def __init__(self):
        self.__generated = False
        self.__ports = {}
        self.__wires = []

    def __getattr__(self, name):
        return self.__ports[name]

    @abstractmethod
    def name(self):
        pass

    def add_port(self, name, T):
        assert name not in self.__ports
        self.__ports[name] = Generator._Port(self, name, T)

    def add_ports(self, **kwargs):
        for name, T in kwargs.items():
            self.add_port(name, T)

    def wire(self, port0, port1):
        assert isinstance(port0, Generator._Port)
        assert isinstance(port1, Generator._Port)
        self.__wires.append((port0, port1))

    def decl(self):
        io = []
        for name, port in self.__ports.items():
            io += [name, port.T]
        return io

    def children(self):
        children = set()
        for ports in self.__wires:
            for port in ports:
                if port.owner == self:
                    continue
                children.add(port.owner)
        return children

    @staticmethod
    def __get_port(circ, name, ops):
        # NOTE(raj): This is a hack!!
        src = f"circ.{name}{''.join(ops)}"
        port = eval(src, None, {"circ": circ})
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
            inst0 = instances[port0.owner]
            inst1 = instances[port1.owner]
            wire0 = Generator.__get_port(inst0, port0.name, port0.ops)
            wire1 = Generator.__get_port(inst1, port1.name, port1.ops)
            magma.wire(wire0, wire1)
        magma.EndCircuit()
        return circ
