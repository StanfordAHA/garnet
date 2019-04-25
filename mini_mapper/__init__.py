import coreir
import lassen.mode as mode
from lassen.isa import gen_alu_type
from lassen.asm import inst
from lassen.family import gen_pe_type_family
from hwtypes import BitVector

family = gen_pe_type_family(BitVector.get_family())
alu_types = gen_alu_type(family)


def __get_alu_mapping(op_str):
    if op_str == "add":
        return alu_types.Add, False
    elif op_str == "mux":
        return alu_types.Sel, False
    elif op_str == "sub":
        return alu_types.Sub, False
    elif op_str == "mul":
        return alu_types.Mult0, False
    elif op_str == "ashr":
        return alu_types.SHR, True
    elif op_str == "ule":
        return alu_types.LTE_Min, False
    elif op_str == "uge":
        return alu_types.GTE_Max, False
    else:
        raise NotImplemented()


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


def map_app(src_file):
    context = coreir.Context()
    context.load_library("commonlib")
    mod = context.load_from_file(src_file)
    top_def = mod.definition

    instance_to_instr = {}
    id_to_name = {}
    instance_type = {}

    mode_type = mode.gen_mode_type(family)

    for instance in top_def.instances:
        inst_name = instance.selectpath[0]
        inst_type = instance.module.name
        namespace = instance.module.namespace.name

        op_kind = instance.module.generator_args["op_kind"].value
        instr = None
        if namespace == "cgralib" and inst_type == "PE":
            # it"s a PE
            if op_kind in {"alu", "combined"}:
                op_str = instance.config["alu_op"].value
                alu_op, signed = __get_alu_mapping(op_str)
                reg_modes = {"ra_mode": mode_type.BYPASS,
                             "rb_mode": mode_type.BYPASS}
                kargs = {"signed": int(signed)}
                kargs.update(reg_modes)
                instr = inst(alu_op, **kargs)
            else:
                assert op_kind == "bit"
                raise NotImplemented("lut")
            blk_id = f"P{len(id_to_name)}"
            id_to_name[blk_id] = inst_name
            instance_type[inst_name] = "PE"
        elif namespace == "cgralib" and inst_type == "Mem":
            # memory tile
            # only linebuffer is supported
            instr = instance.config["depth"].value
            blk_id = f"m{len(id_to_name)}"
            id_to_name[blk_id] = inst_name
            instance_type[inst_name] = "MEM"
        elif namespace == "coreir" and inst_type == "reg":
            # it"s a reg
            # no op
            alu_op, signed = __get_alu_mapping("add")
            reg_modes = {"ra_mode": mode_type.VALID,
                         "rb_mode": mode_type.CONST}
            reg_values = {"ra_const": 0, "rb_const": 0}
            kargs = {"signed": int(signed)}
            kargs.update(reg_modes)
            kargs.update(reg_values)
            instr = inst(alu_op, **kargs)
            blk_id = f"r{len(id_to_name)}"
            id_to_name[blk_id] = inst_name
            instance_type[inst_name] = "reg"
        elif namespace == "coreir" and inst_type == "const":
            # change it into a ADD
            value = instance.config["value"].value.as_uint()
            alu_op, signed = __get_alu_mapping("add")
            reg_modes = {"ra_mode": mode_type.CONST,
                         "rb_mode": mode_type.CONST}
            reg_values = {"ra_const": 0, "rb_const": value}
            kargs = {"signed": int(signed)}
            kargs.update(reg_modes)
            kargs.update(reg_values)
            instr = inst(alu_op, **kargs)
            blk_id = f"P{len(id_to_name)}"
            id_to_name[blk_id] = inst_name
            instance_type[inst_name] = "const"
        elif namespace == "cgralib" and inst_type == "IO":
            # 16-bit IO
            # no-op
            blk_id = f"I{len(id_to_name)}"
            id_to_name[blk_id] = inst_name
            instance_type[inst_name] = "IO"
        elif namespace == "cgralib" and inst_type == "BitIO":
            # 1-bit IO
            blk_id = f"i{len(id_to_name)}"
            id_to_name[blk_id] = inst_name
            instance_type[inst_name] = "PE"

        if instr is not None:
            instance_to_instr[inst_name] = instr

    # get name to id
    name_to_id = {}
    for blk_id, name in id_to_name.items():
        name_to_id[name] = blk_id

    netlist = {}
    src_list = {}
    bus = {}

    # now the netlist connections
    for conn in mod.directed_module.connections:
        src = conn.source
        dst = conn.sink
        src_name = src[0]
        dst_name = dst[0]
        src_id = name_to_id[src_name]
        dst_id = name_to_id[dst_name]

        def get_port_name(name_, is_src):
            inst_name_ = name_.split(".")
            inst_port_ = ".".join(name_.split(".")[1:])
            if inst_name_ not in instance_type:
                return None
            if instance_type[inst_name_] == "PE":
                return __PORT_RENAME[inst_port_]
            elif instance_type[inst_name_] == "reg":
                return "reg"
            elif instance_type[inst_name_] == "const":
                return "alu_res"
            elif instance_type[inst_name] == "I":
                return "io2f_16" if is_src else "f2io_16"
            elif instance_type[inst_name_] == "i":
                return "io2f_1" if is_src else "f2io_1"
            elif instance_type[inst_name_] == "MEM":
                return inst_port_
            else:
                raise ValueError(name)

        src_port = get_port_name(src_name, True)
        dst_port = get_port_name(dst_name, False)

        if src_port is None or dst_port is None:
            # drop the net
            continue
        curr = top_def
        for select_step in src:
            curr = curr.select(select_step)
        width = curr.type.size

        if src_name not in src_list:
            net_id = f"e{len(src_list)}"
            src_list[src_name] = net_id
            netlist[net_id] = [(name_to_id[src_name], src_port)]
            bus[net_id] = width
        net_id = src_list[src_name]
        assert bus[net_id] == width
        netlist[net_id].append((name_to_id[dst_name], dst_port))

    return id_to_name, instance_to_instr, netlist
