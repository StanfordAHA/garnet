from lassen.cond import Cond_t
from lassen.mode import Mode_t
from lassen.lut import LUT_t_fc
from lassen.alu import ALU_t, Signed_t
from lassen.asm import inst
from hwtypes import BitVector
from peak.family import PyFamily

import json
import os
import six
import subprocess
import tempfile
from memory_core.memory_mode import Mode as MemoryMode
import copy

family = PyFamily()
ALU, Signed = ALU_t, Signed_t
Mode = Mode_t
LUT = LUT_t_fc(family)
Cond = Cond_t

# LUT constants
B0 = BitVector[8]([0,1,0,1,0,1,0,1])
B1 = BitVector[8]([0,0,1,1,0,0,1,1])
B2 = BitVector[8]([0,0,0,0,1,1,1,1])


def __get_alu_mapping(op_str):
    if op_str == "add":
        return ALU.Add, Signed.unsigned
    elif op_str == "mux":
        return ALU.Sel, Signed.unsigned
    elif op_str == "sub":
        return ALU.Sub, Signed.unsigned
    elif op_str == "mul" or op_str == "mult_0":
        return ALU.Mult0, Signed.unsigned
    elif op_str == "ashr":
        return ALU.SHR, Signed.signed
    elif op_str == "ule":
        return ALU.Sub, Signed.unsigned
    elif op_str == "uge":
        return ALU.Sub, Signed.unsigned
    elif op_str == "ult":
        return ALU.Sub, Signed.unsigned
    elif op_str == "ugt":
        return ALU.Sub, Signed.unsigned
    elif op_str == "sle":
        return ALU.Sub, Signed.unsigned
    elif op_str == "sge":
        return ALU.Sub, Signed.unsigned
    elif op_str == "slt":
        return ALU.Sub, Signed.unsigned
    elif op_str == "sgt":
        return ALU.Sub, Signed.unsigned
    elif op_str == "smax":
        return ALU.GTE_Max, Signed.signed
    elif op_str == "umax":
        return ALU.GTE_Max, Signed.unsigned
    elif op_str == "umin":
        return ALU.LTE_Min, Signed.unsigned
    elif op_str == "smin":
        return ALU.LTE_min, Signed.signed
    elif op_str == "sel":
        return ALU.Sel, Signed.unsigned
    elif op_str == "rshft":
        return ALU.SHR, Signed.unsigned
    elif op_str == "srshft":
        return ALU.SHR, Signed.signed
    elif op_str == "and":
        return ALU.And, Signed.unsigned
    elif op_str == "xor":
        return ALU.XOr, Signed.unsigned
    elif op_str == "or":
        return ALU.Or, Signed.unsigned
    elif op_str == "fadd":
        return ALU.FP_add, Signed.unsigned
    elif op_str == "fmul":
        return ALU.FP_mult, Signed.unsigned
    elif op_str == "abs":
        return ALU.Abs, Signed.signed
    elif op_str == "eq":
        return ALU.Sub, Signed.unsigned
    elif op_str == "neq":
        return ALU.Sub, Signed.unsigned
    else:
        print(op_str)
        raise NotImplemented


def __get_lut_mapping(op_str):
    value = int(op_str[3:], 16)
    value &= 0xFF
    return value


__PORT_RENAME = {
    "data.in.0": "data0",
    "data.in.1": "data1",
    "data.in.2": "data2",
    "data.out": "alu_res",
    "bit.in.0": "bit0",
    "bit.in.1": "bit1",
    "bit.in.2": "bit2",
    "bit.out": "alu_res_p",
}


def is_conn_out(raw_name):
    #port_names = ["out", "outb", "valid", "rdata", "res", "res_p", "io2f_16",
     #             "alu_res", "tofab", "data_out_0"]
    port_names = ["out", "outb", "valid", "rdata", "res", "res_p", "io2f_16",
                  "alu_res", "tofab", "data_out"]
    if isinstance(raw_name, six.text_type):
        raw_name = raw_name.split(".")
    if len(raw_name) > 1:
        raw_name = raw_name[1:]
    for name in port_names:
        if name == raw_name[-1]:
            return True
    return False


def is_conn_in(raw_name):
#    port_names = ["in", "wen", "cg_en", "ren", "wdata", "in0", "in1", "in",
 #                 "inb", "data0", "data1", "f2io_16", "clk_en", "fromfab",
  #                "data_in_0", "wen_in_0", "ren_in_0"]
    port_names = ["in", "wen", "cg_en", "ren", "wdata", "in0", "in1", "in",
                  "inb", "data0", "data1", "f2io_16", "clk_en", "fromfab",
                  "data_in", "wen_in", "ren_in"]
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


def rename_id_changed(id_to_name, changed_pe):
    new_changed_pe = set()
    for blk_id in changed_pe:
        # need to make sure ID to name is correct
        blk_name = id_to_name.pop(blk_id, None)
        assert (blk_name is not None)
        new_blk_id = "p" + blk_id[1:]
        id_to_name[new_blk_id] = blk_name
        new_changed_pe.add(new_blk_id)
    changed_pe.clear()
    changed_pe.update(new_changed_pe)


def determine_track_bus(netlists, id_to_name):
    track_mode = {}
    for net_id in netlists:
        net = netlists[net_id]
        bus = 16
        for blk_id, port in net:
            if "bit" in port or "en" in port:
                bus = 1
                break
            blk_name = id_to_name[blk_id]
            if "io1_" in blk_name:
                bus = 1
                break
            elif "outb" in port:
                bus = 1
                break
            elif "valid" in port:
                bus = 1
                break
            print(blk_id, port)
        track_mode[net_id] = bus
    return track_mode


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
                assert (next_blk is not None and
                        next_blk[0] != "c" and next_blk[0] != "r"
                        and next_blk[0] != "b")
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
            elif instance_type == "global.raw_dual_port_sram_tile":
                blk_type = "m"
            elif instance_type == "coreir.const":
                blk_type = "c"
            elif instance_type == "coreir.reg":
                blk_type = "r"
            else:
                raise Exception("Unknown instance type", instance_type)
        blk_id = blk_type + str(id_count)
        id_count += 1
        name_to_id[name] = blk_id
        print('Name:', name, 'blk_type: ', blk_type)
    return name_to_id


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


def get_ub_params(instance):
    genargs = instance["modargs"]
    ignored_params = {"width", "mode"}
    result = {}
    for name, (_, val) in genargs.items():
        if name in ignored_params:
            continue
        if name == "init":
            if val is not None:
                # preload everything at 512
                preload = []
                for idx, data in enumerate(val["init"]):
                    preload.append((idx + 512, data))
                result["content"] = preload
        else:
            val = int(val)
            result[name] = val
    return json.dumps(result)


def get_tile_op(instance, blk_id, changed_pe, rename_op=True):
    """rename_op (False) is used to calculate delay"""
    if "genref" not in instance:
        assert ("modref" in instance)
        assert (instance["modref"] in {"cgralib.BitIO", "corebit.reg"})
        return None, None
    pe_type = instance["genref"]
    if pe_type == "coreir.reg":
        # reg tile, reg in and reg out
        if blk_id in changed_pe:
            if rename_op:
                return "add", 0
            else:
                return "alu", 0
        else:
            return None, None
    elif pe_type == "global.raw_dual_port_sram_tile":
        if rename_op:
            # this depends on the mode
            mode = "sram"
            assert mode in {"sram", "linebuffer", "unified_buffer"}
            if mode == "linebuffer":
                op = "mem_lb_" + str(instance["modargs"]["depth"][-1])
            elif mode == "sram":
                op = "mem_sram_[]"
 #                    json.dumps(instance["modargs"]["init"][-1]["init"])
            else:
                op = "mem_ub_" + get_ub_params(instance)
        else:
            op = "mem"
        print_order = 3
    elif pe_type == "cgralib.Mem":
        if rename_op:
            # this depends on the mode
            mode = instance["modargs"]["mode"][-1]
            assert mode in {"sram", "linebuffer", "unified_buffer"}
            if mode == "linebuffer":
                op = "mem_lb_" + str(instance["modargs"]["depth"][-1])
            elif mode == "sram":
                op = "mem_sram_" + \
                     json.dumps(instance["modargs"]["init"][-1]["init"])
            else:
                op = "mem_ub_" + get_ub_params(instance)
        else:
            op = "mem"
        print_order = 3
    elif pe_type == "cgralib.IO":
        return None, None  # don't care yet
    else:
        print(instance)
        op = instance["genargs"]["op_kind"][-1]
        if op == "bit":
            lut_type = instance["modargs"]["lut_value"][-1][3:].lower()
            print_order = 0
            if lut_type == "3f":
                print_order = 2
            if rename_op:
                op = "lut" + lut_type.upper()
            else:
                op = "alu"
        elif op == "alu" or op == "combined":
            if "alu_op_debug" in instance["modargs"]:
                op = instance["modargs"]["alu_op_debug"][-1]
            else:
                op = instance["modargs"]["alu_op"][-1]
            if not rename_op:
                op = "alu"
            # get signed or unsigned
            if "signed" in instance["modargs"]:
                signed = instance["modargs"]["signed"][-1]
                if type(signed) != bool:
                    assert isinstance(signed, six.string_types)
                    signed = False if signed[-1] == "0" else True
                if signed and rename_op:
                    op = "s" + op
            print_order = 0
        else:
            raise Exception("Unknown PE op type " + op)
    return op, print_order


def get_blks(netlist):
    result = set()
    for _, blks in netlist.items():
        for blk in blks:
            if blk[0][0] != "I" and blk[0][0] != "i":
                result.add(blk[0])
    return result


def get_const_value(instance):
    if "modref" in instance:
        modref = instance["modref"]
        if modref == "corebit.const":
            val = instance["modargs"]["value"][-1]
            if val:
                return "const1_1"
            else:
                return "const0_0"
    elif "genref" in instance:
        genref = instance["genref"]
        if genref == "coreir.const":
            str_val = instance["modargs"]["value"][-1]
            if isinstance(str_val, int):
                int_val = str_val
            else:
                start_index = str_val.index("h")
                str_val = str_val[start_index + 1:]
                int_val = int(str_val, 16)
            return "const{0}_{0}".format(int_val)
    return None


def get_lut_pins(instance):
    assert ("genref" in instance and instance["genref"] == "cgralib.PE")
    assert ("genargs" in instance and
            instance["genargs"]["op_kind"][-1] == "bit")
    assert ("modargs" in instance)
    modargs = instance["modargs"]
    bit0_value = modargs["bit0_value"][-1]
    bit1_value = modargs["bit1_value"][-1]
    bit2_value = modargs["bit2_value"][-1]
    return int(bit0_value), int(bit1_value), int(bit2_value)


def get_tile_pins(blk_id, op, folded_block, instances, changed_pe,
                  id_to_name, connections):
    instance_name = id_to_name[blk_id]
    if op[:3] == "mem":
        return None
    if "lut" in op:
        lut_pins = get_lut_pins(instances[instance_name])
        pins = ["const{0}_{0}".format(i) for i in lut_pins]
        assert len(pins) == 3
    elif op[:3] == "mux" or op[:3] == "sel":
        pins = [None, None, None]
    else:
        pins = [None, None]

    # second pass to write wires
    for net in connections:
        for conn in net:
            pin_name = conn.split(".")[0]
            pin_port = ".".join(conn.split(".")[1:])
            if pin_name == instance_name and "out" not in pin_port:
                if (op == "mux" or op == "sel") and "bit.in.0" == pin_port:
                    index = 2
                elif pin_port != "in":
                    index = int(pin_port[-1])
                else:
                    index = 0
                pins[index] = "wire"

    # third pass to determine the consts/regs
    for entry in folded_block:
        entry_data = folded_block[entry]
        if len(entry_data) == 2:
            # reg folding
            assert (entry[0][0] == "r")
            b_id, port = entry_data
            pin_name = "reg"
        elif len(entry_data) == 3:
            b_id, pin_name, port = entry_data
            # it's constant
            pin_name = get_const_value(instances[pin_name])
        else:
            raise Exception("Unknown folded block data " + str(entry_data))
        if b_id == blk_id:
            # mux is very special
            if port == "bit0" and (op == "mux" or op == "sel"):
                index = 2
            else:
                index = int(port[-1])
            assert (pin_name is not None)
            pins[index] = pin_name
    if blk_id in changed_pe:
        pins[0] = "reg"
        pins[1] = "const0_0"

    if op == "abs":
        pins[1] = "const0_0"

    # sanity check
    for pin in pins:
        if pin is None:
            raise Exception("pin is none for blk_id: " + blk_id)

    return tuple(pins)


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
                    #port = "data_out_0"
                    port = "data_out"
                elif port == "wdata":
                    #port = "data_in_0"
                    port = "data_in"
                elif port == "ren":
                    #port = "ren_in_0"
                    port = "ren_in"
                elif port == "wen":
                    #port = "wen_in_0"
                    port = "wen_in"
                elif port == "addr":
                    port = "addr_in_0"
                elif port == "valid":
                    port = "valid_out_0"

            net[i] = blk_id, port
    return netlist


def wire_reset_to_flush(netlist, id_to_name, bus):
    # find all mem tiles and io reset
    mems = []
    io_blk = None
    for blk_id, name in id_to_name.items():
        if "cgramem" in name and "rom" not in name:
            assert blk_id[0] == "m"
            mems.append(blk_id)
        if "reset" in name and blk_id[0] in {"i", "I"}:
            io_blk = blk_id
    print("Found mems", mems, "io", io_blk)
    if io_blk is None:
        return
    reset_net_id = None
    for net_id, net in netlist.items():
        if net[0][0] == io_blk:
            reset_net_id = net_id
            break
    if reset_net_id is None:
        new_id = get_new_id("e", len(netlist), netlist)
        netlist[new_id] = [(io_blk, "io2f_1")]
        reset_net_id = new_id
        bus[new_id] = 1
    net = netlist[reset_net_id]
    for mem in mems:
        net.append((mem, "flush"))
        print("add flush to", mem)


def has_rom(id_to_name):
    # this is very hacky
    for blk_name in id_to_name.values():
        if "rom" in blk_name:
            return True
    return False


def get_new_id(prefix, init_num, groups):
    num = init_num
    while True:
        new_id = prefix + str(num)
        if new_id not in groups:
            return new_id
        num += 1


def insert_valid(id_to_name, netlist, bus):
    io_valid = None
    for net_id, net in netlist.items():
        if bus[net_id] != 1:
            continue
        for blk_id, port in net[1:]:
            blk_name = id_to_name[blk_id]
            if blk_id[0] in {"i", "I"} and "valid" in blk_name:
                return
    # need to insert the const 1 bit net as well
    alu_instr, _ = __get_alu_mapping("add")
    lut = __get_lut_mapping("lutFF")
    kargs = {}
    kargs["cond"] = Cond.LUT
    kargs["lut"] = lut
    instr = inst(alu_instr, **kargs)
    # adding a new pe block
    new_pe_blk = get_new_id("p", len(id_to_name), id_to_name)
    new_net_id = get_new_id("e", len(netlist), netlist)
    new_io_blk = get_new_id("i", len(id_to_name), id_to_name)
    netlist[new_net_id] = [(new_pe_blk, "res_p"), (new_io_blk, "f2io_1")]
    id_to_name[new_pe_blk] = "always_valid"
    id_to_name[new_io_blk] = "io1_valid"
    bus[new_net_id] = 1
    print("inserting net", new_net_id, netlist[new_net_id])


def remove_dead_regs(netlist, bus):
    pre_netlist_size = len(netlist)
    while True:
        net_id_remove = []
        for net_id, net in netlist.items():
            blk_to_remove = []
            for blk_id, port in net[1:]:
                if blk_id[0] != "r":
                    continue
                has_src = False
                for next_net_id, next_net in netlist.items():
                    if next_net[0][0] == blk_id and len(next_net) > 1:
                        has_src = True
                        break
                if not has_src:
                    blk_to_remove.append((blk_id, port))
            for entry in blk_to_remove:
                print("removing dead reg", blk_id)
                net.remove(entry)
            if len(net) == 1:
                net_id_remove.append(net_id)

        for net_id in net_id_remove:
            print("removing dead net", net_id)
            netlist.pop(net_id)
            bus.pop(net_id)

        if len(netlist) == pre_netlist_size:
            break
        pre_netlist_size = len(netlist)


def insert_reset(id_to_name):
    # insert reset if there isn't any
    for blk_id, blk_name in id_to_name.items():
        if blk_id[0] in {"i", "I"} and "reset" in blk_name:
            return blk_id
    new_io_blk = get_new_id("i", len(id_to_name), id_to_name)
    id_to_name[new_io_blk] = "io1in_reset"
    return new_io_blk


def split_ub(mem_blk, netlist, id_to_name, bus, instance_to_instr, instr_orig):
    depth = instr_orig["depth"]
    num_banks = (depth - 1) // 512  # this is additional banks

    blk_ids = []
    names = []
    for idx in range(num_banks):
        new_mem_blk_id = get_new_id("m", len(id_to_name), id_to_name)
        blk_ids.append(new_mem_blk_id)
        new_mem_blk_id_name = mem_blk + "_chain_cgramem_" + str(idx)
        id_to_name[new_mem_blk_id] = new_mem_blk_id_name
        names.append(new_mem_blk_id_name)
    blk_ids.append(mem_blk)

    for index in range(num_banks):
        new_mem_blk_id = blk_ids[index]
        new_mem_blk_id_name = id_to_name[new_mem_blk_id]
        print("splitting", mem_blk, "into", mem_blk, new_mem_blk_id,
              "name", new_mem_blk_id_name)
        instr = {}
        #instr.update(instr_orig)
      #  instr["depth"] = depth
       # instr["mode"] = MemoryMode.DB
   #     instr["chain_en"] = 1
    #    instr["chain_idx"] = index
     #   if index == 0:
 #           instr["chain_wen_in_sel"] = 1
  #          instr["chain_wen_in_reg"] = 0
        instance_to_instr[new_mem_blk_id_name] = instr

        # search for the fan out net
        for net_id, net in netlist.items():
            for (blk_id, port) in net[1:]:
                if blk_id == mem_blk and port == "wdata":
                    # we found the net
                    net.append((new_mem_blk_id, "wdata"))
                elif blk_id == mem_blk and port == "wen":
                    net.append((new_mem_blk_id, "wen"))
                elif blk_id == mem_blk and port =="ren":
                    net.append((new_mem_blk_id, "ren"))

        # chain the new block together
        new_net_id = get_new_id("e", len(netlist), netlist)
        bus[new_net_id] = 16
        netlist[new_net_id] = [(new_mem_blk_id, "chain_out"), (blk_ids[index + 1], "chain_in")]
        new_net_id = get_new_id("e", len(netlist), netlist)
        bus[new_net_id] = 1
        netlist[new_net_id] = [(new_mem_blk_id, "chain_valid_out"),
                               (blk_ids[index + 1], "chain_wen_in")]
    return names, num_banks


def insert_valid_delay(id_to_name, instance_to_instr, netlist, bus):
    # find out the valid out
    io_valid = None
    new_reg_id = None
    found = False
    for net_id, net in netlist.items():
        if bus[net_id] != 1:
            continue
        for idx, (blk_id, port) in enumerate(net[1:]):
            blk_name = id_to_name[blk_id]
            if blk_id[0] in {"i", "I"} and "valid" in blk_name:
                io_valid = (blk_id, port)
                # we have to create two new nets
                new_reg_id = get_new_id("p", len(id_to_name), id_to_name)
                id_to_name[new_reg_id] = "reg_valid_delay"
                # this is a lut as well with delay on one side
                alu_instr, _ = __get_alu_mapping("add")
                kargs = {}
                kargs["cond"] = Cond.LUT
                kargs["lut"] = B0
                kargs["rd_mode"] = Mode.DELAY
                instr = inst(alu_instr, **kargs)
                instance_to_instr[id_to_name[new_reg_id]] = instr

                # add a mux to the valid output
                new_pe_id = get_new_id("p", len(id_to_name), id_to_name)
                id_to_name[new_pe_id] = "reset_valid_reg"
                alu_instr, _ = __get_alu_mapping("add")
                kargs = {}
                kargs["cond"] = Cond.LUT
                kargs["lut"] = (B2 & B1) | ((~B2) & B0)
                kargs["re_mode"] = Mode.CONST
                kargs["re_const"] = 0
                instr = inst(alu_instr, **kargs)
                instance_to_instr[id_to_name[new_pe_id]] = instr

                new_net_id = get_new_id("e", len(netlist), netlist)
                netlist[new_net_id] = [(new_pe_id, "res_p"), (new_reg_id, "bit0")]
                bus[new_net_id] = 1

                net[1 + idx] = (new_pe_id, "bit0")

                # find the reset net
                reset_blk_id = insert_reset(id_to_name)
                reset_net_id = None
                for net_id, net in netlist.items():
                    if net[0][0] == reset_blk_id:
                        reset_net_id = net_id
                        break
                if reset_net_id is None:
                    reset_net_id = get_new_id("e", len(netlist), netlist)
                    netlist[reset_net_id] = [(reset_blk_id, "io2f_1")]
                    bus[reset_net_id] = 1
                netlist[reset_net_id].append((new_pe_id, "bit2"))
                found = True
                break
        if found:
            break

    assert io_valid is not None
    assert new_reg_id is not None
    new_net_id = get_new_id("e", len(netlist), netlist)
    print("adding delay reg net", new_net_id)
    netlist[new_net_id] = [(new_reg_id, "res_p"), io_valid]
    bus[new_net_id] = 1


def map_app(pre_map):
    with tempfile.NamedTemporaryFile() as temp_file:
        src_file = pre_map
        #src_file = temp_file.name
        #subprocess.check_call(["mapper", pre_map, src_file])
        netlist, folded_blocks, id_to_name, changed_pe = \
            parse_and_pack_netlist(src_file, fold_reg=True)
        rename_id_changed(id_to_name, changed_pe)
        bus = determine_track_bus(netlist, id_to_name)
        blks = get_blks(netlist)
        connections, instances = read_netlist_json(src_file)

    name_to_id = {}
    for blk_id in id_to_name:
        name_to_id[id_to_name[blk_id]] = blk_id

    instance_to_instr = {}
    for name in instances:
        instance = instances[name]
        blk_id = name_to_id[name]
        if blk_id in folded_blocks:
            continue
        blk_id = name_to_id[name]
        # it might be absorbed already
        if blk_id not in blks:
            continue

        # find out the PE type
        tile_op, _ = get_tile_op(instance, blk_id, changed_pe)
        if tile_op is None:
            continue
        pins = get_tile_pins(blk_id, tile_op, folded_blocks, instances,
                             changed_pe, id_to_name, connections)

        def get_mode(pin_name):
            if pin_name == "wire":
                return Mode.BYPASS, 0
            elif pin_name == "reg":
                return Mode.DELAY, 0
            else:
                assert "const" in pin_name
                return Mode.CONST, int(pin_name.split("_")[-1])
        if "mem" in tile_op:
            args = tile_op.split("_")
            mem_mode = args[1]
            instr = {}
            if mem_mode == "lb":
                instr["mode"] = MemoryMode.DB
                instr["depth"] = int(args[-1])
                if instr["depth"] > 512:
                    split_ub(blk_id, netlist, id_to_name, bus,
                             instance_to_instr, instr)
                    instr["chain_en"] = 1
                    instr["chain_idx"] = 0
            elif mem_mode == "sram":
                instr["mode"] = MemoryMode.SRAM
                content = json.loads(args[-1])
                instr["content"] = content
            elif mem_mode == "ub":
                instr["is_ub"] = True
                instr["mode"] = MemoryMode.DB
                params = json.loads("_".join(args[2:]))
                instr.update(params)
                if instr["depth"] > 512:
                    new_ub_names, idx = split_ub(blk_id, netlist, id_to_name,
                                           bus, instance_to_instr,
                                           instr)
                    instr["chain_en"] = 1
                    instr["chain_idx"] = idx
        else:
            ra_mode, ra_value = get_mode(pins[0])
            rb_mode, rb_value = get_mode(pins[1])

            kargs = {"ra_mode": ra_mode,
                     "rb_mode": rb_mode,
                     "ra_const": ra_value, "rb_const": rb_value}
            if len(pins) > 2 and "lut" not in tile_op:
                # it's a mux
                rd_mode, rd_value = get_mode(pins[2])
                kargs["rd_mode"] = rd_mode
                kargs["rd_const"] = rd_value
            if "lut" == tile_op[:3]:
                alu_instr, signed = __get_alu_mapping("add")
                lut = __get_lut_mapping(tile_op)
                kargs["cond"] = Cond.LUT
                kargs["lut"] = lut

                # lut has different mode names
                # this is fine because we never do packing for different widths
                rd_mode, rd_value = get_mode(pins[0])
                re_mode, re_value = get_mode(pins[1])
                rf_mode, rf_value = get_mode(pins[2])
                kargs["rd_mode"] = rd_mode
                kargs["re_mode"] = re_mode
                kargs["rf_mode"] = rf_mode
                kargs["rd_const"] = rd_value
                kargs["re_const"] = re_value
                kargs["rf_const"] = rf_value
            else:
                alu_instr, signed = __get_alu_mapping(tile_op)
                if tile_op == "uge":
                    kargs["cond"] = Cond.UGE
                elif tile_op == "ule":
                    kargs["cond"] = Cond.ULE
                elif tile_op == "ugt":
                    kargs["cond"] = Cond.UGT
                elif tile_op == "ult":
                    kargs["cond"] = Cond.ULT
                elif tile_op == "sge":
                    kargs["cond"] = Cond.SGE
                elif tile_op == "sle":
                    kargs["cond"] = Cond.SLE
                elif tile_op == "sgt":
                    kargs["cond"] = Cond.SGT
                elif tile_op == "slt":
                    kargs["cond"] = Cond.SLT
                elif tile_op == "eq":
                    kargs["cond"] = Cond.Z
                elif tile_op == "neq":
                    kargs["cond"] = Cond.Z_n
            kargs["signed"] = signed
            instr = inst(alu_instr, **kargs)
        instance_to_instr[name] = instr

    netlist = port_rename(netlist)
    insert_valid(id_to_name, netlist, bus)
    if has_rom(id_to_name):
        insert_valid_delay(id_to_name, instance_to_instr, netlist, bus)

    wire_reset_to_flush(netlist, id_to_name, bus)
    remove_dead_regs(netlist, bus)
    return id_to_name, instance_to_instr, netlist, bus
