import shutil
import os


def verilator_available():
    return shutil.which("verilator") is not None


def run_verilator(params: dict, top, files, test_driver):
    if not verilator_available():
        raise Exception("Verilator not available")  # pragma: nocover
    if len(files) == 0:
        print("Warning: verilator requires at least 1 input file. \
              Skipping verilator.")
        return True
    files_string = " ".join(files)
    verilator_cmd = f"verilator {files_string} --top-module {top} -cc -O3 \
            -Wno-fatal -exe {test_driver} --trace -CFLAGS \"-std=c++11\""
    param_strs = [f"-G{k}='{str(v)}'"
                  for k, v in params.items()]
    verilator_cmd = verilator_cmd + " " + " ".join(param_strs)
    if not os.system(verilator_cmd) == 0:
        return False
    make_cmd = f"make -C ./obj_dir -f V{top}.mk"
    if not os.system(make_cmd) == 0:
        return False
    preprocessor_strs = [f"{k} '{str(v)}'"
                         for k, v in params.items()]
    exe_cmd = f"./obj_dir/V{top} " + " ".join(preprocessor_strs)
    if not os.system(exe_cmd) == 0:
        return False

    return True
