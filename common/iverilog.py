import os
import tempfile


def iverilog(files):
    with tempfile.TemporaryFile() as temp_file:
        if not os.system(f"iverilog -o {temp_file} {' '.join(files)}"):
            raise Exception(f"Could not compile verilog files {files} with "
                            "iverilog")
        return os.system(f"./{temp_file}")
