"""Guards of the app-bundle power flow (mflowgen/CLAUDE.md "App bundles"):

- common/application/check_bundle.py: a bundle must match this build's spec,
  mode and tile RTL (tile ports + the MEM tile's lake controller ports).
- common/tile-post-*-power/run_all_tiles.py: every tile's sim must replay the
  recorded app run exactly ("cycle N: <port>: got X, expected Y" lines).
- sweep_specs.py: memtile_power.csv reports the replay result per level.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

MFLOWGEN = Path(__file__).resolve().parents[2] / "mflowgen"
APP = MFLOWGEN / "common" / "application"
LEVELS = ("rtl", "synth", "pnr")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(Path(path).parent))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.pop(0)
    return mod


# ------------------------------------------------------------ replay check --

RUN_ALL = MFLOWGEN / "common" / "tile-post-synth-power" / "run_all_tiles.py"


def test_run_all_tiles_copies_identical():
    texts = {lvl: (MFLOWGEN / "common" / f"tile-post-{lvl}-power" / "run_all_tiles.py").read_text()
             for lvl in LEVELS}
    assert len(set(texts.values())) == 1, "tile-post-{rtl,synth,pnr}-power/run_all_tiles.py differ"


def test_replay_result_parsing():
    rat = load(RUN_ALL, "run_all_tiles")
    log = ("xcelium> run\n"
           "cycle           3: SB_T0_EAST_SB_OUT_B17: got 0012, expected 0013\n"
           "cycle          40: SB_T0_EAST_SB_OUT_B17: got xxxx, expected 0000\n"
           "cycle          41: read_config_data: got 00000001, expected 00000002\n"
           "Simulation complete via $finish(2) at time 7539 NS + 0\n")
    r = rat.replay_result(log)
    assert r["finished"] and r["mismatches"] == 3 and r["x_mismatches"] == 1
    assert (r["first_cycle"], r["last_cycle"]) == (3, 41)
    assert r["ports"] == {"SB_T0_EAST_SB_OUT_B17": 2, "read_config_data": 1}
    assert r["examples"][1] == "cycle 40: SB_T0_EAST_SB_OUT_B17: got xxxx, expected 0000"
    assert len(r["lines"]) == 3
    clean = rat.replay_result("Simulation complete via $finish(2) at time 5 NS + 0\n")
    assert clean == {"finished": True, "mismatches": 0, "x_mismatches": 0, "first_cycle": None,
                     "last_cycle": None, "ports": {}, "examples": [], "lines": []}
    assert not rat.replay_result("xmsim: *F,INTERR: crashed\n")["finished"]


FAKE_RUN_SH = """#!/bin/bash
# stand-in for the per-tile sub-graph: a sim log + (unless NOHIER) a power report
mkdir -p $tile_id/3-cadence-xcelium-sim
log=$tile_id/3-cadence-xcelium-sim/xrun.log
: > $log
[ "$tile_id" = "$BAD_TILE" ] && echo "cycle 7: SB_T0_EAST_SB_OUT_B17: got 0001, expected 0002" >> $log
[ "$tile_id" = "$NOFINISH_TILE" ] || echo 'Simulation complete via $finish(2) at time 5 NS + 0' >> $log
[ "$tile_id" = "$NOHIER_TILE" ] || echo report > outputs/reports/$tile_id.hier
"""


def run_step(tmp_path, **env):
    (tmp_path / "inputs").mkdir(exist_ok=True)
    (tmp_path / "inputs" / "tiles_Tile_PE.list").write_text("p1,04,05\np2,05,06\n")
    (tmp_path / "run.sh").write_text(FAKE_RUN_SH)
    (tmp_path / "run.sh").chmod(0o755)
    full = dict(os.environ, design_name="Tile_PE")
    for k in ("replay_check", "app_bundle", "BAD_TILE", "NOFINISH_TILE", "NOHIER_TILE"):
        full.pop(k, None)
    full.update(env)
    r = subprocess.run([sys.executable, str(RUN_ALL)], cwd=tmp_path, env=full,
                       capture_output=True, text=True)
    summary = (tmp_path / "outputs" / "reports" / "replay_summary.txt").read_text()
    return r.returncode, summary, r.stdout + r.stderr


def test_step_clean(tmp_path):
    rc, summary, _ = run_step(tmp_path, app_bundle="/some/bundle")
    assert rc == 0 and "2/2 tiles replayed exactly" in summary
    rep = json.loads((tmp_path / "outputs/reports/Tile_X04_Y05.replay.json").read_text())
    assert rep["problems"] == [] and rep["finished"] and rep["report"]


@pytest.mark.parametrize("env,rc", [
    (dict(replay_check="fail"), 1),
    (dict(replay_check="warn", app_bundle="/b"), 0),
    (dict(replay_check="auto", app_bundle="/b"), 1),   # auto + bundle = fail
    (dict(app_bundle="/b"), 1),                        # unset = auto
    (dict(replay_check="auto"), 0),                    # auto, legacy (no bundle) = warn
])
def test_step_mismatch_modes(tmp_path, env, rc):
    got, summary, out = run_step(tmp_path, BAD_TILE="Tile_X05_Y06", **env)
    assert got == rc, out
    assert "Tile_X05_Y06: 1 replay mismatches (0 with x/z, cycles 7-7; SB_T0_EAST_SB_OUT_B17 1)" in summary
    assert "Tile_X04_Y05: OK" in summary and "1/2 tiles replayed exactly" in summary
    mm = (tmp_path / "outputs/reports/Tile_X05_Y06.mismatches.txt").read_text()
    assert mm == "cycle 7: SB_T0_EAST_SB_OUT_B17: got 0001, expected 0002\n"
    assert not (tmp_path / "outputs/reports/Tile_X04_Y05.mismatches.txt").exists()
    assert "lines" not in json.loads((tmp_path / "outputs/reports/Tile_X05_Y06.replay.json").read_text())


@pytest.mark.parametrize("bad,why", [("NOFINISH_TILE", "sim did not reach $finish"),
                                     ("NOHIER_TILE", "no power report")])
def test_step_incomplete_tile(tmp_path, bad, why):
    rc, summary, _ = run_step(tmp_path, app_bundle="/b", **{bad: "Tile_X04_Y05"})
    assert rc == 1 and f"Tile_X04_Y05: {why}" in summary


# ------------------------------------------------------------ check_bundle --

DESIGN_V = """module Tile_MemCore (
    input clk,
    input [16:0] SB_T0_EAST_SB_IN_B17,
    output [16:0] SB_T0_EAST_SB_OUT_B17,
    output [31:0] read_config_data
);
MemCore MemCore_inst0 (
    .clk(clk)
);
endmodule
module MemCore (
    input clk
);
lakespec_mem_flat mem_ctrl_lakespec_mem_flat (
    .clk(clk)
);
endmodule
module lakespec_mem_flat (
    input logic clk,
    input logic [{cfg_hi}:0] lakespec_mem_inst_config_memory,
    output logic [16:0] port_1_f_
);
endmodule
"""
SPEC = {"data_width": 16, "storage_capacity": 8192, "vec_width": 4, "in_ports": 2, "out_ports": 2}


def make_bundle(tmp_path, mode="rv", cfg_bits=1421):
    b = tmp_path / "bundle"
    b.mkdir()
    (b / "manifest.json").write_text(json.dumps({"app": "tests/conv_3_3", "mode": mode, "spec_config": SPEC,
                                                 "width": 16, "height": 16}))
    (b / "tile_ports.json").write_text(json.dumps({"Tile_MemCore": {
        "inputs": [["clk", 1], ["SB_T0_EAST_SB_IN_B17", 17]],
        "outputs": [["read_config_data", 32], ["SB_T0_EAST_SB_OUT_B17", 17]]}}))
    (b / "core_ports.json").write_text(json.dumps({
        "path": "MemCore_inst0.mem_ctrl_lakespec_mem_flat", "module": "lakespec_mem_flat",
        "inputs": [["clk", 1], ["lakespec_mem_inst_config_memory", cfg_bits]],
        "outputs": [["port_1_f_", 17]]}))
    (tmp_path / "spec.json").write_text(json.dumps(dict(SPEC, vec_capacity=2)))
    return b / "manifest.json"


def check(tmp_path, manifest, design_v_text=None, **kw):
    cb = load(APP / "check_bundle.py", "check_bundle")
    argv = [str(manifest)]
    for k, v in kw.items():
        argv += [f"--{k.replace('_', '-')}", v]
    if design_v_text is not None:
        dv = tmp_path / "design.v"
        dv.write_text(design_v_text)
        argv += ["--design-v", str(dv), "--design-name", "Tile_MemCore"]
    return cb.main(argv)


def test_check_bundle_ok(tmp_path, capsys):
    m = make_bundle(tmp_path)
    assert check(tmp_path, m, DESIGN_V.format(cfg_hi=1420), spec=str(tmp_path / "spec.json"), mode="rv") == 0
    assert "app bundle OK (spec+mode, Tile_MemCore ports" in capsys.readouterr().out


def test_check_bundle_stale_controller(tmp_path, capsys):
    # same spec + mode, controller config layout changed (lake 144e2062's case)
    m = make_bundle(tmp_path, cfg_bits=1453)
    assert check(tmp_path, m, DESIGN_V.format(cfg_hi=1420), spec=str(tmp_path / "spec.json"), mode="rv") == 1
    assert "lakespec_mem_inst_config_memory 1453 -> 1421" in capsys.readouterr().err


def test_check_bundle_tile_ports(tmp_path, capsys):
    m = make_bundle(tmp_path)
    narrow = DESIGN_V.format(cfg_hi=1420).replace("output [16:0] SB_T0_EAST_SB_OUT_B17,",
                                                  "output [15:0] SB_T0_EAST_SB_OUT_B17,\n    output extra_port,")
    assert check(tmp_path, m, narrow) == 1
    err = capsys.readouterr().err
    assert "SB_T0_EAST_SB_OUT_B17 17 -> 16" in err and "not in the bundle: extra_port" in err


def test_check_bundle_missing_module(tmp_path, capsys):
    m = make_bundle(tmp_path)
    assert check(tmp_path, m, "module Tile_PE (\n    input clk\n);\nendmodule\n") == 1
    assert "has no module Tile_MemCore" in capsys.readouterr().err


@pytest.mark.parametrize("kw,msg", [
    (dict(mode="static"), "mode rv != this build's static"),
    (dict(spec="", mode="rv"), "this build has no lake_spec_config"),
])
def test_check_bundle_spec_mode(tmp_path, capsys, kw, msg):
    m = make_bundle(tmp_path)
    assert check(tmp_path, m, **kw) == 1
    assert msg in capsys.readouterr().err


def test_check_bundle_other_spec(tmp_path, capsys):
    m = make_bundle(tmp_path)
    (tmp_path / "spec4096.json").write_text(json.dumps(dict(SPEC, storage_capacity=4096)))
    assert check(tmp_path, m, spec=str(tmp_path / "spec4096.json"), mode="rv") == 1
    assert "!= this build's" in capsys.readouterr().err


# ------------------------------------------------------------ sweep_specs --

def test_sweep_specs_replay_column(tmp_path):
    ss = load(MFLOWGEN / "sweep_specs.py", "sweep_specs")
    rep = tmp_path / "21-post-synth-power" / "outputs" / "reports"
    rep.mkdir(parents=True)
    (rep / "Tile_X03_Y02.hier").write_text("Tile_MemCore  1.0e-03  2.0e-03  3.0e-05  3.03e-03  100.0\n")
    (rep / "Tile_X03_Y02.replay.json").write_text(json.dumps({"problems": []}))
    (rep / "Tile_X07_Y05.replay.json").write_text(json.dumps({"problems": ["3 replay mismatches"]}))
    row = ss._tile_app_power_metrics(tmp_path, None)
    assert row["tile_synth_replay_exact"] == "1/2"
    assert row["tile_rtl_replay_exact"] is None and row["tile_pnr_replay_exact"] is None


PE_V = """module Tile_PE (
    input clk,
    input [16:0] SB_T0_EAST_SB_IN_B17,
    output [31:0] read_config_data
);
PondCore PondCore_inst0 (
    .clk(clk)
);
endmodule
module PondCore (
    input clk
);
{pond} {pond}_inst0 (
    .clk(clk)
);
endmodule
module {pond} (
    input logic clk,
    input logic [{cfg_hi}:0] config_memory
);
endmodule
"""


def make_pe_bundle(tmp_path, pond="PondTop", cfg_hi=99):
    import gzip
    b = tmp_path / "pe_bundle"
    b.mkdir()
    (b / "manifest.json").write_text(json.dumps({"app": "tests/conv_3_3", "mode": "static"}))
    (b / "tile_ports.json").write_text(json.dumps({"Tile_PE": {
        "inputs": [["clk", 1], ["SB_T0_EAST_SB_IN_B17", 17]], "outputs": [["read_config_data", 32]]}}))
    with gzip.open(b / "garnet.v.gz", "wt") as f:
        f.write(PE_V.format(pond=pond, cfg_hi=cfg_hi))
    return b / "manifest.json"


@pytest.mark.parametrize("built,cfg_hi,rc,msg", [
    ("PondTop", 99, 0, "app bundle OK (Tile_PE ports"),
    ("lakespec_pond", 99, 1, "pond module lakespec_pond != the bundle's PondTop (an RV-mode CGRA's PE tile has the RV spec pond: build Tile_PE with LAKE_SPEC_CONFIG"),
    ("PondTop", 63, 1, "pond PondTop ports: inputs width changed: config_memory 100 -> 64"),
])
def test_check_bundle_pe_pond(tmp_path, capsys, built, cfg_hi, rc, msg):
    m = make_pe_bundle(tmp_path)
    dv = tmp_path / "design.v"
    dv.write_text(PE_V.format(pond=built, cfg_hi=cfg_hi))
    cb = load(APP / "check_bundle.py", "check_bundle")
    assert cb.main([str(m), "--design-v", str(dv), "--design-name", "Tile_PE"]) == rc
    out = capsys.readouterr()
    assert msg in (out.out + out.err)
