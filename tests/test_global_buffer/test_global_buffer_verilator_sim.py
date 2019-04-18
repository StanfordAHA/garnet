import shutil
import os
import pytest


def verilator_available():
    return shutil.which("verilator") is not None


def run_verilator(parameters: dict, top, test_driver):
    if not verilator_available():
        raise Exception("Verilator not available")  # pragma: nocover
    param_strs = [f"-G{k}='{str(v)}'"
                  for k, v in parameters.items()]
    preprocessor_strs = [f"{k} '{str(v)}'"
                         for k, v in parameters.items()]
    verilator_cmd = f"verilator {top}.sv -cc -I{top}/genesis -O3 -Wno-fatal \
            -exe {test_driver} --trace -CFLAGS \"-std=c++11\""
    verilator_cmd = verilator_cmd + " " + " ".join(param_strs)
    if not os.system(verilator_cmd) == 0:
        return False
    make_cmd = f"make -C ./obj_dir -f V{top}.mk"
    if not os.system(make_cmd) == 0:
        return False
    exe_cmd = f"./obj_dir/V{top} " + " ".join(preprocessor_strs)
    if not os.system(exe_cmd) == 0:
        return False

    return True


def run_verilator_regression(params, top, test_driver):
    return run_verilator(params, top, test_driver)


@pytest.mark.skipif(not verilator_available(),
                    reason="verilator not available")
@pytest.mark.parametrize('params', [
    {
        "NUM_BANKS": 4,
        "BANK_DATA_WIDTH": 64,
        "BANK_ADDR_WIDTH": 10,
        "CONFIG_ADDR_WIDTH": 32,
        "CONFIG_DATA_WIDTH": 32
    }
])
def test_global_buffer_verilator(params):
    test_driver = f"tests/test_global_buffer/verilator/test_global_buffer.cpp"
    res = run_verilator_regression(params, "global_buffer", test_driver)
    assert res == 1
