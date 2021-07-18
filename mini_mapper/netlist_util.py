import json
import os
import six


def change_name_to_id(instances):
    name_to_id = {}
    id_count = 0
    instances_name = list(instances.keys())
    instances_name.sort()
    for name in instances_name:
        attrs = instances[name]
        if "genref" not in attrs:
            assert ("modref" in attrs)
            if attrs["modref"] == u"corebit.const":
                blk_type = "b"
            elif attrs["modref"] == u"cgralib.BitIO":
                blk_type = "i"
            elif attrs["modref"] == "alu_ns.PE" or attrs["modref"] == "lassen.PE":
                blk_type = "p"
            elif attrs["modref"] == "alu_ns.io16" or attrs["modref"] == "lassen.io16":
                blk_type = "I"
            elif attrs["modref"] == "corebit.reg":
                blk_type = "r"
            else:
                raise Exception("Unknown instance type " + str(attrs))
        else:
            # TODO: stupid 1 bit IO thing need to take care of
            instance_type = attrs["genref"]
            if instance_type == "cgralib.PE":
                blk_type = "p"
            elif instance_type == "cgralib.IO":
                blk_type = "I"
            elif instance_type == "cgralib.Mem":
                blk_type = "m"
            elif instance_type == "cgralib.Pond":
                blk_type = "M"
            elif instance_type == "coreir.const":
                blk_type = "c"
            elif instance_type == "coreir.reg":
                blk_type = "r"
            else:
                raise Exception("Unknown instance type", instance_type)
        blk_id = blk_type + str(id_count)
        id_count += 1
        name_to_id[name] = blk_id
    return name_to_id


def is_conn_out(raw_name):
    port_names = ["out", "outb", "valid", "rdata", "res", "res_p", "io2f_16",
                  "alu_res", "tofab", "data_out_0", "data_out_1",
                  "stencil_valid", "data_out_pond"]
    if isinstance(raw_name, six.text_type):
        raw_name = raw_name.split(".")
    if len(raw_name) > 1:
        raw_name = raw_name[1:]
    for name in port_names:
        if name == raw_name[-1]:
            return True
    return False


def is_conn_in(raw_name):
    port_names = ["in", "wen", "cg_en", "ren", "wdata", "in0", "in1", "in",
                  "inb", "data0", "data1", "f2io_16", "clk_en", "fromfab",
                  "data_in_0", "wen_in_0", "ren_in_0", "data_in_pond"]
    if isinstance(raw_name, six.text_type):
        raw_name = raw_name.split(".")
    if len(raw_name) > 1:
        raw_name = raw_name[1:]
    for name in port_names:
        if name == raw_name[-1]:
            return True
    return False


def convert2netlist(connections):
    netlists = []
    skip_index = set()
    for i in range(len(connections)):
        if i in skip_index:
            continue
        conn = connections[i]
        assert(len(conn) == 2)
        # brute force search
        net = [conn[0], conn[1]]
        for j in range(len(connections)):
            if i == j:
                continue
            conn0 = connections[j][0]
            conn1 = connections[j][1]

            if conn0 in net and conn1 not in net:
                net.append(conn1)
                skip_index.add(j)
            if conn1 in net and conn0 not in net:
                skip_index.add(j)
                net.append(conn0)

        def sort_value(key):
            raw_splits = key.split(".")
            if is_conn_in(raw_splits):
                return 2
            elif is_conn_out(raw_splits):
                return 0
            else:
                return 1
        # rearrange the net so that it's src -> sink
        net.sort(key=lambda p: sort_value(p))
        # sanity check to make sure that the first one is indeed an out
        assert (is_conn_out(net[0]))
        netlists.append(net)
    # print("INFO: before conversion connections", len(connections),
    #       "after conversion netlists:", len(netlists))
    return netlists


def read_netlist_json(netlist_filename):
    assert (os.path.isfile(netlist_filename))
    with open(netlist_filename) as f:
        raw_data = json.load(f)
    namespace = raw_data["namespaces"]
    # load design names
    top = raw_data["top"].split(".")[-1]
    design = namespace["global"]["modules"][top]
    instances = design["instances"]
    connections = design["connections"]
    # the standard json input is not a netlist
    connections = convert2netlist(connections)
    return connections, instances


def generate_netlists(connections, instances):
    """
    convert connection to netlists with (id, port).
    port is something like reg, data0, or const, or value, which will be packed
    later
    """
    name_to_id = change_name_to_id(instances)
    h_edge_count = 0
    netlists = {}
    for conn in connections:
        edge_id = "e" + str(h_edge_count)
        h_edge_count += 1
        hyper_edge = []
        for idx, v in enumerate(conn):
            raw_names = v.split(".")
            blk_name = raw_names[0]
            blk_id = name_to_id[blk_name]
            port = ".".join(raw_names[1:])
            # FIXME: don't care about these so far
            if port == "cg_en" or port == "clk_en":
                continue
            if port == "data.in.0" or port == "data0" or port == "in0":
                port = "data0"
            elif port == "data.in.1" or port == "data1" or port == "in1":
                port = "data1"
            elif port == "in" and "io1_" in v:
                port = "inb"
            elif port == "in":
                # either a reg or IO
                port = "in"
            elif port == "bit.in.0":
                port = "bit0"
            elif port == "bit.in.1":
                port = "bit1"
            elif port == "bit.in.2":
                port = "bit2"
            # need to be change to mem_in/mem_out in bitstream writer
            elif port == "rdata":
                port = "rdata"
            elif port == "wdata":
                port = "wdata"
            elif port == "addr":
                port = "addr"
            elif port == "data.out" or (port == "out" and "io1in" not in v):
                port = "out"
            elif port == "bit.out" or (port == "out" and "io1in" in v):
                port = "outb"
            elif port == "res":
                port = "res"
            elif port == "alu_res":
                port = "alu_res"
            elif port == "res_p":
                port = "res_p"
            elif port == "io2f_16" or port == "tofab":
                port = "io2f_16"
            elif port == "f2io_16" or port == "fromfab":
                port = "f2io_16"
            hyper_edge.append((blk_id, port))
        netlists[edge_id] = hyper_edge
    return netlists, name_to_id


def pack_netlists(raw_netlists, name_to_id, fold_reg=True):
    netlist_ids = set(raw_netlists.keys())
    folded_blocks = {}
    id_to_name = {}
    for name in name_to_id:
        id_to_name[name_to_id[name]] = name

    print("Absorbing constants and registers")
    changed_pe = set()
    dont_absorb = set()
    nets_to_remove = set()

    # first pass to figure out the reg's net connections
    connected_pe_tiles = {}
    for net_id in netlist_ids:
        net = raw_netlists[net_id]
        for index, (blk_id, port) in enumerate(net):
            if blk_id[0] == "r" and port == "out":
                for b_id, b_port in net:
                    if b_id == blk_id and port == b_port:
                        continue
                    if b_id[0] == "r":
                        # oh damn
                        dont_absorb.add(blk_id)
                    elif b_id[0] == "p":
                        if blk_id not in connected_pe_tiles:
                            connected_pe_tiles[blk_id] = set()
                        connected_pe_tiles[blk_id].add((b_id, b_port))

    for blk_id in connected_pe_tiles:
        connected = connected_pe_tiles[blk_id]
        if len(connected) > 1:
            # you can't drive two PE tiles. damn
            dont_absorb.add(blk_id)

    for net_id in netlist_ids:
        net = raw_netlists[net_id]
        remove_blks = set()
        for index, (blk_id, port) in enumerate(net):
            if index != len(net) - 1:
                next_index = index + 1
            else:
                next_index = None
            if next_index is None:
                next_blk, next_port = None, None
            else:
                next_blk, next_port = net[next_index]
            # replace them if they're already folded
            if (blk_id, port) in folded_blocks:
                net[index] = folded_blocks[blk_id]
                continue
            if blk_id[0] == "c" or blk_id[0] == "b":
                # FIXME:
                # it happens when a const connected to something
                # we don't care about yet
                if next_blk is None:
                    nets_to_remove.add(net_id)
                    break
                assert (next_blk is not None and next_blk[0] != "c" and next_blk[0] != "r" and next_blk[0] != "b")
                # absorb blk to the next one
                remove_blks.add((blk_id, id_to_name[next_blk], port))
                folded_blocks[(blk_id, port)] = (next_blk, id_to_name[blk_id],
                                                 next_port)
                # override the port to its name with index
                net[next_index] = (next_blk, id_to_name[blk_id])
            # NOTE:
            # disable reg folding to the same block that i's connected to
            elif blk_id[0] == "r":
                if blk_id not in dont_absorb and next_blk is not None and  \
                        len(net) == 2:
                    # only PE blocks can absorb registers
                    new_port = next_port
                    remove_blks.add((blk_id, id_to_name[next_blk], port))
                    folded_blocks[(blk_id, port)] = (next_blk, new_port)
                    # override the port to reg
                    net[next_index] = (next_blk, new_port)
                elif blk_id in dont_absorb:
                    changed_pe.add(blk_id)

        for entry in remove_blks:
            blk_id = entry[0]
            # print("Absorb", id_to_name[blk_id], "to", entry[1])
            item = (entry[0], entry[2])
            net.remove(item)
            assert (blk_id not in changed_pe)

        assert(len(net) > 0)

        # remove netlists
        if len(net) == 1:
            # a net got removed
            nets_to_remove.add(net_id)

    for net_id in nets_to_remove:
        # print("Remove net_id:", net_id, "->".join(
        #     ["{}::{}".format(id_to_name[blk], port)
        #     for blk, port in raw_netlists[net_id]]), file=sys.stderr)
        raw_netlists.pop(net_id, None)

    # second pass to reconnect nets
    for net_id in raw_netlists:
        net = raw_netlists[net_id]
        for index, (blk_id, port) in enumerate(net):
            if port == "in" and (blk_id, "out") in folded_blocks:
                # replace with new folded blocks
                net[index] = folded_blocks[(blk_id, "out")]

    # Keyi:
    # Improved routing so that we are able to allow src -> reg -> reg
    # remove the code while keep it in the git history in case in the future
    # we do need this kind of way to cope with long reg chains.
    if fold_reg:
        # re-do the change_pe
        changed_pe.clear()

    for blk_id in changed_pe:
        print("Change", id_to_name[blk_id], "to a PE tile")
        # rewrite the nets
        for net_id in raw_netlists:
            net = raw_netlists[net_id]
            for index, (b_id, port) in enumerate(net):
                if b_id == blk_id and port == "in":
                    # always fold at data0 port
                    b_id = "p" + b_id[1:]
                    net[index] = (b_id, "data0")
                elif b_id == blk_id and port == "out":
                    b_id = "p" + b_id[1:]
                    net[index] = (b_id, "out")

    if fold_reg:
        # last pass to change any un-folded register's port to "reg"
        for net_id in raw_netlists:
            net = raw_netlists[net_id]
            for index, (blk_id, port) in enumerate(net):
                if blk_id[0] == "r" and blk_id not in changed_pe:
                    net[index] = (blk_id, "reg")
    else:
        assert (len(changed_pe) == len(dont_absorb))
        for net_id in raw_netlists:
            net = raw_netlists[net_id]
            for blk_id, port in net:
                assert (port != "reg")

    return raw_netlists, folded_blocks, changed_pe


def parse_and_pack_netlist(netlist_filename, fold_reg=True):
    connections, instances = read_netlist_json(netlist_filename)
    netlists, name_to_id = generate_netlists(connections, instances)
    pes = set()
    ios = set()
    mems = set()
    regs = set()

    id_to_name = {}
    for name in name_to_id:
        blk_id = name_to_id[name]
        id_to_name[blk_id] = name

    for net_id in netlists:
        net = netlists[net_id]
        for blk_id, _ in net:
            if blk_id[0] == "p":
                pes.add(blk_id)
            elif blk_id[0] == "i" or blk_id[0] == "I":
                ios.add(blk_id)
            elif blk_id[0] == "m":
                mems.add(blk_id)
            elif blk_id[0] == "r":
                regs.add(blk_id)
    print("Before packing:")
    print("PE:", len(pes), "IO:", len(ios), "MEM:", len(mems), "REG:",
          len(regs))

    before_packing = len(netlists)
    netlists, folded_blocks, changed_pe = pack_netlists(netlists, name_to_id,
                                                        fold_reg=fold_reg)
    after_packing = len(netlists)
    print("Before packing: num of netlists:", before_packing,
          "After packing: num of netlists:", after_packing)

    pes = set()
    ios = set()
    mems = set()
    regs = set()

    id_to_name = {}
    for name in name_to_id:
        blk_id = name_to_id[name]
        id_to_name[blk_id] = name

    for net_id in netlists:
        net = netlists[net_id]
        for blk_id, _ in net:
            if blk_id[0] == "p":
                pes.add(blk_id)
            elif blk_id[0] == "i" or blk_id[0] == "I":
                ios.add(blk_id)
            elif blk_id[0] == "m":
                mems.add(blk_id)
            elif blk_id[0] == "r":
                regs.add(blk_id)
    print("After packing:")
    print("PE:", len(pes), "IO:", len(ios), "MEM:", len(mems), "REG:",
          len(regs))
    return netlists, folded_blocks, id_to_name, changed_pe


def port_rename(netlist):
    # this is for the garnet weird names
    for net_id in netlist:
        net = netlist[net_id]
        for i in range(len(net)):
            blk_id, port = net[i]
            if blk_id[0] == "I":
                if port == "in":
                    port = "f2io_16"
                else:
                    port = "io2f_16"
            elif blk_id[0] == "i":
                if port == "inb":
                    port = "f2io_1"
                else:
                    port = "io2f_1"
            elif blk_id[0] == "p":
                if port == "out":
                    port = "alu_res"
                elif port == "outb":
                    port = "res_p"
            elif blk_id[0] == "m":
                if port == "rdata":
                    port = "data_out_0"
                elif port == "wdata":
                    port = "data_in_0"
                elif port == "ren":
                    port = "ren_in_0"
                elif port == "wen":
                    port = "wen_in_0"
                elif port == "addr":
                    port = "addr_in_0"
                elif port == "valid":
                    port = "valid_out_0"

            net[i] = blk_id, port
    return netlist
