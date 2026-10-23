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
import re
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


def test_replay_waves_off_by_default():
    """A replayed tile's full-depth SHM is GBs at gate level and nothing reads
    it (power comes from the SAIF): a 16x16 dw16 cgra_app_power run filled
    166 GB with them. Env REPLAY_WAVES=True turns them back on."""
    for lvl in LEVELS:
        step = MFLOWGEN / "common" / f"tile-post-{lvl}-power"
        assert re.search(r"^\s*waves:\s*False\s*$", (step / "configure.yml").read_text(), re.M), lvl
        assert "os.environ.get('REPLAY_WAVES') or os.environ.get('waves')" in (step / "construct.py").read_text()


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
    assert r["checked_from"] is None
    clean = rat.replay_result("Simulation complete via $finish(2) at time 5 NS + 0\n")
    assert clean == {"finished": True, "checked_from": None, "app_start": None, "pre_app_x": 0,
                     "pre_app_x_examples": [], "mismatches": 0, "x_mismatches": 0,
                     "first_cycle": None, "last_cycle": None, "ports": {}, "examples": [], "lines": []}
    held = rat.replay_result("replay: reset held and outputs not checked before cycle 2 (first recorded reset)\n")
    assert held["checked_from"] == 2 and held["app_start"] is None


def test_replay_pre_app_x():
    """Before the app starts (first flush), X where the recording has a known
    value is reset-less state the recording zero-initialized: not a mismatch.
    Known-value mismatches before it, and X after it, still are."""
    rat = load(RUN_ALL, "run_all_tiles")
    log = ("replay: reset held and outputs not checked before cycle 2 (first recorded reset)\n"
           "replay: app starts at cycle 2404 (first flush after the reset)\n"
           "cycle 1201: SB_T0_EAST_SB_OUT_B17: got 0xxxx, expected 00000\n"
           "cycle 1202: SB_T0_WEST_SB_OUT_B17: got 0xxxx, expected 00000\n"
           "cycle 1300: read_config_data: got 00000001, expected 00000002\n"
           "cycle 2404: SB_T0_EAST_SB_OUT_B17: got 0xxxx, expected 00000\n"
           "Simulation complete via $finish(2) at time 7539 NS + 0\n")
    r = rat.replay_result(log)
    assert (r["checked_from"], r["app_start"], r["pre_app_x"]) == (2, 2404, 2)
    assert r["pre_app_x_examples"][0] == "cycle 1201: SB_T0_EAST_SB_OUT_B17: got 0xxxx, expected 00000"
    assert (r["mismatches"], r["x_mismatches"], r["first_cycle"], r["last_cycle"]) == (2, 1, 1300, 2404)
    assert r["ports"] == {"read_config_data": 1, "SB_T0_EAST_SB_OUT_B17": 1}
    only_pre = rat.replay_result("\n".join(log.splitlines()[:4]) + "\n")
    assert (only_pre["pre_app_x"], only_pre["mismatches"]) == (2, 0)
    assert not rat.replay_result("xmsim: *F,INTERR: crashed\n")["finished"]


FAKE_RUN_SH = """#!/bin/bash
# stand-in for the per-tile sub-graph: a sim log + (unless NOHIER) a power report
mkdir -p $tile_id/3-cadence-xcelium-sim
log=$tile_id/3-cadence-xcelium-sim/xrun.log
: > $log
[ "$tile_id" = "$BAD_TILE" ] && echo "cycle 7: SB_T0_EAST_SB_OUT_B17: got 0001, expected 0002" >> $log
[ "$tile_id" = "$PREAPP_TILE" ] && printf 'replay: app starts at cycle 100 (first flush after the reset)\ncycle 7: SB_T0_EAST_SB_OUT_B17: got 0xxxx, expected 00000\n' >> $log
[ "$tile_id" = "$NOFINISH_TILE" ] || echo 'Simulation complete via $finish(2) at time 5 NS + 0' >> $log
[ "$tile_id" = "$NOHIER_TILE" ] || echo report > outputs/reports/$tile_id.hier
# what a real sub-graph leaves behind: a sim snapshot, SAIF, input copies, a link out
mkdir -p $tile_id/3-cadence-xcelium-sim/xcelium.d $tile_id/3-cadence-xcelium-sim/outputs \
    $tile_id/1-setup/outputs $tile_id/.mflowgen $tile_id/4-synopsys-ptpx-synth
echo snap > $tile_id/3-cadence-xcelium-sim/xcelium.d/worklib.pak
echo saif > $tile_id/3-cadence-xcelium-sim/outputs/run.saif
echo step > $tile_id/3-cadence-xcelium-sim/mflowgen-run.log
echo vec > $tile_id/1-setup/outputs/test_vectors.txt
echo pt > $tile_id/4-synopsys-ptpx-synth/mflowgen-run.log
ln -sf "$PWD/inputs" $tile_id/1-setup/inputs_link
ln -sf "$PWD/inputs/tiles_Tile_PE.list" $tile_id/1-setup/outputs/xrun.log
"""


def run_step(tmp_path, **env):
    (tmp_path / "inputs").mkdir(exist_ok=True)
    (tmp_path / "inputs" / "tiles_Tile_PE.list").write_text("p1,04,05\np2,05,06\n")
    (tmp_path / "run.sh").write_text(FAKE_RUN_SH)
    (tmp_path / "run.sh").chmod(0o755)
    full = dict(os.environ, design_name="Tile_PE")
    for k in ("replay_check", "app_bundle", "BAD_TILE", "NOFINISH_TILE", "NOHIER_TILE", "REPLAY_KEEP_TILES"):
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


SLOW_RUN_SH = """#!/bin/bash
# a tile that takes a second: records when it ran, then reports like FAKE_RUN_SH
mkdir -p $tile_id/3-cadence-xcelium-sim
echo "$tile_id start $(date +%s.%N) queue=$SNPSLMD_QUEUE" >> times.log
sleep 1
echo 'Simulation complete via $finish(2) at time 5 NS + 0' > $tile_id/3-cadence-xcelium-sim/xrun.log
echo report > outputs/reports/$tile_id.hier
echo "$tile_id end $(date +%s.%N)" >> times.log
"""


@pytest.mark.parametrize("jobs,overlap", [("1", False), ("3", True)])
def test_step_replays_tiles_in_parallel(tmp_path, jobs, overlap):
    """REPLAY_TILE_JOBS=N runs N tiles' sub-graphs at once (each with its own
    tile_id and PrimeTime license queueing); the summary keeps the tile order."""
    (tmp_path / "inputs").mkdir()
    (tmp_path / "inputs" / "tiles_Tile_PE.list").write_text("a,01,01\nb,02,01\nc,03,01\n")
    (tmp_path / "run.sh").write_text(SLOW_RUN_SH)
    (tmp_path / "run.sh").chmod(0o755)
    env = dict(os.environ, design_name="Tile_PE", app_bundle="/b", REPLAY_TILE_JOBS=jobs)
    r = subprocess.run([sys.executable, str(RUN_ALL)], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    summary = (tmp_path / "outputs" / "reports" / "replay_summary.txt").read_text().splitlines()
    assert summary[:3] == [f"Tile_X0{i}_Y01: OK" for i in (1, 2, 3)]
    ev = [line.split() for line in (tmp_path / "times.log").read_text().splitlines()]
    assert all(e[3] == "queue=true" for e in ev if e[1] == "start")
    starts = sorted(float(e[2]) for e in ev if e[1] == "start")
    first_end = min(float(e[2]) for e in ev if e[1] == "end")
    assert (starts[1] < first_end) == overlap


def test_replay_tools_queue_for_licenses():
    run_sim = (MFLOWGEN / "common" / "cadence-xcelium-sim" / "run_sim.sh").read_text()
    replay = run_sim[run_sim.index('if [ "${app_replay:-False}" = "True" ]'):]
    assert "-licqueue" in replay.split("\nfi\n")[0]


def tree(d):
    return sorted(str(p.relative_to(d)) for p in d.rglob("*") if p.is_file() or p.is_symlink())


def test_step_prunes_replayed_tiles(tmp_path):
    """Once a tile's reports are written, its sub-workspace keeps only its logs
    (a 16x16 cgra_app_power run filled the build disk with snapshots, SAIFs and
    vector copies); symlinks are removed, not followed."""
    rc, summary, _ = run_step(tmp_path, app_bundle="/b")
    assert rc == 0 and "2/2 tiles replayed exactly" in summary
    assert tree(tmp_path / "Tile_X04_Y05") == ["3-cadence-xcelium-sim/mflowgen-run.log",
                                               "3-cadence-xcelium-sim/xrun.log",
                                               "4-synopsys-ptpx-synth/mflowgen-run.log"]
    assert (tmp_path / "inputs" / "tiles_Tile_PE.list").read_text().startswith("p1,")
    assert (tmp_path / "outputs" / "reports" / "Tile_X05_Y06.hier").is_file()


def test_step_keeps_tiles_on_request(tmp_path):
    rc, _, _ = run_step(tmp_path, app_bundle="/b", REPLAY_KEEP_TILES="True")
    assert rc == 0
    assert "3-cadence-xcelium-sim/xcelium.d/worklib.pak" in tree(tmp_path / "Tile_X04_Y05")


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


def test_step_pre_app_x_passes(tmp_path):
    rc, summary, out = run_step(tmp_path, app_bundle="/b", PREAPP_TILE="Tile_X05_Y06")
    assert rc == 0, out
    assert "Tile_X05_Y06: OK (1 X outputs before the app start at cycle 100 not counted)" in summary
    assert "2/2 tiles replayed exactly" in summary
    rep = json.loads((tmp_path / "outputs/reports/Tile_X05_Y06.replay.json").read_text())
    assert (rep["pre_app_x"], rep["app_start"], rep["mismatches"]) == (1, 100, 0)


@pytest.mark.parametrize("bad,why", [("NOFINISH_TILE", "sim did not reach $finish"),
                                     ("NOHIER_TILE", "no power report")])
def test_step_incomplete_tile(tmp_path, bad, why):
    rc, summary, _ = run_step(tmp_path, app_bundle="/b", **{bad: "Tile_X04_Y05"})
    assert rc == 1 and f"Tile_X04_Y05: {why}" in summary


# ---------------------------------------------------------------- testbench --

TB_GEN = MFLOWGEN / "common" / "testbench" / "generate_testbench.py"


def test_testbench_pads_short_tiles(tmp_path, monkeypatch):
    """One testbench serves every tile: it runs the longest tile's vector count
    and a shorter tile's files get its last vector repeated (an untouched tile
    can have fewer simvisdbutil rows than a placed one); it used to run past
    the end of them -> spurious mismatches."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "inputs").mkdir()
    (tmp_path / "inputs" / "manifest.json").write_text(json.dumps({"scope": "tb.dut"}))
    (tmp_path / "inputs" / "tile_ports.json").write_text(json.dumps(
        {"Tile_PE": {"inputs": [["clk", 1], ["SB_IN", 17]], "outputs": [["SB_OUT", 17]]}}))
    (tmp_path / "inputs" / "tiles_Tile_PE.list").write_text("idle,0E,10\nop,01,01\n")
    gt = load(TB_GEN, "generate_testbench")
    rows = {"Tile_X0E_Y10": 3, "Tile_X01_Y01": 5}
    current = {}
    monkeypatch.setattr(gt, "generate_raw", lambda tile, i, o: current.update(tile=tile))

    def fake_convert(signals, inp, out):
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        n = rows[current["tile"]]
        Path(out).write_text("".join(f"{k:04x}\n" for k in range(n)))
        return n, {s: 17 for s in signals}
    monkeypatch.setattr(gt, "convert_raw", fake_convert)
    monkeypatch.setenv("design_name", "Tile_PE")
    gt.main()
    assert "`define NUM_TEST_VECTORS 5" in (tmp_path / "testbench.sv").read_text()
    for name in ("test_vectors.txt", "test_outputs.txt"):
        assert (tmp_path / "outputs/tile_tbs/Tile_X0E_Y10" / name).read_text().split() == \
            ["0000", "0001", "0002", "0002", "0002"]
        assert len((tmp_path / "outputs/tile_tbs/Tile_X01_Y01" / name).read_text().split()) == 5


@pytest.mark.parametrize("bundle", [True, False])
def test_testbench_holds_reset_until_first_recorded(tmp_path, monkeypatch, bundle):
    """Bundle replays drive reset until the recording's first reset and skip
    the checks before it (gate-level flops are X until then); the legacy
    testbench is unchanged."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "inputs").mkdir()
    (tmp_path / "inputs" / "manifest.json").write_text(json.dumps({"scope": "tb.dut"} if bundle else {}))
    gt = load(TB_GEN, "generate_testbench")
    assert gt.app_bundle is bundle
    gt.create_testbench("Tile_MemCore", ["reset", "stall", "SB_IN"], ["SB_OUT"],
                        {"reset": 1, "stall": 1, "SB_IN": 17}, {"SB_OUT": 17}, 10, ["clk"],
                        hold_reset=gt.app_bundle)
    tb = (tmp_path / "testbench.sv").read_text()
    if not bundle:
        assert "first_reset" not in tb
        assert "wire reset = test_vectors[test_vector_addr][`SLICE_RESET];" in tb
        assert "if (SB_OUT != test_outputs[test_vector_addr][`SLICE_SB_OUT] || $isunknown(SB_OUT)) begin" in tb
        assert "always #(`CLK_PERIOD/2) clk =~clk;" in tb
        return
    assert "wire reset = test_vectors[test_vector_addr][`SLICE_RESET] | (test_vector_addr < first_reset);" in tb
    assert ("if (test_vector_addr >= first_reset && (SB_OUT != test_outputs[test_vector_addr][`SLICE_SB_OUT]"
            " || $isunknown(SB_OUT))) begin") in tb
    assert tb.index("integer first_reset;") < tb.index("wire reset =")
    assert "#(`CLK_PERIOD * 4);\n      forever #(`CLK_PERIOD/2) clk = ~clk;" in tb   # reset settles first
    assert "always #(`CLK_PERIOD/2)" not in tb
    assert "integer app_start;" not in tb   # no flush input
    # what the sim prints is what run_all_tiles.py parses into checked_from
    msg = re.search(r'\$display\("(replay: [^"]*)"', tb).group(1).replace("%0d", "2")
    assert load(RUN_ALL, "run_all_tiles").replay_result(msg)["checked_from"] == 2
    gt.create_testbench("Tile_MemCore", ["reset", "flush", "SB_IN"], ["SB_OUT"],
                        {"reset": 1, "flush": 1, "SB_IN": 17}, {"SB_OUT": 17}, 10, ["clk"], hold_reset=True)
    tb = (tmp_path / "testbench.sv").read_text()
    assert "test_vectors[app_start][`SLICE_FLUSH] !== 1'b1" in tb
    msgs = "\n".join(m.replace("%0d", str(c)) for m, c in
                     zip(re.findall(r'\$display\("(replay: [^"]*)"', tb), (2, 2404)))
    r = load(RUN_ALL, "run_all_tiles").replay_result(msgs)
    assert (r["checked_from"], r["app_start"]) == (2, 2404)


def test_testbench_saif_window_for_unstalled_tiles(tmp_path, monkeypatch):
    """cmd.tcl dumps the SAIF from saif_window, which rises at the tile's first
    stall release. The GLB stalls only the columns an app uses, so an idle tile
    elsewhere records stall 0 throughout (conv_3_3 A's Tile_X0F_Y10: its sim ran
    to $finish without a SAIF, "no power report"): its window opens where the
    design's other tiles are released."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "inputs").mkdir()
    (tmp_path / "inputs" / "manifest.json").write_text(json.dumps({"scope": "tb.dut"}))
    (tmp_path / "inputs" / "tile_ports.json").write_text(json.dumps(
        {"Tile_MemCore": {"inputs": [["clk", 1], ["reset", 1], ["stall", 1], ["SB_IN", 17]],
                          "outputs": [["SB_OUT", 17]]}}))
    (tmp_path / "inputs" / "tiles_Tile_MemCore.list").write_text("idle,0F,10\nhw,03,03\n")
    gt = load(TB_GEN, "generate_testbench")
    stall = {"Tile_X0F_Y10": [0, 0, 0, 0, 0, 0], "Tile_X03_Y03": [0, 1, 1, 0, 1, 0]}

    def fake_raw(tile, i, o):
        rows = [f"tb.dut.{tile}.stall[0:0],tb.dut.{tile}.SB_IN[16:0]"] + [f"{v},0" for v in stall[tile]]
        Path("raw_input.csv").write_text("\n".join(rows) + "\n")
        fake_raw.tile = tile
    monkeypatch.setattr(gt, "generate_raw", fake_raw)

    def fake_convert(signals, inp, out):
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text("0000\n" * 6)
        return 6, {s: 17 for s in signals}
    monkeypatch.setattr(gt, "convert_raw", fake_convert)
    monkeypatch.setenv("design_name", "Tile_MemCore")
    assert gt.stall_release("missing.csv") is None
    gt.main()
    assert gt.stall_release("raw_input.csv") == 3            # the last tile's CSV: X03_Y03
    tb = (tmp_path / "testbench.sv").read_text()
    # rises with stall (same address); the never-stalled fallback is X03_Y03's release
    assert "wire saif_window = (pt_addr >= app_window);" in tb
    assert "app_window = 3;  // never stalled (the other tiles' release)" in tb
    # no tile released at all: the first reset (no flush input here)
    gt.create_testbench("Tile_MemCore", ["reset", "stall", "SB_IN"], ["SB_OUT"],
                        {"reset": 1, "stall": 1, "SB_IN": 17}, {"SB_OUT": 17}, 6, ["clk"], hold_reset=True)
    assert "app_window = first_reset;" in (tmp_path / "testbench.sv").read_text()
    # the legacy testbench has no saif_window; cmd.tcl keeps its stall-count window for it
    gt.create_testbench("Tile_MemCore", ["reset", "stall", "SB_IN"], ["SB_OUT"],
                        {"reset": 1, "stall": 1, "SB_IN": 17}, {"SB_OUT": 17}, 6, ["clk"])
    assert "saif_window" not in (tmp_path / "testbench.sv").read_text()
    cmd = (MFLOWGEN / "common" / "testbench" / "cmd.tcl").read_text()
    assert "value $::env(testbench_name).saif_window" in cmd and "-object $::env(testbench_name).stall" in cmd
    assert "-condition [format {#%s.saif_window == 1} $::env(testbench_name)]" in cmd
    # the new display line is not a mismatch for run_all_tiles.py
    r = load(RUN_ALL, "run_all_tiles").replay_result("replay: power window opens at cycle 2389\n")
    assert r["mismatches"] == 0 and r["checked_from"] is None


@pytest.mark.parametrize("design,frac", [("Tile_MemCore", 0.2), ("Tile_PE", 0.3), ("Tile_Other", None)])
def test_testbench_sdc_input_timing(tmp_path, monkeypatch, design, frac):
    """Bundle replays drive passthrough inputs (config, stall, reset, flush) at
    the SDC's pt_i_delay and the rest at i_delay, not all at 0.2 ns (a PnR
    netlist's clock arrives ~0.2 ns late: config registers raced it)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "inputs").mkdir()
    (tmp_path / "inputs" / "manifest.json").write_text(json.dumps({"scope": "tb.dut"}))
    gt = load(TB_GEN, "generate_testbench")
    ins = ["reset", "flush", "config_config_data", "stall", "SB_IN"]
    gt.create_testbench(design, ins, ["SB_OUT"], {"reset": 1, "flush": 1, "config_config_data": 32, "stall": 1,
                                                  "SB_IN": 17}, {"SB_OUT": 17}, 10, ["clk"],
                        hold_reset=True, sdc_inputs=True)
    tb = (tmp_path / "testbench.sv").read_text()
    if frac is None:   # no SDC values for this design: inputs as before
        assert "pt_addr" not in tb and "wire [16:0] SB_IN = test_vectors[test_vector_addr]" in tb
        return
    assert f"`define IN_ASSIGNMENT_DELAY ({frac} * `CLK_PERIOD)" in tb
    assert "`define PT_ASSIGNMENT_DELAY 0.7" in tb
    assert "wire [16:0] SB_IN = test_vectors[in_addr][`SLICE_SB_IN];" in tb
    for pt in ("flush", "stall"):
        assert f"wire [0:0] {pt} = test_vectors[pt_addr][`SLICE_{pt.upper()}];" in tb
    assert "wire [31:0] config_config_data = test_vectors[pt_addr]" in tb
    assert "wire reset = test_vectors[pt_addr][`SLICE_RESET] | (pt_addr < first_reset);" in tb
    assert "in_addr <= # `IN_ASSIGNMENT_DELAY (test_vector_addr + 1);" in tb
    assert "pt_addr <= # `PT_ASSIGNMENT_DELAY (test_vector_addr + 1);" in tb


def test_testbench_fixed_input_delay(tmp_path, monkeypatch):
    """TILE_I_DELAY_NS (sweep_specs --i-delay-ns): the SDC's data-input delay in
    ns, so a replay drives the data inputs then, not at the fraction."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TILE_I_DELAY_NS", "0.15")
    (tmp_path / "inputs").mkdir()
    (tmp_path / "inputs" / "manifest.json").write_text(json.dumps({"scope": "tb.dut"}))
    gt = load(TB_GEN, "generate_testbench")
    gt.create_testbench("Tile_PE", ["reset", "SB_IN"], ["SB_OUT"], {"reset": 1, "SB_IN": 17},
                        {"SB_OUT": 17}, 10, ["clk"], hold_reset=True, sdc_inputs=True)
    assert "`define IN_ASSIGNMENT_DELAY 0.15\n" in (tmp_path / "testbench.sv").read_text()


@pytest.mark.parametrize("design", ["Tile_MemCore", "Tile_PE"])
def test_testbench_sdc_input_timing_matches_constraints(monkeypatch, tmp_path, design):
    """generate_testbench.py's input arrival times are copies of the tile SDC
    (constraints/common.tcl, onyx branch): fail when the two drift apart."""
    monkeypatch.chdir(tmp_path)
    gt = load(TB_GEN, "generate_testbench")
    tcl = (MFLOWGEN / design / "constraints" / "common.tcl").read_text()
    assert float(re.search(r"^set pt_i_delay ([0-9.]+)", tcl, re.M).group(1)) == gt.PT_INPUT_DELAY_NS
    # the last i_delay is the onyx one (Tile_PE sets the amber value first)
    fracs = re.findall(r"^set i_delay \[expr ([0-9.]+) \* \$\{clock_period\}\]", tcl, re.M)
    assert float(fracs[-1]) == gt.INPUT_DELAY_FRACTION[design]
    pt_block = re.search(r'^set pt_inputs \[get_ports "(.*?)"\]', tcl, re.M | re.S).group(1)
    pt = {p.rstrip("*") for p in pt_block.replace("\\", " ").split()}
    pt |= set(re.search(r"^set pt_read_data_inputs \[get_ports (\S+)\]", tcl, re.M).group(1).split())
    assert pt == set(gt.PT_INPUT_PREFIXES)
    for group in ("pt_inputs", "pt_read_data_inputs"):
        assert re.search(rf"set_input_delay -clock \$\{{clock_name\}} \$\{{pt_i_delay\}} \${group}\b", tcl), group


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


# ---------------------------------------------------------- gen_app_bundle --

def test_gen_app_bundle_dual_port_flag(tmp_path):
    """A dual-port spec's bundle needs garnet.py --dual-port (build + pnr), as
    the tile graphs get from DUAL_PORT; lake IndexErrors without it."""
    gab = load(APP / "gen_app_bundle.py", "gen_app_bundle")
    spec = tmp_path / "spec_config.json"
    for extra, flags in (({"dual_port": True}, ["--dual-port"]), ({"dual_port": False}, []), ({}, [])):
        spec.write_text(json.dumps(dict({"storage_capacity": 4096}, **extra)))
        assert gab.spec_garnet_flags(spec) == flags
    kw, mode, thesis = gab.sweep_config("fw2_dw16_sc4096_dp_in2_out2_vc2_rv")
    assert kw.get("dual_port") is True and mode == "rv" and not thesis
    kw, _, _ = gab.sweep_config("fw4_dw16_sc8192_sp_in2_out2_vc2")
    assert not kw.get("dual_port")


def test_gen_app_bundle_thesis_config():
    """A `_thesis` sweep config records on the thesis fabric: the spec without the
    sweep-only key, plus the thesis flag (garnet.py --thesis <mode>)."""
    gab = load(APP / "gen_app_bundle.py", "gen_app_bundle")
    for name, want in (("fw4_dw16_sc4096_sp_in2_out2_vc2_thesis", "static"),
                       ("fw4_dw16_sc4096_sp_in2_out2_vc2_ff8_portcg_thesis_rv", "rv")):
        kw, mode, thesis = gab.sweep_config(name)
        assert thesis and mode == want and "thesis" not in kw
    assert gab.THESIS_RV_PNR_ENV == {"DENSE_READY_VALID": "1"}   # no EXHAUSTIVE_PIPE


def test_cgra_app_power_thesis_bundle_tiles(tmp_path):
    """A thesis bundle replays on thesis tiles: THESIS_FABRIC for both tile graphs,
    and the spec for Tile_PE too (garnet.py --thesis needs it in both modes)."""
    from types import SimpleNamespace
    cap = load(MFLOWGEN / "cgra_app_power.py", "cgra_app_power")
    args = SimpleNamespace(flatten_effort=None, clock_mhz=400.0)
    for mode in ("static", "rv"):
        man = {"spec_config": {"storage_capacity": 4096}, "mode": mode, "thesis": mode}
        for tile in ("Tile_PE", "Tile_MemCore"):
            env = cap.tile_env(tile, tmp_path, man, [("A", tmp_path)], "cfg", args)
            assert env["THESIS_FABRIC"] == mode and env["LAKE_SPEC_MODE"] == mode
            assert env["LAKE_SPEC_CONFIG"] == str(tmp_path / "spec_config.json")
    man = {"spec_config": {"storage_capacity": 4096}, "mode": "static"}
    env = cap.tile_env("Tile_PE", tmp_path, man, [("A", tmp_path)], "cfg", args)
    assert "THESIS_FABRIC" not in env and "LAKE_SPEC_CONFIG" not in env


def test_cgra_app_power_builds_pe_with_the_bundles_pond(tmp_path):
    """A bundle recorded with a PE-tile spec pond (--pond-spec) must replay on a
    Tile_PE built with it: cgra_app_power.py sets LAKE_POND_SPEC_CONFIG."""
    from types import SimpleNamespace
    cap = load(MFLOWGEN / "cgra_app_power.py", "cgra_app_power")
    args = SimpleNamespace(flatten_effort=None, clock_mhz=750.0)
    man = {"spec_config": {"storage_capacity": 8192}, "mode": "static", "pond_spec": {}}
    pe = cap.tile_env("Tile_PE", tmp_path, man, [("A", tmp_path)], "cfg", args)
    assert pe["LAKE_POND_SPEC_CONFIG"] == str(tmp_path / "pond_spec.json")
    assert "LAKE_POND_SPEC_CONFIG" not in cap.tile_env("Tile_MemCore", tmp_path, man, [("A", tmp_path)], "cfg", args)
    man["pond_spec"] = None
    assert "LAKE_POND_SPEC_CONFIG" not in cap.tile_env("Tile_PE", tmp_path, man, [("A", tmp_path)], "cfg", args)


def test_cgra_app_power_any_config(tmp_path):
    """Default: configs every variant has; --any-config: configs any variant
    has, each with the variants that have it (one variant per app, where some
    apps fail on some specs)."""
    cap = load(MFLOWGEN / "cgra_app_power.py", "cgra_app_power")
    for v, cfgs in (("A", ("c1", "c2")), ("B", ("c1",))):
        for c in cfgs:
            (tmp_path / v / c).mkdir(parents=True)
            (tmp_path / v / c / "manifest.json").write_text("{}")
    variants = [("A", tmp_path / "A"), ("B", tmp_path / "B")]
    assert cap.configs_of(variants, []) == ["c1"]
    assert cap.configs_of(variants, [], any_config=True) == ["c1", "c2"]
    assert [v for v, _ in cap.variants_of(variants, "c1")] == ["A", "B"]
    assert [v for v, _ in cap.variants_of(variants, "c2")] == ["A"]
    with pytest.raises(SystemExit):
        cap.configs_of(variants, ["c2"])           # B has no c2
    assert cap.configs_of(variants, ["c2"], any_config=True) == ["c2"]
