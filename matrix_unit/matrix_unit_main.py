from dataclasses import dataclass, field, asdict
import math
import os



def gen_param_header(top_name, params, output_folder):
    h_filename = os.path.join(output_folder, f"{top_name}.h")
    svh_filename = os.path.join(output_folder, f"{top_name}.svh")
    gen_header_files(params=params,
                     svh_filename=svh_filename,
                     h_filename=h_filename,
                     header_name="matrix_unit")

def gen_header_files(params, svh_filename, h_filename, header_name):
    # mod_params = asdict(params)

    folder = svh_filename.rsplit('/', 1)[0]
    # parameter pass to systemverilog package
    if not os.path.exists(folder):
        os.makedirs(folder)

    os.makedirs(os.path.dirname(svh_filename), exist_ok=True)
    with open(svh_filename, "w") as f:
        f.write(f"`ifndef {header_name.upper()}_PARAM\n")
        f.write(f"`define {header_name.upper()}_PARAM\n")
        f.write(f"package {header_name}_param;\n")
        for k, v in params.items():
            if type(v) is str:
                continue
            v = int(v)
            f.write(f"localparam int {k.upper()} = {v};\n")
        f.write("endpackage\n")
        f.write("`endif\n")

    os.makedirs(os.path.dirname(h_filename), exist_ok=True)
    with open(h_filename, "w") as f:
        f.write("#pragma once\n")
        for k, v in params.items():
            if type(v) is str:
                continue
            v = int(v)
            f.write(f"#define {k.upper()} {v}\n")

@dataclass
class Reg():
    name: str
    addr: int
    lsb: int
    msb: int


def gen_regspace_header(header_list, path: str):
    svh_path = path + '.svh'
    with open(svh_path, "w") as f:
        for header in header_list:
            if isinstance(header, Reg):
                f.write(f"`define {header.name} 'h{format(header.addr, 'x')}\n")
                f.write(f"`define {header.name + '_LSB'} {header.lsb}\n")
                f.write(f"`define {header.name + '_MSB'} {header.msb}\n")
            else:
                exception = f"Unknown header type: {type(header)}"
                raise TypeError(exception)

    h_path = path + '.h'
    with open(h_path, "w") as f:
        f.write(f"#pragma once\n")
        for header in header_list:
            if isinstance(header, Reg):
                f.write(f"#define {header.name} {hex(header.addr)}\n")
            else:
                exception = f"Unknown header type: {type(header)}"
                raise TypeError(exception)
