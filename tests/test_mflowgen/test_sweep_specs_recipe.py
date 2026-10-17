"""sweep_specs.py --recipe and the tile-variant configs it builds
(mflowgen/CLAUDE.md "The sweep driver"): stock tiles, the PE pond knob, the
static fabric, Tile_PE's clock, and the parts of the thesis recipe.
"""
import importlib.util
import json
import sys
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
