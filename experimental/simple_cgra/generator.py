from abc import ABC, abstractmethod
import magma


class Generator(ABC):
    class _Port:
        def __init__(self, name, T):
            self.name = name
            self.T = T

    def __init__(self):
        self.__generated = False
        self.__ports = {}
        self.__wires = []

    @abstractmethod
    def name(self):
        pass

    def add_port(self, name, T):
        assert name not in self.__ports
        self.__ports[name] = Generator._Port(name, T)

    def add_ports(self, **kwargs):
        for name, T in kwargs.items():
            self.add_port(name, T)

    def wire(self, self_port, other, other_port):
        self.__wires.append((self_port, other, other_port))

    def decl(self):
        io = []
        for name, port in self.__ports.items():
            io += [name, port.T]
        return io

    def children(self):
        children = {}
        for (self_port, other, other_port) in self.__wires:
            if self == other:
                continue
            if other not in children:
                children[other] = []
            children[other] = [(self_port, other_port)]
        return children

    @staticmethod
    def __get_port(circ, port_str):
        # NOTE(rsetaluri): This is a hack!!
        src = f"circ.{port_str}"
        port = eval(src, None, {"circ": circ})
        return port

    def circuit(self):
        children = self.children()
        circ = magma.DefineCircuit(self.name(), *self.decl())
        for child, wires in children.items():
            child_circ = child.circuit()
            child_inst = child_circ()
            for self_port, child_port in wires:
                wire0 = Generator.__get_port(circ, self_port)
                wire1 = Generator.__get_port(child_inst, child_port)
                magma.wire(wire0, wire1)
        magma.EndCircuit()
        return circ


def wire(module0, port0, module1, port1):
    pass
