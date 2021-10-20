from global_buffer.design.global_buffer_parameter import gen_global_buffer_params
from abc import ABC


class RdlNode(ABC):
    def __init__(self, name="", desc=""):
        self.name = name
        self._desc = desc

    @property
    def desc(self):
        return self._desc

    @desc.setter
    def desc(self, value):
        self._desc = value


class RdlNonLeafNode(RdlNode):
    def __init__(self, name="", desc=""):
        super().__init__(name=name, desc=desc)
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def add_children(self, children):
        self.children += children


class Rdl:
    def __init__(self, name):
        self.name = name
        self.addrmap = None


class AddrMap(RdlNonLeafNode):
    type = "addrmap"

    def __init__(self, name):
        super().__init__(name=name)


class RegFile(RdlNonLeafNode):
    type = "regfile"

    def __init__(self, name):
        super().__init__(name=name)


class Reg(RdlNonLeafNode):
    type = "reg"

    def __init__(self, name):
        super().__init__(name=name)


class Field(RdlNode):
    type = "field"

    def __init__(self, name, width=1):
        super().__init__(name=name)
        self.width = width


class Rdl:
    def __init__(self, top):
        self.top = top

    def dump_rdl(self, filename):
        if not isinstance(self.top, AddrMap):
            raise Exception("Top RdlNode should be AddrMap Class")
        with open(filename, 'w') as f:
            f.write(self._get_rdl_node_expr(self.top))

    def _get_rdl_node_expr(self, rdl_node, level=0):
        expr = ""
        expr += "\t" * level
        expr += f"{rdl_node.type} {rdl_node.name} {{\n"

        expr += "\t" * (level + 1)
        expr += f"name = \"{rdl_node.name}\";\n"

        if rdl_node.desc:
            expr += "\t" * (level + 1)
            expr += f"desc = \"{rdl_node.desc}\";\n"

        if not isinstance(rdl_node, Field):
            for child in rdl_node.children:
                expr += self._get_rdl_node_expr(child, level+1)

        if isinstance(rdl_node, Field):
            expr += f"\t" * level
            expr += f"}} {rdl_node.name}[{rdl_node.width}] = 0;\n"
        elif not isinstance(rdl_node, AddrMap):
            expr += f"\t" * level
            expr += f"}} {rdl_node.name};\n"
        else:
            expr += f"\t" * level
            expr += f"}};\n"

        return expr


if __name__ == "__main__":
    params = gen_global_buffer_params()
    addr_map = AddrMap("glb")

    # Data Network Ctrl Register
    data_network_ctrl = Reg("data_network_ctrl")
    data_network_ctrl.add_children([Field("strm_f2g_mux", 2),
                                    Field("strm_g2f_mux", 2),
                                    Field("tile_connected", 1),
                                    Field("strm_latency", params.latency_width)])
    addr_map.add_child(data_network_ctrl)

    # Pcfg Network Ctrl Register
    pcfg_network_ctrl = Reg("pcfg_network_ctrl")
    pcfg_network_ctrl.add_children([Field("pcfg_tile_connected", 1),
                                    Field("pcfg_latency", params.latency_width)])
    addr_map.add_child(pcfg_network_ctrl)

    # # Store DMA Header
    # for i in range(params.queue_depth):
    #     st_dma_header_rf = RegFile(F"st_dma_header_rf")


    glb_rdl = Rdl(addr_map)
    glb_rdl.dump_rdl("temp.rdl")
