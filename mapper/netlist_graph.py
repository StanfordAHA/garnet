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
        self.pe_nodes = []
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
            assert len(node.sources) == 1
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
        if "IO2MEM_REG_CHAIN" in os.environ or "MEM2PE_REG_CHAIN" in os.environ:
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

    def manually_place_resnet(self, app_dir):
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
            is_output_mem = False
            # if mem_chain and len(node.sources) == 3 and "I" in node.sinks[1].node_name:
            if mem_chain and len(node.sources) == 3:
                for sink_node in node.sinks:
                    if "I" in sink_node.node_name:
                        is_output_mem = True
                        break
                if is_output_mem:
                    output_mem.append(node)
                    self._find_source_mem(node, output_mem)
            elif not mem_chain and len(node.sources) == 2:
                output_mem.append(node)

        # place output mem
        # starting from the first MEM column
        assert k_oc > 4, "k_oc is too small; please unset MANUAL_PLACER"
        output_mem_x = 3
        output_mem_y = 1
        if k_oc <= 8:
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
        glb_i_match = re.search(r'glb_i=(\d+)', HALIDE_GEN_ARGS)
        glb_i = int(glb_i_match.group(1)) if glb_i_match else None
        if not glb_o_match:
            stencil_x = 3
            stencil_y = 5
            for node in self.mem_nodes:
                if len(node.sources) == 0:
                    (node.x, node.y) = (stencil_x, stencil_y)
                    if stencil_x == round(k_oc / 4) * 4 - 5 or glb_o <= 4:
                        stencil_x += 8
                    else:
                        stencil_x += 4
        else:
            stencil_x = 3
            stencil_y = 4
            for node in self.mem_nodes:
                if "port_controller" in node.node_id:
                    (node.x, node.y) = (stencil_x, stencil_y)
                    if stencil_x == round(k_oc / 4) * 4 - 9:
                        stencil_x += 4
                        stencil_y = 5
                    elif stencil_x == round(k_oc / 4) * 4 - 5:
                        if stencil_y == 5:
                            stencil_y += 2
                        else:
                            stencil_x += 8
                            stencil_y = 4
                    else:
                        stencil_x += 4

        # place IO tile, currently use fixed positions
        if glb_o == 8:
            weight_IO_idx = [0, 24, 28, 4, 8, 12, 16, 20]
            ifmap_IO_idx = [2, 6, 26, 10, 22, 14, 18, 30]
        elif glb_o == 7:
            weight_IO_idx = [0, 24, 4, 8, 12, 16, 20]
            ifmap_IO_idx = [2, 6, 26, 10, 22, 14, 18]
        if glb_o == 4:
            output_IO_idx = [3, 11, 19, 27]
        else:
            output_IO_idx = []
        if glb_i == 8:
            output_IO_idx = [1, 5, 9, 11, 19, 23, 27, 31]
        elif glb_i == 7:
            output_IO_idx = [1, 5, 9, 11, 19, 23, 27]
        else:
            output_IO_idx = []
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

    def manually_place_fused_quant(self, app_dir):
        MU_IO_Y_COORD = 17
        placed_pos = []

        # ----Place MU IOs----
        # Extract all MU IOs
        mu_io_nodes = []
        for node in self.nodes:
            if "MU_io16in_mu_input_host_stencil" in node.node_id:
                mu_io_nodes.append(node)
        # Sort based on the idx 'clkwrk_'
        mu_io_nodes.sort(
            key=lambda n: int(n.node_id.split("clkwrk_")[1].split("_")[0])
        )
        # Place MU IOs
        mu_x_sequential = []
        if os.path.exists(os.path.join(app_dir, "glb_bank_config.json")):
            with open(os.path.join(app_dir, "glb_bank_config.json"), "r") as f:
                glb_bank_config = json.load(f)
            assert glb_bank_config["mu_inputs"][0]["mu_input_host_stencil"]["x_coord"], f"MU IO positions are not found in glb_bank_config.json"
            mu_x_sequential = glb_bank_config["mu_inputs"][0]["mu_input_host_stencil"]["x_coord"]
        else:
            mu_x_sequential = [x for x in range(12, 28) for _ in range(2)]
        idx = 0
        for node in mu_io_nodes:
            (node.x, node.y) = (mu_x_sequential[idx], MU_IO_Y_COORD)
            # Only MU IOs can be placed at the same coordinate
            if (node.x, node.y) not in placed_pos:
                placed_pos.append((node.x, node.y))
            idx += 1

        # ----Place MU buffer MEMs----
        buffer_mem_nodes = []
        for mu_io_node in reversed(mu_io_nodes):
            assert len(mu_io_node.sinks) == 1, f"MU IO {mu_io_node.node_id} should have exactly one sink"
            sink_buffer_mem_node = mu_io_node.sinks[0]
            buffer_mem_nodes.append(sink_buffer_mem_node)
            (current_x, current_y) = (mu_io_node.x, mu_io_node.y)
            while_guard = 0
            while (current_x, current_y) in placed_pos or (current_x + 1) % 4 != 0:
                while_guard += 1
                if while_guard > 1000:
                    raise ValueError(f"while loop guard exceeded for MU buffer MEM {sink_buffer_mem_node.node_id}")
                if (current_x + 1) % 4 != 0:
                    current_x += 1
                elif (current_x, current_y) in placed_pos:
                    current_y -= 1
                if current_x < 12 or current_x > 28 or current_y < 1 or current_y > 17:
                    raise ValueError(f"Cannot find a valid position for the MU buffer MEM {sink_buffer_mem_node.node_id}, invalid position: ({current_x}, {current_y})")
            (sink_buffer_mem_node.x, sink_buffer_mem_node.y) = (current_x, current_y)
            placed_pos.append((current_x, current_y))

        # ----Place first stage of reduction tree PEs----
        first_stage_pe_nodes = []
        for buffer_mem_node in buffer_mem_nodes:
            for pe_sink_node in buffer_mem_node.sinks:
                if "op_hcompute_tree" in pe_sink_node.node_id and pe_sink_node.x is None and buffer_mem_node.y % 2 == 0:
                    first_stage_pe_nodes.append(pe_sink_node)
                    if buffer_mem_node.x < 20:
                        if (buffer_mem_node.x - 2, buffer_mem_node.y) not in placed_pos:
                            (pe_sink_node.x, pe_sink_node.y) = (buffer_mem_node.x - 2, buffer_mem_node.y)
                            placed_pos.append((buffer_mem_node.x - 2, buffer_mem_node.y))
                        else:
                            (pe_sink_node.x, pe_sink_node.y) = (buffer_mem_node.x - 2, buffer_mem_node.y - 1)
                            placed_pos.append((buffer_mem_node.x - 2, buffer_mem_node.y - 1))
                    else:
                        if (buffer_mem_node.x - 1, buffer_mem_node.y) not in placed_pos:
                            (pe_sink_node.x, pe_sink_node.y) = (buffer_mem_node.x - 1, buffer_mem_node.y)
                            placed_pos.append((buffer_mem_node.x - 1, buffer_mem_node.y))
                        else:
                            (pe_sink_node.x, pe_sink_node.y) = (buffer_mem_node.x - 1, buffer_mem_node.y - 1)
                            placed_pos.append((buffer_mem_node.x - 1, buffer_mem_node.y - 1))

        # ----Place second stage of reduction tree PEs----
        second_stage_pe_nodes = []
        first_stage_pe_nodes.sort(key=lambda node: node.y, reverse=True)
        for first_stage_pe_node in first_stage_pe_nodes:
            assert len(first_stage_pe_node.sinks) == 1, "Reduction tree PE should have only one sink node."
            if first_stage_pe_node.sinks[0].x is None:
                second_stage_pe_nodes.append(first_stage_pe_node.sinks[0])
                if first_stage_pe_node.x < 20:
                    (first_stage_pe_node.sinks[0].x, first_stage_pe_node.sinks[0].y) = (first_stage_pe_node.x + 1, first_stage_pe_node.y - 1)
                    placed_pos.append((first_stage_pe_node.x + 1, first_stage_pe_node.y - 1))
                else:
                    (first_stage_pe_node.sinks[0].x, first_stage_pe_node.sinks[0].y) = (first_stage_pe_node.x - 1, first_stage_pe_node.y - 1)
                    placed_pos.append((first_stage_pe_node.x - 1, first_stage_pe_node.y - 1))

        # ----Place third stage of reduction tree PEs----
        third_stage_pe_nodes = []
        second_stage_pe_nodes.sort(key=lambda node: node.y, reverse=True)
        for second_stage_pe_node in second_stage_pe_nodes:
            assert len(second_stage_pe_node.sinks) == 1, "Reduction tree PE should have only one sink node."
            if second_stage_pe_node.sinks[0].x is None:
                third_stage_pe_nodes.append(second_stage_pe_node.sinks[0])
                if second_stage_pe_node.x > 13:
                    (second_stage_pe_node.sinks[0].x, second_stage_pe_node.sinks[0].y) = (second_stage_pe_node.x, second_stage_pe_node.y - 2)
                    placed_pos.append((second_stage_pe_node.x, second_stage_pe_node.y - 2))
                else:
                    (second_stage_pe_node.sinks[0].x, second_stage_pe_node.sinks[0].y) = (second_stage_pe_node.x, second_stage_pe_node.y + 1)
                    placed_pos.append((second_stage_pe_node.x, second_stage_pe_node.y + 1))

        # ----Place fourth stage of reduction tree PEs----
        fourth_stage_pe_nodes = []
        third_stage_pe_nodes.sort(key=lambda node: node.x)
        for third_stage_pe_node in third_stage_pe_nodes:
            assert len(third_stage_pe_node.sinks) == 1, "Reduction tree PE should have only one sink node."
            if third_stage_pe_node.sinks[0].x is None:
                fourth_stage_pe_nodes.append(third_stage_pe_node.sinks[0])
                if third_stage_pe_node.x < 20:
                    (third_stage_pe_node.sinks[0].x, third_stage_pe_node.sinks[0].y) = (third_stage_pe_node.x + 2, third_stage_pe_node.y)
                    placed_pos.append((third_stage_pe_node.x + 2, third_stage_pe_node.y))
                else:
                    (third_stage_pe_node.sinks[0].x, third_stage_pe_node.sinks[0].y) = (third_stage_pe_node.x + 3, third_stage_pe_node.y)
                    placed_pos.append((third_stage_pe_node.x + 3, third_stage_pe_node.y))

        # ----Place fifth stage of reduction tree PEs----
        fifth_stage_pe_nodes = []
        fourth_stage_pe_nodes.sort(key=lambda node: node.x)
        for fourth_stage_pe_node in fourth_stage_pe_nodes:
            assert len(fourth_stage_pe_node.sinks) == 1, "Reduction tree PE should have only one sink node."
            if fourth_stage_pe_node.sinks[0].x is None:
                fifth_stage_pe_nodes.append(fourth_stage_pe_node.sinks[0])
                (fourth_stage_pe_node.sinks[0].x, fourth_stage_pe_node.sinks[0].y) = (fourth_stage_pe_node.x + 4, fourth_stage_pe_node.y)
                placed_pos.append((fourth_stage_pe_node.x + 4, fourth_stage_pe_node.y))

        # ----Place sixth stage of reduction tree PEs
        sixth_stage_pe_nodes = []
        fifth_stage_pe_nodes.sort(key=lambda node: node.y, reverse=True)
        for fifth_stage_pe_node in fifth_stage_pe_nodes:
            assert len(fifth_stage_pe_node.sinks) == 1, "Reduction tree PE should have only one sink node."
            if fifth_stage_pe_node.sinks[0].x is None:
                sixth_stage_pe_nodes.append(fifth_stage_pe_node.sinks[0])
                (fifth_stage_pe_node.sinks[0].x, fifth_stage_pe_node.sinks[0].y) = (fifth_stage_pe_node.x, fifth_stage_pe_node.y - 5)
                placed_pos.append((fifth_stage_pe_node.x, fifth_stage_pe_node.y - 5))

        # ----Place get-scale PE----
        assert len(sixth_stage_pe_nodes) == 1 and len(sixth_stage_pe_nodes[0].sinks) == 1
        get_scale_pe_node = sixth_stage_pe_nodes[0].sinks[0]
        (get_scale_pe_node.x, get_scale_pe_node.y) = (sixth_stage_pe_nodes[0].x, sixth_stage_pe_nodes[0].y - 3)
        placed_pos.append((sixth_stage_pe_nodes[0].x, sixth_stage_pe_nodes[0].y - 3))

        # # ----Place apply-scale PEs----
        # buffer_mem_nodes.sort(key=lambda node: node.y, reverse=True)
        # for buffer_mem_node in buffer_mem_nodes:
        #     current_x = buffer_mem_node.x
        #     current_y = buffer_mem_node.y
        #     for pe_sink_node in buffer_mem_node.sinks:
        #         if "apply_scale" in pe_sink_node.node_id:
        #             if buffer_mem_node.x in [15, 19]:
        #                 (pe_sink_node.x, pe_sink_node.y) = (current_x + 6, current_y - 8)
        #                 placed_pos.append((current_x + 6, current_y - 8))
        #                 current_x += 1
        #             elif buffer_mem_node.x in [23, 27]:
        #                 (pe_sink_node.x, pe_sink_node.y) = (current_x - 10, current_y - 8)
        #                 placed_pos.append((current_x - 10, current_y - 8))
        #                 current_x -= 1

        # ----Place quantized output pair MEMs and one of the data packing PEs----
        # Place one PE close to quantized output pair MEM to ensure MEM don't get data from two input ports at the same time
        # Place quantized output pair MEM first
        current_x = 15
        current_y = 1
        for mem_node in self.mem_nodes:
            if "mem_quantized_output_pair" in mem_node.node_id:
                (mem_node.x, mem_node.y) = (current_x, current_y)
                placed_pos.append((current_x, current_y))
                current_y += 1
                if current_y == 5:
                    current_y -= 4
                    current_x += 4
        for mem_node in self.mem_nodes:
            if "mem_quantized_output_pair" in mem_node.node_id:
                for pe_source in mem_node.sources:
                    if "data_packing_pair" in pe_source.node_id:
                        if mem_node.x < 20:
                            (pe_source.x, pe_source.y) = (mem_node.x - 1, mem_node.y)
                            placed_pos.append((mem_node.x - 1, mem_node.y))
                        else:
                            (pe_source.x, pe_source.y) = (mem_node.x - 3, mem_node.y)
                            placed_pos.append((mem_node.x - 3, mem_node.y))

        # Check placed_pos and expose repeated positions if any
        assert len(placed_pos) == len(set(placed_pos)), f"placed_pos contains duplicate positions: {placed_pos}"

        # # Hardcoded placement to ensure scale IOs paths are pipelined and one won't backpressure the other
        # for pe_node in self.pe_nodes:
        #     if "scale_output_data_packing" in pe_node.node_id:
        #         (pe_node.x, pe_node.y) = (13, 1)



        # # Place reduction tree stage 0 PEs right above MU IOs
        # for node in self.pe_nodes:
        #     if len(node.sources) == 2 and (all(source.node_type in ["U", "V"] for source in node.sources)):
        #         assert node.sources[0].x == node.sources[1].x, "Source MU IOs should locate at the same coordinate."
        #         current_x = node.sources[0].x
        #         current_y = node.sources[0].y - 1
        #         while (current_x, current_y) in placed_pos or (current_x + 1) % 4 == 0:
        #             if (current_x, current_y) in placed_pos:
        #                 # Position occupied, move to above
        #                 current_y -= 1
        #             elif (current_x + 1) % 4 == 0:
        #                 # This is MEM column, move to left
        #                 current_x -= 1
        #             if current_x < 12 or current_y < 1:
        #                 raise ValueError(f"Cannot find a valid position for the PE {node.node_id}, invalid position: ({current_x}, {current_y})")
        #         (node.x, node.y) = (current_x, current_y)
        #         placed_pos.append((current_x, current_y))

        # # Place activation buffering MEM tiles close to the MU IOs
        # for node in self.mem_nodes:
        #     if len(node.sources) == 1 and node.sources[0].node_type in ["U", "V"]:
        #         current_x = node.sources[0].x
        #         current_y = node.sources[0].y - 1
        #         while (current_x, current_y) in placed_pos or (current_x + 1) % 4 != 0:
        #             if (current_x, current_y) in placed_pos:
        #                 # Position occupied, move to above
        #                 current_y -= 1
        #             elif (current_x + 1) % 4 != 0:
        #                 # This is not MEM column, move to right
        #                 current_x += 1
        #         (node.x, node.y) = (current_x, current_y)
        #         placed_pos.append((current_x, current_y))

        # # Place reduction PEs as close as possible to each other
        # middle_x = 20
        # middle_y = 13
        # guard_cnt = 0
        # abs_max_reduction_pes = []
        # for node in self.pe_nodes:
        #     if len(node.sources) == 2 and len(node.sinks) == 1 and "float_abs_max" in node.node_id:
        #         abs_max_reduction_pes.append(node)
        # while any(node.x is None for node in abs_max_reduction_pes):
        #     guard_cnt += 1
        #     if guard_cnt > 1000:
        #         raise ValueError("Cannot find valid positions for the reduction PEs")
        #     for node in abs_max_reduction_pes:
        #         if node.x is not None or any(source.x is None for source in node.sources):
        #             # Already placed or sources not placed yet, skip
        #             continue
        #         elif node.sources[0].x is not None and node.sources[1].x is not None:
        #             current_x = node.sources[0].x if abs(node.sources[0].x - middle_x) < abs(node.sources[1].x - middle_x) else node.sources[1].x
        #             current_y = node.sources[0].y if abs(node.sources[0].y - middle_y) < abs(node.sources[1].y - middle_y) else node.sources[1].y
        #             while (current_x, current_y) in placed_pos or (current_x + 1) % 4 == 0:
        #                 if abs(current_x - middle_x) > abs(current_y - middle_y):
        #                     current_x += 1 if current_x < middle_x else -1
        #                 else:
        #                     current_y += 1 if current_y < middle_y else -1
        #                 if current_x < 12 or current_y < 1:
        #                     raise ValueError(f"Cannot find a valid position for the PE {node.node_id}, invalid position: ({current_x}, {current_y})")
        #             (node.x, node.y) = (current_x, current_y)
        #             placed_pos.append((current_x, current_y))

        # # Place apply scale PEs at least 5 hops away from MU IOs
        # hpwl_dist = 8
        # for node in self.pe_nodes:
        #     if "apply_scale" in node.node_id and any(source.node_type in ["U", "V"] for source in node.sources):
        #         for source in node.sources:
        #             if source.node_type in ["U", "V"]:
        #                 current_x = source.x
        #                 current_y = source.y - 1
        #                 while (current_x, current_y) in placed_pos or (current_x + 1) % 4 == 0 or abs(current_x - source.x) + abs(current_y - source.y) < hpwl_dist:
        #                     print(f"Trying to place PE {node.node_id} at ({current_x}, {current_y})")
        #                     if (current_x + 1) % 4 == 0:
        #                         # This is MEM column, move to left
        #                         current_x -= 1
        #                     elif current_y > 1:
        #                         current_y -= 1
        #                     elif current_x > 1:
        #                         current_x -= 1
        #                     else:
        #                         current_x += 1
        #                     if current_x < 12 or current_y < 1:
        #                         raise ValueError(f"Cannot find a valid position for the PE {node.node_id}, invalid position: ({current_x}, {current_y})")
        #         (node.x, node.y) = (current_x, current_y)
        #         placed_pos.append((current_x, current_y))

        # Write position info into file
        with open(app_dir + "/manual.place", "w") as f:
            for node in self.nodes:
                if node.x is not None:
                    f.write("{} {} {}\n".format(node.node_name, node.x, node.y))

    def manually_place_apply_scale_single_IO(self, app_dir):

        # Place scale output IOs using glb_bank_config.json
        glb_bank_config_path = os.path.join(app_dir, "glb_bank_config.json")
        if not os.path.exists(glb_bank_config_path):
            return

        with open(glb_bank_config_path, "r") as f:
            glb_bank_config = json.load(f)

        scale_output_x_coords = []
        for output_entry in glb_bank_config.get("outputs", []):
            hw_scale_cfg = output_entry.get("hw_scale_packed_output")
            if hw_scale_cfg is None:
                continue
            coords = hw_scale_cfg.get("x_coord", [])
            scale_output_x_coords.extend(coords)

        if not scale_output_x_coords:
            return

        def _extract_node_idx(node_id):
            match = re.search(r"clkwrk_(\d+)", node_id)
            return int(match.group(1)) if match else 0

        scale_output_nodes = [
            node
            for node in self.io_nodes
            if "io16_hw_scale_packed_output_stencil" in node.node_id
        ]

        if not scale_output_nodes:
            return

        scale_output_nodes.sort(key=lambda node: _extract_node_idx(node.node_id))

        for node, x_coord in zip(scale_output_nodes, scale_output_x_coords):
            node.x = x_coord
            node.y = 0

        # Place scale packing PE close to the first scale output IO
        if scale_output_nodes[0].x is not None:
            pe_x_coord = scale_output_nodes[0].x if scale_output_nodes[0].x >= 12 else 12
            pe_y_coord = 2
            for pe_node in self.pe_nodes:
                if scale_output_nodes[1] in pe_node.sinks:
                    pe_node.x = pe_x_coord
                    pe_node.y = pe_y_coord
                    break

        manual_place_path = os.path.join(app_dir, "manual.place")
        with open(manual_place_path, "w") as f:
            for node in self.nodes:
                if node.x is not None:
                    f.write(f"{node.node_name} {node.x} {node.y}\n")

    def manually_place_pe_mem_flush_test(self, app_dir):
        HALIDE_GEN_ARGS = os.environ.get("HALIDE_GEN_ARGS")
        mem_column_idx_match = re.search(r'mem_column_idx=(\d+)', HALIDE_GEN_ARGS)
        column_start_y_match = re.search(r'column_start_y=(\d+)', HALIDE_GEN_ARGS)
        assert mem_column_idx_match, "No mem_column_idx in HALIDE_GEN_ARGS. Please turn off MANUAL_PLACER or re-define HALIDE_GEN_ARGS for pe_mem_flush_test."
        assert column_start_y_match, "No column_start_y in HALIDE_GEN_ARGS. Please turn off MANUAL_PLACER or re-define HALIDE_GEN_ARGS for pe_mem_flush_test."
        mem_column_idx = int(mem_column_idx_match.group(1))
        column_start_y = int(column_start_y_match.group(1))
        assert (mem_column_idx + 1) % 4 == 0, "mem_column_idx + 1 must be divisible by 4"

        current_y = column_start_y
        for node in self.mem_nodes:
            node.x = mem_column_idx
            node.y = current_y
            current_y += 1

        manual_place_path = os.path.join(app_dir, "manual.place")
        with open(manual_place_path, "w") as f:
            for node in self.nodes:
                if node.x is not None:
                    f.write(f"{node.node_name} {node.x} {node.y}\n")
