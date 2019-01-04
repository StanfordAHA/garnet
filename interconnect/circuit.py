"""
This is a layer build on top of Cyclone
"""
from abc import abstractmethod
from .cyclone import NodeABC, Node, PortNode, SwitchBoxNode
from generator import generator as generator
from common.mux_wrapper import MuxWrapper


class Circuit(generator.Generator):
    @abstractmethod
    def name(self):
        pass

    @staticmethod
    def create_name(name: str):
        tokens = " (),"
        for t in tokens:
            name = name.replace(t, "_")
        return name


class Connectable(Circuit):
    def __init__(self, node: NodeABC):
        super().__init__()
        if not isinstance(node, NodeABC):
            raise ValueError(node, NodeABC.__name__)

        self.node = node
        self.node.circuit = self
        self.x = node.x
        self.y = node.y
        self.width = node.width

    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def create_circuit(self) -> Circuit:
        pass

    def connect(self, other: "Connectable"):
        if not isinstance(other, Connectable):
            raise ValueError(other, Connectable.__name__)
        self.node.add_edge(other.node)


class MuxBlock(Connectable):
    WIRE_DELAY = 0

    def __init__(self, node: Node):
        super().__init__(node)
        self.mux: MuxWrapper = None

    def __create_mux(self) -> MuxWrapper:
        if self.mux is None:
            conn_in = self.node.get_conn_in()
            height = len(conn_in)
            self.mux = MuxWrapper(height, self.node.width)
            return self.mux

    def create_circuit(self):
        self.__create_mux()
        # make connections
        # because it's a digraph, we create based on the edge directions
        for node in self.node:
            input_port = self.mux.ports.O
            idx = node.get_conn_in().index(self.node)
            output_port = node.circuit.mux.ports.I[idx]
            self.wire(input_port, output_port)
        return self.mux

    @abstractmethod
    def name(self):
        pass


class CB(MuxBlock):
    def __init__(self, node: PortNode):
        if not isinstance(node, PortNode):
            raise ValueError(node, PortNode.__name__)
        super().__init__(node)

    def name(self):
        return self.create_name(str(self.node))


class SwitchBoxMux(MuxBlock):
    def __init__(self, node: SwitchBoxNode):
        if not isinstance(node, SwitchBoxNode):
            raise ValueError(node, PortNode.__name__)
        super().__init__(node)

    def name(self):
        return self.create_name(str(self.node))


class EmptyCircuit(Connectable):
    """This one does not realize to any RTL circuit"""
    def __init__(self, node: PortNode):
        if not isinstance(node, PortNode):
            raise ValueError(node, PortNode.__name__)
        super().__init__(node)

    def name(self):
        return self.create_name(str(self.node))

    def create_circuit(self):
        return None
