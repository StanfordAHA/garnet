import os


def run_genesis(top: str,
                infile: str,
                parameters: dict,
                genesis_cmd: str = "Genesis2.pl"):
    param_strs = [f"-parameter {top}.{k}='{str(v)}'"
                  for k, v in parameters.items()]
    cmd = f"{genesis_cmd} -parse -generate -top {top} -input {infile}"
    cmd += " " + " ".join(param_strs)
    print(f"Running cmd '{cmd}'")
    os.system(cmd)
    return f"{top}.v"
