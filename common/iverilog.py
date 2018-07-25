import os


def iverilog(exe_name, files):
    if not os.system(f"iverilog -o {exe_name} {' '.join(files)}"):
        raise Exception(f"Could not compile verilog files {files} with "
                        "iverilog")
    return os.system(f"./{exe_name}")
