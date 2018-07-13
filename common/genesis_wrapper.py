import os


def run_genesis(top: str,
                infile: str,
                parameters: dict,
                genesis_cmd: str = "Genesis2.pl"):
    """
    Run genesis using the .vp file @infile using @parameters with the top as
    @top. Returns the path of the output verilog file if successfull; 'None'
    otherwise.
    """
    param_strs = [f"-parameter {top}.{k}='{str(v)}'"
                  for k, v in parameters.items()]
    cmd = f"{genesis_cmd} -parse -generate -top {top} -input {infile}"
    cmd += " " + " ".join(param_strs)
    print(f"Running genesis cmd '{cmd}'")
    res = os.system(cmd)
    if not res == 0:
        return None
    return f"genesis_verif/{top}.v"
