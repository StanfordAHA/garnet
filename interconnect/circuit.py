"""
This is a layer build on top of Cyclone
"""
from abc import abstractmethod
from .cyclone import NodeABC, Node, PortNode, SwitchBoxNode, RegisterNode
from generator import generator as generator
from common.mux_wrapper import MuxWrapper
from typing import Union, List


class Circuit(generator.Generator):
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def realize(self) -> Union[generator.Generator, List[generator.Generator]]:
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

    def connect(self, other: "Connectable"):
        if not isinstance(other, Connectable):
            raise ValueError(other, Connectable.__name__)
        self.node.add_edge(other.node)

    def disconnect(self, other: "Connectable"):
        if not isinstance(other, Connectable):
            raise ValueError(other, Connectable.__name__)
        self.node.remove_edge(other.node)

    def is_connected(self, other: "Connectable"):
        return other.node in self.node


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

    def realize(self):
        self.__create_mux()
        # make connections
        # because it's a digraph, we create based on the edge directions
        for node in self.node:
            input_port = self.mux.ports.O
            idx = node.get_conn_in().index(self.node)
            # create the mux if not exist
            if node.circuit.mux is None:
                node.circuit.__create_mux()
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

    def realize(self):
        return None


class RegisterCircuit(Connectable):
    def __init__(self, node: RegisterNode):
        if not isinstance(node, RegisterNode):
            raise ValueError(node, RegisterNode.__name__)
        super().__init__(node)

    def name(self):
        return self.create_name(str(self.node))

    def realize(self):
        # TODO: add register magma circuit
        return None
