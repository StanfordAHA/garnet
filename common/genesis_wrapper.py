import os
from typing import Union, List, Any, Dict
import magma as m


def run_genesis(top: str,
                in_file_or_files: Union[str, List[str]],
                parameters: dict,
                genesis_cmd: str = "Genesis2.pl"):
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
        return None
    return f"genesis_verif/{top}.v"


def define_genesis_generator(top_name: str=None,
                             input_files: List[str]=None,
                             param_mapping: Dict[str, str]=None,
                             **default_params):
    """
    `input_files` : a list of .vp files to pass to genesis
    `top_name`: the name of the top module
    `**kwargs`: the parameters to the generator and their default values
    `param_mapping`: (optional) a partial mapping between generator name and
        genesis name (used to rename parameters in the original genesis)
    ``

    """
    def define_from_genesis(*args, **kwargs):
        if args:
            raise NotImplementedError(
                "Currently only supports arguments passed explicity as kwargs"
                " Ideally we'd support no kwargs, or partial ordered args with"
                " kwargs. We would need to ensure they are consistent")
        parameters = {}
        for param, param_default in default_params.items():
            if param_mapping is not None and param in param_mapping:
                param = param_mapping[param]
            parameters[param] = kwargs.get(param, param_default)

        # Allow user to override default input_files
        _input_files = kwargs.get("input_files", input_files)

        outfile = run_genesis(top_name, _input_files, parameters)
        if outfile is None:
            return None
        return m.DefineFromVerilogFile(outfile)[0]
    return define_from_genesis
