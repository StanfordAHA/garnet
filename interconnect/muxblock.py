from abc import ABC, abstractmethod
from .graph import NodeABC, Node, PortNode, SwitchBoxNode
from generator import generator
from common.mux_wrapper import MuxWrapper


class MuxBlockABC(ABC):
    def __init__(self, node: NodeABC):
        if not isinstance(node, NodeABC):
            raise ValueError(node, NodeABC.__name__)

        super(generator).__init__()
        self.node = node
        self.x = node.x
        self.y = node.y
        self.width = node.width

        # set the node's mux
        self.node.mux_block = self

    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def connect(self, other: "MuxBlockABC"):
        pass

    @abstractmethod
    def create_mux(self) -> MuxWrapper:
        pass


class MuxBlock(MuxBlockABC, generator):
    WIRE_DELAY = 0

    def __init__(self, node: Node):
        super(MuxBlockABC, self).__init__(node)
        super(generator, self).__init__()
        self.mux: MuxWrapper = None

    def __create_mux(self) -> MuxWrapper:
        if self.mux is None:
            conn_in = self.node.get_conn_in()
            height = len(conn_in)
            self.mux = MuxWrapper(height, self.node.width)
            return self.mux

    def create_mux(self):
        self.__create_mux()
        # make connections
        # because it's a digraph, we create based on the edge directions
        for idx, node in enumerate(self.node):
            if node.mux_block.mux is None:
                node.mux_block.__create_mux()
            input_port = self.mux.ports.O
            output_port = node.mux_block.mux.ports.I[idx]
            self.wire(input_port, output_port)
        return self.mux

    @abstractmethod
    def name(self):
        pass

    def connect(self, other: "MuxBlock"):
        # making sure the other mux's node is not pointing to None
        assert other.node.mux_block is not None
        # making connection to the graph first
        self.node.add_edge(other.node, self.WIRE_DELAY)

    @staticmethod
    def create_name(name: str):
        tokens = " (),"
        for t in tokens:
            name = name.replace(t, "_")
        return name


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
