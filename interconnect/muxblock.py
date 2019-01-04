from abc import ABC, abstractmethod
from .graph import NodeABC, Node, PortNode, SwitchBoxNode
from generator import generator
from common.mux_wrapper import MuxWrapper


class MuxBlockABC(ABC, generator):
    def __init__(self, node: NodeABC):
        if not isinstance(node, NodeABC):
            raise ValueError(node, NodeABC.__name__)

        super(generator).__init__()
        self.node = node
        self.x = node.x
        self.y = node.y
        self.width = node.width

    @abstractmethod
    def name(self):
        pass


class MuxBlock(MuxBlockABC):
    def __init__(self, node: Node):
        super().__init__(node)
        self.mux = self.__create_mux()

    def __create_mux(self) -> MuxWrapper:
        conn_in = self.node.get_conn_in()
        height = len(conn_in)
        return MuxWrapper(height, self.node.width)

    @abstractmethod
    def name(self):
        pass


class ConnectionBox(MuxBlock):
    def __init__(self, node: PortNode):
        if not isinstance(node, PortNode):
            raise ValueError(node, PortNode.__name__)
        super().__init__(node)

    def name(self):
        return str(self.node)


class SwitchBoxMux(MuxBlock):
    def __init__(self, node: SwitchBoxNode):
        if not isinstance(node, SwitchBoxNode):
            raise ValueError(node, PortNode.__name__)
        super().__init__(node)

    def name(self):
        return str(self.node)
