import pytest
from common.run_verilog_sim import \
    irun, run_verilog_sim, irun_available, verilog_sim_available


def run_sim(run_func, available_func):
    files = ["test_common/hello_world.sv"]
    success = False
    try:
        res = run_func(files, top_name="hello_world", cleanup=True)
        success = res
    except Exception:
        success = False
    assert success == available_func()


def test_irun():
    run_sim(irun, irun_available)


@pytest.mark.skip(reason="iverilog is not supported")
def test_iverilog():
    run_sim(iverilog, iverilog_available)


def test_run_verilog_sim():
    run_sim(run_verilog_sim, verilog_sim_available)
