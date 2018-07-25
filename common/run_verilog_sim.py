import os
import tempfile
from common.util import irun_available, iverilog_available


TCL_FILE = "common/irun/cmd.tcl"


# We don't cover this function because irun is not available on travis
def irun(input_files,
         top_name="top",
         tcl_file=TCL_FILE,
         cleanup=True):  # pragma: nocover
    if len(input_files) == 0:
        print("Warning: irun requires at least 1 input file. Skipping irun.")
        return True
    files = " ".join(input_files)
    irun_cmd = f"irun -sv -top {top_name} -timescale 1ns/1ps -l irun.log " \
               f"-access +rwc -notimingchecks -input {tcl_file} {files}"
    print(f"Running irun cmd: {irun_cmd}")
    res = os.system(irun_cmd)
    if not res == 0:
        return False
    if cleanup:
        res = os.system("rm -rf verilog.vcd INCA_libs irun.*")
    return res == 0


def iverilog(files):
    with tempfile.TemporaryFile() as temp_file:
        if not os.system(f"iverilog -o {temp_file} {' '.join(files)}"):
            raise Exception(f"Could not compile verilog files {files} with "
                            "iverilog")
        return os.system(f"./{temp_file}") == 0


def run_verilog_sim(files):
    if irun_available():
        return irun(files)
    elif iverilog_available():
        return iverilog(files)
    else:
        raise Exception("Verilog simulator (irun/ncsim or iverilog) not "
                        "available")
