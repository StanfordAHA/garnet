# need to run apt install graphviz
# python3 visualize_netlist.py Halide-to-Hardware/apps/hardware_benchmarks/apps/resnet_output_stationary/bin/design.packed tile_list
import sys
from graphviz import Digraph
import argparse

def node_to_tile_from_place(design_place_file):
    node_to_tile = {}
    with open(design_place_file, 'r') as f:
        lines = f.readlines()
        lines = lines[2:]
        for line in lines:
            print(line.strip())
            node_name = line.split()[-1].split("#")[1]
            print(f"Node name: {node_name}")
            tile_x = int(line.split()[1])
            tile_y = int(line.split()[2])
            print("Tile X: ", tile_x)
            print("Tile Y: ", tile_y)
            node_to_tile[node_name] = (tile_x, tile_y)
    return node_to_tile

def emit_signal_rc(ports_to_print, rc_file, node_to_tile, fsdb_file_path="cgra.fsdb"):

    boilerplate = ""
    boilerplate += f"openDirFile -d / \"\" \"{fsdb_file_path}\"\n"
    boilerplate += "\n"
    boilerplate += "; file time scale:\n"
    boilerplate += "\n"
    boilerplate += "cursor 0.000000\n"
    boilerplate += "marker 0.000000\n"
    boilerplate += "\n"
    boilerplate += "\n"
    boilerplate += "\n"
    boilerplate += "; user define markers\n"
    boilerplate += "; userMarker time_pos marker_name color linestyle\n"
    boilerplate += "; visible top row signal index\n"
    boilerplate += "\n"
    boilerplate += "\n"
    boilerplate += "\n"
    boilerplate += "COMPLEX_EVENT_BEGIN\n"
    boilerplate += "\n"
    boilerplate += "\n"
    boilerplate += "COMPLEX_EVENT_END\n"
    boilerplate += "\n"

    print(ports_to_print)

    for prim, port_dict in ports_to_print.items():

        print(node_to_tile)
        print("PRIM: ", prim)
        tile_x, tile_y = node_to_tile[prim]

        # format tile_x to be a two digit hex numbers
        tile_x = format(tile_x, '02x')
        tile_y = format(tile_y, '02x')

        if "m" in prim or "p" in prim:
            # Won't be expanded when opening....
            boilerplate += f"addGroup \"{prim}\" -e FALSE\n"
            boilerplate += f"activeDirFile \"\" \"{fsdb_file_path}\"\n"
            boilerplate += f"CMT_NODE_BEGIN\n"

            # Legend comment is of the form:
            # incoming:

            legend_cmt = f"\t{prim}:\n\n"
            # legend_cmt = f"{prim}"

            for port, _other_info_list in port_dict.items():
                legend_cmt += f"\t\t{port}:\n"
                for other_info in _other_info_list:
                    other_node, other_port, out_in_n = other_info
                    # Output
                    if out_in_n == 1:
                        legend_cmt += f"\t\t\t{port} -> {other_node}:{other_port}\n"
                    else:
                        legend_cmt += f"\t\t\t{other_node}:{other_port} -> {port}\n"

            boilerplate += f"-legendcmt \"{legend_cmt}\" -color ID_RED4 -h 45\n"
            boilerplate += f"CMT_NODE_END\n"

        if "m" in prim:
            # Deal with memory... (lakespec)
            # boilerplate += f"addSignal -h 15 /top/dut/Interconnect_inst0/Tile_X{tile_x}_Y{tile_y}/PE_inst0/PE_inner_W_inst0/PE_inner/clk\n"
            boilerplate += f"addSignal -h 15 /top/dut/Interconnect_inst0/Tile_X{tile_x}_Y{tile_y}/MemCore_inst0/MemCore_inner_W_inst0/MemCore_inner/clk\n"
            for port, _other_info_list in port_dict.items():
                boilerplate += f"addSignal -h 15 -holdScope flush\n"
                boilerplate += f"addSignal -h 15 -holdScope {port}[0:0]\n"
                boilerplate += f"addSignal -h 15 -holdScope {port}_ready\n"
                boilerplate += f"addSignal -h 15 -holdScope {port}_valid\n"
        elif "p" in prim:
            # Deal with PE...
            boilerplate += f"addSignal -h 15 /top/dut/Interconnect_inst0/Tile_X{tile_x}_Y{tile_y}/PE_inst0/PE_inner_W_inst0/PE_inner/clk\n"
            for port, _other_info_list in port_dict.items():
                boilerplate += f"addSignal -h 15 -holdScope flush\n"
                boilerplate += f"addSignal -h 15 -holdScope {port}[0:0]\n"
                boilerplate += f"addSignal -h 15 -holdScope {port}_ready\n"
                boilerplate += f"addSignal -h 15 -holdScope {port}_valid\n"

    with open(rc_file, 'w') as rc:
        rc.write(boilerplate)

if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Visualize a netlist.')
    parser.add_argument('--design_packed_file', type=str, help='The design.packed file')
    parser.add_argument('--design_place_file', type=str, help='The design.place file')
    parser.add_argument('--fsdb', type=str, help='FSDB filepath')
    parser.add_argument('--output_file', type=str, help='The output file')
    parser.add_argument('--rc_file', type=str, help='The rc file')
    label_edges = parser.add_argument('--label_edges', action='store_true', help='Label edges with source and destination ports')
    args = parser.parse_args()


    # Map
    ports_to_print = {}

    label_edges = args.label_edges
    design_packed_file = args.design_packed_file
    design_place_file = args.design_place_file
    output_file = args.output_file
    rc_file = args.rc_file
    fsdb = args.fsdb

    colors = {
    "p": "blue",
    "m": "orange",
    "M": "purple",
    "I": "green",
    "i": "green",
    "r": "red",
    }

    design_packed_file = open(design_packed_file, 'r')
    lines = design_packed_file.readlines()

    graph = Digraph()
    read_netlist = False
    for line in lines:
        if line == "\n":
            break
        if read_netlist:
            edge_id = line.split(":")[0]
            source = line.split("(")[1].split(")")[0].split(",")[0]
            graph.node(source, color=colors[source[0]])

            source_port = line.split("(")[1].split(")")[0].split(",")[1].strip()
            print(f"SOURCE: {source}")
            print(f"SOURCEPORT: {source_port}")

            if source not in ports_to_print:
                ports_to_print[source] = {}
            ports_to_print[source][source_port] = []

            for dest_line in line.split("\t")[1:]:
                dest = dest_line.split("(")[1].split(")")[0].split(",")[0]
                print(f"DEST: {dest}")
                graph.node(dest, color=colors[dest[0]])
                dest_port = dest_line.split("(")[1].split(")")[0].split(",")[1].strip()

                if dest not in ports_to_print:
                    ports_to_print[dest] = {}
                ports_to_print[dest][dest_port] = []

                print(f"DESTPORT: {dest_port}")
                if label_edges:
                    graph.edge(source, dest, label=f"{source_port} {dest_port}")
                else:
                    graph.edge(source, dest)

                ports_to_print[dest][dest_port].append((source, source_port, 0))
                ports_to_print[source][source_port].append((dest, dest_port, 1))

        if line == "Netlists:\n":
            read_netlist = True

    print("Ports to print:")
    for node, port_dict in ports_to_print.items():
        print(node)
        for port_, other_tuple_list in port_dict.items():
            print(f"\t{port_}")
            for other_tuple in other_tuple_list:
                other_node, other_port, out_in_n = other_tuple
                print("OTHER: ", other_node)
                print("OTHERPORT: ", other_port)
                print("OUT_IN_N: ", out_in_n)

    print("MEK")
    node_to_tile = node_to_tile_from_place(design_place_file)

    if rc_file is not None:
        print(f"Emitting rc file at {rc_file}")
        emit_signal_rc(ports_to_print, rc_file, node_to_tile, fsdb_file_path=fsdb)
    else:
        print("Skipping rc file emit...")

    graph.render(output_file)

