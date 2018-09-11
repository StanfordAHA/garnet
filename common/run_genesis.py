import os
from typing import Union, List, Any


def run_genesis(top: str,
                in_file_or_files: Union[str, List[str]],
                parameters: dict,
                genesis_cmd: str = "Genesis2.pl",
                system_verilog: bool = False):
    """
    Run genesis using the .vp file(s) @in_file_or_files using @parameters with
    the top as @top. Returns the path of the output verilog file if
    successfull; 'None' otherwise.
    """
    param_strs = [f"-parameter {top}.{k}='{str(v)}'"
                  for k, v in parameters.items()]
    files = in_file_or_files
    if isinstance(files, list):
        files = " ".join(files)

    cmd = (f"{genesis_cmd} -parse -generate -top {top} "
           f"-input {files} " + " ".join(param_strs))
    print(f"Running genesis cmd '{cmd}'")
    res = os.system(cmd)
    if not res == 0:
        raise RuntimeError(f"Genesis failed! cmd = {cmd}")
    return f"genesis_verif/{top}.{'sv' if system_verilog else 'v'}"
