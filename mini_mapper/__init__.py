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
from memory_core.memory_mode import MemoryMode as MemoryMode
from .netlist_util import read_netlist_json, parse_and_pack_netlist, port_rename


family = PyFamily()
ALU, Signed = ALU_t, Signed_t
Mode = Mode_t
LUT = LUT_t_fc(family)
Cond = Cond_t

# LUT constants
B0 = BitVector[8]([0, 1, 0, 1, 0, 1, 0, 1])
B1 = BitVector[8]([0, 0, 1, 1, 0, 0, 1, 1])
B2 = BitVector[8]([0, 0, 0, 0, 1, 1, 1, 1])


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
        return ALU.LTE_Min, Signed.signed
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
        track_mode[net_id] = bus
    return track_mode


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
    elif pe_type == "cgralib.Mem" or pe_type == "cgralib.Pond":
        if rename_op:
            # this depends on the mode
            mode = instance["modargs"]["mode"][-1]
            assert mode in {"sram", "linebuffer", "unified_buffer", "lake"}
            if mode == "lake":
                op = "mem_lake_{}"
            elif mode == "linebuffer":
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
    assert ("genargs" in instance and instance["genargs"]["op_kind"][-1] == "bit")
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


def wire_reset_to_flush(netlist, id_to_name, bus):
    # find all mem tiles and io reset
    mems = []
    io_blk = None
    for blk_id, name in id_to_name.items():
        if "cgramem" in name or "rom" in name or "lakemem" in name:
            if blk_id[0] not in {"m", "M"}:
                continue
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
    used_ports = set()
    for net in netlist.values():
        for port in net:
            used_ports.add(port)

    if reset_net_id is None:
        new_id = get_new_id("e", len(netlist), netlist)
        netlist[new_id] = [(io_blk, "io2f_1")]
        reset_net_id = new_id
        bus[new_id] = 1
    net = netlist[reset_net_id]
    for mem in mems:
        blk_port = (mem, "flush")
        if blk_port not in used_ports:
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


def get_app_name(name):
    path = os.path.dirname(name)
    app_name = os.path.basename(path)
    while app_name == "bin":
        path = os.path.dirname(path)
        app_name = os.path.basename(path)
    return app_name


def merge_row_buffer(id_to_name, netlist, bus):
    row_buffers = {}
    for blk_id, blk_name in id_to_name.items():
        if blk_id[0] != "m":
            continue
        if "lb" not in blk_name:
            continue
        # these is the row buffer
        prefix = blk_name.split("$")[0]
        if prefix not in row_buffers:
            row_buffers[prefix] = []
        row_buffers[prefix].append(blk_id)
    # sort blk id based on names. this will be the same ordering
    for name in row_buffers:
        row_buffers[name].sort(key=lambda x: id_to_name[x])

    # merge every interested row buffers
    for ids in row_buffers.values():
        first_id = ids[0]
        assert len(ids[1:]) == 1
        second_id = ids[1]
        # need to rename every output of the second id into the first one (second port)
        for net_id in netlist:
            for i in range(len(netlist[net_id])):
                blk_id, port_name = netlist[net_id][i]
                if blk_id == second_id and port_name == "data_out_0":
                    netlist[net_id][i] = (first_id, "data_out_1")
                elif blk_id == second_id and port_name == "valid_out_0":
                    netlist[net_id][i] = (first_id, "valid_out_1")
        # first pass to remove some netlist
        netlist_to_remove = set()
        for net_id in netlist:
            if netlist[net_id][0] == (first_id, "data_out_0"):
                netlist[net_id].remove((second_id, "data_in_0"))
            elif netlist[net_id][0] == (first_id, "valid_out_0"):
                netlist_to_remove.add(net_id)
            elif netlist[net_id][-1] == (second_id, "ren_in_0"):
                netlist_to_remove.add(net_id)
        for net_id in netlist_to_remove:
            netlist.pop(net_id)
            bus.pop(net_id)
        id_to_name.pop(second_id)


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


def rewire_valid(id_to_name, netlist, bus):
    valid_io = None
    mem_id = None
    for blk_id, blk_name in id_to_name.items():
        if blk_id[0] == "i" and "valid" in blk_name and valid_io is None:
            valid_io = blk_id
        if blk_id[0] == "m" and "lb" in blk_name and mem_id is None:
            mem_id = blk_id

    assert valid_io is not None
    assert mem_id is not None
    # rewrite the netlist
    net_to_edit = None
    for net_id in netlist:
        for blk_id, _ in netlist[net_id][1:]:
            if blk_id == valid_io:
                net_to_edit = net_id
                break
    netlist[net_id] = [(mem_id, "stencil_valid"), (valid_io, "io2f_1")]


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
        instr.update(instr_orig)
        instr["depth"] = depth
        instr["mode"] = MemoryMode.UNIFIED_BUFFER
        instr["chain_en"] = 1
        instr["chain_idx"] = index
        if index == 0:
            instr["chain_wen_in_sel"] = 1
            instr["chain_wen_in_reg"] = 0
        instance_to_instr[new_mem_blk_id_name] = instr

        # search for the fan out net
        for net_id, net in netlist.items():
            for (blk_id, port) in net[1:]:
                if blk_id == mem_blk and port == "wdata":
                    # we found the net
                    net.append((new_mem_blk_id, "wdata"))
                elif blk_id == mem_blk and port == "wen":
                    net.append((new_mem_blk_id, "wen"))
                elif blk_id == mem_blk and port == "ren":
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


def get_total_cycle_from_app(halide_src):
    # in some cases there are delay files in the same directory as halide
    # design top
    dirname = os.path.dirname(halide_src)
    config_file = os.path.join(dirname, "testing.json")
    if os.path.isfile(config_file):
        with open(config_file) as f:
            data = json.load(f)
            if "total_cycles" in data:
                return data["total_cycles"]
    return 0


def map_app(pre_map):
    src_file = pre_map
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
        if blk_id in folded_blocks or blk_id not in id_to_name:
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
            instr["name"] = name
            instr["app_name"] = get_app_name(pre_map)
            if "is_rom" in instance["genargs"] and instance["genargs"]["is_rom"][1] is True:
                instr.update(instance["modargs"])
                instr["mode"] = MemoryMode.ROM
            elif mem_mode == "lake":
                instr["depth"] = 0
                instr.update(instance["modargs"])
                instr["mode"] = MemoryMode.UNIFIED_BUFFER
            elif mem_mode == "lb":
                instr["mode"] = MemoryMode.UNIFIED_BUFFER
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
                instr["mode"] = MemoryMode.UNIFIED_BUFFER
                params = json.loads("_".join(args[2:]))
                instr.update(params)
                if "depth" in instr and instr["depth"] > 512:
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

    wire_reset_to_flush(netlist, id_to_name, bus)
    remove_dead_regs(netlist, bus)
    return id_to_name, instance_to_instr, netlist, bus
