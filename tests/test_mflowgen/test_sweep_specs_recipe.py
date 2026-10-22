"""sweep_specs.py --recipe and the tile-variant configs it builds
(mflowgen/CLAUDE.md "The sweep driver"): stock tiles, the PE pond knob, the
static fabric, Tile_PE's clock, and the parts of the thesis recipe.
"""
import importlib.util
import json
import sys
import zipfile
from argparse import Namespace
from pathlib import Path

import pytest

MFLOWGEN = Path(__file__).resolve().parents[2] / "mflowgen"


@pytest.fixture(scope="module")
def ss():
    spec = importlib.util.spec_from_file_location("sweep_specs", MFLOWGEN / "sweep_specs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def listed(ss, capsys, *argv):
    assert ss.main([*argv, "--list"]) == 0
    return capsys.readouterr().out.split()


def test_pe_tile_and_fabric_names(ss, capsys):
    assert listed(ss, capsys, "--spec-set", "pe_tile", "--runtime-mode", "static,rv") == [
        "stock_specpond", "stock_nopond", "fw4_dw16_sc4096_sp_in2_out2_vc2_rv",
        "fw4_dw16_sc4096_sp_in2_out2_vc2_nopond_rv", "stock_staticfab_nopond"]
    assert listed(ss, capsys, "--spec-set", "fabric") == ["stock", "stock_staticfab"]
    # the PnR preset names exist (_resolve_names checks them)
    names = listed(ss, capsys, "--spec-set", "pe_tile", "--pnr-set", "pe_tile_pnr")
    assert set(ss.PRESETS["pe_tile_pnr"]) <= set(names)


def test_stock_tiles_have_no_rv(ss):
    assert ss._unsupported_reason({"stock": True}, "rv")
    assert ss._unsupported_reason({"fabric": "static"}, "rv")
    assert ss._unsupported_reason({"stock": True}, "static") is None


def test_bad_knob_values(ss):
    args = ss.build_argparser().parse_args([])
    args.modes = ["static"]
    args.extra_specs = None
    args.replace = False
    ss.SPEC_SETS["_bad"] = [dict(pond="lake")]
    try:
        args.spec_set = "_bad"
        with pytest.raises(SystemExit, match="pond"):
            ss._collect_configs(args)
    finally:
        del ss.SPEC_SETS["_bad"]


def env_for(ss, tmp_path, monkeypatch, cfg, *argv):
    monkeypatch.setenv("LAKE_SPEC_CONFIG", "/inherited.json")
    monkeypatch.setenv("LAKE_SPEC_MODE", "rv")
    args = ss.build_argparser().parse_args(list(argv))
    return ss._tile_env(cfg, tmp_path, args)


def test_tile_env_stock_static_fabric(ss, tmp_path, monkeypatch):
    env = env_for(ss, tmp_path, monkeypatch, dict(fabric="static", pond="none"))
    assert "LAKE_SPEC_CONFIG" not in env and "LAKE_SPEC_MODE" not in env
    assert env["DENSE_ONLY"] == "True" and env["NO_POND"] == "True"


def test_tile_env_spec_pond(ss, tmp_path, monkeypatch):
    env = env_for(ss, tmp_path, monkeypatch, dict(stock=True, pond="spec"))
    assert env["LAKE_POND_SPEC_CONFIG"] == str(tmp_path / ss.POND_SPEC_FILE)
    assert "DENSE_ONLY" not in env and "NO_POND" not in env and "LAKE_SPEC_CONFIG" not in env


def test_tile_env_spec_config_unchanged(ss, tmp_path, monkeypatch):
    env = env_for(ss, tmp_path, monkeypatch, dict(runtime_mode="rv"))
    assert env["LAKE_SPEC_CONFIG"] == str(tmp_path / "spec_config.json")
    assert env["LAKE_SPEC_MODE"] == "rv"
    assert not {"DENSE_ONLY", "NO_POND", "LAKE_POND_SPEC_CONFIG"} & set(env)


@pytest.mark.parametrize("graph,key", [("Tile_PE", "clock_period_PE"),
                                       ("Tile_MemCore", "CLOCK_PERIOD")])
def test_clock_goes_to_the_graphs_env_var(ss, tmp_path, monkeypatch, graph, key):
    env = env_for(ss, tmp_path, monkeypatch, dict(stock=True),
                  "--graph", str(MFLOWGEN / graph), "--clock-mhz", "400")
    assert env[key] == "2.5"
    assert not {"CLOCK_PERIOD", "clock_period_PE"} - {key} & set(env)


def test_spec_files_record_the_knobs(ss, tmp_path):
    ss._write_spec_files(dict(stock=True, pond="spec", runtime_mode="static"), tmp_path,
                         "make-this", graph="Tile_PE")
    assert json.loads((tmp_path / "spec_config.json").read_text()) == {}
    assert json.loads((tmp_path / ss.POND_SPEC_FILE).read_text()) == {}
    meta = json.loads((tmp_path / "sweep_meta.json").read_text())
    assert meta["graph"] == "Tile_PE" and meta["pond"] == "spec" and meta["stock"] is True
    row = ss._sweep_meta(tmp_path, meta["config_name"])
    assert row["graph"] == "Tile_PE" and row["pond"] == "spec"


def test_meta_columns_only_when_present(ss):
    old = [{"config_name": "a"}, {"config_name": "b"}]
    ss._fill_meta_columns(old)
    assert old == [{"config_name": "a"}, {"config_name": "b"}]
    new = [{"config_name": "a", "graph": "Tile_PE"}, {"config_name": "b"}]
    ss._fill_meta_columns(new)
    assert new[1]["graph"] == ""


def test_new_param_off_is_not_stale(ss):
    built = {"no_pond": "False"}
    assert ss._new_param_off("dense_only", built, {"dense_only": "False"})
    assert ss._new_param_off("lake_pond_spec_config", built, {"lake_pond_spec_config": ""})
    assert not ss._new_param_off("dense_only", built, {"dense_only": "True"})
    assert not ss._new_param_off("no_pond", built, {"no_pond": "True"})


def test_stale_check_ignores_a_new_off_param(ss, tmp_path):
    def run_script(path, params):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(f"export {k}={v}\n" for k, v in params.items()))
    run_script(tmp_path / "4-rtl" / "mflowgen-run", {"no_pond": "False"})
    (tmp_path / "4-rtl" / ".execstamp").write_text("")
    run_script(tmp_path / ".mflowgen" / "4-rtl" / "mflowgen-run",
               {"no_pond": "False", "dense_only": "False"})
    assert ss._stale_steps(tmp_path) == []
    run_script(tmp_path / ".mflowgen" / "4-rtl" / "mflowgen-run",
               {"no_pond": "False", "dense_only": "True"})
    assert ss._stale_steps(tmp_path) == [("4-rtl", "dense_only None->True")]


def test_recipe_passthrough(ss):
    argv = ["--recipe", "thesis", "--out=/o", "--config-jobs", "4", "--app-bundles", "/b",
            "--zip", "--recipe=pe_tile", "--out-dir", "/o2", "--zip-slim"]
    assert ss._recipe_passthrough(argv) == ["--config-jobs", "4", "--zip", "--zip-slim"]


def test_recipe_runs_each_part(ss, monkeypatch, tmp_path):
    calls = []
    real_main = ss.main
    monkeypatch.setattr(ss, "main", lambda argv: calls.append(argv) or 0)
    args = ss.build_argparser().parse_args(["--recipe", "thesis", "--out-dir", str(tmp_path),
                                            "--pnr-jobs", "2"])
    assert ss._run_recipe(args, ["--recipe", "thesis", "--out-dir", str(tmp_path),
                                 "--pnr-jobs", "2"]) == 0
    assert [c[-1] for c in calls] == [str(tmp_path / p) for p in ("fabric_mem", "pe_tile", "memtile")]
    for part, c in zip(("fabric_mem", "pe_tile", "memtile"), calls):
        assert c[:len(ss.RECIPE_FLAGS[part])] == ss.RECIPE_FLAGS[part]
        assert c[len(ss.RECIPE_FLAGS[part]):] == ["--pnr-jobs", "2", "--out-dir", str(tmp_path / part)]
    monkeypatch.setattr(ss, "main", real_main)


def test_recipe_part_failure_keeps_going(ss, monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(ss, "main", lambda argv: calls.append(argv) or (1 if "fabric" in argv else 0))
    args = ss.build_argparser().parse_args(["--recipe", "thesis", "--out-dir", str(tmp_path)])
    assert ss._run_recipe(args, []) == 1
    assert len(calls) == 3


def bundles(root, apps, configs):
    for app in apps:
        for c in configs:
            (root / app / c).mkdir(parents=True)
            (root / app / c / "manifest.json").write_text("{}")


def test_app_power_command(ss, monkeypatch, tmp_path):
    bundles(tmp_path / "b", ["conv_3_3", "gaussian"], ["fw4_dw16_sc8192_sp_in2_out2_vc2"])
    (tmp_path / "b" / "notes").mkdir()
    ran = []
    monkeypatch.setattr(ss.subprocess, "run", lambda cmd, **kw: ran.append(cmd) or Namespace(returncode=0))
    args = ss.build_argparser().parse_args(["--recipe", "app_power", "--out-dir", str(tmp_path),
                                            "--app-bundles", str(tmp_path / "b"), "--zip"])
    assert ss._run_recipe(args, []) == 0
    (cmd,) = ran
    assert cmd[1].endswith("cgra_app_power.py")
    assert cmd[cmd.index("--variants") + 1] == (f"conv_3_3={tmp_path / 'b' / 'conv_3_3'},"
                                                f"gaussian={tmp_path / 'b' / 'gaussian'}")
    assert cmd[cmd.index("--clock-mhz") + 1] == str(ss.APP_POWER_MHZ)
    assert cmd[cmd.index("--out-dir") + 1] == str(tmp_path / "app_power")
    assert "--any-config" in cmd and "--zip" in cmd


def test_app_power_one_app_dir_and_skip(ss, tmp_path):
    bundles(tmp_path, ["conv-3-3"], ["c1"])
    assert ss._app_power_variants(tmp_path / "conv-3-3") == [("conv_3_3", tmp_path / "conv-3-3")]
    args = ss.build_argparser().parse_args(["--recipe", "app_power", "--out-dir", str(tmp_path)])
    assert ss._run_app_power(args, tmp_path / "app_power") == 0   # no --app-bundles: skipped


def test_app_bundles_needs_a_recipe(ss, capsys):
    assert ss.main(["--app-bundles", "/x", "--list"]) == 2


def test_memtile_power_needs_memtile_graph(ss):
    args = ss.build_argparser().parse_args(["--graph", str(MFLOWGEN / "Tile_PE"), "--memtile-power",
                                            "--dry-run"])
    with pytest.raises(SystemExit, match="memtile-power"):
        ss._preflight(args)
    assert ss._memtile_power_targets(dict(stock=True), Namespace(memtile_power=True)) == []


def test_relative_graph_is_made_absolute(ss, capsys, monkeypatch, tmp_path):
    """`mflowgen run --design` runs inside the workspace, so --graph
    ./mflowgen/Tile_PE given from the garnet checkout must reach it absolute."""
    monkeypatch.chdir(MFLOWGEN.parent)
    assert ss.main(["--graph", "./mflowgen/Tile_PE", "--spec-set", "pe_tile", "--only", "stock_specpond",
                    "--out-dir", str(tmp_path / "out"), "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert f"mflowgen run --design {MFLOWGEN / 'Tile_PE'}" in out


def test_dw8_32_64_preset_is_the_thesis_set_at_those_widths(ss, capsys):
    names = listed(ss, capsys, "--spec-set", "thesis", "--data-width", "8,32,64", "--runtime-mode", "static,rv")
    assert len(names) == 24
    assert sorted(ss.PRESETS["dw8_32_64"]) == sorted(names)


def test_thesis_mem_opt_recipe(ss, capsys, tmp_path):
    """thesis_mem_opt: the thesis MemTile with lake's options, all three through PnR:
    static with clock gating, RV with clock gating and the filter path as an 8-deep
    FIFO, RV with clock gating and no filter path. Not part of thesis_fabric."""
    assert listed(ss, capsys, "--spec-set", "thesis_fabric_opt") == ss.PRESETS["thesis_opt_pnr"]
    assert ss.main(ss.RECIPE_FLAGS["thesis_mem_opt"] + ["--out-dir", str(tmp_path), "--list"]) == 0
    assert "3 -> synopsys-pt-timing-signoff" in capsys.readouterr().err
    assert "thesis_mem_opt" not in ss.RECIPES["thesis_fabric"]
    static, ff8, nofp = ss.THESIS_OPT_SPEC_POINTS
    for cfg, keys in ((static, {"share_clk_ctr": True, "clock_gate_ports": True}),
                      (ff8, {"clock_gate_ports": True, "filter_fifo_depth": 8}),
                      (nofp, {"clock_gate_ports": True, "add_filter_path": False})):
        ws = tmp_path / ss._config_name(cfg)
        ws.mkdir()
        ss._write_spec_files(cfg, ws, "make-this")
        spec = json.loads((ws / "spec_config.json").read_text())
        assert {k: spec[k] for k in keys} == keys and "thesis" not in spec


def test_thesis_opt_recipe_and_pe_clock(ss):
    """thesis_opt = the three optimized MemTiles + the thesis PE pair; the PE pair
    runs at the pe_tile/app-power clock, which it can meet, not Tile_PE's 1.1 ns."""
    assert ss.RECIPES["thesis_opt"] == ["thesis_mem_opt", "thesis_pe"]
    flags = ss.RECIPE_FLAGS["thesis_pe"]
    assert flags[flags.index("--clock-mhz") + 1] == str(ss.APP_POWER_MHZ)
    assert "--clock-mhz" not in ss.RECIPE_FLAGS["thesis_mem_opt"]


def test_thesis_memtiles_get_power(ss, capsys, tmp_path):
    """The thesis MemTile recipes run the idle/active power tests (their test
    generator builds the thesis fabric); the PE part has none (Tile_PE)."""
    for part in ("thesis_mem", "thesis_mem_opt"):
        assert "--memtile-power" in ss.RECIPE_FLAGS[part]
    assert "--memtile-power" not in ss.RECIPE_FLAGS["thesis_pe"]
    assert ss.main(ss.RECIPE_FLAGS["thesis_mem_opt"] + ["--out-dir", str(tmp_path), "--list"]) == 0
    assert "memtile-power-pnr-idle" in capsys.readouterr().err


def test_no_filter_path_knob(ss):
    base = dict(storage_capacity=4096, add_filter_path=False)
    assert ss._config_name(dict(base, runtime_mode="rv")) == "fw4_dw16_sc4096_sp_in2_out2_vc2_nofp_rv"
    assert ss._unsupported_reason(base, "rv") is None
    assert "build_spec_rv" in ss._unsupported_reason(base, "static")
    assert ss._unsupported_reason(dict(base, filter_fifo_depth=8), "rv")
    # unset = the filter path as built: names and spec identity unchanged
    assert ss._config_name(dict(storage_capacity=4096, runtime_mode="rv")) == "fw4_dw16_sc4096_sp_in2_out2_vc2_rv"
    assert ss._spec_key({}) == ss._spec_key({"add_filter_path": True})


@pytest.mark.parametrize("extra, summary", [
    ([], ["36 -> synopsys-pt-timing-signoff", "160 -> cadence-genus-synthesis",
          "PnR model: fit on 8, validated on 28 held-out"]),
    (["--preset", "dw8_32_64"], ["24 -> synopsys-pt-timing-signoff", "PnR model: fit on 0, validated on 24 held-out"]),
    (["--preset", "memtile_pnr"], ["36 -> synopsys-pt-timing-signoff", "PnR model: fit on 8, validated on 28 held-out"]),
])
def test_memtile_recipe_pnr_at_every_width_dw16_fit_only(ss, capsys, tmp_path, extra, summary):
    """The memtile part builds every dw 8/32/64 config through PnR, held out
    of the synth->PnR fit, which stays the 8 dw16_fit8 configs."""
    assert ss.main(ss.RECIPE_FLAGS["memtile"] + extra + ["--out-dir", str(tmp_path), "--list"]) == 0
    err = capsys.readouterr().err
    for line in summary:
        assert line in err


def test_zip_has_pnr_and_synth_reports(ss, tmp_path, monkeypatch):
    """--zip carries every Innovus step's reports (timeDesign's per-group .tarpt
    path reports, not only signoff.summary) and every Genus report; a report over
    REPORT_ZIP_MAX is left out, not the whole zip."""
    ws = tmp_path / "out" / "cfg"
    reports = ["24-cadence-innovus-signoff/reports/signoff.summary",
               "24-cadence-innovus-signoff/reports/signoff_in2reg.tarpt",
               "24-cadence-innovus-signoff/reports/timingReports/signoff_all.tarpt.gz",
               "20-cadence-innovus-cts/reports/cts.summary",
               "19-cadence-innovus-place/reports/place.congestion.rpt",
               "14-cadence-genus-synthesis/reports/qor.rpt",
               "14-cadence-genus-synthesis/results_syn/final_time_default_c.rpt",
               "14-cadence-genus-synthesis/results_syn/syn_power.rpt"]
    for r in reports + ["spec_config.json", "22-cadence-innovus-route/reports/huge.tarpt",
                        "22-cadence-innovus-route/outputs/design.def"]:
        (ws / r).parent.mkdir(parents=True, exist_ok=True)
        (ws / r).write_text("x" * (100 if "huge" in r else 1))
    monkeypatch.setattr(ss, "REPORT_ZIP_MAX", 50)
    args = Namespace(zip_slim=True, zip_path=str(tmp_path / "out.zip"), dry_run=False)
    assert ss._zip_results(tmp_path / "out", None, args)
    names = {n.split("/", 1)[1] for n in zipfile.ZipFile(tmp_path / "out.zip").namelist()}
    assert {f"cfg/{r}" for r in reports} <= names
    assert "cfg/22-cadence-innovus-route/reports/huge.tarpt" not in names
    assert "cfg/22-cadence-innovus-route/outputs/design.def" not in names


def test_rtl_only_memtile_power_makes_the_container_steps(ss, capsys, tmp_path):
    """--rtl-only --memtile-power makes rtl + memtile-power-test-gen (the two
    docker steps) on the full run's graph, so the full run needs no docker."""
    argv = ss.RECIPE_FLAGS["memtile"] + ["--preset", "memtile_pnr", "--out-dir", str(tmp_path)]
    assert ss.main(argv + ["--rtl-only", "--list"]) == 0
    assert "36 -> rtl memtile-power-test-gen" in capsys.readouterr().err
    assert ss.main(argv + ["--rtl-only", "--only", "fw4_dw32_sc8192_sp_in2_out2_vc2", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "DRY-RUN cmd: make rtl" in out
    assert "DRY-RUN cmd: make memtile-power-test-gen" in out
    assert "MEMTILE_POWER" in out
    # The full run's settings (what --skip-existing compares) don't depend on --rtl-only.
    args = ss.build_argparser().parse_args(argv)
    cfg = dict(storage_capacity=8192, data_width=32, vec_width=4, in_ports=2, out_ports=2, vec_capacity=2,
               runtime_mode="static")
    full = ss._build_settings(ss._tile_env(cfg, tmp_path, args))
    args.rtl_only = True
    assert ss._build_settings(ss._tile_env(cfg, tmp_path, args)) == full
