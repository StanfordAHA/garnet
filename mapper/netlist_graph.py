import math
import os
import re
import json
import glob

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

        
    def count_input_latencies(self, output_mem, pe_node):
        def dfs_out_mem_to_pe(current_node, target_node):
            if current_node.node_id not in visited1:
                visited1.add(current_node.node_id)
                path1.append(current_node)
                if current_node.node_id == target_node.node_id:
                    return len(path1) - 1
                for source_node in current_node.sources:
                    if "m" not in source_node.node_name:
                        result = dfs_out_mem_to_pe(source_node, target_node)
                        if result is not None:
                            return result
                visited1.remove(current_node.node_id)
                path1.pop()
                
        def dfs_pe_to_in_mem(current_node):
            if current_node.node_id not in visited2:
                visited2.add(current_node.node_id)
                path2.append(current_node)

                if "input_cgra_stencil" in current_node.node_id and "m" in current_node.node_name:
                    return len(path2) - 2 

                for source_node in current_node.sources:
                    result = dfs_pe_to_in_mem(source_node)
                    if result is not None:
                        return result
                visited2.remove(current_node.node_id)
                path2.pop()

        def dfs_pe_to_out_mem(current_node):
            if current_node.node_id not in visited2:
                visited3.add(current_node.node_id)
                path3.append(current_node)

                if "output_cgra_stencil" in current_node.node_id and "m" in current_node.node_name:
                    return len(path3) - 2 

                for source_node in current_node.sources:
                    result = dfs_pe_to_out_mem(source_node)
                    if result is not None:
                        return result
                visited3.remove(current_node.node_id)
                path3.pop()

        visited1 = set()
        path1 = []
        latency_out_mem_to_pe = dfs_out_mem_to_pe(output_mem, pe_node)

        if latency_out_mem_to_pe:
            visited2 = set()
            path2 = []
            visited3 = set()
            path3 = []
            if "add_pipelined" in pe_node.node_id:
                latency_pe_to_out_mem = dfs_pe_to_out_mem(pe_node)
                return latency_out_mem_to_pe + latency_pe_to_out_mem
            else:
                latency_pe_to_in_mem = dfs_pe_to_in_mem(pe_node)
                return latency_out_mem_to_pe + latency_pe_to_in_mem

    def get_compute_kernel_latency(self, app_dir):
        kernel_latencies_file = glob.glob(f"{app_dir}/*_compute_kernel_latencies.json")[0]
        assert os.path.exists(kernel_latencies_file)
        f = open(kernel_latencies_file, "r")
        existing_kernel_latencies = json.load(f)

        kernel_latencies = existing_kernel_latencies
        for kernel, latency_dict in kernel_latencies.items():
            if "_glb_" in kernel:
                continue
            if "hcompute_output_cgra_stencil" in kernel:
                for kernel_port, d1 in latency_dict.items():
                    if "input_cgra_stencil" in kernel_port:
                        for port_num, d2 in d1.items():
                            pe_id = d2["pe_port"][0][0]
                            for node in self.pe_nodes:
                                if pe_id in node.node_id:
                                    pe_node = node
                            for mem_node in self.mem_nodes:
                                if "ub_output_cgra_stencil" in mem_node.node_id:
                                    if self.count_input_latencies(mem_node, pe_node):
                                        d2["latency"] = self.count_input_latencies(mem_node, pe_node)
                    elif "in2_output_cgra_stencil" in kernel_port:
                        for port_num, d2 in d1.items():
                            pe_id = d2["pe_port"][0][0]
                            for node in self.pe_nodes:
                                if pe_id in node.node_id:
                                    pe_node = node
                            for mem_node in self.mem_nodes:
                                if "ub_output_cgra_stencil" in mem_node.node_id:
                                    if self.count_input_latencies(mem_node, pe_node):
                                        d2["latency"] = self.count_input_latencies(mem_node, pe_node)
        fout = open(f"{app_dir}/updated_kernel_latencies.json", "w")
        fout.write(json.dumps(kernel_latencies, indent=4))


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
    
    def _find_root_node(self, start_node):
        """
        This function assumes there's only one source for each node,
        then it will find the root node of the start_node.
        """
        current_node = start_node
        while len(current_node.sources) > 0:
            current_node = current_node.sources[0]
        return current_node
    
    def _get_node_by_name(self, node_name):
        match_nodes = []
        for node in self.nodes:
            if node_name == node.node_name:
                match_nodes.append(node)
        assert len(match_nodes) > 0, "No node with the name {}".format(node_name)
        assert len(match_nodes) == 1, "There should be only one node with the name {}".format(node_name)
        return match_nodes[0]

    def _analyze_pe_chain(self, app_dir, dump=False):
        pe_chains = []
        for node in self.pe_nodes:
            if "mul_" in node.node_id:
                # found a start of a pe chain, start traching and record the chain
                new_pe_chain = {}
                pe_node = node
                # ---- [kernel_io] node name of the kernel IO node
                for source_node in node.sources:
                    root_node = self._find_root_node(start_node=source_node)
                    if "kernel" in root_node.node_id:
                        new_pe_chain["kernel_io"] = root_node.node_name
                        break
                # ---- [pe_chain] nodes names for each PE in the chain
                new_pe_chain["pe_chain"] = []
                current_node = node
                while current_node.node_type == "p":
                    new_pe_chain["pe_chain"].append(current_node.node_name)
                    current_node = current_node.sinks[0]
                # ---- [output_mem] node name for the accumulation output mem node
                output_mem_node = current_node
                new_pe_chain["output_mem"] = output_mem_node.node_name
                # ---- [const] node name for the constant node
                for source_node in output_mem_node.sources:
                    if "const" in source_node.node_id:
                        new_pe_chain["const"] = source_node.node_name
                        break
                # ---- [mem_chain_is_last] whether this pe chain is the last one
                is_last = True
                for sink_node in output_mem_node.sinks:
                    if sink_node.node_type == "m":
                        is_last = False
                        break
                new_pe_chain["mem_chain_is_last"] = is_last
                # ---- [output_io] The final 16b output IO node
                current_node = output_mem_node
                while len(current_node.sinks) > 0:
                    sink_nodes_except_pe = [sink_node for sink_node in current_node.sinks if sink_node.node_type != "p"]
                    current_node = sink_nodes_except_pe[0]
                new_pe_chain["output_io"] = current_node.node_name
                # Finally, append the info of this pe chain to the list
                pe_chains.append(new_pe_chain)
            else:
                # skip, not a start of a chain
                pass
        # Sort by kernel_io, output_io, and mem_chain_is_last
        pe_chains.sort(key=lambda x: x["kernel_io"])
        for i in range(0, len(pe_chains), 4):
            pe_chains[i:i+4] = sorted(pe_chains[i:i+4], key=lambda x: x["output_io"])
        for i in range(0, len(pe_chains), 2):
            pe_chains[i:i+2] = sorted(pe_chains[i:i+2], key=lambda x: x["mem_chain_is_last"])
        # write out pe chain info using json
        if dump:
            with open(app_dir + "/resnet_pe_chains_info.json", "w") as f:
                f.write(json.dumps(pe_chains, indent=4))
        return pe_chains

    def manualy_place_resnet(self, app_dir):

        # traverse and analyze the pe chain first
        pe_chains = self._analyze_pe_chain(app_dir=app_dir, dump=True)

        # place input mem from bottom to top
        mem_node_names = ["m6", "m5", "m4", "m3", "m2", "m1", "m15", "m14", "m13", "m12", "m11", "m10", "m9", "m8", "m7", "m0"]
        mem_node_x, mem_node_y = 15, 16
        for node_name in mem_node_names:
            node = self._get_node_by_name(node_name)
            node.x, node.y = mem_node_x, mem_node_y
            mem_node_y -= 1
        
        # Place the output mem
        mem_node_names = [pe_chain["output_mem"] for pe_chain in pe_chains]
        out_mem_pos = [
            (3, 3),
            (3, 2),
            (3, 6),
            (3, 5),
            (11, 3),
            (11, 2),
            (11, 6),
            (11, 5),
            (19, 3),
            (19, 2),
            (19, 6),
            (19, 5),
            (23, 3),
            (23, 2),
            (23, 6),
            (23, 5)
        ]
        for node_name in mem_node_names:
            node = self._get_node_by_name(node_name)
            node.x, node.y = out_mem_pos.pop(0)
        
        # Place the const
        const_node_names = [pe_chain["const"] for pe_chain in pe_chains]
        const_pos = [
            (1, 8),
            (1, 7),
            (5, 8),
            (5, 7),
            (10, 10),
            (10, 9),
            (10, 8),
            (10, 7),
            (20, 10),
            (20, 9),
            (20, 8),
            (20, 7),
            (25, 10),
            (25, 9),
            (25, 8),
            (25, 7)
        ]
        for node_name in const_node_names:
            node = self._get_node_by_name(node_name)
            node.x, node.y = const_pos.pop(0)
        
        # Place the PE chain (MAC only)
        adder_collection = []
        pe_chain_pos_x = [0, 2, 4, 6, 8, 9, 12, 13, 14, 16, 17, 18, 21, 22, 24, 26]
        for pe_chain in pe_chains:
            pe_pos_x = pe_chain_pos_x.pop(0)
            pe_pos_y = 16
            for node_name in pe_chain["pe_chain"]:
                node = self._get_node_by_name(node_name)
                # skip the adder, do it later
                if "$add_" in node.node_id:
                    adder_collection.append(node)
                    continue
                node.x, node.y = pe_pos_x, pe_pos_y
                pe_pos_y -= 1
        
        # Place the adders
        adder_pos = [
            (1, 3),
            (1, 2),
            (5, 6),
            (5, 5),
            (10, 3),
            (10, 2),
            (10, 6),
            (10, 5),
            (20, 3),
            (20, 2),
            (20, 6),
            (20, 5),
            (25, 3),
            (25, 2),
            (25, 6),
            (25, 5)
        ]
        for node in adder_collection:
            node.x, node.y = adder_pos.pop(0)
        
        # Place the ofmap IO nodes
        ofmap_io_node_pos = [
            (1, 0),
            (3, 0),
            (9, 0),
            (11, 0),
            (19, 0),
            (21, 0),
            (23, 0),
            (25, 0)
        ]
        for node_name in ["I2", "I6", "I3", "I7", "I0", "I4", "I1", "I5"]:
            pos = ofmap_io_node_pos.pop(0)
            io16_node = self._get_node_by_name(node_name.upper())
            io1_node = self._get_node_by_name(node_name.lower())
            io16_node.x, io16_node.y = pos
            io1_node.x, io1_node.y = pos
        
        # Place the kernel IO nodes
        kernel_io_node_pos = [
            (4, 0),
            (10, 0),
            (16, 0),
            (24, 0)
        ]
        for node_name in ["I16", "I17", "I18", "I19"]:
            node = self._get_node_by_name(node_name)
            node.x, node.y =  kernel_io_node_pos.pop(0)
        
        # Place the ifmap IO nodes
        ifmap_io_node_pos = [
            (6, 0),  # This ifmap io node should connect to: m7, m15
            (8, 0),  # This ifmap io node should connect to: m9, m2
            (12, 0), # This ifmap io node should connect to: m11, m4
            (14, 0), # This ifmap io node should connect to: m13, m6
            (18, 0), # This ifmap io node should connect to: m12, m5
            (20, 0), # This ifmap io node should connect to: m10, m3
            (22, 0), # This ifmap io node should connect to: m8, m1
            (26, 0)  # This ifmap io node should connect to: m0, m14
        ]
        for mem_node_name in ["m7", "m9", "m11", "m13", "m12", "m10", "m8", "m0"]:
            # find the root IO node for each mem node in the list, then assign its position
            mem_node = self._get_node_by_name(mem_node_name)
            node = self._find_root_node(start_node=mem_node)
            node.x, node.y = ifmap_io_node_pos.pop(0)
        
        # Place the mem nodes for ofmap 1bit valid (stencil valid)
        valid_mem_node_pos = [
            (3, 1),
            (3, 4),
            (11, 1),
            (11, 4),
            (19, 1),
            (19, 4),
            (23, 1),
            (23, 4)
        ]
        for io1_node_name in ["i2", "i6", "i3", "i7", "i0", "i4", "i1", "i5"]:
            io1_node = self._get_node_by_name(io1_node_name)
            node = self._find_root_node(start_node=io1_node)
            node.x, node.y = valid_mem_node_pos.pop(0)

        # write position info into file
        with open(app_dir + "/manual.place", "w") as f:
            for node in self.nodes:
                if node.x is not None:
                    f.write("{} {} {}\n".format(node.node_name, node.x, node.y))
