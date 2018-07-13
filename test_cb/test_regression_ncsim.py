import os
import magma as m
from cb.cb import define_cb
from common.genesis_wrapper import run_genesis
from common.util import make_relative
import pytest


@pytest.mark.skipif(os.environ.get("TRAVIS") == "true",
                    reason="ncsim not available on travis")
def run_ncsim_regression(params):
    # Magma version.
    # TODO(rsetaluri): factor out this code since it is exactly the same as
    # that in test_regression.py.
    magma_cb = define_cb(**params)
    m.compile(f"build/{magma_cb.name}", magma_cb, output='coreir')
    json_file = make_relative(f"build/{magma_cb.name}.json")
    magma_verilog = make_relative(f"build/{magma_cb.name}.v")
    os.system(f'coreir -i {json_file} -o {magma_verilog}')

    # Genesis version.
    genesis_outfile = run_genesis("cb", make_relative("cb.vp"), params)
    genesis_outfile = "genesis_verif/" + genesis_outfile
    genesis_outfile = genesis_outfile

    # Run ncsim.
    TCL_FILE = make_relative("cmd.tcl")
    tb_file = make_relative(f"{magma_cb.name}_tb.v")
    res = os.system("rm -rf INCA_libs irun.*")
    assert res == 0
    irun_cmd = f"irun -sv -top top -timescale 1ns/1ps -l irun.log -access" \
        f" +rwc -notimingchecks -input {TCL_FILE} {tb_file}" \
        f" {genesis_outfile} {magma_verilog}"  # nopep8
    print(f"Running irun cmd: {irun_cmd}")
    res = os.system(irun_cmd)
    assert res == 0


@pytest.mark.skipif(os.environ.get("TRAVIS") == "true",
                    reason="ncsim not available on travis")
def test_16_10_111110111_1_7():
    params = {
        "width": 16,
        "num_tracks": 10,
        "feedthrough_outputs": "1111101111",
        "has_constant": 1,
        "default_value": 7,
    }
    run_ncsim_regression(params)


@pytest.mark.skipif(os.environ.get("TRAVIS") == "true",
                    reason="ncsim not available on travis")
def test_7_8_11111111_0_0():
    params = {
        "width": 7,
        "num_tracks": 8,
        "feedthrough_outputs": "11111111",
        "has_constant": 0,
        "default_value": 0,
    }
    run_ncsim_regression(params)
