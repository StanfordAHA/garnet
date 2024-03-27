import networkx as nx
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='Generates waveform_cmds.rc file for verdi.')
    parser.add_argument('bin_folder', help='bin folder with design files')
    args = parser.parse_args()

    # Call with bin folder 
    design_packed = args.bin_folder + 'design.packed'
    design_mapped = args.bin_folder + 'design.mapped'

    # Construct Graph from packed design
    edges = []
    with open(design_packed, 'r') as file:
        for line in file:
            if line.strip().startswith("e") and line.strip().endswith(")"):
                _, edge = line.strip().split(": ")
                src, dest = edge.split(")\t(")
                src = src.split(',')[0][1:]
                dest = dest.split(',')[0]
                edges.append((src, dest))

    # Create a NetworkX graph and add edges
    G = nx.DiGraph()
    G.add_edges_from(edges)

    # Topologically sort the graph
    topological_order = list(nx.topological_sort(G))

    # Remove GLB nodes from the topological order
    topological_order = [node for node in topological_order if "I" not in node]

    # Read in mapping
    with open(design_mapped, 'r') as file:
        # Read all lines into a list
        lines = file.readlines()

    tiles = []

    # Parse the lines to get the tile name, type, and location
    for line in lines:  
        tile_name = line.split("===>")[0].strip("\t").strip("\n")
        tile_type = line.split("===>")[1].strip("\t").strip("\n")
        tile_location = line.split("===>")[2].strip("\t").strip("\n")

        tiles.append((tile_name, tile_type, tile_location))

    # Create a dictionary mapping node names to their information
    info_dict = {node[0]: node[1:] for node in tiles}

    # Reorder the information array based on the topological order
    tiles = [info_dict[node] for node in topological_order if node in info_dict]

    # Change if Hardware Changes
    prefix = "/top/dut/Interconnect_inst0/Tile_"
    pe_tile = "/PE_inst0/PE_inner_W_inst0/PE_inner/mem_ctrl_"
    mem_tile = "/MemCore_inst0/MemCore_inner_W_inst0/MemCore_inner/mem_ctrl_"

    tile_dict = {
        "fiber_access": ["fiber_access_16", mem_tile, ["read_scanner_us_pos_in", "read_scanner_coord_out", "read_scanner_pos_out", "write_scanner_data_in"]],
        "RepeatSignalGenerator": ["RepeatSignalGenerator", pe_tile, ["base_data_in", "repsig_data_out"]],
        "Repeat ": ["Repeat", pe_tile, ["repsig_data_in", "proc_data_in", "ref_data_out"]],
        "intersect": ["intersect_unit", pe_tile, ["coord_in_0", "coord_in_1", "pos_in_0", "pos_in_1", "coord_out", "pos_out_0", "pos_out_1"]],
        "Mul": ["reduce_pe_cluster", pe_tile, ["data0", "data1", "res"]],
        "Add": ["reduce_pe_cluster", pe_tile, ["data0", "data1", "res"]],
        "CrdDrop": ["crddrop", pe_tile, ["cmrg_coord_in_0", "cmrg_coord_in_1", "cmrg_coord_out_0", "cmrg_coord_out_1"]],
        "Reduce": ["reduce_pe_cluster", pe_tile, ["reduce_data_in", "reduce_data_out"]],
    }

    count = 0
    colors = ["ID_YELLOW5", "ID_ORANGE5", "ID_RED5", "ID_CYAN4", "ID_PURPLE4", "ID_GREEN4"]

    # Generate Signal RC
    cmds = []
    for tile in tiles:
        cmd_prefix = f"addSignal -c {colors[count % len(colors)]} -ls solid -lw 1 -h 15 {prefix}{tile[1]}"
        for tile_type, (tile_name, tile_path, signals) in tile_dict.items():
            if tile_type in tile[0]:
                count += 1
                for signal in signals:
                    group_cmd = f"addGroup {tile[0]}"
                    signal_cmds = [f"{cmd_prefix}{tile_path}{tile_name}_flat/{signal}_{suffix}_" for suffix in ("f", "ready_f", "valid_f")]
                    cmds.extend([group_cmd] + signal_cmds)
                
    with open('waveform_cmds.rc', 'w') as file:
        for cmd in cmds:
            file.write(cmd + "\n")

if __name__ == "__main__":
    main()
