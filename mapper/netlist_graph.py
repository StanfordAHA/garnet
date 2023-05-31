import math
import os
import re
import json

class Node:
    def __init__(self, node_type, node_name, node_id):
        self.node_type = node_type
        self.node_name = node_name
        self.node_id = node_id
        self.sinks = []
        self.sources = []
        self.x = None
        self.y = None
    def add_sink(self, node):
        if node not in self.sinks:
            self.sinks.append(node)
    def add_source(self, node):
        if node not in self.sources:
            self.sources.append(node)
    def remove_sink(self, node):
        if node in self.sinks:
            self.sinks.remove(node)
    def remove_source(self, node):
        if node in self.sources:
            self.sources.remove(node)


class NetlistGraph:
    def __init__(self, info):
        self.nodes = []
        self.name_to_node = {}
        self.pe_nodes= []
        self.mem_nodes = []
        self.pond_nodes = []
        self.reg_nodes = []
        self.io_nodes = []
        for edge_name, edge in info["netlist"].items():
            edge_node_name = []
            edge_node_list = []
            for edge_node in edge:
                if edge_node[0] not in self.name_to_node.keys():
                    node = Node(edge_node[0][0], edge_node[0], info["id_to_name"][edge_node[0]])
                    self.name_to_node[edge_node[0]] = node
                    self.nodes.append(node)
                    if edge_node[0][0] == 'p':
                        self.pe_nodes.append(node)
                    if edge_node[0][0] == 'm':
                        self.mem_nodes.append(node)
                    if edge_node[0][0] == 'M':
                        self.pond_nodes.append(node)
                    if edge_node[0][0] == 'r':
                        self.reg_nodes.append(node)
                    if edge_node[0][0] == 'i' or edge_node[0][0] == 'I':
                        self.io_nodes.append(node)
                node = self.name_to_node[edge_node[0]]
                edge_node_name.append(edge_node[0])
                edge_node_list.append(node)
            source_node = None
            sink_node = []
            for _ in range(len(edge_node_list)):
                if _ == 0:
                    source_node = edge_node_list[_]
                else:
                    sink_node.append(edge_node_list[_])
            for node in sink_node:
                source_node.add_sink(node)
                node.add_source(source_node)
        # merge pond connections into pe
        for node in self.pond_nodes:
            assert(len(node.sources) == 1) and (len(node.sinks) == 1)
            pond_source = node.sources[0]
            pond_sink = node.sinks[0]
            pond_source.remove_sink(node)
            pond_source.add_sink(pond_sink)
            pond_sink.remove_source(node)
            pond_sink.add_source(pond_source)
    
    def generate_tile_conn(self, app_dir):
        with open(app_dir + "/tile_conn.txt", "w") as f:
            for node in self.nodes:
                f.write(80 * "=" + "\n")
                f.write("node name\tnode id\tnode source length\tnode sink length\n")
                f.write("{}\t{}\t{}\t{}\n\n".format(node.node_name, node.node_id, len(node.sources), len(node.sinks)))
                f.write("source node name\tsource node id\n")
                for snode in node.sources:
                    f.write("{}\t{}\n".format(snode.node_name, snode.node_id))
                f.write("sink node name\tsink node id\n")
                for sinode in node.sinks:
                    f.write("{}\t{}\n".format(sinode.node_name, sinode.node_id))

    def generate_tile_id(self, app_dir):
        with open(app_dir + "/tile_id.txt", "w") as f:
            for node in self.nodes:
                f.write("{}\t{}\t{}\t{}\n".format(node.node_name, node.node_id, len(node.sources), len(node.sinks)))

    def get_in_ub_latency(self, app_dir):
        ub_latency = {}
        for node in self.nodes:
            if "ub" in node.node_id and "output" not in node.node_id and "reg" not in node.node_id:
                node_ub_name = node.node_id.split("$")[0]
                if node_ub_name not in ub_latency:
                    ub_latency[node_ub_name] = {}
                if re.search(r'BANK_(\d+)', node.node_id):
                    ub_bank_id = re.search(r'BANK_(\d+)', node.node_id).group(1)
                ub_bank_latency = self.count_reg_sources(node)
                ub_latency[node_ub_name][ub_bank_id] = {"bank": int(ub_bank_id), "latency": ub_bank_latency}
        if "IO2MEM_REG_CHAIN" in os.environ:
            with open(app_dir + "/ub_latency.json", "w") as f:
                f.write(json.dumps(ub_latency, indent=4))
    
    def count_reg_sources(self, node):
        num_reg_sources = 0
        for source_node in node.sources:
            if "r" in source_node.node_name:
                num_reg_sources += 1
            num_reg_sources += self.count_reg_sources(source_node)
        return num_reg_sources

    def remove_mem_reg_tree(self):
        for mem_node in self.mem_nodes:
            for sink_node in mem_node.sinks[:]:
                if sink_node.node_type == 'r':
                    self._remove_reg_node(sink_node, mem_node)

    def _remove_reg_node(self, reg_node, source_node):
        for sink_node in reg_node.sinks[:]:
            if sink_node.node_type == 'r':
                self._remove_reg_node(sink_node, source_node)
            else:
                source_node.add_sink(sink_node)
                sink_node.add_source(source_node)
        reg_node.remove_sink(sink_node)
        source_node.remove_sink(reg_node)

    def manualy_place_resnet(self, app_dir):
        HALIDE_GEN_ARGS = os.environ.get("HALIDE_GEN_ARGS")
        k_oc_match = re.search(r'k_oc=(\d+)', HALIDE_GEN_ARGS)
        k_ic_match = re.search(r'k_ic=(\d+)', HALIDE_GEN_ARGS)
        assert k_oc_match, "No k_oc in HALIDE_GEN_ARGS. Please turn off MANUAL_PLACER or re-define HALIDE_GEN_ARGS for resnet."
        assert k_ic_match, "No k_ic in HALIDE_GEN_ARGS. Please turn off MANUAL_PLACER or re-define HALIDE_GEN_ARGS for resnet."
        k_oc = int(k_oc_match.group(1))
        k_ic = int(k_ic_match.group(1))
        input_mem = []
        output_mem = []

        # extract input mem from bottom to top
        for node in self.mem_nodes:
            if len(node.sinks) == k_oc and "mul" in node.sinks[0].node_id and "add" not in node.sinks[0].node_id:
                input_mem.append(node)
                break
        next_pe = input_mem[0].sinks[0].sinks[0]
        while True:
            for node in next_pe.sources:
                if "m" in node.node_name:
                    input_mem.append(node)
            next_pe = next_pe.sinks[0]
            if "mul" not in next_pe.node_id:
                for node in next_pe.sinks[0].sources:
                    if "m" in node.node_name:
                        input_mem.append(node)
                break

        # place input mem from bottom to top
        input_mem_x = round(k_oc / 4) * 4 - 1
        input_mem_y = k_ic
        for node in input_mem:
            (node.x, node.y) = (input_mem_x, input_mem_y)
            input_mem_y -= 1

        # extract output mem 
        # check whether have mem chaining
        mem_chain = False
        for node in self.mem_nodes:
            for snode in node.sources:
                if "m" in snode.node_name:
                    mem_chain = True
                    break
            if mem_chain:
                break
        # add output mem to list
        for node in self.mem_nodes:
            if mem_chain and len(node.sources) == 3:
                output_mem.append(node)
                for snode in node.sources:
                    if "m" in snode.node_name:
                        output_mem.append(snode)
            elif not mem_chain and len(node.sources) == 2:
                output_mem.append(node)

        # place output mem
        # starting from the first MEM column
        assert k_oc > 4, "k_oc is too small; please unset MANUAL_PLACER"
        output_mem_x = 3
        output_mem_y = 1
        if k_oc <= 14:
            for node in output_mem:
                (node.x, node.y) = (output_mem_x, output_mem_y)
                if output_mem_y < 2:
                    output_mem_y += 1
                elif output_mem_x == round(k_oc / 4) * 4 - 5 and output_mem_y == 2:
                    output_mem_x += 8
                    output_mem_y = 1
                else:
                    output_mem_x += 4
                    output_mem_y = 1
        else:
            for node in output_mem:
                (node.x, node.y) = (output_mem_x, output_mem_y)
                if output_mem_y < 2 or (output_mem_x == round(k_oc / 4) * 4 - 5 and output_mem_y < 4):
                    output_mem_y += 1
                elif output_mem_x != round(k_oc / 4) * 4 - 5:
                    output_mem_x += 4
                    output_mem_y = 1
                else:
                    output_mem_x += 8
                    output_mem_y = 1

        # place pe chains and const pes
        accum_pe = []
        const_pe = []
        pe_x = 1
        pe_y = 1
        for node in output_mem:
            for snode in node.sources:
                if "const" in snode.node_id:
                    (snode.x, snode.y) = (node.x - 3, node.y)
                    if node.y > 2:
                        (snode.x, snode.y) = (node.x + 1, node.y - 2)
                    const_pe.append(snode)
                elif "muladd" in snode.node_id:
                    next_pe = snode
                    (next_pe.x, next_pe.y) = (pe_x, pe_y)
                    pe_y += 1
                    while True:
                        for snext_pe in next_pe.sources:
                            if "p" in snext_pe.node_name:
                                if "add" in snext_pe.node_id and "mul" not in snext_pe.node_id:
                                    accum_pe.append(snext_pe)
                                (snext_pe.x, snext_pe.y) = (pe_x, pe_y)
                                if "muladd" in snext_pe.node_id:
                                    pe_y += 1
                                next_pe = snext_pe
                                break
                        if "mul" in next_pe.node_id and "add" not in next_pe.node_id:
                            pe_y = 1
                            break
            if (pe_x + 2) % 4 != 0:
                pe_x += 1
            else:
                pe_x += 3

        # place accum pes separately
        for _ in range(len(const_pe)):
            (accum_pe[_].x, accum_pe[_].y) = (const_pe[_].x, const_pe[_].y + 2)

        # place stencil mem
        glb_o_match = re.search(r'glb_o=(\d+)', HALIDE_GEN_ARGS)
        glb_o = int(glb_o_match.group(1)) if glb_o_match else None
        if not glb_o_match or glb_o <= 7:
            stencil_x = 3
            stencil_y = 4
            for node in self.mem_nodes:
                if len(node.sources) == 0:
                    (node.x, node.y) = (stencil_x, stencil_y)
                    if stencil_x == round(k_oc / 4) * 4 - 5:
                        stencil_x += 8
                    else:
                        stencil_x += 4
        else:
            stencil_x = 3
            stencil_y = 5
            for node in self.mem_nodes:
                if len(node.sources) == 0:
                    (node.x, node.y) = (stencil_x, stencil_y)
                    if stencil_x == round(k_oc / 4) * 4 - 5:
                        if stencil_y == 5:
                            stencil_y += 1
                        else: 
                            stencil_x += 8
                            stencil_y = 5
                    else:
                        stencil_x += 4

        # place IO tiles
        # currently hardcoded
        weight_IO_idx = [0, 4, 8, 12, 16, 20, 24, 28]
        ifmap_IO_idx = [2, 6, 10, 14, 18, 22, 26, 30]
        output_IO_idx = [3, 7, 11, 15, 19, 23, 27, 31]
        weight_IO = []
        ifmap_IO = []
        output_IO = []
        stencil_IO = []

        for node in self.io_nodes:
            if "io16in_kernel_host_stencil_clkwrk" in node.node_id:
                weight_IO.append(node)
            elif "io16in_input_host_stencil_clkwrk" in node.node_id:
                ifmap_IO.append(node)
            elif "io16_hw_output_stencil_clkwrk" in node.node_id:
                output_IO.append(node)
            else:
                stencil_IO.append(node)
        
        for _ in range(len(weight_IO)):
            weight_IO[_].x = weight_IO_idx[_]
            weight_IO[_].y = 0
        for _ in range(len(ifmap_IO)):
            ifmap_IO[_].x = ifmap_IO_idx[_]
            ifmap_IO[_].y = 0
        for _ in range(len(output_IO)):
            output_IO[_].x = output_IO_idx[_]
            output_IO[_].y = 0
        for _ in range(len(stencil_IO)):
            stencil_IO[_].x = output_IO_idx[_]
            stencil_IO[_].y = 0 

        # write position info into file
        with open(app_dir + "/manual.place", "w") as f:
            for node in self.nodes:
                if node.x is not None:
                    f.write("{} {} {}\n".format(node.node_name, node.x, node.y))