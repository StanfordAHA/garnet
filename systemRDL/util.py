import json
import argparse
import sys
import os
from systemrdl import RDLCompiler, node, RDLCompileError
from peakrdl.html import HTMLExporter
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
    lsb: int
    msb: int


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
                f.write(f"`define {header.name} 'h{format(header.addr, 'x')}\n")
                f.write(f"`define {header.name + '_LSB'} {header.lsb}\n")
                f.write(f"`define {header.name + '_MSB'} {header.msb}\n")
            elif isinstance(header, Field):
                f.write(f"`define {header.name + '_F_LSB'} {header.lsb}\n")
                f.write(f"`define {header.name + '_F_MSB'} {header.msb}\n")

    h_path = path + '.h'
    with open(h_path, "w") as f:
        f.write(f"#pragma once\n")
        for header in header_list:
            if isinstance(header, Reg):
                f.write(f"#define {header.name} {hex(header.addr)}\n")
            elif isinstance(header, Field):
                f.write(f"#define {header.name + '_F_LSB'} {header.lsb}\n")
                f.write(f"#define {header.name + '_F_MSB'} {header.msb}\n")


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
        reg_name = (name + '_R').upper()
        lsb = rdl_json['children'][0]['lsb']
        msb = rdl_json['children'][-1]['msb']
        reg = Reg(name=reg_name, addr=addr, lsb=lsb, msb=msb)
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


def gen_rdl_header(top_name, rdl_file, output_folder):
    # Generate HTML and addressmap header
    rdlc = RDLCompiler()
    try:
        rdlc.compile_file(rdl_file)
        # Elaborate the design
        root = rdlc.elaborate()
    except RDLCompileError:
        # A compilation error occurred. Exit with error code
        sys.exit(1)
    root = rdlc.elaborate()
    exporter = HTMLExporter()
    exporter.export(root, os.path.join(output_folder, f"{top_name}_html"))
    rdl_json = convert_addrmap(rdlc, root.top)
    convert_to_json(rdl_json, os.path.join(output_folder, f"{top_name}.json"))
    convert_to_header(rdl_json, os.path.join(output_folder, top_name))


def run_systemrdl(ordt_path, name, rdl_file, parms_file, output_folder):
    os.system(
        f"java -jar {ordt_path} -reglist {os.path.join(output_folder, name + '.reglist')}"
        f" -parms {parms_file} -systemverilog {output_folder} {rdl_file}")

def fix_systemrdl(rdl_folder, top_name):
    with open(os.path.join(rdl_folder, f"{top_name}_jrdl_decode.sv"), "r+") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if line.strip().startswith("pio_read_active <=  1'b0;"):
                lines.insert(i + 1, "      pio_dec_address_d1 <= 0;\n      pio_dec_write_data_d1 <= 0;\n")
                break
        f.seek(0)
        f.truncate()
        for line in lines:
            f.write(line)

