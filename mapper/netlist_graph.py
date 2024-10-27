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
                return root_mem_node.node_name
        return None


    def manualy_place_resnet(self, app_dir):


        pe_chains = []
        
        for node in self.pe_nodes:
            if "mul_" in node.node_id:
                # found a start of a pe chain, start traching and record the chain
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
                            break
                # trace the entire pe chain
                new_pe_chain["pe_chain"] = [pe_node.node_name]
                new_pe_chain["input_mem"] = [self._find_pe_source_ifmap_node(pe_node)]
                while pe_node.sinks[0].node_type == "p":
                    pe_node = pe_node.sinks[0]
                    assert len(pe_node.sinks) == 1, "Each PE should have only one sink"
                    new_pe_chain["pe_chain"].append(pe_node.node_name)
                    if "mul" in pe_node.node_id:
                        new_pe_chain["input_mem"].append(self._find_pe_source_ifmap_node(pe_node))
                # the last node should be a memory node
                assert pe_node.sinks[0].node_type == "m", "PE chain should end with a memory node"
                output_mem_node = pe_node.sinks[0]
                new_pe_chain["output_mem"] = output_mem_node.node_name
                # find the const node
                for source_node in output_mem_node.sources:
                    if "const" in source_node.node_id:
                        new_pe_chain["const"] = source_node.node_name
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
                # append this pe chain to the list
                pe_chains.append(new_pe_chain)
            else:
                # skip, not a start of a chain
                pass
        
        # write out pe chain info using json
        with open(app_dir + "/resnet_pe_chains_info.txt", "w") as f:
            f.write(json.dumps(pe_chains, indent=4))
        
        breakpoint()
        exit()

        # HALIDE_GEN_ARGS = os.environ.get("HALIDE_GEN_ARGS")
        # k_oc_match = re.search(r'k_oc=(\d+)', HALIDE_GEN_ARGS)
        # k_ic_match = re.search(r'k_ic=(\d+)', HALIDE_GEN_ARGS)
        # assert k_oc_match, "No k_oc in HALIDE_GEN_ARGS. Please turn off MANUAL_PLACER or re-define HALIDE_GEN_ARGS for resnet."
        # assert k_ic_match, "No k_ic in HALIDE_GEN_ARGS. Please turn off MANUAL_PLACER or re-define HALIDE_GEN_ARGS for resnet."
        # k_oc = int(k_oc_match.group(1))
        # k_ic = int(k_ic_match.group(1))
        # input_mem = []
        # output_mem = []

        # # extract input mem from bottom to top
        # for node in self.mem_nodes:
        #     if len(node.sinks) == k_oc and "mul" in node.sinks[0].node_id and "add" not in node.sinks[0].node_id:
        #         input_mem.append(node)
        #         break
        # next_pe = input_mem[0].sinks[0].sinks[0]
        # while True:
        #     for node in next_pe.sources:
        #         if "m" in node.node_name:
        #             input_mem.append(node)
        #     next_pe = next_pe.sinks[0]
        #     if "mul" not in next_pe.node_id:
        #         for node in next_pe.sinks[0].sources:
        #             if "m" in node.node_name:
        #                 input_mem.append(node)
        #         break

        # # place input mem from bottom to top
        # input_mem_x = 15
        # input_mem_y = 16
        # for node in input_mem:
        #     (node.x, node.y) = (input_mem_x, input_mem_y)
        #     input_mem_y -= 1

        # # extract output mem 
        # # check whether have mem chaining
        # mem_chain = False
        # for node in self.mem_nodes:
        #     for snode in node.sources:
        #         if "m" in snode.node_name:
        #             mem_chain = True
        #             break
        #     if mem_chain:
        #         break
        # # add output mem to list
        # for node in self.mem_nodes:
        #     is_output_mem = False
        #     # if mem_chain and len(node.sources) == 3 and "I" in node.sinks[1].node_name:
        #     if mem_chain and len(node.sources) == 3:
        #         for sink_node in node.sinks:
        #             if "I" in sink_node.node_name:
        #                 is_output_mem = True
        #                 break
        #         if is_output_mem:
        #             output_mem.append(node)
        #             self._find_source_mem(node, output_mem)
        #     elif not mem_chain and len(node.sources) == 2:
        #         output_mem.append(node)

        # # place output mem
        # # starting from the first MEM column
        # # assert k_oc > 4, "k_oc is too small; please unset MANUAL_PLACER"
        # # output_mem_x = 3
        # # output_mem_y = 1
        # # if k_oc <= 8:
        # #     for node in output_mem:
        # #         (node.x, node.y) = (output_mem_x, output_mem_y)
        # #         if output_mem_y < 2:
        # #             output_mem_y += 1
        # #         elif output_mem_x == round(k_oc / 4) * 4 - 5 and output_mem_y == 2:
        # #             output_mem_x += 8
        # #             output_mem_y = 1
        # #         else:
        # #             output_mem_x += 4
        # #             output_mem_y = 1
        # # else:
        # #     for node in output_mem:
        # #         (node.x, node.y) = (output_mem_x, output_mem_y)
        # #         if output_mem_y < 2 or (output_mem_x == round(k_oc / 4) * 4 - 5 and output_mem_y < 4):
        # #             output_mem_y += 1
        # #         elif output_mem_x != round(k_oc / 4) * 4 - 5:
        # #             output_mem_x += 4
        # #             output_mem_y = 1
        # #         else:
        # #             output_mem_x += 8
        # #             output_mem_y = 1
        # out_mem_xy = [
        #     (3, 2),
        #     (3, 3),
        #     (3, 5),
        #     (3, 6),
        #     (11, 2),
        #     (11, 3),
        #     (11, 5),
        #     (11, 6),
        #     (19, 2),
        #     (19, 3),
        #     (19, 5),
        #     (19, 6),
        #     (23, 2),
        #     (23, 3),
        #     (23, 5),
        #     (23, 6)
        # ]
        # for node in output_mem:
        #     (node.x, node.y) = out_mem_xy.pop(0)

        # # place pe chains and const pes
        # const_xy = [
        #     (1, 7),
        #     (1, 8),
        #     (5, 7),
        #     (5, 8),
        #     (10, 7),
        #     (10, 8),
        #     (10, 9),
        #     (10, 10),
        #     (20, 7),
        #     (20, 8),
        #     (20, 9),
        #     (20, 10),
        #     (25, 7),
        #     (25, 8),
        #     (25, 9),
        #     (25, 10)
        # ]
        # pe_xy = [
        #     (0, 1),  (1, 2),  (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8), (0, 9), (0, 10), (0, 11), (0, 12), (0, 13), (0, 14), (0, 15), (0, 16),
        #     (2, 1),  (1, 3),  (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 8), (2, 9), (2, 10), (2, 11), (2, 12), (2, 13), (2, 14), (2, 15), (2, 16),
        #     (4, 1),  (5, 5),  (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (4, 7), (4, 8), (4, 9), (4, 10), (4, 11), (4, 12), (4, 13), (4, 14), (4, 15), (4, 16),
        #     (6, 1),  (5, 6),  (6, 2), (6, 3), (6, 4), (6, 5), (6, 6), (6, 7), (6, 8), (6, 9), (6, 10), (6, 11), (6, 12), (6, 13), (6, 14), (6, 15), (6, 16),
        #     (8, 1),  (10, 2), (8, 2), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7), (8, 8), (8, 9), (8, 10), (8, 11), (8, 12), (8, 13), (8, 14), (8, 15), (8, 16),
        #     (9, 1),  (10, 3), (9, 2), (9, 3), (9, 4), (9, 5), (9, 6), (9, 7), (9, 8), (9, 9), (9, 10), (9, 11), (9, 12), (9, 13), (9, 14), (9, 15), (9, 16),
        #     (12, 1), (10, 5), (12, 2), (12, 3), (12, 4), (12, 5), (12, 6), (12, 7), (12, 8), (12, 9), (12, 10), (12, 11), (12, 12), (12, 13), (12, 14), (12, 15), (12, 16),
        #     (13, 1), (10, 6), (13, 2), (13, 3), (13, 4), (13, 5), (13, 6), (13, 7), (13, 8), (13, 9), (13, 10), (13, 11), (13, 12), (13, 13), (13, 14), (13, 15), (13, 16),
        #     (14, 1), (20, 2), (14, 2), (14, 3), (14, 4), (14, 5), (14, 6), (14, 7), (14, 8), (14, 9), (14, 10), (14, 11), (14, 12), (14, 13), (14, 14), (14, 15), (14, 16),
        #     (16, 1), (20, 3), (16, 2), (16, 3), (16, 4), (16, 5), (16, 6), (16, 7), (16, 8), (16, 9), (16, 10), (16, 11), (16, 12), (16, 13), (16, 14), (16, 15), (16, 16),
        #     (17, 1), (20, 5), (17, 2), (17, 3), (17, 4), (17, 5), (17, 6), (17, 7), (17, 8), (17, 9), (17, 10), (17, 11), (17, 12), (17, 13), (17, 14), (17, 15), (17, 16),
        #     (18, 1), (20, 6), (18, 2), (18, 3), (18, 4), (18, 5), (18, 6), (18, 7), (18, 8), (18, 9), (18, 10), (18, 11), (18, 12), (18, 13), (18, 14), (18, 15), (18, 16),
        #     (21, 1), (25, 2), (21, 2), (21, 3), (21, 4), (21, 5), (21, 6), (21, 7), (21, 8), (21, 9), (21, 10), (21, 11), (21, 12), (21, 13), (21, 14), (21, 15), (21, 16),
        #     (22, 1), (25, 3), (22, 2), (22, 3), (22, 4), (22, 5), (22, 6), (22, 7), (22, 8), (22, 9), (22, 10), (22, 11), (22, 12), (22, 13), (22, 14), (22, 15), (22, 16),
        #     (24, 1), (25, 5), (24, 2), (24, 3), (24, 4), (24, 5), (24, 6), (24, 7), (24, 8), (24, 9), (24, 10), (24, 11), (24, 12), (24, 13), (24, 14), (24, 15), (24, 16),
        #     (26, 1), (25, 6), (26, 2), (26, 3), (26, 4), (26, 5), (26, 6), (26, 7), (26, 8), (26, 9), (26, 10), (26, 11), (26, 12), (26, 13), (26, 14), (26, 15), (26, 16)
        # ]
        # accum_pe = []
        # const_pe = []
        # pe_x = 1
        # pe_y = 1
        # for node in output_mem:
        #     for snode in node.sources:
        #         if "const" in snode.node_id:
        #             # (snode.x, snode.y) = (node.x - 3, node.y)
        #             # if node.y > 2:
        #             #     (snode.x, snode.y) = (node.x + 1, node.y - 2)
        #             (snode.x, snode.y) = const_xy.pop(0)
        #             const_pe.append(snode)
        #         elif "muladd" in snode.node_id:
        #             next_pe = snode
        #             # (next_pe.x, next_pe.y) = (pe_x, pe_y)
        #             # pe_y += 1
        #             while True:
        #                 (next_pe.x, next_pe.y) = pe_xy.pop(0)
        #                 for snext_pe in next_pe.sources:
        #                     if "p" in snext_pe.node_name:
        #                         # if "add" in snext_pe.node_id and "mul" not in snext_pe.node_id:
        #                         #     accum_pe.append(snext_pe)
        #                         # (snext_pe.x, snext_pe.y) = (pe_x, pe_y)
        #                         # if "muladd" in snext_pe.node_id:
        #                         #     pe_y += 1
        #                         next_pe = snext_pe
        #                         break
        #                 if "mul" in next_pe.node_id and "add" not in next_pe.node_id:
        #                     # pe_y = 1
        #                     (next_pe.x, next_pe.y) = pe_xy.pop(0)
        #                     break
        #     # if (pe_x + 2) % 4 != 0:
        #     #     pe_x += 1
        #     # else:
        #     #     pe_x += 3
        # assert len(pe_xy) == 0, "[error-manual-placer] Not all predefined positions are used"

        # # place accum pes separately
        # # for _ in range(len(const_pe)):
        # #     (accum_pe[_].x, accum_pe[_].y) = (const_pe[_].x, const_pe[_].y + 2)

        # # place stencil mem
        # # glb_o_match = re.search(r'glb_o=(\d+)', HALIDE_GEN_ARGS)
        # # glb_o = int(glb_o_match.group(1)) if glb_o_match else None
        # # glb_i_match = re.search(r'glb_i=(\d+)', HALIDE_GEN_ARGS)
        # # glb_i = int(glb_i_match.group(1)) if glb_i_match else None
        # # if not glb_o_match:
        # #     stencil_x = 3
        # #     stencil_y = 5
        # #     for node in self.mem_nodes:
        # #         if len(node.sources) == 0:
        # #             (node.x, node.y) = (stencil_x, stencil_y)
        # #             if stencil_x == round(k_oc / 4) * 4 - 5 or glb_o <= 4:
        # #                 stencil_x += 8
        # #             else:
        # #                 stencil_x += 4
        # # else:
        # #     stencil_x = 3
        # #     stencil_y = 4
        # #     for node in self.mem_nodes:
        # #         if "port_controller" in node.node_id:
        # #             (node.x, node.y) = (stencil_x, stencil_y)
        # #             if stencil_x == round(k_oc / 4) * 4 - 9:
        # #                 stencil_x += 4
        # #                 stencil_y = 5
        # #             elif stencil_x == round(k_oc / 4) * 4 - 5:
        # #                 if stencil_y == 5:
        # #                     stencil_y += 2
        # #                 else:
        # #                     stencil_x += 8
        # #                     stencil_y = 4
        # #             else:
        # #                 stencil_x += 4
        # out_valid_xy = [
        #     (3, 1),
        #     (3, 4),
        #     (11, 1),
        #     (11, 4),
        #     (19, 1),
        #     (19, 4),
        #     (23, 1),
        #     (23, 4)
        # ]
        # for node in self.mem_nodes:
        #         if "port_controller" in node.node_id:
        #             (node.x, node.y) = out_valid_xy.pop(0)

        # # place IO tile, currently use fixed positions
        # # if glb_o == 8:
        # #     weight_IO_idx = [0, 24, 28, 4, 8, 12, 16, 20]
        # #     ifmap_IO_idx = [2, 6, 26, 10, 22, 14, 18, 30]
        # # elif glb_o == 7:
        # #     weight_IO_idx = [0, 24, 4, 8, 12, 16, 20]
        # #     ifmap_IO_idx = [2, 6, 26, 10, 22, 14, 18]
        # # if glb_o == 4:
        # #     output_IO_idx = [3, 11, 19, 27]
        # # else:
        # #     output_IO_idx = []
        # # if glb_i == 8:
        # #     output_IO_idx = [1, 5, 9, 11, 19, 23, 27, 31]
        # # elif glb_i == 7:
        # #     output_IO_idx = [1, 5, 9, 11, 19, 23, 27]
        # # else:
        # #     output_IO_idx = []
        # weight_IO = []
        # ifmap_IO = []
        # output_IO = []
        # stencil_IO = []

        # for node in self.io_nodes:
        #     if "io16in_kernel_host_stencil_clkwrk" in node.node_id:
        #         weight_IO.append(node)
        #     elif "io16in_input_host_stencil_clkwrk" in node.node_id:
        #         ifmap_IO.append(node)
        #     elif "io16_hw_output_stencil_clkwrk" in node.node_id:
        #         output_IO.append(node)
        #     else:
        #         stencil_IO.append(node)
        
        # # override
        # weight_IO_idx = [4, 10, 16, 24]
        # ifmap_IO_idx = [6, 8, 12, 14, 18, 20, 22, 26]
        # output_IO_idx = [1, 3, 9, 11, 19, 21, 23, 25]
        
        # for _ in range(len(weight_IO)):
        #     weight_IO[_].x = weight_IO_idx[_]
        #     weight_IO[_].y = 0
        # for _ in range(len(ifmap_IO)):
        #     ifmap_IO[_].x = ifmap_IO_idx[_]
        #     ifmap_IO[_].y = 0
        # for _ in range(len(output_IO)):
        #     output_IO[_].x = output_IO_idx[_]
        #     output_IO[_].y = 0
        # for _ in range(len(stencil_IO)):
        #     stencil_IO[_].x = output_IO_idx[_]
        #     stencil_IO[_].y = 0 

        # write position info into file
        with open(app_dir + "/manual.place", "w") as f:
            for node in self.nodes:
                if node.x is not None:
                    f.write("{} {} {}\n".format(node.node_name, node.x, node.y))
