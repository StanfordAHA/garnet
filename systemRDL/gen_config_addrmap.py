#!/usr/bin/env python3

import json
import argparse
from systemrdl import RDLCompiler, node
from dataclasses import dataclass


def convert_field(rdlc: RDLCompiler, obj: node.FieldNode) -> dict:
    json_obj = dict()
    json_obj['type'] = 'field'
    json_obj['inst_name'] = obj.inst_name
    json_obj['lsb'] = obj.lsb
    json_obj['msb'] = obj.msb
    json_obj['reset'] = obj.get_property('reset')
    json_obj['sw_access'] = obj.get_property('sw').name
    return json_obj


def convert_reg(rdlc: RDLCompiler, obj: node.RegNode) -> dict:
    if obj.is_array:
        # Use the RDL Compiler message system to print an error
        # fatal() raises RDLCompileError
        rdlc.msg.fatal(
            "JSON export does not support arrays",
            obj.inst.inst_src_ref
        )
    # Convert information about the register
    json_obj = dict()
    json_obj['type'] = 'reg'
    json_obj['inst_name'] = obj.inst_name
    json_obj['addr_offset'] = obj.address_offset

    # Iterate over all the fields in this reg and convert them
    json_obj['children'] = []
    for field in obj.fields():
        json_field = convert_field(rdlc, field)
        json_obj['children'].append(json_field)

    return json_obj


def convert_addrmap(rdlc: RDLCompiler, obj) -> dict:
    if obj.is_array:
        rdlc.msg.fatal(
            "JSON export does not support arrays",
            obj.inst.inst_src_ref
        )

    json_obj = dict()
    if isinstance(obj, node.AddrmapNode):
        json_obj['type'] = 'addrmap'
    elif isinstance(obj, node.RegfileNode):
        json_obj['type'] = 'regfile'
    else:
        raise RuntimeError

    json_obj['inst_name'] = obj.inst_name
    json_obj['addr_offset'] = obj.address_offset

    json_obj['children'] = []
    for child in obj.children():
        if isinstance(child, (node.AddrmapNode, node.RegfileNode)):
            json_child = convert_addrmap(rdlc, child)
        elif isinstance(child, node.RegNode):
            json_child = convert_reg(rdlc, child)

        json_obj['children'].append(json_child)

    return json_obj


def convert_to_json(rdl_json, path: str):
    # Write to a JSON file
    with open(path, "w") as f:
        json.dump(rdl_json, f, indent=4)


@dataclass
class Reg():
    name: str
    addr: int


@dataclass
class Field():
    name: str
    lsb: int
    msb: int


def convert_to_header(rdl_json, path: str):
    header_list = _convert_to_regmap(rdl_json, "", 0)
    svh_path = path + '.svh'
    with open(svh_path, "w") as f:
        for header in header_list:
            if isinstance(header, Reg):
                f.write(
                    f"`define {header.name}\t'h{format(header.addr, 'x')}\n")
            elif isinstance(header, Field):
                f.write(f"`define {header.name + '_F_LSB'}\t{header.lsb}\n")
                f.write(f"`define {header.name + '_F_MSB'}\t{header.msb}\n")

    h_path = path + '.h'
    with open(h_path, "w") as f:
        f.write(f"#pragma once\n")
        for header in header_list:
            if isinstance(header, Reg):
                f.write(f"#define {header.name}\t{hex(header.addr)}\n")
            elif isinstance(header, Field):
                f.write(f"#define {header.name + '_F_LSB'}\t{header.lsb}\n")
                f.write(f"#define {header.name + '_F_MSB'}\t{header.msb}\n")


def _convert_to_regmap(rdl_json, base_name, base_addr):
    header_list = []
    if rdl_json is None:
        return
    if base_name != "":
        base_name += "_"
    if rdl_json['type'] == 'addrmap' or rdl_json['type'] == 'regfile':
        name = base_name + rdl_json['inst_name']
        addr = base_addr + rdl_json['addr_offset']
        for child in rdl_json['children']:
            child_header_list = _convert_to_regmap(child, name, addr)
            header_list += child_header_list
    elif rdl_json['type'] == 'reg':
        name = base_name + rdl_json['inst_name']
        addr = base_addr + rdl_json['addr_offset']
        reg_name = (name + '_R_ADDR').upper()
        reg = Reg(name=reg_name, addr=addr)
        header_list.append(reg)
        # child
        for child in rdl_json['children']:
            child_header_list = _convert_to_regmap(child, name, addr)
            header_list += child_header_list
    elif rdl_json['type'] == 'field':
        field_name = (base_name + rdl_json['inst_name']).upper()
        lsb = rdl_json['lsb']
        msb = rdl_json['msb']
        field = Field(name=field_name, lsb=lsb, msb=msb)
        header_list.append(field)

    return header_list


def parse_arguments():
    # Create argument parser
    parser = argparse.ArgumentParser()

    # Arguments
    parser.add_argument("--rdl", nargs='+', default=[], required=True)
    parser.add_argument(
        "--output", help="systemRDL: output directory", type=str, default="")
    parser.add_argument(
        "--name", help="glb: name of the addrmap", type=str, default="addrmap")
    parser.add_argument("--json", help="export json", action='store_true')
    parser.add_argument("--html", help="export html", action='store_true')
    parser.add_argument("--header", help="export h and svh",
                        action='store_true')

    # Parse arguments
    args = parser.parse_args()

    return args
