from abc import ABC
from kratos import clog2
import os


class RdlNode(ABC):
    def __init__(self, name="", desc="", property=[]):
        self.name = name
        self._desc = desc
        self.property = property
        self.children = []

    @property
    def desc(self):
        return self._desc

    @desc.setter
    def desc(self, value):
        self._desc = value


class RdlNonLeafNode(RdlNode):
    def __init__(self, name="", desc="", size=1, property=[]):
        super().__init__(name=name, desc=desc, property=property)
        self.size = size

    def add_child(self, child):
        self.children.append(child)

    def add_children(self, children):
        self.children += children


class AddrMap(RdlNonLeafNode):
    type = "addrmap"

    def __init__(self, name, size=1):
        super().__init__(name=name, size=size)
        self.regwidth = 32
        self.accesswidth = 32
        self.property = ["addressing = compact",
                         "default regwidth = 32",
                         "default sw = rw",
                         "default hw = r"]


class RegFile(RdlNonLeafNode):
    type = "regfile"

    def __init__(self, name, size=1):
        super().__init__(name=name, size=size)


class Reg(RdlNonLeafNode):
    type = "reg"

    def __init__(self, name, size=1):
        super().__init__(name=name, size=size)


class Field(RdlNode):
    type = "field"

    def __init__(self, name, width=1, property=[]):
        super().__init__(name=name, property=property)
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
        if isinstance(rdl_node, RdlNonLeafNode) and rdl_node.size > 1:
            for i in range(rdl_node.size):
                expr += "\t" * level
                if isinstance(rdl_node, AddrMap):
                    expr += f"{rdl_node.type} {rdl_node.name}{{\n"
                else:
                    expr += f"{rdl_node.type} {{\n"

                expr += "\t" * (level + 1)
                expr += f"name = \"{rdl_node.name}\";\n"

                if rdl_node.desc:
                    expr += "\t" * (level + 1)
                    expr += f"desc = \"{rdl_node.desc}\";\n"

                for e in rdl_node.property:
                    expr += "\t" * (level + 1)
                    expr += f"{e};\n"

                if not isinstance(rdl_node, Field):
                    for child in rdl_node.children:
                        expr += self._get_rdl_node_expr(child, level + 1)

                elab_name = rdl_node.name + f"_{i}"
                if isinstance(rdl_node, Field):
                    expr += f"\t" * level
                    expr += f"}} {elab_name}[{rdl_node.width}] = 0;\n"
                elif not isinstance(rdl_node, AddrMap):
                    expr += f"\t" * level
                    expr += f"}} {elab_name};\n"
                else:
                    expr += f"\t" * level
                    expr += f"}};\n"
                expr += "\n"
        else:
            expr += "\t" * level
            if isinstance(rdl_node, AddrMap):
                expr += f"{rdl_node.type} {rdl_node.name}{{\n"
            else:
                expr += f"{rdl_node.type} {{\n"

            expr += "\t" * (level + 1)
            expr += f"name = \"{rdl_node.name}\";\n"

            if rdl_node.desc:
                expr += "\t" * (level + 1)
                expr += f"desc = \"{rdl_node.desc}\";\n"

            for e in rdl_node.property:
                expr += "\t" * (level + 1)
                expr += f"{e};\n"

            if not isinstance(rdl_node, Field):
                for child in rdl_node.children:
                    expr += self._get_rdl_node_expr(child, level + 1)

            elab_name = rdl_node.name
            if isinstance(rdl_node, Field):
                expr += f"\t" * level
                expr += f"}} {elab_name}[{rdl_node.width}] = 0;\n"
            elif not isinstance(rdl_node, AddrMap):
                expr += f"\t" * level
                expr += f"}} {elab_name};\n"
            else:
                expr += f"\t" * level
                expr += f"}};\n"
            expr += "\n"

        return expr


def gen_global_buffer_rdl(name, params):
    addr_map = AddrMap(name)

    # Data Network Ctrl Register
    data_network_ctrl = Reg("data_network")
    tile_connected_f = Field("tile_connected", 1)
    strm_latency_f = Field("latency", params.latency_width)
    data_network_ctrl.add_children([tile_connected_f, strm_latency_f])
    addr_map.add_child(data_network_ctrl)

    # Pcfg Network Ctrl Register
    pcfg_network_ctrl = Reg("pcfg_network")
    pcfg_network_ctrl.add_children([Field("tile_connected", 1),
                                    Field("latency", params.latency_width)])
    addr_map.add_child(pcfg_network_ctrl)

    # Store DMA Ctrl
    st_dma_ctrl_r = Reg("st_dma_ctrl")
    st_dma_mode_f = Field("mode", 2)
    st_dma_ctrl_r.add_child(st_dma_mode_f)
    st_dma_use_valid_f = Field("use_valid", 1)
    st_dma_ctrl_r.add_child(st_dma_use_valid_f)
    st_dma_data_mux_f = Field("data_mux", 2)
    st_dma_ctrl_r.add_child(st_dma_data_mux_f)
    st_dma_num_repeat_f = Field("num_repeat", clog2(params.queue_depth) + 1)
    st_dma_ctrl_r.add_child(st_dma_num_repeat_f)
    addr_map.add_child(st_dma_ctrl_r)

    # Store DMA Header
    if params.queue_depth == 1:
        st_dma_header_rf = RegFile(f"st_dma_header_0", size=params.queue_depth)
    else:
        st_dma_header_rf = RegFile(f"st_dma_header", size=params.queue_depth)

    # dim reg
    dim_r = Reg(f"dim")
    dim_f = Field(f"dim", width=clog2(params.loop_level) + 1)
    dim_r.add_child(dim_f)
    st_dma_header_rf.add_child(dim_r)

    # start_addr reg
    start_addr_r = Reg(f"start_addr")
    start_addr_f = Field(f"start_addr", width=params.glb_addr_width)
    start_addr_r.add_child(start_addr_f)
    st_dma_header_rf.add_child(start_addr_r)

    # cycle_start_addr reg
    cycle_start_addr_r = Reg(f"cycle_start_addr")
    cycle_start_addr_f = Field(f"cycle_start_addr", width=params.glb_addr_width)
    cycle_start_addr_r.add_child(cycle_start_addr_f)
    st_dma_header_rf.add_child(cycle_start_addr_r)

    # num_word reg
    range_r = Reg(f"range", size=params.loop_level)
    range_f = Field("range", width=params.axi_data_width)
    range_r.add_child(range_f)
    stride_r = Reg(f"stride", size=params.loop_level)
    stride_f = Field("stride", width=params.axi_data_width)
    stride_r.add_child(stride_f)
    cycle_stride_r = Reg(f"cycle_stride", size=params.loop_level)
    cycle_stride_f = Field("cycle_stride", width=params.axi_data_width)
    cycle_stride_r.add_child(cycle_stride_f)
    st_dma_header_rf.add_child(range_r)
    st_dma_header_rf.add_child(stride_r)
    st_dma_header_rf.add_child(cycle_stride_r)

    addr_map.add_child(st_dma_header_rf)

    # Load DMA Ctrl
    ld_dma_ctrl_r = Reg("ld_dma_ctrl")
    ld_dma_mode_f = Field("mode", 2)
    ld_dma_ctrl_r.add_child(ld_dma_mode_f)
    ld_dma_use_valid_f = Field("use_valid", 1)
    ld_dma_ctrl_r.add_child(ld_dma_use_valid_f)
    ld_dma_data_mux_f = Field("data_mux", 2)
    ld_dma_ctrl_r.add_child(ld_dma_data_mux_f)
    ld_dma_num_repeat_f = Field("num_repeat", clog2(params.queue_depth) + 1)
    ld_dma_ctrl_r.add_child(ld_dma_num_repeat_f)
    addr_map.add_child(ld_dma_ctrl_r)

    # Load DMA Header
    if params.queue_depth == 1:
        ld_dma_header_rf = RegFile(f"ld_dma_header_0", size=params.queue_depth)
    else:
        ld_dma_header_rf = RegFile(f"ld_dma_header", size=params.queue_depth)

    # dim reg
    dim_r = Reg(f"dim")
    dim_f = Field(f"dim", width=clog2(params.loop_level) + 1)
    dim_r.add_child(dim_f)
    ld_dma_header_rf.add_child(dim_r)

    # start_addr reg
    start_addr_r = Reg(f"start_addr")
    start_addr_f = Field(f"start_addr", width=params.glb_addr_width)
    start_addr_r.add_child(start_addr_f)
    ld_dma_header_rf.add_child(start_addr_r)

    # cycle_start_addr reg
    cycle_start_addr_r = Reg(f"cycle_start_addr")
    cycle_start_addr_f = Field(f"cycle_start_addr", width=params.glb_addr_width)
    cycle_start_addr_r.add_child(cycle_start_addr_f)
    ld_dma_header_rf.add_child(cycle_start_addr_r)

    # num_word reg
    range_r = Reg(f"range", size=params.loop_level)
    range_f = Field("range", width=params.axi_data_width)
    range_r.add_child(range_f)
    stride_r = Reg(f"stride", size=params.loop_level)
    stride_f = Field("stride", width=params.axi_data_width)
    stride_r.add_child(stride_f)
    cycle_stride_r = Reg(f"cycle_stride", size=params.loop_level)
    cycle_stride_f = Field("cycle_stride", width=params.axi_data_width)
    cycle_stride_r.add_child(cycle_stride_f)
    ld_dma_header_rf.add_child(range_r)
    ld_dma_header_rf.add_child(stride_r)
    ld_dma_header_rf.add_child(cycle_stride_r)

    addr_map.add_child(ld_dma_header_rf)

    # Pcfg DMA Ctrl
    pcfg_dma_ctrl_r = Reg("pcfg_dma_ctrl")
    pcfg_dma_mode_f = Field("mode", 1)
    pcfg_dma_ctrl_r.add_child(pcfg_dma_mode_f)
    addr_map.add_child(pcfg_dma_ctrl_r)

    # Pcfg DMA Header RegFile
    pcfg_dma_header_rf = RegFile("pcfg_dma_header")
    # start_addr reg
    start_addr_r = Reg(f"start_addr")
    start_addr_f = Field(f"start_addr", width=params.glb_addr_width)
    start_addr_r.add_child(start_addr_f)
    pcfg_dma_header_rf.add_child(start_addr_r)
    # num cfg reg
    num_cfg_r = Reg(f"num_cfg")
    num_cfg_f = Field(f"num_cfg", width=params.max_num_cfg_width)
    num_cfg_r.add_child(num_cfg_f)
    pcfg_dma_header_rf.add_child(num_cfg_r)
    addr_map.add_child(pcfg_dma_header_rf)
    glb_rdl = Rdl(addr_map)

    return glb_rdl


def gen_glb_pio_wrapper(src_file, dest_file):
    os.system(f"sed '/\.\*/d' {src_file} > {dest_file}")  # nopep8
    return dest_file
