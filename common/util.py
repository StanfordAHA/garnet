import os
import magma as m
import tempfile


def compile_to_verilog(module, name, outpath, use_coreir=True):
    """
    Note(rsetaluri): Be wary calling this function! Multiple invocations of
    this function in the same runtime may not work due to a caching bug in
    magma.
    """
    verilog_file = f"{outpath}/{name}.v"
    if use_coreir:
        with tempfile.TemporaryDirectory() as temp_dir:
            m.compile(os.path.join(temp_dir, name), module, output="coreir")
            json_file = os.path.join(temp_dir, f"{name}.json")
            res = os.system(f"coreir -i {json_file} -o {verilog_file}")
            return res == 0
    print("Warning: compiling magma straight to verilog will not import "
          "CoreIR modules")
    m.compile(f"{verilog_file}", module, output="verilog")
    return True
