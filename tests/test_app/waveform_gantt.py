import networkx as nx
import sys
import argparse
import subprocess
import matplotlib
matplotlib.use('pdf')  # resolve the subplot() stuck issue
import matplotlib.pyplot as plt
import pdb

# might need the following package
# apt-get install libnuma-dev

# This version uses fsdbreport instead of fsdb2ns
def get_signal_duration(report_f, start_index):
    termination = "10000000100000000"
    # termination = "10100"
    dur_list = []
    cur_seg = []
    Started = False
    st_line = 1
    cur_line = 0
    with open(report_f, 'r') as file:
        for line in file:
            if cur_line < st_line:
                cur_line += 1
                continue
            line = line.split(",")
            if len(line) == 0:
                continue
            if int(line[start_index]) != 1 or int(line[start_index + 1]) != 1:
                continue
            # print(line[start_index], line[start_index + 1], line[start_index + 2])
            if not Started:
                cur_seg.append(int(line[0]))
                Started = True
            
            if Started:  # May have an empty fiber
                if termination in line[start_index + 2]:
                    cur_seg.append(int(line[0]))
                    seg = (cur_seg[0], cur_seg[1])
                    dur_list.append(seg)
                    # print(seg)
                    assert len(cur_seg) == 2
                    assert cur_seg[0] <= cur_seg[1]
                    cur_seg = []
                    Started = False
    # print(len(dur_list))
    # print(dur_list)
    return dur_list


def get_glb_duration(report_f, start_index, trx=1):
    dur_list = []
    cur_seg = []
    trx_cnt = 0
    TRX_ACT = False
    trx_length = 0
    st_line = 1
    cur_line = 0
    with open(report_f, 'r') as file:
        for line in file:
            if cur_line < st_line:
                cur_line += 1
                continue
            line = line.split(",")
            if len(line) == 0:
                continue
            if int(line[start_index]) != 1 or int(line[start_index + 1]) != 1:
                continue
            if not TRX_ACT:
                assert trx_length == 0
                if trx_cnt == 0:
                    cur_seg.append(int(line[0]))
                TRX_ACT = True
                trx_length = int(line[start_index + 2], 2)
                # print(trx_length)
                trx_cnt += 1
            else:
                trx_length -= 1
                if trx_length == 0:
                    TRX_ACT = False
                    if trx_cnt == trx:
                        trx_cnt = 0
                        cur_seg.append(int(line[0]))
                        seg = (cur_seg[0], cur_seg[1])
                        dur_list.append(seg)
                        assert len(cur_seg) == 2
                        assert cur_seg[0] <= cur_seg[1]
                        cur_seg = []
    # print(len(dur_list))
    # print(dur_list)
    return dur_list



def get_signal_report(fsdb_file, signal_list, output_f="signal_report.txt"):
    signal = []
    for s in signal_list:
        s_ = s[1:]
        for s_sub in s_:
            signal.extend(s_sub)
    signal_mul = " ".join(signal)
    cmd = f"fsdbreport {fsdb_file} -csv -s {signal_mul} -of b -o {output_f}"
    # print(cmd)
    subprocess.run(cmd, shell=True)
    st_index = 1
    all_durs_f = []
    for s in signal_list:
        print(s[0])  # For debugging
        all_durs = []
        

        if "glb" not in s[0]:
            for s_sub in s[1:]:
                dur = get_signal_duration(output_f, st_index)
                st_index += len(s_sub)
                if len(dur) == 0:
                    print("No signal")
                    continue
                else:
                    all_durs.append(dur)
        elif "_v" in s[0]:
            dur = get_glb_duration(output_f, st_index, trx=1)
            all_durs.append(dur)
            st_index += len(s[1])
        else:
            dur = get_glb_duration(output_f, st_index, trx=2)
            all_durs.append(dur)
            st_index += len(s[1])

        f_dur = []
        len_t = [len(i) for i in all_durs]
        max_len = max(len_t)
        all_durs = [i for i in all_durs if len(i) == max_len]  # Edge case of the root mode Repeat

        # print(s[0])
        # print(len_t)
        for i in range(len(all_durs[0])):
            st = -1
            ed = -1
            for j in range(len(all_durs)):
                if j == 0:
                    st = all_durs[j][i][0]
                    ed = all_durs[j][i][1]
                else:
                    st = min(st, all_durs[j][i][0])
                    ed = max(ed, all_durs[j][i][1])
            f_dur.append((st, ed-st))
        # print(f_dur)
        all_durs_f.append([s[0], f_dur])
    return all_durs_f

            
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

    # It has finer granularity than needed, just for potential future need
    # In the current version, the input duration is used as the gantt chart signals
    tile_dict = {
        "fiber_access": ["fiber_access_16", mem_tile, [["read_scanner_us_pos_in"], ["read_scanner_coord_out", "read_scanner_pos_out"]], ["write_scanner_data_in"]],
        "RepeatSignalGenerator": ["RepeatSignalGenerator", pe_tile, ["base_data_in"], ["repsig_data_out"]],
        "Repeat ": ["Repeat", pe_tile, ["repsig_data_in", "proc_data_in"], ["ref_data_out"]],
        "intersect": ["intersect_unit", pe_tile, ["coord_in_0", "coord_in_1", "pos_in_0", "pos_in_1"], ["coord_out", "pos_out_0", "pos_out_1"]],
        "union": ["intersect_unit", pe_tile, ["coord_in_0", "coord_in_1", "pos_in_0", "pos_in_1"], ["coord_out", "pos_out_0", "pos_out_1"]],
        "Mul": ["reduce_pe_cluster", pe_tile, ["data0", "data1"], ["res"]],
        "Add": ["reduce_pe_cluster", pe_tile, ["data0", "data2"], ["res"]],
        "CrdDrop": ["crddrop", pe_tile, ["cmrg_coord_in_0", "cmrg_coord_in_1"], ["cmrg_coord_out_0", "cmrg_coord_out_1"]],
        "CrdHold": ["crdhold", pe_tile, ["cmrg_coord_in_0", "cmrg_coord_in_1"], ["cmrg_coord_out_0", "cmrg_coord_out_1"]],  # TODO, verify this is correct
        "Reduce": ["reduce_pe_cluster", pe_tile, ["reduce_data_in"], ["reduce_data_out"]],
    }

    count = 0
    # colors = ["ID_YELLOW5", "ID_ORANGE5", "ID_RED5", "ID_CYAN4", "ID_PURPLE4", "ID_GREEN4"]
    # sample color from rainbow

    colors = plt.get_cmap('rainbow')(range(0, 256, 256 // 16))
    
    glb_write_signal = "fiber_access_16_inst/write_scanner/block_wr_in"
    
    clk = "/top/dut/clk_in"
    fsdb_file = "cgra.fsdb"
    report_f = "signal_report.txt"

    # Generate Signal RC
    signal_tracker = []
    cmds = []
    for tile in tiles:
        cmd_prefix = f"{prefix}{tile[1]}"
        sub_tracker = []
        for tile_type, (tile_name, tile_path, signals_in, signals_out) in tile_dict.items():
            if tile_type in tile[0]:
                count += 1
                sub_tracker.append(tile[0])
                if "fiber_access" in tile[0]:
                    if "X" not in tile[0] and "x" not in tile[0]:  # Use only the write signals
                        # for signal in signals_in[0]:
                        #     signal_rv = [f"{cmd_prefix}{tile_path}{tile_name}_flat/{signal}_{suffix}_" for suffix in ("ready_f", "valid_f", "f")]
                        #     sub_tracker.append(signal_rv)
                        
                        for signal in signals_in[1]:  # Avoid the issue with Val mode
                            signal_rv = [f"{cmd_prefix}{tile_path}{tile_name}_flat/{signal}_{suffix}_" for suffix in ("ready_f", "valid_f", "f")]
                            sub_tracker.append(signal_rv)

                        tile_name_display = tile[0] + "_glb_write"
                        if "v" in tile[0] or "V" in tile[0]:
                            tile_name_display = tile[0] + "_glb_write_v"
                            
                        glb_signal_rv = [f"{cmd_prefix}{tile_path}{tile_name}_flat/{glb_write_signal}{suffix}" for suffix in ("_ready", "_valid", "")]
                        signal_tracker.append([tile_name_display, glb_signal_rv])


                    else:  # Use only the read signals
                        for signal in signals_out:
                            signal_rv = [f"{cmd_prefix}{tile_path}{tile_name}_flat/{signal}_{suffix}_" for suffix in ("ready_f", "valid_f", "f")]
                            sub_tracker.append(signal_rv)

                else:
                    for signal in signals_in:
                        # group_cmd = f"addGroup {tile[0]}"
                        signal_rv = [f"{cmd_prefix}{tile_path}{tile_name}_flat/{signal}_{suffix}_" for suffix in ("ready_f", "valid_f", "f")]
                        sub_tracker.append(signal_rv)

                    # for signal in signals_out:
                    #     # group_cmd = f"addGroup {tile[0]}"
                    #     signal_rv = [f"{cmd_prefix}{tile_path}{tile_name}_flat/{signal}_{suffix}_" for suffix in ("ready_f", "valid_f", "f")]
                    #     sub_tracker.append(signal_rv)
        signal_tracker.append(sub_tracker)
    # print(signal_tracker)
    all_dur = get_signal_report(fsdb_file, signal_tracker, report_f)
    height = int(0.3 * len(all_dur))
    print(height)
    fig, ax = plt.subplots(figsize=(30, height))
    # fig, ax = plt.subplots()
    # ax.set_xlim(0, 40000000)
    y_ticks = [15 + 10 * i for i in range(len(all_dur))]
    y_labels = [i[0] for i in all_dur]
    y_labels.reverse()
    ax.set_yticks(y_ticks, labels=y_labels)
    for i, dur in enumerate(all_dur):
        for j, d in enumerate(dur[1]):
            if j < 3:
                ax.broken_barh([d], (y_ticks[len(all_dur) - 1 - i] - 5, 8), facecolors=colors[j % len(colors)])
            else:
                break
    plt.savefig("gantt.png")
    plt.cla()
    plt.clf()
    plt.close()


if __name__ == "__main__":
    main()
