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

    # count the number of register sources until the first non-reg node
    # assume node isn't connected by multiple regs
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
            if "add_" in pe_node.node_id and "muladd_" not in pe_node.node_id:
                latency_pe_to_out_mem = dfs_pe_to_out_mem(pe_node)
                return latency_out_mem_to_pe + latency_pe_to_out_mem
            else:
                latency_pe_to_in_mem = dfs_pe_to_in_mem(pe_node)
                return latency_out_mem_to_pe + latency_pe_to_in_mem

    # this is for IO2MEM and MEM2PE pipelining in resnet w/ manual placement
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
                        pe_id = d1["pe_port"][0][0]
                        for node in self.pe_nodes:
                            if pe_id in node.node_id:
                                pe_node = node
                        for mem_node in self.mem_nodes:
                            if "ub_output_cgra_stencil" in mem_node.node_id:
                                if self.count_input_latencies(mem_node, pe_node):
                                    d1["latency"] = self.count_input_latencies(mem_node, pe_node)
                    elif "in2_output_cgra_stencil" in kernel_port:
                        pe_id = d1["pe_port"][0][0]
                        for node in self.pe_nodes:
                            if pe_id in node.node_id:
                                pe_node = node
                        for mem_node in self.mem_nodes:
                            if "ub_output_cgra_stencil" in mem_node.node_id:
                                if self.count_input_latencies(mem_node, pe_node):
                                    d1["latency"] = self.count_input_latencies(mem_node, pe_node)
        fout = open(f"{app_dir}/updated_kernel_latencies.json", "w")
        fout.write(json.dumps(kernel_latencies, indent=4))

    # this deals with port latency of PE at glb level, e.g. residual addition
    def get_glb_kernel_latency(self, app_dir, has_glb_PE=False):
        kernel_latencies_file = glob.glob(f"{app_dir}/*_compute_kernel_latencies.json")[0]
        assert os.path.exists(kernel_latencies_file)
        f = open(kernel_latencies_file, "r")
        existing_kernel_latencies = json.load(f)

        kernel_latencies = existing_kernel_latencies
        for kernel, latency_dict in kernel_latencies.items():
            if "_glb_" in kernel:
                # Reset glb_PE_base_lat for each kernel
                glb_PE_base_lat = None
                # find the base latency for the current kernel
                for kernel_port, d1 in latency_dict.items():
                    if d1["pe_port"] != [] and "_output_" in kernel_port:
                        has_glb_PE = True
                        glb_PE_base_lat = d1["latency"]
                        break
                if glb_PE_base_lat is not None:
                    # update latencies for the current kernel based on the base latency
                    for kernel_port, d1 in latency_dict.items():
                        # skip if there's no PE port or if it's the output port we already processed
                        if d1["pe_port"] == [] or "_output_" in kernel_port:
                            continue
                        pe_id = d1["pe_port"][0][0]
                        for node in self.pe_nodes:
                            if pe_id in node.node_id:
                                pe_node = node
                                # update latency based on the base latency
                                d1["latency"] = glb_PE_base_lat + self.count_reg_sources(pe_node)
        if has_glb_PE:
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

    def _find_source_mem(self, node, mem_list):
        for snode in node.sources:
            if "m" in snode.node_name:
                mem_list.append(snode)
                self._find_source_mem(snode, mem_list)

    
    def _find_root_io_node(self, start_node):
        node = start_node
        while len(node.sources) > 0:
            assert len(node.sources) == 1, "The assumption is that there is only one source for each node"
            node = node.sources[0]
        assert node.node_type == "I", "The root node should be an IO node"
        assert "io16in" in node.node_id, "The root node should be an 16bit input node"
        return node
    
    def _find_root_mem_node(self, start_node):
        node = start_node
        while len(node.sources) > 0:
            assert len(node.sources) == 1, "The assumption is that there is only one source for each node"
            if node.node_type == "m":
                return node
            node = node.sources[0]
        return None
    
    def _find_pe_source_ifmap_node(self, pe_node):
        for source_node in pe_node.sources:
            root_mem_node = self._find_root_mem_node(source_node)
            if root_mem_node is not None:
                return root_mem_node
        return None


    def _get_node_by_name(self, node_name):
        match_nodes = []
        for node in self.nodes:
            if node_name == node.node_name:
                match_nodes.append(node)
        assert len(match_nodes) > 0, "No node with the name {}".format(node_name)
        assert len(match_nodes) == 1, "There should be only one node with the name {}".format(node_name)
        return match_nodes[0]


    def manualy_place_resnet(self, app_dir):


        pe_chains = []
        input_mem_nodes = []
        output_mem_nodes = []
        const_nodes = []
        pe_chain_nodes = []
        output_io_nodes = []
        kernel_io_nodes = []
        
        for node in self.pe_nodes:
            if "mul_" in node.node_id:
                # found a start of a pe chain, start tracing and record the chain
                new_pe_chain = {}
                pe_node = node
                # find its kernel IO node
                for source_node in pe_node.sources:
                    # the sources could be (1) itself, (2) kernel input, or (3) ifmap input
                    # we need to find (2)
                    if "p" in source_node.node_name:
                        # this is case (1)
                        continue
                    else:
                        root_io_node = self._find_root_io_node(start_node=source_node)
                        if "kernel" in root_io_node.node_id:
                            new_pe_chain["kernel_io"] = root_io_node.node_name
                            kernel_io_nodes.append(root_io_node)
                            break
                # trace the entire pe chain
                new_pe_chain["pe_chain"] = [pe_node.node_name]
                new_pe_chain_node = [pe_node]
                input_mem_node = self._find_pe_source_ifmap_node(pe_node)
                new_pe_chain["input_mem"] = [input_mem_node.node_name]
                input_mem_nodes = []
                input_mem_nodes.append(input_mem_node)
                while pe_node.sinks[0].node_type == "p":
                    pe_node = pe_node.sinks[0]
                    assert len(pe_node.sinks) == 1, "Each PE should have only one sink"
                    new_pe_chain["pe_chain"].append(pe_node.node_name)
                    new_pe_chain_node.append(pe_node)
                    if "mul" in pe_node.node_id:
                        input_mem_node = self._find_pe_source_ifmap_node(pe_node)
                        new_pe_chain["input_mem"].append(input_mem_node.node_name)
                        input_mem_nodes.append(input_mem_node)
                # the last node should be a memory node
                assert pe_node.sinks[0].node_type == "m", "PE chain should end with a memory node"
                output_mem_node = pe_node.sinks[0]
                new_pe_chain["output_mem"] = output_mem_node.node_name
                output_mem_nodes.append(output_mem_node)
                # find the const node
                for source_node in output_mem_node.sources:
                    if "const" in source_node.node_id:
                        new_pe_chain["const"] = source_node.node_name
                        const_nodes.append(source_node)
                        break
                # is mem the end of mem chain?
                is_last = True
                for sink_node in output_mem_node.sinks:
                    if sink_node.node_type == "m":
                        is_last = False
                        break
                new_pe_chain["mem_chain_is_last"] = is_last
                # trace the final output IO
                temp_node = output_mem_node
                while len(temp_node.sinks) > 0:
                    sink_nodes_except_pe = [sink_node for sink_node in temp_node.sinks if sink_node.node_type != "p"]
                    assert len(sink_nodes_except_pe) == 1, "Each node should have only one sink after excluding PE nodes"
                    temp_node = sink_nodes_except_pe[0]
                assert temp_node.node_type == "I", "The final node should be an IO node"
                assert "io16" in temp_node.node_id, "The final node should be 16bit"
                assert "output" in temp_node.node_id, "The final node should be an output node"
                new_pe_chain["output_io"] = temp_node.node_name
                output_io_nodes.append(temp_node)
                # append this pe chain to the list
                pe_chains.append(new_pe_chain)
                pe_chain_nodes.append(new_pe_chain_node)
            else:
                # skip, not a start of a chain
                pass

        # Sort by kernel io tiles first
        pe_chains.sort(key=lambda x: x["kernel_io"])
        
        # Then sort by output io tile
        for i in range(0, len(pe_chains), 4):
            pe_chains[i:i+4] = sorted(pe_chains[i:i+4], key=lambda x: x["output_io"])
        
        # Then sort by mem_chain_is_last
        for i in range(0, len(pe_chains), 2):
            pe_chains[i:i+2] = sorted(pe_chains[i:i+2], key=lambda x: x["mem_chain_is_last"])
        
        with open(app_dir + "/resnet_pe_chains_info.json", "w") as f:
            f.write(json.dumps(pe_chains, indent=4))
        
        # Place the input mem
        for i, input_mem_node in enumerate(input_mem_nodes):
            input_mem_node.x = 15
            input_mem_node.y = 16 - i

        # Place the output mem
        for output_mem_node in output_mem_nodes:
            i = next(i for i, pe_chain in enumerate(pe_chains) if pe_chain["output_mem"] == output_mem_node.node_name)
            if int(i / 4) == 0:
                output_mem_node.x = 3
            elif int(i / 4) == 1:
                output_mem_node.x = 11
            elif int(i / 4) == 2:
                output_mem_node.x = 19
            elif int(i / 4) == 3:
                output_mem_node.x = 23
            if i % 4 == 0:
                output_mem_node.y = 3
            elif i % 4 == 1:
                output_mem_node.y = 2
            elif i % 4 == 2:
                output_mem_node.y = 6
            elif i % 4 == 3:
                output_mem_node.y = 5

        # Place the consts
        for const_node in const_nodes:
            i = next(i for i, pe_chain in enumerate(pe_chains) if pe_chain["const"] == const_node.node_name)
            if i < 4:
                if int(i / 2) == 0:
                    const_node.x = 1
                elif int(i / 2) == 1:
                    const_node.x = 5
                const_node.y = 7 + (i % 2)
            else:
                if int(i / 4) == 1:
                    const_node.x = 10
                elif int(i / 4) == 2:
                    const_node.x = 20
                elif int(i / 4) == 3:
                    const_node.x = 25
                const_node.y = 7 + (i % 4)
        
        # Place the pe chains
        for pe_chain_node in pe_chain_nodes:
            i = next(i for i, pe_chain in enumerate(pe_chains) if pe_chain["pe_chain"] == [node.node_name for node in pe_chain_node])
            for j, pe_node in enumerate(pe_chain_node):
                if j == 15:
                    if i < 2:
                        pe_node.x = 1
                        pe_node.y = 2 if i == 0 else 3
                    elif i < 4:
                        pe_node.x = 5
                        pe_node.y = 5 if i == 2 else 6
                    else:
                        if int(i / 4) == 1:
                            pe_node.x = 10
                        elif int(i / 4) == 2:
                            pe_node.x = 20
                        elif int(i / 4) == 3:
                            pe_node.x = 25
                        if i % 4 == 0:
                            pe_node.y = 2
                        elif i % 4 == 1:
                            pe_node.y = 3
                        elif i % 4 == 2:
                            pe_node.y = 5
                        elif i % 4 == 3:
                            pe_node.y = 6
                else:
                    x_pos = [0, 2, 4, 6, 8, 9, 12, 13, 14, 16, 17, 18, 21, 22, 24, 26]
                    pe_node.x = x_pos[i]
                    pe_node.y = 16 - j if j < 16 else 1
        
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
        for ofmap_io_node_name in ["I2", "I6", "I3", "I7", "I0", "I4", "I1", "I5"]:
            pos = ofmap_io_node_pos.pop(0)
            io16_node = self._get_node_by_name(ofmap_io_node_name.upper())
            io1_node = self._get_node_by_name(ofmap_io_node_name.lower())
            io16_node.x, io16_node.y = pos
            io1_node.x, io1_node.y = pos

        # Place the kernel IO nodes
        kernel_io_node_pos = [
            (4, 0),
            (10, 0),
            (16, 0),
            (24, 0)
        ]
        for kernel_io_node_name in ["I16", "I17", "I18", "I19"]:
            pos = kernel_io_node_pos.pop(0)
            kernel_io_node = self._get_node_by_name(kernel_io_node_name)
            kernel_io_node.x, kernel_io_node.y = pos
        
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
            mem_node = self._get_node_by_name(mem_node_name)
            # trace back to its source IO node
            current_node = mem_node
            while len(current_node.sources) > 0:
                current_node = current_node.sources[0]
            root_io_node = current_node
            # assign position to this root IO node
            assert root_io_node.node_type == "I", "The root node should be an IO node"
            root_io_node.x, root_io_node.y = ifmap_io_node_pos.pop(0)
        
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
        for output_io1_node_name in ["i2", "i6", "i3", "i7", "i0", "i4", "i1", "i5"]:
            output_io1_node = self._get_node_by_name(output_io1_node_name)
            # trace to its source mem node
            current_node = output_io1_node
            while len(current_node.sources) > 0:
                current_node = current_node.sources[0]
            root_mem_node = current_node
            # assign position to this root mem node
            assert root_mem_node.node_type == "m", "The root node should be a memory node"
            root_mem_node.x, root_mem_node.y = valid_mem_node_pos.pop(0)

        # write position info into file
        with open(app_dir + "/manual.place", "w") as f:
            for node in self.nodes:
                if node.x is not None:
                    f.write("{} {} {}\n".format(node.node_name, node.x, node.y))
