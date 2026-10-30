"""MemTile idle/active power sims (common/memtile-power-{test-gen,sim}).

The PnR level simulates the signoff netlist with its SDF and drives the inputs at the
tile SDC's arrival times (garnet/pnr-power-sim-no-sdf-race): without the SDF, one RV
output port of two thesis_dse tiles never moved in the signoff-netlist sim.
"""
import importlib.util
import os
import re
import subprocess
from pathlib import Path

import pytest

MFLOWGEN = Path(__file__).resolve().parents[2] / "mflowgen"
GEN = MFLOWGEN / "common" / "memtile-power-test-gen" / "gen_memtile_power_tests.py"
SIM = MFLOWGEN / "common" / "memtile-power-sim"
SDC = MFLOWGEN / "Tile_MemCore" / "constraints" / "common.tcl"


def load_gen():
    spec = importlib.util.spec_from_file_location("gen_memtile_power_tests", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_tb(tmp_path):
    pins = [("input", 1, "clk"), ("input", 1, "reset"), ("input", 1, "flush"), ("input", 1, "stall"),
            ("input", 16, "tile_id"), ("input", 32, "config_config_addr"), ("input", 32, "config_config_data"),
            ("input", 1, "config_write"), ("input", 9, "SB_T0_WEST_SB_IN_B9"), ("input", 1, "SB_T0_WEST_SB_IN_B9_valid"),
            ("output", 9, "SB_T0_EAST_SB_OUT_B9"), ("input", 1, "SB_T0_EAST_SB_OUT_B9_ready")]
    path = tmp_path / "testbench.active.sv"
    load_gen().write_testbench(path, "active", pins, [(0x10, 0x5)], 3, 10, {"SB_T0_WEST_SB_IN_B9": "rand"},
                               ["SB_T0_WEST_SB_IN_B9"], 4, {"SB_T0_EAST_SB_OUT_B9": 5}, 1.0)
    return path.read_text()


def test_testbench_drives_passthrough_inputs_at_pt_in_delay(tmp_path):
    tb = write_tb(tmp_path)
    # without the defines (synth level) both delays are the old 0.2 periods
    assert "`ifdef IN_DELAY\n    localparam real D = `IN_DELAY;\n`else\n    localparam real D = `CLK_PERIOD * 0.2;" in tb
    assert "`ifdef PT_IN_DELAY\n    localparam real DPT = `PT_IN_DELAY;\n`else\n    localparam real DPT = D;" in tb
    # passthrough inputs (reset, config, flush) wait DPT after the edge
    assert "#(DPT) reset = 1'b0;" in tb
    assert re.search(r"#\(DPT\);\n\s+config_config_addr = cfg_addr\[i\];", tb)
    assert re.search(r"#\(DPT\);\n\s+config_write = 1'b0;", tb)
    assert "#(DPT) flush = 1'b0;" in tb
    # switch-box inputs wait D: valid/ready and the first stimulus word at flush
    # release, then each later word
    release = tb[tb.index("        fork"):tb.index("        join")]
    assert "#(D);" in release
    for n in ("SB_T0_WEST_SB_IN_B9_valid = 1'b1;", "SB_T0_EAST_SB_OUT_B9_ready = 1'b1;",
              "SB_T0_WEST_SB_IN_B9 = stim[0 * N_STREAM];"):
        assert n in release
    assert "SB_T0_WEST_SB_IN_B9 <= #(D) stim[" in tb
    assert "#(D) reset" not in tb and not re.search(r"#\(D\);\n\s+config_", tb)


def test_sim_sdc_delays_match_constraints():
    """run_sim.sh's input arrival times are copies of the tile SDC (onyx values and
    the same env overrides): fail when the two drift apart."""
    sh = (SIM / "run_sim.sh").read_text()
    tcl = SDC.read_text()
    frac = re.search(r"^set i_delay \[expr ([0-9.]+) \* \$\{clock_period\}\]", tcl, re.M).group(1)
    pt = re.search(r"^set pt_i_delay ([0-9.]+)", tcl, re.M).group(1)
    assert float(re.search(r"SDC_I_DELAY_FRAC=([0-9.]+)", sh).group(1)) == float(frac)
    assert float(re.search(r"SDC_PT_I_DELAY_NS=([0-9.]+)", sh).group(1)) == float(pt)
    for env in ("TILE_I_DELAY_NS", "PT_I_DELAY_FRAC"):
        assert f"::env({env})" in tcl and "${" + env + ":-}" in sh


def run_sim(tmp_path, sdf, **env):
    """run_sim.sh in a step dir with a fake xrun that records its arguments."""
    step = tmp_path / "step"
    (step / "inputs" / "adk").mkdir(parents=True)
    for f in ("run_sim.sh", "cmd.tcl"):
        (step / f).write_text((SIM / f).read_text())
    for f in ("design.v", "testbench.sv"):
        (step / "inputs" / f).write_text("")
    if sdf:
        (step / "inputs" / "design.sdf").write_text("")
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    (bin_ / "xrun").write_text('#!/bin/sh\necho "$@" > xrun.args\n'
                               'echo "MEMTILE_POWER_TEST active PASS window=10" > logs/sim.log\ntouch run.saif\n')
    (bin_ / "xrun").chmod(0o755)
    full = dict(os.environ, PATH=f"{bin_}{os.pathsep}{os.environ['PATH']}", clock_period="1.493",
                variant="active", tool="XCELIUM")
    for k in ("TILE_I_DELAY_NS", "PT_I_DELAY_FRAC"):
        full.pop(k, None)
    full.update(env)
    res = subprocess.run(["bash", "run_sim.sh"], cwd=step, env=full, capture_output=True, text=True)
    assert res.returncode == 0, res.stdout + res.stderr
    return (step / "xrun.args").read_text().split(), step


def test_sim_synth_level_unchanged(tmp_path):
    args, step = run_sim(tmp_path, sdf=False, TILE_I_DELAY_NS="0.23", PT_I_DELAY_FRAC="0.25")
    assert "-notimingchecks" in args and "-nonotifier" not in args and "-sdf_cmd_file" not in args
    assert not [a for a in args if "IN_DELAY" in a]
    assert "+define+CLK_PERIOD=1.493" in args


@pytest.mark.parametrize("env,i_delay,pt_delay", [
    ({}, 0.2986, 0.7),                                                # onyx: 0.2 T, 0.7 ns
    ({"TILE_I_DELAY_NS": "0.23", "PT_I_DELAY_FRAC": "0.25"}, 0.23, 0.37325),  # thesis recipes
])
def test_sim_pnr_level_annotates_sdf(tmp_path, env, i_delay, pt_delay):
    args, step = run_sim(tmp_path, sdf=True, **env)
    assert "-nonotifier" in args and "-notimingchecks" not in args and "-negdelay" in args
    cmd = (step / args[args.index("-sdf_cmd_file") + 1]).read_text()
    assert 'SDF_FILE = "inputs/design.sdf"' in cmd and "SCOPE = testbench.dut," in cmd
    defs = dict(a[len("+define+"):].split("=") for a in args if a.startswith("+define+") and "=" in a)
    assert float(defs["IN_DELAY"]) == pytest.approx(i_delay)
    assert float(defs["PT_IN_DELAY"]) == pytest.approx(pt_delay)
